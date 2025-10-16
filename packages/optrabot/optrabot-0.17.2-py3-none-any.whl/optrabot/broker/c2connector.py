import asyncio
from decimal import Decimal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dataclasses import dataclass
from enum import Enum
import datetime as dt
import json

import pytz
from optrabot.exceptions.orderexceptions import PlaceOrderException, PrepareOrderException
from optrabot.managedtrade import ManagedTrade
import optrabot.symbolinfo as symbolInfo
from typing import List
import httpx
from loguru import logger
from fastapi import status
from optrabot.broker.optionpricedata import OptionStrikePriceData
from optrabot.models import Account
from optrabot.broker.brokerconnector import BrokerConnector
from optrabot.broker.order import Leg, OptionRight, Order as GenericOrder, OrderStatus as GenericOrderStatus, OrderAction, OrderStatus, OrderType
from optrabot.tradetemplate.templatefactory import Template
import optrabot.config as optrabotcfg

class C2OrderSide(str, Enum):
	"""
	Represents the side of an order
	"""
	BUY = "1"
	SELL = "2"

class C2OrderType(str, Enum):
	"""
	Represents the type of an order
	"""
	MARKET = "1"
	LIMIT = "2"
	STOP = "3"

@dataclass
class C2ExchangeSymbol:
	"""
	Class for Collective2 Exchange Symbol Data
	"""
	Symbol: str = None
	Currency: str = None
	SecurityExchange: str = None
	SecurityType: str = None
	MaturityMonthYear: str = None
	PutOrCall: int = None
	StrikePrice: int = None
	PriceMultiplier: int = 1

	def __init__(self, symbol: str, symbol_type: str, right: OptionRight, strike: float):
		self.Symbol = symbol
		self.SecurityType = symbol_type
		self.PutOrCall = 1 if right == OptionRight.CALL else 0
		self.StrikePrice = strike
		self.SecurityExchange = 'DEFAULT'
		self.Currency = 'USD'

	def to_dict(self):
		"""
		Returns the JSON representation of the order
		"""
		return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class C2Order:
	"""
	Class for Collective2 Order
	"""
	StrategyId: str = None
	OrderType: C2OrderType = None
	Side: C2OrderSide = None
	OrderQuantity: int = 0
	Limit: str = None
	Stop: str = None
	TIF: str = None
	ExchangeSymbol: C2ExchangeSymbol = None
	ParentSignalId: int = None
	CancelReplaceSignalId: int = None			# Id of the Signal Id which is to be replaced (used for Adjust Order)

	def __init__(self, type: C2OrderType, side: C2OrderSide, quantity: int = 1, strategy_id: str = None, **kwargs):
		self.StrategyId = strategy_id
		self.OrderType = type
		self.Side = side
		self.OrderQuantity = quantity
		self.TIF= '0'

	def to_dict(self):
		"""
		Returns the JSON representation of the order
		"""
		result = {}
		result['StrategyId'] = self.StrategyId
		result['OrderType'] = self.OrderType.value
		result['Side'] = self.Side.value
		result['OrderQuantity'] = self.OrderQuantity
		result['TIF'] = self.TIF
		if self.ParentSignalId is not None:
			result['ParentSignalId'] = self.ParentSignalId
		if self.Limit is not None:
			result['Limit'] = self.Limit
		if self.Stop is not None:
			result['Stop'] = self.Stop
		if self.ExchangeSymbol is not None:
			result['ExchangeSymbol'] = self.ExchangeSymbol.to_dict()
		if self.CancelReplaceSignalId is not None:
			result['CancelReplaceSignalId'] = self.CancelReplaceSignalId
		return result
	
