import asyncio
from bisect import bisect_left
from dataclasses import dataclass
import datetime as dt
from decimal import Decimal
from httpx import ConnectError
from typing import Dict, List
import certifi
import httpx
import ssl
from optrabot.exceptions.orderexceptions import PlaceOrderException, PrepareOrderException
from optrabot.optionhelper import OptionHelper
from optrabot.broker.optionpricedata import OptionStrikeData, OptionStrikePriceData
from optrabot.broker.brokerconnector import BrokerConnector
from pydantic import ValidationError
from loguru import logger
from datetime import date, timedelta
import re
from tastytrade import Account, AlertStreamer, DXLinkStreamer, Session
from optrabot.models import Account as ModelAccount
from tastytrade.instruments import NestedOptionChain, NestedOptionChainExpiration, Strike
from tastytrade.utils import TastytradeError
from tastytrade.dxfeed import Greeks, Quote, Candle
from tastytrade.instruments import Option, OptionType
from tastytrade.order import NewOrder, NewComplexOrder, OrderTimeInForce, OrderType, OrderAction, PlacedOrder, OrderStatus
import optrabot.config as optrabotcfg
from optrabot.broker.order import OptionRight, Order as GenericOrder, OrderAction as GenericOrderAction, Leg as GenericOrderLeg, OrderStatus as GenericOrderStatus, PriceEffect
from optrabot.tradetemplate.templatefactory import Template
import optrabot.symbolinfo as symbolInfo
from optrabot.managedtrade import ManagedTrade
from websockets import ConnectionClosedOK, ConnectionClosedError

@dataclass
class TastySymbolData:
	def __init__(self) -> None:
		self.symbol: str = None
		self.tastySymbol: str = None
		self.noPriceDataCount: int = 0
		self.optionPriceData: Dict[dt.date, OptionStrikeData] = {}
		self.chain: NestedOptionChain = None
		self.lastPrice: float = 0
		self.lastAtmStrike: float = 0