class C2Connector(BrokerConnector):
	"""
	Connector for the Collective2 platform for submitting trades to C2 strategies
	"""
	def __init__(self) -> None:
		super().__init__()
		self.id = 'C2'
		self.broker = 'C2'
		self._base_url = 'https://api4-general.collective2.com'
		self._api_key = None
		self._broker_connector = None
		self._http_headers = None
		self._strategies = []
		self._orders: List[GenericOrder] = []
		self._connected = False
		self._backgroundScheduler = AsyncIOScheduler()
		self._backgroundScheduler.start()
		self._start_date: dt.datetime = None
		self._initialize()

	def _initialize(self):
		"""
		Initialize the C2 connector
		"""
		config :optrabotcfg.Config = optrabotcfg.appConfig
		try:
			config.get('c2')
		except KeyError as keyErr:
			logger.debug('No Collective2 configuration found')
			return

		try:
			self._api_key = config.get('c2.apikey')
		except KeyError as keyErr:
			logger.error('No Collective2 API key configured!')
			return
		
		try:
			broker = config.get('c2.broker')
		except KeyError as keyErr:
			broker = None
			logger.error('No broker configured for C2 Connector!')
			return
		from optrabot.broker.brokerfactory import BrokerFactory

		self._broker_connector = BrokerFactory().get_connector_by_id(broker)
		if self._broker_connector is None:
			logger.error(f'Broker connector with id {broker} not found for C2 Connector!')
			return
		
		try:
			self._strategies = str(config.get('c2.strategies')).split(',')
		except KeyError as keyErr:
			logger.error('No strategies configured for C2 Connector!')
			return
		self._start_date = dt.datetime.now()
		self._http_headers = {'Authorization': 'Bearer ' +  self._api_key, "Content-Type": "application/json"}
		self._initialized = True
		self._backgroundScheduler.add_job(self._track_orders, 'interval', seconds=5, id='_track_signals', misfire_grace_time=None)

	def ___del__(self):
		"""
		Cleanup when the connector object gets deleted
		"""
		self._backgroundScheduler.remove_all_jobs()
		self._backgroundScheduler.shutdown()

	async def adjustOrder(self, managed_trade: ManagedTrade, order: GenericOrder, price: float) -> bool:
		""" 
		Adjusts the given order with the given new price
		"""
		if order.status == GenericOrderStatus.FILLED:
			logger.info('Order {} is already filled. Adjustment not required.', order)
			return True
		if order.status == GenericOrderStatus.CANCELLED:
			logger.info('Order {} is already cancelled. Adjustment not possible.', order)
			return True
		
		# For credit trades, the price must be negative
		if not managed_trade.long_legs_removed and (managed_trade.template.is_credit_trade() and order.price > 0) or (managed_trade.template.is_credit_trade() == False and order.price < 0):
			price = -price
		
		previous_order_signal_id = order.brokerSpecific['order_signal']
		c2order: C2Order = order.brokerSpecific['c2order']
		
		# Adjust the price of the order
		if order.type == OrderType.LIMIT:
			c2order.Limit = str(price)
		elif order.type == OrderType.STOP:
			c2order.Stop = str(price)
		c2order.CancelReplaceSignalId = previous_order_signal_id

		data = {
            'Order': c2order.to_dict()
        }
		logger.debug(f'Payload: {data}')
		response = httpx.put(self._base_url + '/Strategies/ReplaceStrategyOrder', headers=self._http_headers, json=data)
		if response.status_code != status.HTTP_200_OK:
			logger.error('Failed to adjust order: {}', response.text)
			return False
		
		logger.debug(response.json())
		json_data = json.loads(response.text)
		response_status = json_data.get('ResponseStatus')
		if response_status.get('ErrorCode') != str(status.HTTP_200_OK):
			logger.error('Failed to adjust order!')
			return False
		
		# Signal speichern
		result = json_data.get('Results')[0]
		order_signal = result.get('SignalId')
		order.brokerSpecific['order_signal'] = order_signal
		logger.info(f'Order adjusted successfully. Previous Signal ID: {previous_order_signal_id} New Signal ID: {order_signal}')
		return True

	async def cancel_order(self, order: GenericOrder):
		""" 
		Cancels the given order
		"""
	
	async def connect(self):
		"""
		Establish a connection to the C2 platform with the API key
		"""
		await super().connect()
		data = { 'Name': 'OptraBot'}
		connect_ok = False
		try:
			response = httpx.post(self._base_url + '/General/Hello', json=data, headers=self._http_headers)
		except Exception as excp:
			logger.error('Failed to connect to C2: {}', excp)
	
		if response.status_code != status.HTTP_200_OK:
			logger.error('Failed to connect to C2: {}', response.text)
			self._log_rate_limit_info(response)
		else:
			json_data = json.loads(response.text)
			#if json_data.get('message') != 'CONNECTION_ACCEPTED':
			results = json_data.get('Results')
			if results[0] == 'Hello, OptraBot!':
				connect_ok = True
				await self.set_trading_enabled(True, "Broker connected")
			else:
				logger.error('Failed to connect to C2: Unexpected Results {}', results)
		
		if not connect_ok:
			self._emitConnectFailedEvent()
			self._connected = False
		else:
			self._connected = True
			self._emitConnectedEvent()

	async def disconnect(self):
		await super().disconnect()
		self._connected = False
		await self.set_trading_enabled(False, "Broker disconnected")

	def getAccounts(self) -> List[Account]:
		"""
		Returns the strategys managed by the user. The strategy ids is used as account ids
		"""
		if len(self._managedAccounts) == 0 and self.isConnected():
			for strategy_id in self._strategies:
				account = Account(id =strategy_id, name = strategy_id, broker = self.broker, pdt = False)
				self._managedAccounts.append(account)
		return self._managedAccounts

	def getFillPrice(self, order: GenericOrder) -> float:
		""" 
		Returns the fill price of the given order if it is filled
		"""
		return abs(order.averageFillPrice)
	
	def getLastPrice(self, symbol: str) -> float:
		""" 
		Returns the last price of the given symbol
		"""
		return self._broker_connector.getLastPrice(symbol)
	
	def get_last_option_price_update_time(self) -> dt.datetime:
		"""
		Returns the last update time of the option price data
		"""
		return self._broker_connector.get_last_option_price_update_time()

	def get_option_strike_data(self, symbol, expiration):
		"""
		Returns the option strike data for the given symbol and expiration date.
		"""
		return self._broker_connector.get_option_strike_data(symbol, expiration)

	def get_option_strike_price_data(self, symbol: str, expiration: dt.date, strike: float) -> OptionStrikePriceData:
		""" 
		Returns the option strike price data based on the real broker connector
		"""
		return self._broker_connector.get_option_strike_price_data(symbol, expiration, strike)

	def get_strike_by_delta(self, symbol: str, right: str, delta: int) -> float:
		""" 
		Returns the strike price based on the given delta using the real broker connector
		"""
		return self._broker_connector.get_strike_by_delta(symbol, right, delta)
	
	def get_strike_by_price(self, symbol: str, right: str, price: float) -> float:
		""" 
		Returns the strike price based on the given premium price based on the buffered option price data
		"""
		return self._broker_connector.get_strike_by_price(symbol, right, price)

	def isConnected(self) -> bool:
		return self._connected

	async def place_complex_order(self, take_profit_order: GenericOrder, stop_loss_order: GenericOrder, template: Template) -> bool:
		"""
		TWS doesn't support complex orders
		"""
		raise NotImplementedError()
	
	async def placeOrder(self, managed_trade: ManagedTrade, order: GenericOrder, parent_order: GenericOrder = None) -> None:
		""" 
		Places the given order for a managed account via the broker connection.
		
		Raises:
			PlaceOrderException: If the order placement fails with a specific reason.
		"""
		if len(order.legs) > 1:
			raise PlaceOrderException('Only single leg orders are supported for Collective2 Strategies', order)
		
		c2order: C2Order = order.brokerSpecific.get('c2order')
		if c2order is None:
			raise PlaceOrderException('Order not prepared', order)
		
		leg: Leg = order.legs[0]
		c2order.OrderQuantity = order.quantity
		c2order.StrategyId = managed_trade.template.account
		if order.type == OrderType.LIMIT:
			c2order.Limit = str(order.price)
		elif order.type == OrderType.STOP:
			c2order.Stop = str(order.price)

		# Parent Signal Id if there is a parent order
		if parent_order is not None and order.type != OrderType.MARKET:   # Not use parent order for market orders now
			c2order.ParentSignalId = parent_order.brokerSpecific['order_signal']

		data = {
            'Order': c2order.to_dict()
        }
		logger.debug(f'Payload: {data}')
		response = httpx.post(self._base_url + '/Strategies/NewStrategyOrder', headers=self._http_headers, json=data)
		if response.status_code != status.HTTP_200_OK:
			raise PlaceOrderException(f'{response.text}', order)
		
		logger.debug(response.json())
		json_data = json.loads(response.text)
		response_status = json_data.get('ResponseStatus')
		if response_status.get('ErrorCode') != str(status.HTTP_200_OK):
			raise PlaceOrderException(f'Communication Error Code: {response_status.get("ErrorCode")} Message: {response_status.get("Message")}', order)
		
		# Signal speichern
		result = json_data.get('Results')[0]
		order_signal = result.get('SignalId')
		logger.info('Order placed successfully. Signal ID: {}', order_signal)
		order.brokerSpecific['c2order'] = c2order
		order.brokerSpecific['order_signal'] = order_signal
		self._orders.append(order)
	
	async def prepareOrder(self, order: GenericOrder, need_valid_price_data: bool = True) -> None:
		"""
		Prepares the given order for execution.
		- Retrieve current market data for order legs

		Raises:
			PrepareOrderException: If the order preparation fails with a specific reason.
		"""
		if len(order.legs) > 1:
			raise PrepareOrderException('Only single leg orders are supported for Collective2 Strategies', order)
		
		symbolInformation = symbolInfo.symbol_infos[order.symbol]
		current_date = dt.date.today()
		
		leg = order.legs[0]
		if need_valid_price_data:
			strike_price_data = self._broker_connector.get_option_strike_price_data(order.symbol, current_date, leg.strike)
			if not strike_price_data.is_outdated():
				leg.askPrice = strike_price_data.putAsk if leg.right == OptionRight.PUT else strike_price_data.callAsk
				leg.bidPrice = strike_price_data.putBid if leg.right == OptionRight.PUT else strike_price_data.callBid
			else:
				raise PrepareOrderException(f'Price data for strike {leg.strike} is outdated', order)
		
		c2order = C2Order(self._map_order_type(order.type), side=self._map_order_side(leg.action))

		c2order.ExchangeSymbol = C2ExchangeSymbol(symbolInformation.trading_class, 'OPT', leg.right, leg.strike)
		c2order.ExchangeSymbol.MaturityMonthYear = leg.expiration.strftime('%Y%m%d')
		order.brokerSpecific['c2order'] = c2order
		order.determine_price_effect()
	
	async def requestTickerData(self, symbols: List[str]):
		"""
		Ticker data don't need to be requested for C2 as they're consumed from the configured broker connection.
		"""
		pass

	def _log_rate_limit_info(self, response: httpx.Response):
		"""
		Logs the rate limit information from the response
		"""
		rate_limit = response.headers.get('X-Limit-Limit')
		rate_limit_type = response.headers.get('X-Limit-Type')
		rate_limit_remaining = response.headers.get('X-Limit-Remaining')
		rate_limit_reset = response.headers.get('X-Limit-Reset')
		logger.debug(f'Rate Limit: {rate_limit}/{rate_limit_type} Remaining: {rate_limit_remaining} Reset: {rate_limit_reset}')

	async def _track_orders(self):
		"""
		Tracks active Orders status at Collective2
		"""
		try:
			if not self.isConnected():
				return
			
			open_orders = any(order.status == OrderStatus.OPEN for order in self._orders)
			if not open_orders:
				return

			self._backgroundScheduler.reschedule_job('_track_signals', trigger=IntervalTrigger(seconds=60)) # Postpone the next run
			account_index = 0
			start_date = self._start_date.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
			for account in self._managedAccounts:
				account_index += 1
				if account_index > 1:
					await asyncio.sleep(5)  # wait 5 second between account requests to avoid rate limiting
				logger.debug(f'Checking orders for strategy {account.id}')
				query = {
							"StrategyId" : account.id,
							"StartDate" : start_date
						}
				try:
					response = httpx.get(self._base_url + '/Strategies/GetStrategyHistoricalOrders', headers=self._http_headers, params=query)
				except Exception as excp:
					logger.error('C2 HTTP request GetStrategyHistoricalOrders failed: {}', excp)
					continue

				if response.status_code != status.HTTP_200_OK:
					logger.error('Failed to get order status: {}', response.text)
					self._log_rate_limit_info(response)
					continue
			
				json_data = json.loads(response.text)
				results = json_data.get('Results')
				if len(results) == 0:
					continue
				else:
					logger.debug(f'Received {len(results)} orders for strategy {account.id}')
			
				for order in self._orders:
					if order.status == OrderStatus.OPEN:
						for result in results:
							if result.get('SignalId') == order.brokerSpecific['order_signal']:
								order_status = result.get('OrderStatus')
								if order_status == '2': # Order filled
									filled_quantity = result.get('FilledQuantity')
									order.averageFillPrice = result.get('AvgFillPrice')
									self._emitOrderStatusEvent(order, OrderStatus.FILLED, filledAmount=filled_quantity)
								if order_status == '4':
									self._emitOrderStatusEvent(order, OrderStatus.CANCELLED)
		except asyncio.exceptions.CancelledError as excp:
			logger.warning('Track Orders Task was cancelled!')
	
		# Schedule the next run in 5 seconds
		self._backgroundScheduler.reschedule_job('_track_signals', trigger=IntervalTrigger(seconds=5))

	def _map_order_side(self, action: OrderAction) -> C2OrderSide:
		"""
		Maps the action from a generic order to the C2 order side
		"""
		match action:
			case OrderAction.BUY:
				return C2OrderSide.BUY
			case OrderAction.BUY_TO_CLOSE:
				return C2OrderSide.BUY
			case OrderAction.SELL:
				return C2OrderSide.SELL
			case OrderAction.SELL_TO_CLOSE:
				return C2OrderSide.SELL
			case _:
				logger.error('Unsupported order action {}', action)
				return None

	def _map_order_type(self, order_type: OrderType) -> C2OrderType:
		"""
		Maps the order type from the generic order to the C2 order type
		"""
		match order_type:
			case OrderType.MARKET:
				return C2OrderType.MARKET
			case OrderType.LIMIT:
				return C2OrderType.LIMIT
			case OrderType.STOP:
				return C2OrderType.STOP
			case _:
				logger.error('Unsupported order type {}', order_type)
				return None

	def _get_osi_month(self, month: int, right: OptionRight) -> str:
		"""
		Returns the month code according to OSI based on the month and the option right.
		Reference: https://www.collective2.com/options
		"""
		match month:
			case 1:
				return 'A' if right == OptionRight.CALL else 'M'
			case 2:
				return 'B' if right == OptionRight.CALL else 'N'
			case 3:
				return 'C' if right == OptionRight.CALL else 'O'
			case 4:
				return 'D' if right == OptionRight.CALL else 'P'
			case 5:
				return 'E' if right	== OptionRight.CALL else 'Q'
			case 6:
				return 'F' if right == OptionRight.CALL else 'R'
			case 7:
				return 'G' if right == OptionRight.CALL else 'S'
			case 8:
				return 'H' if right == OptionRight.CALL else 'T'
			case 9:
				return 'I' if right == OptionRight.CALL else 'U'
			case 10:
				return 'J' if right == OptionRight.CALL else 'V'
			case 11:
				return 'K' if right == OptionRight.CALL else 'W'
			case 12:
				return 'L' if right == OptionRight.CALL else 'X'
			case _:
				logger.error('Unsupported month {}', month)
				return None