class TastytradeConnector(BrokerConnector):
	task_listen_quotes: asyncio.Task = None

	def __init__(self) -> None:
		super().__init__()
		self._username = ''
		self._password = ''
		self._sandbox = False
		self._initialize()
		self.id = 'TASTY'
		self.broker = 'TASTY'
		self._orders: List[GenericOrder] = []
		self._replacedOrders: List[PlacedOrder] = []
		self._is_disconnecting = False
		self._session = None
		self._streamer: DXLinkStreamer = None
		self._alert_streamer: AlertStreamer = None
		self._quote_symbols = []
		self._candle_symbols = []
		self._greeks_symbols = []
		self._tasty_accounts: List[Account] = []
		self._symbolData: Dict[str, TastySymbolData] = {}
		self._symbolReverseLookup: Dict[str, str] = {}		# maps tastytrade symbol to generic symbol

		self.task_listen_quotes = None
		self.task_listen_accounts = None
		self.task_listen_greeks = None
		self.task_listen_candle = None

	def _initialize(self):
		"""
		Initialize the Tastytrade connector from the configuration
		"""
		if not optrabotcfg.appConfig:
			return
		
		config :optrabotcfg.Config = optrabotcfg.appConfig
		try:
			config.get('tastytrade')
		except KeyError as keyErr:
			logger.debug('No Tastytrade connection configured')
			return
		
		try:
			self._username = config.get('tastytrade.username')
		except KeyError as keyErr:
			logger.error('Tastytrade username not configured')
			return
		try:
			self._password = config.get('tastytrade.password')
		except KeyError as keyErr:
			logger.error('Tastytrade password not configured')
			return
		
		try:
			self._sandbox = config.get('tastytrade.sandbox')
		except KeyError as keyErr:
			pass
		self._initialized = True

	async def cancel_order(self, order: GenericOrder):
		""" 
		Cancels the given order
		"""
		await super().cancel_order(order)
		tasty_order: PlacedOrder = order.brokerSpecific['order']
		account: Account = order.brokerSpecific['account']
		logger.debug(f'Cancelling order {tasty_order.id}')
		account.delete_order(self._session, tasty_order.id)

	async def connect(self):
		await super().connect()
		self._is_disconnecting = False
		try:
			self._session = Session(self._username, self._password, is_test=self._sandbox)
			await self.set_trading_enabled(True, "Broker connected")
			self._emitConnectedEvent()
		except TastytradeError as tastyErr:
			logger.error('Failed to connect to Tastytrade: {}', tastyErr)
			self._emitConnectFailedEvent()
		except ConnectError as connect_error:
			logger.debug(f'Failed to connect to Tastytrade - network connection error')
			self._emitConnectFailedEvent()

	async def _disconnect_internal(self):
		"""
		Perform the operations for disconnecting from Tastytrade
		"""
		self._is_disconnecting = True
		await self.set_trading_enabled(False, "Broker disconnected")

		tasks_to_cancel = [
			self.task_listen_quotes,
			self.task_listen_greeks,
			self.task_listen_candle,
			self.task_listen_accounts
		]

		for task in tasks_to_cancel:
			if task:
				try:
					task.cancel()
					task = None
				except Exception as exc:
					logger.debug(f'Error cancelling task {task}: {exc}')

		if self._streamer:
			try:
				await asyncio.wait_for(self._streamer.close(), timeout=2.0)
			except asyncio.TimeoutError as exc:
				logger.debug(f'Timeout while closing the streamer {exc}')
			except asyncio.CancelledError:
				pass
			except ConnectionClosedError:
				pass
			self._streamer = None
				
		if self._alert_streamer:
			try:
				#await asyncio.shield(self._alert_streamer.close())
				await asyncio.wait_for(self._alert_streamer.close(), timeout=2.0)
			except asyncio.TimeoutError as exc:
				logger.debug(f'Timeout while closing the streamer {exc}')	
			except asyncio.CancelledError:
				pass
			except ConnectionClosedError:
				pass
			except httpx.ReadTimeout:
				pass
			self._alert_streamer = None
			
		if self._session:
			try:
				self._session.destroy()
			except ConnectError:
				pass
			self._session = None
		
		self._emitDisconnectedEvent()

	async def disconnect(self):
		await super().disconnect()
		await self._disconnect_internal()

	def getAccounts(self) -> List[ModelAccount]:
		"""
		Returns the Tastytrade accounts and starts the account update task for listening to updates on orders
		"""
		if len(self._managedAccounts) == 0 and self.isConnected():
			self._tasty_accounts = Account.get(self._session)
			for tastyAccount in self._tasty_accounts:
				account = ModelAccount(id = tastyAccount.account_number, name = tastyAccount.nickname, broker = self.broker, pdt = not tastyAccount.day_trader_status)
				self._managedAccounts.append(account)

			asyncio.create_task(self._request_account_updates())
		return self._managedAccounts
	
	def isConnected(self) -> bool:
		if self._session != None:
			return True
		
	async def prepareOrder(self, order: GenericOrder, need_valid_price_data: bool = True) -> None:
		"""
		Prepares the given order for execution

		Raises:
			PrepareOrderException: If the order preparation fails with a specific reason.
		"""
		symbolData = self._symbolData[order.symbol]
		comboLegs: list[GenericOrderLeg] = []
		for leg in order.legs:
			try:
				optionPriceData = symbolData.optionPriceData[leg.expiration]
			except KeyError as keyErr:
				raise PrepareOrderException(f'No option price data for expiration date {leg.expiration} available!', order)

			optionInstrument: Option = None
			try:
				priceData: OptionStrikePriceData = optionPriceData.strikeData[leg.strike]
				if not priceData.is_outdated():
					if leg.right == OptionRight.CALL:
						leg.askPrice = float(priceData.callAsk)
						if leg.askPrice == None:
							leg.askPrice = 0
						leg.bidPrice = float(priceData.callBid)
						if leg.bidPrice == None:
							leg.bidPrice = 0
						optionInstrument = Option.get(self._session, priceData.brokerSpecific['call_option'])
					elif leg.right == OptionRight.PUT:
						leg.askPrice = float(priceData.putAsk)
						if leg.askPrice == None:
							leg.askPrice = 0
						leg.bidPrice = float(priceData.putBid)
						if leg.bidPrice == None:
							leg.bidPrice = 0
						optionInstrument = Option.get(self._session, priceData.brokerSpecific['put_option'])
				elif need_valid_price_data:
					raise PrepareOrderException(f'Price data for strike {leg.strike} is outdated or not available!', order)

			except KeyError as keyErr:
				# No data for strike available
				raise PrepareOrderException(f'No option price data for strike {leg.strike} available!', order)
			except Exception as excp:
				raise PrepareOrderException(f'Error preparing order: {excp}', order)
			
			# Build the leg for the tasty trade order
			comboLeg = optionInstrument.build_leg(quantity=Decimal(leg.quantity * order.quantity), action=self._mappedOrderAction(order.action, leg.action))
			comboLegs.append(comboLeg)

		order.brokerSpecific['comboLegs'] = comboLegs
		order.determine_price_effect()
		return True
	
	def _transform_generic_order(self, generic_order: GenericOrder) -> NewOrder:
		"""
		Transforms the given generic order to a tastytrade order
		"""
		new_order_legs = generic_order.brokerSpecific['comboLegs']
		price = abs(generic_order.price)
		tasty_price = Decimal(price * -1 if generic_order.price_effect == PriceEffect.DEBIT else price)
		rounded_tasty_price: Decimal = round(tasty_price, 2)
		new_order = None
		if generic_order.type == OrderType.LIMIT:
			new_order = NewOrder(
				time_in_force=OrderTimeInForce.DAY,
				order_type=generic_order.type,	
				legs=new_order_legs,
				price=rounded_tasty_price
			)
		elif generic_order.type == OrderType.STOP:
			if len(generic_order.legs) == 1:
				new_order = NewOrder(
					time_in_force=OrderTimeInForce.DAY,
					order_type=generic_order.type,	
					legs=new_order_legs,
					stop_trigger=rounded_tasty_price
				)
			else:
				# Stop Orders with multiple legs must be Stop Limit Orders
				calculated_limit_price = OptionHelper.roundToTickSize(round(rounded_tasty_price * Decimal('1.25'), 2))  # Round to the nearest tick size
				tasty_limit_price: Decimal = Decimal(calculated_limit_price)
				
				new_order = NewOrder(
					time_in_force=OrderTimeInForce.DAY,
					order_type=OrderType.STOP_LIMIT,
					legs=new_order_legs,
					stop_trigger=Decimal(abs(rounded_tasty_price)),
					price=tasty_limit_price
				)
		return new_order
	
	async def placeOrder(self, managed_trade: ManagedTrade, order: GenericOrder, parent_order: GenericOrder = None) -> None:
		""" 
		Places the given order for a managed account via the broker connection.
		
		Raises:
			PlaceOrderException: If the order placement fails with a specific reason.
		"""
		account = Account.get(self._session, managed_trade.template.account)
		newOrder = self._transform_generic_order(order)
		try:
			response = account.place_order(self._session, newOrder, dry_run=False)
			#placedComplexOrders = account.get_live_complex_orders(session=self._session)
			#placedOrders = account.get_live_orders(session=self._session)
			#for order in placedOrders:
			#	logger.debug(f'Live order: {order.id} underlying: {order.underlying_symbol}')
			#	#account.delete_order(session=self._session, order_id=order.id)
			logger.debug(f'Response of place Order: {response}')
			if response.errors:
				for errorMessage in response.errors:
					raise PlaceOrderException(errorMessage, order=order)
			if response.warnings:
				for warningMessage in response.warnings:
					logger.warning(f'Warning placing order: {warningMessage}')
			
			order.brokerSpecific['order'] = response.order
			order.brokerSpecific['account'] = account
			self._orders.append(order)
			logger.debug(f'Order {response.order.id} placed successfully')
		except TastytradeError as tastyErr:
			raise PlaceOrderException(f'{tastyErr}', order=order)
		except ValidationError as valErr:
			logger.error(f'Validation error placing order: {valErr}')
			err = valErr.errors()[0]
			logger.error(err)
		except Exception as exc:
			raise PlaceOrderException(f'{exc}', order=order)

	async def place_complex_order(self, take_profit_order: GenericOrder, stop_loss_order: GenericOrder, template: Template) -> bool:
		"""
		Places the Take Profit and Stop Loss Order as complex order
		"""
		account = Account.get(self._session, template.account)
		new_order_tp = self._transform_generic_order(take_profit_order)
		new_order_sl = self._transform_generic_order(stop_loss_order)
		oco_order = NewComplexOrder( orders=[ new_order_tp, new_order_sl ] )
		try:
			dry_run = False
			response = account.place_complex_order(self._session, oco_order, dry_run=dry_run)
			logger.debug(f'Response of place_complex_order: {response}')
			if response.errors:
				for errorMessage in response.errors:
					logger.error(f'Error placing order: {errorMessage}')
					return False
			if response.warnings:
				for warningMessage in response.warnings:
					logger.warning(f'Warning placing order: {warningMessage}')
			
			try:
				take_profit_order.brokerSpecific['order'] = response.complex_order.orders[0]
				take_profit_order.brokerSpecific['account'] = account
				self._orders.append(take_profit_order)
			except IndexError as indexErr:
				logger.error(f'Error complex order. Take Profit order not found in complex order response!')
				return False

			try: 
				stop_loss_order.brokerSpecific['order'] = response.complex_order.orders[1]
				stop_loss_order.brokerSpecific['account'] = account
				self._orders.append(stop_loss_order)
			except IndexError as indexErr:
				logger.error(f'Error complex order. Stop Loss order not found in complex order response!')
				return False

			logger.debug(f'Complex Order {response.complex_order.id} placed successfully')
			return True
		except TastytradeError as tastyErr:
			logger.error(f'Error placing order: {tastyErr}')
		except ValidationError as valErr:
			logger.error(f'Validation error placing order: {valErr}')
			err = valErr.errors()[0]
			logger.error(err)
			#logger.error(repr(valErr.errors()[0]['type']))
		except Exception as exc:
			logger.error(f'Unexpected exception placing order: {exc}')
			
		return False		
		
	async def adjustOrder(self, managed_trade: ManagedTrade, order: GenericOrder, price: float) -> bool:
		""" 
		Adjusts the given order with the given new price
		"""
		if order.status == GenericOrderStatus.FILLED:
			logger.info('Order {} is already filled. Adjustment not required.', order)
			return True
		try:
			tasty_order: PlacedOrder = order.brokerSpecific['order']
		except KeyError as keyErr:
			logger.error(f'Order {order.id} not prepared for adjustment. Cannot adjust order.')
			return False
		
		account: Account = order.brokerSpecific['account']
		logger.debug(f'Adjusting order {tasty_order.id} to price {price}')

		order.price = price
		replacement_order = self._transform_generic_order(order)

		#new_order_legs = order.brokerSpecific['comboLegs']
		#new_price = abs(price)
		#tasty_price = Decimal(new_price * -1 if order.price_effect == PriceEffect.DEBIT else new_price)

		# if order.type == OrderType.LIMIT:
		# 	replacement_order = NewOrder(
		# 		time_in_force=OrderTimeInForce.DAY,
		# 		order_type=order.type,	
		# 		legs=new_order_legs,
		# 		price=tasty_price
		# 	)
		# elif order.type == OrderType.STOP:
		# 	replacement_order = NewOrder(
		# 		time_in_force=OrderTimeInForce.DAY,
		# 		order_type=order.type,	
		# 		legs=new_order_legs,
		# 		stop_trigger=tasty_price
		# 	)
		# elif order.type == OrderType.MARKET:
		# 	replacement_order = NewOrder(
		# 		time_in_force=OrderTimeInForce.DAY,
		# 		order_type=order.type,	
		# 		legs=new_order_legs
		# 	)

		try:
			self._replacedOrders.append(tasty_order)  # Merken für das Cancel Event dieser Order
			response: PlacedOrder = account.replace_order(self._session, tasty_order.id, replacement_order)
			order.brokerSpecific['order'] = response
			#self._replacedOrders.append(response) # Auch die neue Order zu den zu ignorierenden Orders hinzufügen
			logger.debug(f'Replacment order {response.id} submitted successfully')
			return True
		
		except TastytradeError as tastyErr:
			logger.error(f'Error adjusting order: {tastyErr}')
			return False
		except ValidationError as valErr:
			logger.error(f'Validation error adjusting order: {valErr}')
			err = valErr.errors()[0]
			logger.error(err)
			return False 

	async def _on_alert_streamer_disconnect(self, streamer: AlertStreamer):
		logger.debug("Tastytrade Alert Streamer disconnected.")

	async def _on_streamer_disconnect(self, streamer: DXLinkStreamer):
		"""
		Callback method which is called when the Tastytrade streamer disconnects
		"""
		logger.debug("Tastytrade Streamer disconnected. Performing disconnect operations")
		if self._is_disconnecting == False:
			await self._disconnect_internal()
	
	async def _subscribe_data(self):
		"""
		Subscribe to the required data
		"""
		logger.debug("Subscribing to streaming data")
		await self._streamer.subscribe(Quote, self._quote_symbols)
		await self._streamer.subscribe(Greeks, self._greeks_symbols)
		startTime = dt.datetime.now() - timedelta(days=1)
		await self._streamer.subscribe_candle(self._candle_symbols, interval='1m', start_time=startTime)

	async def requestTickerData(self, symbols: List[str]):
		"""
		Request ticker data for the given symbols and their options
		"""
		ssl_context = ssl.create_default_context(cafile=certifi.where())
		self._streamer = await DXLinkStreamer(self._session, ssl_context=ssl_context, disconnect_fn=self._on_streamer_disconnect)

		self._quote_symbols = []
		self._candle_symbols = []
		self._greeks_symbols = symbols

		for symbol in symbols:
			match symbol:
				case 'SPX':
					symbolData = TastySymbolData()
					symbolData.symbol = symbol
					symbolData.tastySymbol = 'SPX'
					self._quote_symbols.append('SPX')
					self._symbolData[symbol] = symbolData
					self._symbolReverseLookup[symbolData.tastySymbol] = symbol
				case 'VIX':
					symbolData = TastySymbolData()
					symbolData.symbol = symbol
					symbolData.tastySymbol = 'VIX'
					self._candle_symbols.append('VIX')
					self._symbolData[symbol] = symbolData
					self._symbolReverseLookup[symbolData.tastySymbol] = symbol
				case _:
					logger.error(f'Symbol {symbol} currently not supported by Tastytrade Connector!')
					continue

		await self._subscribe_data()

		if self.task_listen_quotes == None:
			self.task_listen_quotes = asyncio.create_task(self._update_quotes())
			self.task_listen_greeks = asyncio.create_task(self._update_greeks())
			self.task_listen_candle = asyncio.create_task(self._update_candle())
			try:
				await asyncio.gather(self.task_listen_quotes, self.task_listen_greeks, self.task_listen_candle )
			except asyncio.CancelledError:
				logger.debug('Cancelled listening to quotes and greeks')
			except Exception as exc:
				logger.debug(f'Error listening to quotes and greeks: {exc}')

	async def _update_accounts(self):
		"""
		Task for listening to account updates
		"""
		async for order in self._alert_streamer.listen(PlacedOrder):
			additional_info = ''
			if order.status == OrderStatus.REJECTED:
				additional_info = f'Reason: {order.reject_reason}'
			logger.debug(f'Update on order {order.id} status {order.status} {additional_info}')			
			ignore_order_event = False
			# Cancel Events von Preisanpassungen ignorieren, da sie kein echtes Cancel sind
			for replaced_order in self._replacedOrders:
				if replaced_order.id == order.id and order.status == OrderStatus.CANCELLED:
					#self._replacedOrders.remove(replaced_order)
					ignore_order_event = True
					logger.debug('Ignoring cancel event for replaced order')
					continue
				if replaced_order.id == order.id and (order.status == OrderStatus.ROUTED or order.status == OrderStatus.LIVE):
					if order.status == OrderStatus.LIVE:
						self._replacedOrders.remove(replaced_order)
					ignore_order_event = True
					logger.debug('Ignoring placement of new replacement order')
					continue
	
			if ignore_order_event == False:
				relevantOrder: GenericOrder = None
				for managedOrder in self._orders:
					broker_specific_order: PlacedOrder = managedOrder.brokerSpecific['order']
					if broker_specific_order.id == order.id:
						relevantOrder = managedOrder
						break
			
				if relevantOrder == None:
					logger.debug(f'No managed order matched the status event')
				else:
					relevantOrder.brokerSpecific['order'] = order
					filledAmount = int(order.size)
					relevantOrder.averageFillPrice = abs(float(order.price)) if order.price != None else 0
					order_status =	self._genericOrderStatus(order.status)
					if order_status != None:
						self._emitOrderStatusEvent(relevantOrder, order_status, filledAmount)
					else:
						logger.debug(f'Order status {order.status} not mapped to generic order status')

	async def _update_quotes(self):
		async for e in self._streamer.listen(Quote):
			logger.trace(f'Received Quote: {e.event_symbol} bid price: {e.bid_price} ask price: {e.ask_price}')
			# Preisdaten speichern
			if not e.event_symbol.startswith('.'):
				# Symbol ist ein Basiswert
				try:
					genericSymbol = self._symbolReverseLookup[e.event_symbol]
					symbolData: TastySymbolData  = self._symbolData[genericSymbol]
					midPrice = float((e.bid_price + e.ask_price) / 2)
					atmStrike = OptionHelper.roundToStrikePrice(midPrice)
					symbolData.lastPrice = midPrice
					if symbolData.lastAtmStrike != atmStrike:  # Check for missing Option Data only if ATM Strike has changed
						expirationDate = dt.date.today()
						symbolData.lastAtmStrike = atmStrike
						asyncio.create_task(self._requestMissingOptionData(symbolData, expirationDate, atmStrike))
					
				except KeyError as keyErr:
					logger.error(f'No generic symbol found for tastytrade symbol {e.event_symbol}')
			else:
				# Symbol ist eine Option
				try:
					symbol, optionType, expiration, strike = self._getOptionInfos(e.event_symbol)
					symbol_information = symbolInfo.symbol_infos[symbol]
					symbolData = self._symbolData[symbol]
					optionStrikeData = symbolData.optionPriceData[expiration]
					optionStrikePriceData = optionStrikeData.strikeData[strike]
					if optionType == OptionType.CALL:
						optionStrikePriceData.callBid = float(e.bid_price)
						optionStrikePriceData.callAsk = float(e.ask_price)
					else:
						optionStrikePriceData.putBid = float(e.bid_price)
						optionStrikePriceData.putAsk = float(e.ask_price)
					optionStrikePriceData.lastUpdated = dt.datetime.now(symbol_information.timezone)
					self._last_option_price_update_time = optionStrikePriceData.lastUpdated
				except Exception as exc:
					logger.error(f'Error getting option infos: {exc}')
	
	async def _update_greeks(self):
		async for e in self._streamer.listen(Greeks):
			logger.trace(f'Received Greeks: {e.event_symbol} delta: {e.delta}')
			if e.event_symbol.startswith('.'):
				# Symbol ist eine Option
				try:
					symbol, optionType, expiration, strike = self._getOptionInfos(e.event_symbol)
					symbol_information = symbolInfo.symbol_infos[symbol]
					symbolData = self._symbolData[symbol]
					optionStrikeData = symbolData.optionPriceData[expiration]
					optionStrikePriceData = optionStrikeData.strikeData[strike]
					if optionType == OptionType.CALL:
						optionStrikePriceData.callDelta = float(e.delta)
					else:
						optionStrikePriceData.putDelta = float(e.delta)

				except Exception as exc:
					logger.error(f'Error getting option infos: {exc}')

	async def _update_candle(self):
		async for e in self._streamer.listen(Candle):
			logger.trace(f'Received Candle: {e.event_symbol} close: {e.close}')
			if not e.event_symbol.startswith('.'):
				# Symbol ist ein Basiswert
				try:
					symbol = e.event_symbol.split('{')[0]
					genericSymbol = self._symbolReverseLookup[symbol]
					symbolData: TastySymbolData  = self._symbolData[genericSymbol]
					symbolData.lastPrice = float(e.close)
				except KeyError as keyErr:
					logger.error(f'No generic symbol found for tastytrade symbol {e.event_symbol}')

	async def eod_settlement_tasks(self):
		"""
		Perform End of Day settlement tasks
		- Unsubscribe from expired options quote data streaming
		- Delete expired option price data
		"""
		for symbolData in self._symbolData.values():
			try:
				today = dt.date.today()
				todays_option_price_data = symbolData.optionPriceData[today]
				streamer_symbols = []
				for value in todays_option_price_data.strikeData.values():
					option_price_data: OptionStrikePriceData = value
					try:
						call_streamer_symbol = option_price_data.brokerSpecific['call_streamer_symbol']
						streamer_symbols.append(call_streamer_symbol)
						self._quote_symbols.remove(call_streamer_symbol)
					except KeyError as keyErr:
						pass

					try:
						put_streamer_symbol = option_price_data.brokerSpecific['put_streamer_symbol']
						streamer_symbols.append(put_streamer_symbol)
						self._quote_symbols.remove(put_streamer_symbol)
					except KeyError as keyErr:
						pass
				
				await self._streamer.unsubscribe(Quote, streamer_symbols)
				await self._streamer.unsubscribe(Greeks, streamer_symbols)
				symbolData.optionPriceData.pop(today) # Delete the expired option price data
			except KeyError as keyErr:
				pass

	def get_option_strike_data(self, symbol: str, expiration: dt.date) -> OptionStrikeData:
		""" 
		Returns the option strike data for the given symbol and expiration. It is including
		prices and greeks.
		"""
		symbolData = self._symbolData[symbol]
		try:
			return symbolData.optionPriceData[expiration]
		except KeyError:
			raise ValueError(f'No option strike data for symbol {symbol} and expiration {expiration} found!')

	def get_option_strike_price_data(self, symbol: str, expiration: date, strike: float) -> OptionStrikePriceData:
		""" 
		Returns the option strike price data for the given symbol, expiration date, strike price and right
		"""
		symbolData = self._symbolData[symbol]
		optionStrikeData = symbolData.optionPriceData[expiration]
		if strike in optionStrikeData.strikeData.keys():
			return optionStrikeData.strikeData[strike]
		else:
			return None

	def get_strike_by_delta(self, symbol: str, right: str, delta: int) -> float:
		"""
		Returns the strike price based on the given delta based on the buffered option price data
		"""
		symbolData = self._symbolData[symbol]
		current_date = dt.date.today()
		option_price_data: OptionStrikeData= symbolData.optionPriceData[current_date]
		previous_delta = 0
		previous_strike = 0
		reverse = True if right == OptionRight.PUT else False
		sorted_strikes = dict(sorted(option_price_data.strikeData.items(), reverse=reverse))
		for strike, price_data in sorted_strikes.items():
			if right == OptionRight.PUT:
				if price_data.putDelta == None:
					continue
				adjusted_delta = price_data.putDelta * -100
			else:
				if price_data.callDelta == None:
					continue
				adjusted_delta = price_data.callDelta * 100
			if adjusted_delta <= delta:
				if OptionHelper.closest_number(delta, previous_delta, adjusted_delta) == adjusted_delta:
					return strike
				else:
					return previous_strike
			previous_delta = adjusted_delta
			previous_strike = strike

		raise ValueError(f'No strike price found for delta {delta} in symbol {symbol}!')
	
	def get_strike_by_price(self, symbol: str, right: str, price: float) -> float:
		""" 
		Returns the strike price based on the given premium price based on the buffered option price data
		"""
		# TODO: Implement in base class, because TWS Connector got the same code
		symbolData = self._symbolData[symbol]
		current_date = dt.date.today()
		option_price_data: OptionStrikeData= symbolData.optionPriceData[current_date]
		previous_price = 0
		previous_strike = 0
		reverse = True if right == OptionRight.PUT else False
		sorted_strikes = dict(sorted(option_price_data.strikeData.items(), reverse=reverse))
		for strike, price_data in sorted_strikes.items():
			if right == OptionRight.PUT:
				current_strike_price = price_data.getPutMidPrice()
				if current_strike_price == None:
					continue
			elif right == OptionRight.CALL:
				current_strike_price = price_data.getCallMidPrice()
				if current_strike_price == None:
					continue
			if current_strike_price > 0 and current_strike_price <= price:
				if OptionHelper.closest_number(price, previous_price, current_strike_price) == current_strike_price:
					return strike
				else:
					return previous_strike
			previous_price = current_strike_price
			previous_strike = strike
		raise ValueError(f'No strike price found for price {price} in symbol {symbol}!')

	def getFillPrice(self, order: GenericOrder) -> float:
		""" 
		Returns the fill price of the given order if it is filled
		"""
		try:
			tastyOrder: PlacedOrder = order.brokerSpecific['order']
			if tastyOrder.status == OrderStatus.FILLED:
				return abs(float(tastyOrder.price))
			else:
				return 0
		except KeyError as keyErr:
			logger.error(f'No fill price available for order {order}')
	
	def getLastPrice(self, symbol: str) -> float:
		""" 
		Returns the last price of the given symbol
		"""
		try:
			symbolData = self._symbolData[symbol]
			return symbolData.lastPrice
		except KeyError as keyErr:
			logger.error(f'No last price available for symbol {symbol}')
			return 0

	def oco_as_complex_order(self) -> bool:
		"""
		With Tastytrade, the OCO orders have to be placed as one complex order
		"""
		return True
	
	def uses_oco_orders(self) -> bool:
		""" 
		The TWS Connector uses OCO orders for take profit and stop loss orders
		"""
		return True

	async def _requestMissingOptionData(self, symbolData: TastySymbolData, expirationDate: dt.date, atmStrike: float):
		"""
		Request option data for the given symbol and expiration date
		"""
		chain = None
		symbolInformation = symbolInfo.symbol_infos[symbolData.symbol]
		# Bestehende gespeicherte Optionsdaten holen
		try:
			optionStrikeData = symbolData.optionPriceData[expirationDate]
		except KeyError as keyErr:

			# Wenn noch keine Optionsdaten für das Verfallsdatum vorhanden sind, dann bei Tasty anfragen ob es Optionsdaten gibt
			#chains = await a_get_option_chain(self._session, symbolData.tastySymbol)

			# Prüfen ob die Chain für das Symbol bereits abgerufen wurde
			if self._symbolData[symbolData.symbol].chain == None:
				chains = NestedOptionChain.get(self._session, symbolData.tastySymbol)
				for chain in chains:
					if chain.root_symbol == symbolInformation.trading_class:
						break
				assert chain != None
				self._symbolData[symbolData.symbol].chain = chain
			else:
				chain = self._symbolData[symbolData.symbol].chain

			for chain_at_expiration in chain.expirations:
				if chain_at_expiration.expiration_date >= expirationDate:
					break

			if chain_at_expiration == None or chain_at_expiration.expiration_date != expirationDate:
				logger.error(f'No options available for symbol {symbolData.tastySymbol} and expiration date {expirationDate}')
				return
			
			# Convert the available strikes to a list of decimal numbers
			try:
				available_strikes = chain_at_expiration._optrabot_strikes
			except AttributeError as attrErr:
				chain_at_expiration._optrabot_strikes = []
				available_strikes = chain_at_expiration._optrabot_strikes
				for strike in chain_at_expiration.strikes:
					available_strikes.append(strike.strike_price)

			optionStrikeData = OptionStrikeData()
			symbolData.optionPriceData[expirationDate] = optionStrikeData
		
			# Die 20 Strike um den ATM Strike herum abrufen
			symbolInformation = symbolInfo.symbol_infos[symbolData.symbol]
			number_of_strikes_above = 40
			number_of_strikes_below = 40
			pos = bisect_left(available_strikes, atmStrike)
			lower_bound = max(0, pos - number_of_strikes_below)
			upper_bound = min(len(available_strikes), pos + number_of_strikes_above)
			strikes_of_interest = available_strikes[lower_bound:upper_bound]
		
			options_to_be_requested = []
			for strike_price in strikes_of_interest:	
				try:
					optionStrikeData.strikeData[strike_price]
				except KeyError as keyErr:
					option_strike_price_data = OptionStrikePriceData()
					optionStrikeData.strikeData[strike_price] = option_strike_price_data
					options_to_be_requested.append(strike_price)

			if len(options_to_be_requested) > 0:
				streamer_symbols = []
				for item in chain_at_expiration.strikes:
					strike: Strike = item
					if strike.strike_price in options_to_be_requested:
						option_strike_data = optionStrikeData.strikeData[strike.strike_price]
						option_strike_data.brokerSpecific['call_option'] = strike.call
						option_strike_data.brokerSpecific['call_streamer_symbol'] = strike.call_streamer_symbol
						option_strike_data.brokerSpecific['put_option'] =  strike.put
						option_strike_data.brokerSpecific['put_streamer_symbol']  = strike.put_streamer_symbol
						streamer_symbols.append(strike.call_streamer_symbol)
						streamer_symbols.append(strike.put_streamer_symbol)
						self._quote_symbols.append(strike.call_streamer_symbol)
						self._quote_symbols.append(strike.put_streamer_symbol)
				await self._streamer.subscribe(Quote, streamer_symbols)
				await self._streamer.subscribe(Greeks, streamer_symbols)
		
	def _getOptionInfos(self, tastySymbol: str) -> tuple:
		"""
		Extracts the generic symbol and expiration date, strike and option side from the tastytrade option symbol.
		If the option symbol information cannot be parsed as expected, a ValueError exception is raised.
		"""
		error = False
		pattern = r'^.(?P<optionsymbol>[A-Z]+)(?P<expiration>[0-9]+)(?P<type>[CP])(?P<strike>[0-9]+)'
		compiledPattern = re.compile(pattern)
		match = compiledPattern.match(tastySymbol)
		try:
			if match:
				optionSymbol = match.group('optionsymbol')
				for symbol, symbol_info in symbolInfo.symbol_infos.items():
					if symbol_info.symbol + symbol_info.option_symbol_suffix == optionSymbol:
						genericSymbol = symbol_info.symbol
						break
				expirationDate = dt.datetime.strptime(match.group('expiration'), '%y%m%d').date()
				strike = float(match.group('strike'))
				optionType = OptionType.CALL if match.group('type') == 'C' else OptionType.PUT
		except IndexError as indexErr:
			logger.error(f'Invalid option symbol {tastySymbol}')
			error = True
		except ValueError as valueErr:
			logger.error(f'Invalid option symbol {tastySymbol}')
			error = True
		if genericSymbol == None or error == True:
			raise ValueError(f'Invalid option symbol {tastySymbol}')
		return genericSymbol, optionType, expirationDate, strike
	
	def _mappedOrderAction(self, orderAction: GenericOrderAction, legAction: GenericOrderAction) -> OrderAction:
		"""
		Maps the general order action to the Tasty specific order action
		"""
		match orderAction:
			case GenericOrderAction.BUY_TO_OPEN:
				if legAction == GenericOrderAction.BUY:
					return OrderAction.BUY_TO_OPEN
				if legAction == GenericOrderAction.SELL:
					return OrderAction.SELL_TO_OPEN
				else:
					raise ValueError(f'Unknown leg action: {legAction}')
			case GenericOrderAction.SELL_TO_OPEN:
				if legAction == GenericOrderAction.SELL:
					return OrderAction.SELL_TO_OPEN
				elif legAction == GenericOrderAction.BUY:
					return OrderAction.BUY_TO_OPEN
				else:
					raise ValueError(f'Unknown leg action: {legAction}')
			case GenericOrderAction.BUY_TO_CLOSE:
				if legAction == GenericOrderAction.BUY:
					return OrderAction.BUY_TO_CLOSE
				if legAction == GenericOrderAction.SELL:
					return OrderAction.SELL_TO_CLOSE
				else:
					raise ValueError(f'Unknown leg action: {legAction}')
			case GenericOrderAction.SELL_TO_CLOSE:
				if legAction == GenericOrderAction.SELL or legAction == GenericOrderAction.SELL_TO_CLOSE:
					return OrderAction.SELL_TO_CLOSE
				elif legAction == GenericOrderAction.BUY or legAction == GenericOrderAction.BUY_TO_CLOSE:
					return OrderAction.BUY_TO_CLOSE
				else:
					raise ValueError(f'Unknown leg action: {legAction}')
			case _:
				raise ValueError(f'Unknown order action: {orderAction}')
			
	async def _request_account_updates(self):
		"""
		Request Account Updates
		"""
		self._alert_streamer = await AlertStreamer(self._session, disconnect_fn=self._on_alert_streamer_disconnect)
		await self._alert_streamer.subscribe_accounts(self._tasty_accounts)

		if self.task_listen_accounts == None:
			self.task_listen_accounts = asyncio.create_task(self._update_accounts())
			try:
				await asyncio.gather(self.task_listen_accounts)
			except asyncio.CancelledError:
				logger.debug('Cancelled listening to account updates')
			except Exception as exc:
				logger.debug(f'Error listening to account updates: {exc}')

	def _genericOrderStatus(self, status: OrderStatus) -> GenericOrderStatus:
		"""
		Maps the Tastytrade order status to the generic order status
		"""
		match status:
			case OrderStatus.RECEIVED:
				return GenericOrderStatus.OPEN
			case OrderStatus.LIVE:
				return GenericOrderStatus.OPEN
			case OrderStatus.CONTINGENT:
				return GenericOrderStatus.OPEN
			case OrderStatus.CANCELLED:
				return GenericOrderStatus.CANCELLED
			case OrderStatus.FILLED:
				return GenericOrderStatus.FILLED
			case OrderStatus.REJECTED:
				return GenericOrderStatus.CANCELLED
			case _:
				return None