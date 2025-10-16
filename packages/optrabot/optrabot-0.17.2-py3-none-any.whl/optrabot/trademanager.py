import asyncio
import copy
import json
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from loguru import logger
from optrabot.managedtrade import ManagedTrade
from optrabot.broker.brokerconnector import BrokerConnector
from optrabot import crud, schemas
from optrabot.optionhelper import OptionHelper
from optrabot.broker.brokerfactory import BrokerFactory
from optrabot.broker.order import Execution, Leg, OptionRight, Order, OrderAction, OrderStatus, OrderType, PriceEffect
from optrabot.database import get_db_engine
import optrabot.symbolinfo as symbolInfo
from optrabot.stoplossadjuster import StopLossAdjuster
from optrabot.tradehelper import SecurityStatusData, TradeHelper
from optrabot.tradetemplate.templatefactory import Template
from optrabot.tradetemplate.earlyexittrigger import EarlyExitTriggerType
from optrabot.util.singletonmeta import SingletonMeta
from optrabot.exceptions.orderexceptions import PlaceOrderException, PrepareOrderException
from sqlalchemy.orm import Session
from typing import Dict, List	

class TradeManager(metaclass=SingletonMeta):
	"""
	The Trade Manager is a singleton class which is responsible for opening new trades and
	managing existing trades. It is monitoring the open trades and their attachde orders.
	"""
	def __init__(self):
		self._trades: List[ManagedTrade] = []
		self._backgroundScheduler = AsyncIOScheduler()
		self._backgroundScheduler.start()
		# Start monitoring of open trades in next 5 seconds mark
		now = datetime.now()
		next_run_time = (now + timedelta(seconds=(5 - now.second % 5))).replace(microsecond=0)
		self._backgroundScheduler.add_job(self._monitorOpenTrades, 'interval', seconds=5, id='MonitorOpenTrades', misfire_grace_time = None, next_run_time=next_run_time)
		self._backgroundScheduler.add_job(self._performEODTasks, 'cron', hour=16, minute=00, timezone=pytz.timezone('US/Eastern'), id='EODTasks', misfire_grace_time = None)
		self._backgroundScheduler.add_job(self._performEODSettlement, 'cron', hour=16, minute=34, timezone=pytz.timezone('US/Eastern'), id='EODSettlement', misfire_grace_time = None)
		BrokerFactory().orderStatusEvent += self._onOrderStatusChanged
		BrokerFactory().commissionReportEvent += self._onCommissionReportEvent
		BrokerFactory().orderExecutionDetailsEvent += self._onOrderExecutionDetailsEvent
		self._lock = asyncio.Lock()
		self._execution_transaction_map = {} # Maps the Execution ID to the Transaction ID
		self._last_trade_monitoring_time = datetime.now()	# Timestamp of last Trade monitoring

	def shutdown(self):
		"""
		Shutdown the TradeManager. Background scheduler will be stopped
		"""
		logger.debug('Shutting down TradeManager')
		self._backgroundScheduler.remove_all_jobs()
		self._backgroundScheduler.shutdown()

	async def openTrade(self, entryOrder: Order, template: Template):
		brokerConnector = BrokerFactory().getBrokerConnectorByAccount(template.account)
		if brokerConnector == None:
			logger.error(f'No active broker connection found for account {template.account}. Unable to place entry order.')
			return
		
		if brokerConnector.isConnected() == False:
			logger.error(f'Broker connection for account {template.account} is not connected. Unable to place entry order.')
			return
		
		if template.maxOpenTrades > 0:
			openTrades = 0
			for managedTrade in self._trades:
				if managedTrade.template == template and managedTrade.status == 'OPEN':
					openTrades += 1
			if openTrades >= template.maxOpenTrades:
				logger.warning(f'Maximum number of open trades for template {template.name} reached. Unable to place new trade.')
				return

		if brokerConnector.isTradingEnabled() == False:
			logger.error(f'Trading is disabled for account {template.account}. Unable to place entry order.')
			return
		
		try:
			await brokerConnector.prepareOrder(entryOrder)
		except PrepareOrderException as e:
			logger.error(f'Failed to prepare entry order for account {template.account}. Reason: {e.reason}')

			# Send Telegram-Notificiation via OptraBot Server
			from optrabot.tradinghubclient import TradinghubClient, NotificationType
			try:
				await TradinghubClient().send_notification(
					NotificationType.ERROR, 
					f"❌ Failed to prepare entry order for trade {template.strategy}.\n*Reason:* {e.reason}\n*Strikes:* {self._strikes_from_order(entryOrder)}\n*Account:* {template.account}"
				)
			except Exception as notify_error:
				logger.error(f"Unable to send telegram notification: {notify_error}")
			return
		
		logger.info(f'Opening trade at strikes {self._strikes_from_order(entryOrder)}')

		# Midprice calculation and minimum premium check
		entryOrder.price = self._calculateMidPrice(brokerConnector, entryOrder)
		logger.info(f'Calculated midprice for entry order: {entryOrder.price}')
		if template.meetsMinimumPremium(entryOrder.price) == False:
			logger.error(f'Entry order for account {template.account} does not meet minimum premium requirement. Unable to place entry order')
			return

		# Create the Trade in the database
		async with self._lock: # Mit Lock arbeiten, damit die Trade IDs nicht doppelt vergeben werden
			with Session(get_db_engine()) as session:
				newTradeSchema = schemas.TradeCreate(account=template.account, symbol=entryOrder.symbol, strategy=template.strategy)
				newTrade = crud.create_trade(session, newTradeSchema)
			newManagedTrade = ManagedTrade(trade=newTrade, entryOrder=entryOrder, template=template, account=template.account)
			self._trades.append(newManagedTrade)
		entryOrder.orderReference = self._composeOrderReference(newManagedTrade, 'Open')
		try:
			await brokerConnector.placeOrder(newManagedTrade, entryOrder)
			entryOrderPlaced = True
		except PlaceOrderException as e:
			logger.error(f"Failed to place entry order: {e.reason}")
			
			# Send Telegram-Notificiation via OptraBot Server
			from optrabot.tradinghubclient import TradinghubClient, NotificationType
			try:
				await TradinghubClient().send_notification(
					NotificationType.ERROR, 
					f"❌ Failed to place entry order for trade {template.strategy}.\n*Reason:* {e.reason}\n*Strikes:* {self._strikes_from_order(entryOrder)}\n*Account:* {template.account}\n*Price:* ${entryOrder.price:.2f}\n*Quantity:* {entryOrder.quantity}"
				)
			except Exception as notify_error:
				logger.error(f"Unable to send telegram notification: {notify_error}")
			
			# Trade aus der Datenbank löschen, da die Order nicht platziert werden konnte
			await self._deleteTrade(newManagedTrade, "order placement failed")
			entryOrderPlaced = False

		if entryOrderPlaced:
			logger.debug(f'Entry order for account placed. Now track its execution')
			entryOrder.status = OrderStatus.OPEN
			#asyncio.create_task(self._trackEntryOrder(newManagedTrade), name='TrackEntryOrder' + str(newManagedTrade.trade.id))
			self._backgroundScheduler.add_job(self._trackEntryOrder, 'interval', seconds=5, id='TrackEntryOrder' + str(newManagedTrade.trade.id), args=[newManagedTrade], max_instances=1, misfire_grace_time=None)

	def _onCommissionReportEvent(self, order: Order, execution_id: str, commission: float, fee: float):
		"""
		Handles the commission and fee reporting event from the Broker Connector.
		It adds the commission and fee to the transaction in the database.
		"""
		# Determine the transaction based on the execution ID
		try:
			transaction_id = self._execution_transaction_map.get(execution_id)
		except KeyError:
			logger.error(f'No trade transaction found for fill execution id {execution_id}')
			return
		
		for managed_trade in self._trades:
			if order == managed_trade.entryOrder or order == managed_trade.takeProfitOrder or order == managed_trade.stopLossOrder:
				logger.debug(f'Trade {managed_trade.trade.id}: Commission Report for Order received. Commission: {commission} Fee: {fee}')
				with Session(get_db_engine()) as session:
					db_trade = crud.getTrade(session, managed_trade.trade.id)
					transaction = crud.getTransactionById(session, managed_trade.trade.id, transaction_id)
					if transaction == None:
						logger.error('Transaction with id {} for trade {} not found in database!', transaction_id, managed_trade.trade.id)
						return
					transaction.commission += commission
					transaction.fee = +fee
					TradeHelper.updateTrade(db_trade)
					session.commit()
					logger.debug(f'Commissions saved to transaction {transaction.id} for trade {managed_trade.trade.id}')
				break

	def _onOrderExecutionDetailsEvent(self, order: Order, execution: Execution):
		"""
		Handles the order execution details which are sent from the Broker Connector
		when a order has been executed.
		"""
		logger.debug(f'Trade Manager Order Execution Details:')
		for managed_trade in self._trades:
			if order == managed_trade.entryOrder or order == managed_trade.takeProfitOrder or order == managed_trade.stopLossOrder:
				if order == managed_trade.entryOrder:
					logger.debug(f'Trade {managed_trade.trade.id}: Execution Details for Entry Order received')
				with Session(get_db_engine()) as session:
					max_transaction_id = crud.getMaxTransactionId(session, managed_trade.trade.id)
					db_trade = crud.getTrade(session, managed_trade.trade.id)
					if max_transaction_id == 0:
						# Opening transaction of the trade
						db_trade.status = 'OPEN'
					elif order == managed_trade.takeProfitOrder or order == managed_trade.stopLossOrder:
						# Set status to closed if take profit or stop loss order is filled, in order to prevent them to be reestablished
						# by the monitorOpenTrades background job.
						managed_trade.status = 'CLOSED'
					max_transaction_id += 1
					new_transaction = schemas.TransactionCreate(tradeid=managed_trade.trade.id, transactionid=max_transaction_id,
																id=max_transaction_id,
																symbol=order.symbol,
																type=execution.action,
																sectype=execution.sec_type,
																contracts=execution.amount,
																price=execution.price, 
																expiration=execution.expiration,
																strike=execution.strike,
																fee=0,
																commission=0,
																notes='',
																timestamp=execution.timestamp)
					self._execution_transaction_map[execution.id] = new_transaction.id # Memorize the the Execution ID for later commission report
					crud.createTransaction(session, new_transaction)
					managed_trade.transactions.append(new_transaction)

					# Check if trade is closed with all these transactions
					TradeHelper.updateTrade(db_trade)
					session.commit()
					if order == managed_trade.entryOrder:
						self._backgroundScheduler.add_job(self._reportExecutedTrade, id='ReportTrade' + str(managed_trade.trade.id) + '-' + execution.id, args=[managed_trade, execution.amount], misfire_grace_time = None, max_instances=100)

	async def _onOrderStatusChanged(self, order: Order, status: OrderStatus, filledAmount: int = 0):
		"""
		Handles the status change event of an order
		"""
		from optrabot.tradinghubclient import TradinghubClient, NotificationType
		logger.debug(f'Trade Manager Order status changed: {order.symbol} - {status}')
		for managedTrade in self._trades:
			brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
			if managedTrade.entryOrder == order:
				if status == OrderStatus.CANCELLED and managedTrade.status != 'OPEN':
					managedTrade.entryOrder.status = OrderStatus.CANCELLED
					logger.debug(f'Entry order for trade {managedTrade.trade.id} was cancelled')
					
					try:
						job_id = 'TrackEntryOrder' + str(managedTrade.trade.id)
						if self._backgroundScheduler.get_job(job_id):
							logger.debug(f"Removing tracking job for trade {managedTrade.trade.id}")
							self._backgroundScheduler.remove_job(job_id)
					except Exception as e:
						logger.debug(f"No tracking job found for trade {managedTrade.trade.id} or error removing job: {e}")
					
					await self._deleteTrade(managedTrade, "entry order was cancelled")
				if status == OrderStatus.FILLED:
					managedTrade.entryOrder.status = OrderStatus.FILLED
					logger.info(f'Entry Order of trade {managedTrade.trade.id} has been filled at ${managedTrade.entryOrder.averageFillPrice} (Qty: {filledAmount}) and trade is now running.' )
					if managedTrade.status != 'OPEN':
						managedTrade.status = 'OPEN'
						managedTrade.trade.status = 'OPEN'
						managedTrade.current_legs = managedTrade.entryOrder.legs
						with Session(get_db_engine()) as session:
							crud.update_trade(session, managedTrade.trade)

						logger.debug('Create TP SL Order Job')
						self._backgroundScheduler.add_job(self._createTakeProfitAndStop, id='CreateTakeProfitAndStop' + str(managedTrade.trade.id), args=[managedTrade], misfire_grace_time = None)

						# Send Telegram Notification via OptraBot Server
						await TradinghubClient().send_notification(NotificationType.INFO, f'🚀 Trade {managedTrade.trade.id} opened at {brokerConnector.broker}.\n*Strategy:* {managedTrade.template.strategy}\n*Strikes:* {self._strikes_from_order(managedTrade.entryOrder)}\n*Account:* {managedTrade.account}\n*Price:* ${managedTrade.entryOrder.averageFillPrice:.2f}\n*Quantity:* {filledAmount}')
					else:
						logger.debug('Trade is already open. No need to create TP SL Order Job')
			elif managedTrade.takeProfitOrder == order:
				if status == OrderStatus.FILLED:
					managedTrade.takeProfitOrder.status = OrderStatus.FILLED
					logger.debug(f'Take Profit order for trade {managedTrade.trade.id} was filled. Closing trade now')
					managedTrade.status = 'CLOSED'
					managedTrade.trade.status = 'CLOSED'
					with Session(get_db_engine()) as session:
						crud.update_trade(session, managedTrade.trade)
					logger.success('Take Profit Order has been filled. Trade with id {} finished', managedTrade.trade.id)
					await TradinghubClient().send_notification(NotificationType.INFO, f'🎯 Trade {managedTrade.trade.id}\n*Take Profit* order executed at ${order.averageFillPrice:.2f}.') 
				elif status == OrderStatus.CANCELLED:
					managedTrade.takeProfitOrder.status = OrderStatus.CANCELLED
					logger.debug(f'Take Profit order for trade {managedTrade.trade.id} was cancelled.')
				if status == OrderStatus.FILLED or status == OrderStatus.CANCELLED:
					if not brokerConnector.uses_oco_orders() and managedTrade.stopLossOrder:
						logger.info(f'Trade {managedTrade.trade.id} does not use OCO orders. Cancelling Stop Loss order')
						await brokerConnector.cancel_order(managedTrade.stopLossOrder)

			elif managedTrade.stopLossOrder == order:
				if status == OrderStatus.FILLED:
					managedTrade.stopLossOrder.status = OrderStatus.FILLED
					logger.debug(f'Stop Loss order for trade {managedTrade.trade.id} was filled. Closing trade now')
					managedTrade.status = 'CLOSED'
					managedTrade.trade.status = 'CLOSED'
					with Session(get_db_engine()) as session:
						crud.update_trade(session, managedTrade.trade)
					logger.error('Stop Loss Order has been filled. Trade with id {} finished', managedTrade.trade.id)
					await TradinghubClient().send_notification(NotificationType.INFO, f'🏁 Trade {managedTrade.trade.id}\n*Stop Loss* order executed at ${order.averageFillPrice:.2f}.') 
				elif status == OrderStatus.CANCELLED:
					managedTrade.stopLossOrder.status = OrderStatus.CANCELLED
					logger.debug(f'Stop Loss order for trade {managedTrade.trade.id} was cancelled')
				if status == OrderStatus.FILLED or status == OrderStatus.CANCELLED:
					if not brokerConnector.uses_oco_orders() and managedTrade.takeProfitOrder:
						logger.info(f'Trade {managedTrade.trade.id} does not use OCO orders. Cancelling Take Profit order')
						await brokerConnector.cancel_order(managedTrade.takeProfitOrder)
			elif managedTrade.closing_order == order:
				logger.debug(f'Closing order status update for trade {managedTrade.trade.id}: {status}')
				if status == OrderStatus.FILLED:
					managedTrade.closing_order.status = OrderStatus.FILLED
					logger.debug(f'Closing order for trade {managedTrade.trade.id} was filled. Closing trade now')
					managedTrade.status = 'CLOSED'
					managedTrade.trade.status = 'CLOSED'
					with Session(get_db_engine()) as session:
						crud.update_trade(session, managedTrade.trade)
					logger.success(f'Closing Order has been filled at ${order.averageFillPrice}. Trade with id {managedTrade.trade.id} finished')
					await TradinghubClient().send_notification(NotificationType.INFO, f'🏁 Trade {managedTrade.trade.id}\n*Closing* order executed at ${order.averageFillPrice:.2f}.')
				elif status == OrderStatus.CANCELLED:
					managedTrade.closing_order.status = OrderStatus.CANCELLED
					logger.debug(f'Closing order for trade {managedTrade.trade.id} was cancelled')
			else:
				# Try to find a matching adjustment order and update its status
				adjustment_order = next((ord for ord in managedTrade.adjustment_orders if ord == order), None)
				if adjustment_order:
					logger.debug(f'Found matching adjustment order for trade {managedTrade.trade.id}')
					adjustment_order.status = status

	def getManagedTrades(self) -> List[ManagedTrade]:
		"""
		Returns a list of all trades currenty managed by the TradeManager 
		"""
		return self._trades
	
	def _calculateMidPrice(self, broker_connector: BrokerConnector, order: Order) -> float:
		"""
		Calculates the midprice for the given order
		"""
		midPrice = 0
		for leg in order.legs:
			ask_price = leg.askPrice if not OptionHelper.isNan(leg.askPrice) and leg.askPrice >= 0 else 0
			bid_price = leg.bidPrice if not OptionHelper.isNan(leg.bidPrice) and leg.bidPrice >= 0 else 0
			legMidPrice = (ask_price + bid_price) / 2
			if leg.action == OrderAction.SELL:
				midPrice -= legMidPrice
			else:
				midPrice += legMidPrice
		return self._round_order_price(broker_connector, order, midPrice)
	
	async def _process_adjustment_orders(self, managed_trade: ManagedTrade):
		"""
		This Background Job function takes care of execution of the adjustment orders
		"""
		logger.debug(f'Start processing of adjustment orders for trade {managed_trade.trade.id}')
		broker_connector = BrokerFactory().getBrokerConnectorByAccount(managed_trade.template.account)
		oco_cancelled = False
		# Cancel existing Take Profit and Stop Loss Orders for the trade
		if managed_trade.takeProfitOrder and managed_trade.takeProfitOrder.status == OrderStatus.OPEN:
			logger.info(f'Cancelling existing Take Profit order for trade {managed_trade.trade.id} before placing adjustment orders')
			await broker_connector.cancel_order(managed_trade.takeProfitOrder)
			oco_cancelled = True
		if managed_trade.stopLossOrder and managed_trade.stopLossOrder.status == OrderStatus.OPEN:
			if (oco_cancelled == False and broker_connector.uses_oco_orders()) or not broker_connector.uses_oco_orders():
				logger.info(f'Cancelling existing Stop Loss order for trade {managed_trade.trade.id} before placing adjustment orders')
				await broker_connector.cancel_order(managed_trade.stopLossOrder)
		# Wait for the orders to be cancelled
		remaining_time = 60
		while remaining_time > 0:
			if (managed_trade.takeProfitOrder == None or managed_trade.takeProfitOrder.status != OrderStatus.CANCELLED) and (managed_trade.stopLossOrder == None or managed_trade.stopLossOrder.status != OrderStatus.CANCELLED):
				break
			await asyncio.sleep(1)
			remaining_time -= 1

		# If we reach here, the orders are either cancelled or the time has run out
		if remaining_time == 0:
			logger.error(f'Timeout reached while waiting for orders to be cancelled for trade {managed_trade.trade.id}')
			return
		
		symbol_info = symbolInfo.symbol_infos[managed_trade.entryOrder.symbol]
		round_base = symbol_info.multiplier * symbol_info.quote_step
		
		# Process the adjustment orders
		for adjustment_order in managed_trade.adjustment_orders:
			adjustment_order.price = self._calculateMidPrice(broker_connector, adjustment_order)
			logger.info(f'Calculated midprice for adjustment order: {adjustment_order.price}')
			# Debit Orders must have a price > 0
			if adjustment_order.price_effect == PriceEffect.DEBIT and adjustment_order.price <= 0:
				adjustment_order.price += broker_connector.get_min_price_increment(adjustment_order.price)

			try:
				await broker_connector.prepareOrder(adjustment_order)
			except PrepareOrderException as e:
				logger.error(f'Failed to prepare adjustment order for trade {managed_trade.trade.id}. Skipping adjustment orders.')
				managed_trade.adjustment_orders = []
				return

			try:
				await broker_connector.placeOrder(managed_trade, adjustment_order)
			except PlaceOrderException as e:
				logger.error(f'Failed to place adjustment order for trade {managed_trade.trade.id}: {e}')
				managed_trade.adjustment_orders = []
				return
			
			# Adjustment Order has been placed.....wait for execution
			remaining_time = 60
			while remaining_time > 0:
				await asyncio.sleep(5)
				remaining_time -= 5

				if adjustment_order.status == OrderStatus.FILLED:
					logger.info(f'Adjustment order for trade {managed_trade.trade.id} has been filled at ${adjustment_order.averageFillPrice}')
					managed_trade.update_current_legs(adjustment_order)
					
					break
				elif adjustment_order.status == OrderStatus.CANCELLED:
					logger.error(f'Adjustment order for trade {managed_trade.trade.id} has been cancelled.')
					managed_trade.adjustment_orders = []
					return

				calc_adjusted_price = adjustment_order.price + broker_connector.get_min_price_increment(adjustment_order.price)

				# If the calculated Price is below the midprice, adjust it to the midprice...to prevent the market running away
				calculated_mid_price = self._calculateMidPrice(broker_connector, adjustment_order)
				if calc_adjusted_price < calculated_mid_price:
					logger.info('Calculated adjusted price is below current mid price. Adjusting to order price to mid price.')
					calc_adjusted_price = calculated_mid_price

				if len(adjustment_order.legs) == 1:
					# For Single Leg orders the round base depends on the price and the brokers rules
					round_base = broker_connector.get_min_price_increment(calc_adjusted_price) * symbol_info.multiplier
				adjustedPrice = OptionHelper.roundToTickSize(calc_adjusted_price, round_base)
				logger.info('Adjusting adjustment order. Current Limit Price: {} Adjusted Limit Price: {}', OptionHelper.roundToTickSize(adjustment_order.price), adjustedPrice)

				if await broker_connector.adjustOrder(managed_trade, adjustment_order, adjustedPrice) == True:
					adjustment_order.price = adjustedPrice
			
			if remaining_time == 0:
				logger.error(f'Timeout reached while waiting for adjustment order to be filled for trade {managed_trade.trade.id}')
				return
			
		managed_trade.adjustment_orders = [] # Clear the adjustment orders
		logger.success(f'All adjustment orders for trade {managed_trade.trade.id} have been processed successfully.')

	async def _check_and_adjust_stoploss(self, managedTrade: ManagedTrade):
		"""
		Checks if there are Stop Loss adjusters in the template of the trade and if any adjustment of the stop loss is required.
		If so it performs the adjustment of the stoploss order.

		If the trade is a credit trade and multi legged and the a long leg of the stop loss order got no bid price
		anymore because of declining value, the leg needs to be removed from the Stop Loss order.
		"""
		broker_connector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
		if broker_connector == None:
			logger.error(f'No active broker connection found for account {managedTrade.template.account}. Unable to check and adjust stop loss order.')
			return
		if len(managedTrade.stoploss_adjusters) > 0:
			adjuster_index = 0
			for adjuster in managedTrade.stoploss_adjusters:
				# Find first adjuster which has not been triggered yet
				adjuster_index += 1
				if not adjuster.isTriggered():
					logger.debug(f'Checking {adjuster_index}. SL adjuster for trade {managedTrade.trade.id} at profit level {adjuster._trigger}%')
					adjusted_stoploss_price = adjuster.execute(managedTrade.current_price)
					if adjusted_stoploss_price:
						adjusted_stoploss_price = self._round_order_price(broker_connector, managedTrade.stopLossOrder, adjusted_stoploss_price)
						logger.info(f'{adjuster_index}. Stoploss adjustment for trade {managedTrade.trade.id} at profit level {adjuster._trigger}% to ${adjusted_stoploss_price:.2f}')
						if managedTrade.template.is_credit_trade() == False and adjusted_stoploss_price <= 0:
							# Stop Loss order has not been placed yet.
							logger.info(f'Stoploss price is invalid. Not placing stop loss order for trade {managedTrade.trade.id}')
							break
						
						if managedTrade.stopLossOrder.status == None:
							# Stop Loss order has not been placed yet.
							managedTrade.stopLossOrder.price = adjusted_stoploss_price
							try:
								await broker_connector.placeOrder(managedTrade, managedTrade.stopLossOrder, parent_order = managedTrade.entryOrder)
								managedTrade.stopLossOrder.status = OrderStatus.OPEN
							except PlaceOrderException as e:
								logger.error(f"Failed to place stop loss order: {e.reason}")
						else:
							await broker_connector.adjustOrder(managedTrade, managedTrade.stopLossOrder, adjusted_stoploss_price)
					break
		if managedTrade.template.is_credit_trade() and len(managedTrade.stopLossOrder.legs) > 1:
			remaining_long_legs = False
			managedTrade.long_legs_removed = False
			for leg in managedTrade.stopLossOrder.legs[:]:
				if leg.action == OrderAction.BUY: # Watch long leg
					strike_price_data = broker_connector.get_option_strike_price_data(leg.symbol, leg.expiration, leg.strike)
					bid_price = strike_price_data.callBid if leg.right == OptionRight.CALL else strike_price_data.putBid
					if bid_price <= 0:
						# This leg needs to be removed from the stop loss order
						logger.info(f'Long leg of stop loss order at strike {leg.strike} for trade {managedTrade.trade.id} has no bid price anymore. Removing leg from stop loss order.')
						managedTrade.stopLossOrder.legs.remove(leg)
						managedTrade.long_legs_removed = True
					else:
						remaining_long_legs = True

			if managedTrade.long_legs_removed:
				await broker_connector.cancel_order(managedTrade.stopLossOrder) # Cancel the old order. Order Monitoring will create new one
				if not remaining_long_legs:
					# The remaining Short legs must be reverted
					for leg in managedTrade.stopLossOrder.legs:
						if leg.action == OrderAction.SELL:
							leg.action = OrderAction.BUY
						else:
							leg.action = OrderAction.SELL
					if managedTrade.template.is_credit_trade():
						if managedTrade.stopLossOrder:
							managedTrade.stopLossOrder.price = managedTrade.stopLossOrder.price * -1
							if managedTrade.stopLossOrder.action == OrderAction.SELL_TO_CLOSE:
								managedTrade.stopLossOrder.action = OrderAction.BUY_TO_CLOSE
							else:
								managedTrade.stopLossOrder.action = OrderAction.SELL_TO_CLOSE
						if managedTrade.takeProfitOrder:
							managedTrade.takeProfitOrder.price = managedTrade.takeProfitOrder.price * -1
							if managedTrade.takeProfitOrder.action == OrderAction.SELL_TO_CLOSE:
								managedTrade.takeProfitOrder.action = OrderAction.BUY_TO_CLOSE
							else:
								managedTrade.takeProfitOrder.action = OrderAction.SELL_TO_CLOSE

	async def _check_and_adjust_delta(self, managedTrade: ManagedTrade):
		"""
		Checks and adjusts the delta for the managed trade
		"""
		for adjuster in managedTrade.delta_adjusters:
			# Check if the from time for the adjuster is reached already
			if adjuster.from_time.time() > datetime.now().time():
				continue
			
			# If Position Delta is > defined threshold -> an adjustment must be performed.
			relevant_delta = round(abs(managedTrade.current_delta) * 100, 1)
			logger.debug(f'Trade {managedTrade.trade.id} - Delta: {relevant_delta}')
			if relevant_delta > adjuster.threshold and len(managedTrade.adjustment_orders) == 0:
				logger.info(f'Adjusting delta for trade {managedTrade.trade.id} with current delta {managedTrade.current_delta} and threshold {adjuster.threshold}')
				from optrabot.tradinghubclient import TradinghubClient, NotificationType
				notification_message = '📋 Trade ' + str(managedTrade.trade.id) + ': Delta @' + str(relevant_delta) + '. Adjustment required!'
				await TradinghubClient().send_notification(NotificationType.INFO, notification_message) 
				adjustment_orders = adjuster.execute(managedTrade)
				if adjustment_orders:
					managedTrade.adjustment_orders += adjustment_orders
					self._backgroundScheduler.add_job(self._process_adjustment_orders, id='ExecuteDeltaAdjustment ' + str(managedTrade.trade.id), args=[managedTrade], misfire_grace_time = None)

	async def _check_and_perform_early_exit(self, managed_trade: ManagedTrade) -> bool:
		"""
		Checks if an early exit condition for the trade is met and closes the trade
		if necessary.
		In case of the trade is closed, it returns true, otherwise false
		"""
		if managed_trade.closing_order != None:
			logger.debug(f'Trade {managed_trade.trade.id} already has a closing order. No early exit check required any further.')
			return False
		
		early_exit = managed_trade.template.get_early_exit()
		if early_exit:
			if early_exit.type == EarlyExitTriggerType.Breakeven:
				brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managed_trade.template.account)
				underlying_price = brokerConnector.getLastPrice(symbol=managed_trade.entryOrder.symbol)
				breakeven_reached = False
				for leg in managed_trade.current_legs:
					if leg.action == OrderAction.SELL:
						if leg.right == OptionRight.CALL:
							breakeven = float(leg.strike) + abs(managed_trade.entryOrder.averageFillPrice)
							if underlying_price >= breakeven:
								breakeven_reached = True
								break
						elif leg.right == OptionRight.PUT:
							breakeven = float(leg.strike) - abs(managed_trade.entryOrder.averageFillPrice)
							if underlying_price <= breakeven:
								breakeven_reached = True
								break
				if breakeven_reached:
					# Trade must be closed
					logger.debug(f'Breakeven reached for trade {managed_trade.trade.id}. Closing trade now.')
					from optrabot.tradinghubclient import TradinghubClient, NotificationType
					notification_message = '📋 Trade ' + str(managed_trade.trade.id) + ': Breakeven reached. Position will be closed now.'
					await TradinghubClient().send_notification(NotificationType.INFO, notification_message) 
					self._backgroundScheduler.add_job(self._create_closing_order, id='CreateClosingOrder' + str(managed_trade.trade.id), args=[managed_trade], misfire_grace_time = None)
					return True
		return False

	def _composeOrderReference(self, managedTrade: ManagedTrade, action: str) -> str:
		"""
		Composes the order reference for the given trade and action
		"""
		orderReference = 'OTB (' + str(managedTrade.trade.id) + '): ' + managedTrade.template.name + ' - ' + action
		return orderReference
	
	def _round_order_price(self, broker_connector: BrokerConnector, order: Order, price: float) -> float:
		"""
		Rounds the given price to the tick size or if it is a single legged order to the minimum allowed price increment
		"""
		symbolInformation = symbolInfo.symbol_infos[order.symbol]
		roundBase = symbolInformation.multiplier * symbolInformation.quote_step
		# If there is on leg only, the round base depends on the price and the brokers rules
		if len(order.legs) == 1:
			leg = order.legs[0]
			roundBase = broker_connector.get_min_price_increment(price) * symbolInformation.multiplier
		return OptionHelper.roundToTickSize(price, roundBase)

	async def _performEODTasks(self):
		"""
		Performs the end of day tasks at market close
		- Cancel any open orders
		"""
		logger.info('Performing EOD tasks ...')
		has_active_trades = False
		for managedTrade in self._trades:
			if managedTrade.isActive():
				logger.info(f'Trade {managedTrade.trade.id} is still active.')
				has_active_trades = True
				managedTrade.expired = True
				brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
				if not brokerConnector:
					continue
				open_orders = 0
				if managedTrade.stopLossOrder:
					if managedTrade.stopLossOrder.status != OrderStatus.FILLED:
						logger.info(f'Cancelling Stop Loss order for trade {managedTrade.trade.id}')
						open_orders += 1
						await brokerConnector.cancel_order(managedTrade.stopLossOrder)
				if managedTrade.takeProfitOrder:
					if managedTrade.stopLossOrder and managedTrade.stopLossOrder.ocaGroup == managedTrade.takeProfitOrder.ocaGroup:
						logger.info(f'Take Profit order is cancelled automatically.')
					else:
						if managedTrade.takeProfitOrder.status != None and managedTrade.takeProfitOrder.status != OrderStatus.FILLED:
							logger.info(f'Cancelling Take Profit order for trade {managedTrade.trade.id}')
							open_orders += 1
							await brokerConnector.cancel_order(managedTrade.takeProfitOrder)
				if open_orders == 0:
					logger.info(f'No orders to be cancelled for trade {managedTrade.trade.id}.')
		if has_active_trades == False:
			logger.info('no active trades found. Nothing to do')

	async def _performEODSettlement(self):
		"""
		Performs the end of day settlement tasks.
		Open Trades, which are expired get settled and closed.
		"""
		logger.info('Performing EOD Settlement ...')
		for managedTrade in self._trades:
			if managedTrade.expired == True and managedTrade.status == 'OPEN':
				logger.info(f'Settling and closing trade {managedTrade.trade.id}')
				broker_connector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
				settlement_price = broker_connector.getLastPrice(managedTrade.entryOrder.symbol)
				logger.debug(f'Last price for symbol {managedTrade.entryOrder.symbol} is {settlement_price}')
				managedTrade.status = 'EXPIRED'
				managedTrade.trade.status = 'EXPIRED'
				with Session(get_db_engine()) as session:
					crud.update_trade(session, managedTrade.trade)
				logger.info(f'Trade {managedTrade.trade.id} has been settled and closed.')

		for value in BrokerFactory().get_broker_connectors().values():
			broker_connector: BrokerConnector = value
			if broker_connector.isConnected() == True:
				await broker_connector.eod_settlement_tasks()

	def _strikes_from_order(self, order: Order) -> str:
		"""
		Returns the strike prices from the legs of the given order
		"""
		strikes = ''
		for leg in order.legs:
			if strikes != '':
				strikes += '/'
			strikes += str(leg.strike)
		return strikes

	async def _trackEntryOrder(self, managedTrade: ManagedTrade):
		"""
		Tracks the execution of the entry order
		"""
		jobId = 'TrackEntryOrder' + str(managedTrade.trade.id)
		logger.debug(f'Tracking entry order for trade {managedTrade.trade.id} on account {managedTrade.template.account}')
		if not managedTrade in self._trades:
			logger.info(f'Entry order for trade {managedTrade.trade.id} has been cancelled.')
			self._backgroundScheduler.remove_job(jobId)
			return
		
		if managedTrade.entryOrder.status == OrderStatus.FILLED:
			logger.debug(f'Entry order for trade {managedTrade.trade.id} is filled already. Stop tracking it')
			self._backgroundScheduler.remove_job(jobId)
			return

		brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
		if brokerConnector == None:
			logger.error(f'No active broker connection found for account {managedTrade.template.account}. Unable to adjust entry order')
			return
		
		if brokerConnector.isConnected() == False:
			logger.error(f'Broker connection for account {managedTrade.template.account} is not connected. Unable to adjust entry order')
			return
		
		if brokerConnector.isTradingEnabled() == False:
			logger.error(f'Trading is disabled for account {managedTrade.template.account}. Unable to adjust entry order')
			return
		
		# Angepassten Preis berechnen und prüfen ob er über dem Minimum liegt
		symbol_info = symbolInfo.symbol_infos[managedTrade.entryOrder.symbol]
		round_base = symbol_info.multiplier * symbol_info.quote_step
		calc_adjusted_price = managedTrade.entryOrder.price + managedTrade.template.adjustmentStep

		# If the calculated Price is below the midprice, adjust it to the midprice...to prevent the market running away
		calculated_mid_price = self._calculateMidPrice(brokerConnector, managedTrade.entryOrder)
		if calc_adjusted_price < calculated_mid_price:
			logger.info('Calculated adjusted price is below current mid price. Adjusting to order price to mid price.')
			calc_adjusted_price = calculated_mid_price

		if len(managedTrade.entryOrder.legs) == 1:
			# For Single Leg orders the round base depends on the price and the brokers rules
			round_base = brokerConnector.get_min_price_increment(calc_adjusted_price) * symbol_info.multiplier
		adjustedPrice = OptionHelper.roundToTickSize(calc_adjusted_price, round_base)

		# The adjusted price must not cross zero
		if (managedTrade.entryOrder.price < 0 and adjustedPrice >= 0) or (managedTrade.entryOrder.price > 0 and adjustedPrice <= 0):
			logger.info('Cannot adjust the order anymore. Stopping the adjustement of the order')
			self._backgroundScheduler.remove_job(jobId)
			return

		logger.info('Adjusting entry order. Current Limit Price: {} Adjusted Limit Price: {}', OptionHelper.roundToTickSize(managedTrade.entryOrder.price), adjustedPrice)

		if not managedTrade.template.meetsMinimumPremium(adjustedPrice):
			logger.info('Adjusted price does not meet minimum premium requirement. Canceling entry order')
			# TODO: Implement cancel order
			raise NotImplementedError

		if await brokerConnector.adjustOrder(managedTrade, managedTrade.entryOrder, adjustedPrice) == True:
			managedTrade.entryOrder.price = adjustedPrice

	async def _trackClosingOrder(self, managed_trade: ManagedTrade):
		"""
		Track the closing order of the given trade and adjust the price to get filled
		"""
		job_id = 'TrackClosingOrder' + str(managed_trade.trade.id)
		logger.debug(f'Tracking closing order for trade {managed_trade.trade.id} on account {managed_trade.template.account}')

		if managed_trade.closing_order.status == OrderStatus.FILLED:
			logger.debug(f'Closing order for trade {managed_trade.trade.id} is filled already. Stop tracking it')
			self._backgroundScheduler.remove_job(job_id)
			return
		
		brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managed_trade.template.account)
		if brokerConnector == None:
			logger.error(f'No active broker connection found for account {managed_trade.template.account}. Unable to adjust closing order')
			return

		if brokerConnector.isTradingEnabled() == False:
			logger.error(f'Trading is disabled for account {managed_trade.template.account}. Unable to adjust closing order')
			return
		
		# Calculate the adjusted price
		symbol_info = symbolInfo.symbol_infos[managed_trade.entryOrder.symbol]
		round_base = symbol_info.multiplier * symbol_info.quote_step
		if managed_trade.closing_order.price_effect == PriceEffect.DEBIT:
			# Debit Order - increase the price to get filled
			adjusted_price = managed_trade.closing_order.price + managed_trade.template.adjustmentStep
		else:
			# Credit Order - decrease the price to get filled
			adjusted_price = managed_trade.closing_order.price - managed_trade.template.adjustmentStep
		#if managed_trade.template.is_credit_trade():
		#	adjusted_price = managed_trade.closing_order.price - managed_trade.template.adjustmentStep
		#else:
		#	adjusted_price = managed_trade.closing_order.price + managed_trade.template.adjustmentStep

		if len(managed_trade.entryOrder.legs) == 1:
			# For Single Leg orders the round base depends on the price and the brokers rules
			round_base = brokerConnector.get_min_price_increment(adjusted_price) * symbol_info.multiplier
		adjusted_price = OptionHelper.roundToTickSize(adjusted_price, round_base)

		logger.info('Adjusting closing order. Current Limit Price: {} Adjusted Limit Price: {}', OptionHelper.roundToTickSize(managed_trade.closing_order.price), adjusted_price)

		if await brokerConnector.adjustOrder(managed_trade, managed_trade.closing_order, adjusted_price) == True:
			managed_trade.closing_order.price = adjusted_price

	async def _create_closing_order(self, managed_trade: ManagedTrade):
		"""
		Creates the closing order for the given trade
		"""
		logger.debug(f'Acquiring Lock for closing order for trade {managed_trade.trade.id}')
		async with self._lock:
			logger.debug(f'Creating closing order for trade {managed_trade.trade.id}')
			brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managed_trade.template.account)
			if brokerConnector == None:
				logger.error(f'No active broker connection found for account {managed_trade.template.account}. Unable to create closing order')
				return
			
			logger.debug(f'Current position value {managed_trade.current_price}')
			closing_order_legs: List[Leg] = []
			for current_leg in managed_trade.current_legs:
				if current_leg.action == OrderAction.BUY and current_leg.bidPrice <= 0:
					logger.info(f'Leg with strike {current_leg.strike} has no bid price. It will not be closed')
					continue
				# Invert the leg actions for the closing order.
				closing_leg = copy.deepcopy(current_leg)
				if current_leg.action == OrderAction.SELL:
					closing_leg.action = OrderAction.BUY
				elif current_leg.action == OrderAction.BUY:
					closing_leg.action = OrderAction.SELL
				closing_order_legs.append(closing_leg)
			closing_price = OptionHelper.roundToTickSize(abs(managed_trade.current_price), 5)
			closing_order = Order(symbol=managed_trade.trade.symbol, legs=closing_order_legs, action=OrderAction.SELL_TO_CLOSE, quantity=managed_trade.template.amount, type=OrderType.LIMIT, price=closing_price)
			closing_order.orderReference = self._composeOrderReference(managed_trade, 'Close')

			try:
				await brokerConnector.prepareOrder(closing_order, True)
			except PrepareOrderException as e:
				logger.error(f'Failed to prepare closing order. Reason: {e.reason}')
				return

			try:
				await brokerConnector.placeOrder(managed_trade, closing_order)
				managed_trade.closing_order = closing_order
				managed_trade.closing_order.status = OrderStatus.OPEN
				# Now Track the closing order and adjust the price to get filled
				self._backgroundScheduler.add_job(self._trackClosingOrder, 'interval', seconds=5, id='TrackClosingOrder' + str(managed_trade.trade.id), args=[managed_trade], max_instances=1, misfire_grace_time=None)

			except PlaceOrderException as e:
				logger.error(f'Failed to place the closing order for trade {managed_trade.trade.id}: {e.reason}')
				notification_message = f'Failed to close trade {managed_trade.trade.id}'
				from optrabot.tradinghubclient import TradinghubClient, NotificationType
				await TradinghubClient().send_notification(NotificationType.INFO, notification_message) 

			# TODO: At the end the stop loss and/or take profit orders need to be cancelled if they're in place.
		logger.debug(f'Releasing Lock for closing order creation for trade {managed_trade.trade.id}')

	async def _createTakeProfitAndStop(self, managedTrade: ManagedTrade):
		"""
		Creates the take profit and stop loss orders for the given trade
		"""
		from optrabot.tradetemplate.processor.templateprocessor import TemplateProcessor
		logger.debug(f'Acquiring Lock for TP SL creation for trade {managedTrade.trade.id}')
		async with self._lock:
			logger.debug(f'Creating take profit and stop loss orders for trade {managedTrade.trade.id}')
			brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
			if brokerConnector == None:
				logger.error(f'No active broker connection found for account {managedTrade.template.account}. Unable to create take profit and stop loss orders')
				return
			
			managedTrade.entry_price = brokerConnector.getFillPrice(managedTrade.entryOrder)
			logger.debug(f'Fill price for entry order was {managedTrade.entry_price}')

			templateProcessor = TemplateProcessor().createTemplateProcessor(managedTrade.template)

			managedTrade.setup_stoploss_adjusters()
			managedTrade.setup_delta_adjusters()

			notification_message = '⚖️ Trade ' + str(managedTrade.trade.id) + ': following orders attached...'

			# Create and Prepare the Take Profit Order if a take profit is defined in the template
			orderPlaced = False
			if managedTrade.template.hasTakeProfit():
				managedTrade.takeProfitOrder = templateProcessor.composeTakeProfitOrder(managedTrade, managedTrade.entry_price)
				managedTrade.takeProfitOrder.orderReference = self._composeOrderReference(managedTrade, 'TP')
			
				try:
					await brokerConnector.prepareOrder(managedTrade.takeProfitOrder, False)
				except PrepareOrderException as e:
					logger.error(f'Failed to prepare take profit order. Reason: {e.reason}')
					return
			else:
				logger.info(f'Template {managedTrade.template.name} does not have a take profit defined. No take profit order will be created.')

			# Create and Prepare the Stop Loss Order
			if managedTrade.template.hasStopLoss():
				managedTrade.stopLossOrder = templateProcessor.composeStopLossOrder(managedTrade, managedTrade.entry_price)
				managedTrade.stopLossOrder.orderReference = self._composeOrderReference(managedTrade, 'SL')
				try:
					await brokerConnector.prepareOrder(managedTrade.stopLossOrder, False)
				except PrepareOrderException as e:
					logger.error(f'Failed to prepare stop loss order. Reason: {e.reason}')
					return
			else:
				logger.info(f'Template {managedTrade.template.name} does not have a stop loss defined. No stop loss order will be created.')
			
			# Set an OCA Group for the Take Profit and Stop Loss Orders if both are defined
			if managedTrade.takeProfitOrder != None and managedTrade.stopLossOrder != None:
				now = datetime.now()
				ocaGroup = str(managedTrade.trade.id) + '_' + now.strftime('%H%M%S')
				managedTrade.takeProfitOrder.ocaGroup = ocaGroup
				managedTrade.stopLossOrder.ocaGroup = ocaGroup

			if brokerConnector.oco_as_complex_order() and managedTrade.takeProfitOrder != None and managedTrade.stopLossOrder != None:
				# Place the OCO order as one complex order
				orderPlaced = await brokerConnector.place_complex_order(managedTrade.takeProfitOrder, managedTrade.stopLossOrder, managedTrade.template)
				if orderPlaced == True:
					if managedTrade.takeProfitOrder != None:
						managedTrade.takeProfitOrder.status = OrderStatus.OPEN
						notification_message += f'\n*Take Profit:* ${managedTrade.takeProfitOrder.price:.2f}'
					if managedTrade.stopLossOrder != None:
						managedTrade.stopLossOrder.status = OrderStatus.OPEN
						notification_message += f'\n*Stop Loss:* ${managedTrade.stopLossOrder.price:.2f}'
			else:
				if managedTrade.takeProfitOrder != None:
					if managedTrade.template.has_soft_take_profit():
						logger.info(f'Template is using soft take profit. No take profit order will be created.')
						notification_message += f'\n*Take Profit (soft):* ${managedTrade.takeProfitOrder.price:.2f}'
						orderPlaced = True
					else:
						try:
							await brokerConnector.placeOrder(managedTrade, managedTrade.takeProfitOrder, parent_order = managedTrade.entryOrder)
							orderPlaced = True
							logger.debug(f'Take Profit order for account {managedTrade.account} placed.')
							managedTrade.takeProfitOrder.status = OrderStatus.OPEN
							notification_message += f'\n*Take Profit:* ${managedTrade.takeProfitOrder.price:.2f}'
						except PlaceOrderException as e:
							logger.error(f'Failed to place take profit order: {e.reason}')
				else:
					notification_message += '\n*Take Profit:* n/d'

				if managedTrade.stopLossOrder != None:
					if managedTrade.template.is_credit_trade() == False and managedTrade.stopLossOrder.price == 0:
						# Debit Trades with Stop Loss Price of 0 must not be placed here
						logger.info(f'Stop Loss order for trade {managedTrade.trade.id} has a price of 0. No stop loss order will send to broker.')
						notification_message += f'\n*Stop Loss:* ${managedTrade.stopLossOrder.price:.2f}'
					else:
						try:
							await brokerConnector.placeOrder(managedTrade, managedTrade.stopLossOrder, parent_order = managedTrade.entryOrder)
							orderPlaced = True
							logger.debug(f'Stop Loss order for account {managedTrade.account} placed.')
							managedTrade.stopLossOrder.status = OrderStatus.OPEN
							notification_message += f'\n*Stop Loss:* ${managedTrade.stopLossOrder.price:.2f}'
						except PlaceOrderException as e:
							logger.error(f'Failed to place stop loss order: {e.reason}')
				else:
					notification_message += '\n*Stop Loss:* n/d'

			# Send Telegram Notification via OptraBot Server
			if orderPlaced == True:
				from optrabot.tradinghubclient import TradinghubClient, NotificationType
				await TradinghubClient().send_notification(NotificationType.INFO, notification_message) 

		logger.debug(f'Releasing Lock for TP SL creation for trade {managedTrade.trade.id}')

	async def _monitorOpenTrades(self):
		"""
		Monitors the open trades and their orders
		"""
		now = datetime.now()
		for managedTrade in self._trades:
			if managedTrade.status != 'OPEN' or managedTrade.expired == True:
				continue

			self._update_current_price_and_delta(managedTrade)		

			await self._check_and_adjust_delta(managedTrade)

			if await self._check_and_perform_early_exit(managedTrade):
				# No further order management required if trade has been exited.
				continue

			# Check if stop loss order is in place
			if managedTrade.stopLossOrder != None and managedTrade.adjustment_orders == []:
				if managedTrade.stopLossOrder.status == OrderStatus.CANCELLED:
					logger.warning(f'Stop Loss order for open trade {managedTrade.trade.id} was cancelled. Reestablishing it.')
					await self._reestablishStopLossOrder(managedTrade)
				else:
					# Check if the stop loss order needs to be adjusted
					await self._check_and_adjust_stoploss(managedTrade)

			if managedTrade.template.has_soft_take_profit() == False:
				if managedTrade.takeProfitOrder != None and managedTrade.adjustment_orders == []:
					if managedTrade.takeProfitOrder.status == OrderStatus.CANCELLED:
						logger.warning(f'Take Profit order for open trade {managedTrade.trade.id} was cancelled. Restablishing it.')
						await self._reestablishTakeProfitOrder(managedTrade)
			elif managedTrade.takeProfitOrder != None:
				# Check every full minute if the take profit level of the soft take profit has been reached
				if now.minute != self._last_trade_monitoring_time.minute and managedTrade.takeProfitOrder.status == None:
					logger.debug(f'Check if Take Profit has been reached for trade {managedTrade.trade.id}')
					logger.debug(f'Current Price: {managedTrade.current_price:.2f} Take Profit Price: {managedTrade.takeProfitOrder.price:.2f}')
					take_profit_reached = True if (managedTrade.template.is_credit_trade() and managedTrade.current_price <= managedTrade.takeProfitOrder.price) or (not managedTrade.template.is_credit_trade() and managedTrade.current_price >= managedTrade.takeProfitOrder.price) else False
					if take_profit_reached:
						logger.info(f'Take Profit level has been reached for trade {managedTrade.trade.id}. Placing closing take profit order now.')
						
						brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
						if brokerConnector == None:
							logger.error(f'No active broker connection found for account {managedTrade.template.account}. Unable to create take profit and stop loss orders')
							continue
						
						managedTrade.takeProfitOrder.type = OrderType.MARKET
						try:
							await brokerConnector.prepareOrder(managedTrade.takeProfitOrder, False)
						except PrepareOrderException as e:
							logger.error(f'Failed to prepare take profit order. Reason: {e.reason}')
							continue

						try:
							await brokerConnector.placeOrder(managedTrade, managedTrade.takeProfitOrder, parent_order = managedTrade.entryOrder)
							logger.debug(f'Take Profit order for account {managedTrade.account} placed.')
							managedTrade.takeProfitOrder.status = OrderStatus.OPEN
							notification_message = '⚖️ Trade ' + str(managedTrade.trade.id) + ':'
							notification_message += f'\n*Soft Take Profit:* Placed market close order @ ${managedTrade.current_price:.2f}'
							from optrabot.tradinghubclient import TradinghubClient, NotificationType
							await TradinghubClient().send_notification(NotificationType.INFO, notification_message)
						except PlaceOrderException as e:
							logger.error(f'Failed to place take profit order: {e.reason}')
			
		self._last_trade_monitoring_time = now

	async def _reestablishStopLossOrder(self, managedTrade: ManagedTrade):
		"""
		Reestablishes the stop loss order for the given trade
		"""
		brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
		if brokerConnector == None:
			logger.error(f'No active broker connection found for account {managedTrade.template.account}. Unable to reestablish stop loss order')
			return
		
		managedTrade.stopLossOrder.status = OrderStatus.OPEN
		managedTrade.stopLossOrder.price = self._round_order_price(brokerConnector, managedTrade.stopLossOrder, managedTrade.stopLossOrder.price)
		try:
			await brokerConnector.prepareOrder(managedTrade.stopLossOrder, False)
		except PrepareOrderException as e:
			logger.error(f'Failed to prepare stop loss order. Reason: {e.reason}')
			return
		
		if brokerConnector.oco_as_complex_order() and managedTrade.takeProfitOrder != None and managedTrade.stopLossOrder != None:
			orderPlaced = await brokerConnector.place_complex_order(managedTrade.takeProfitOrder, managedTrade.stopLossOrder, managedTrade.template)
		else:
			try:
				await brokerConnector.placeOrder(managedTrade, managedTrade.stopLossOrder, parent_order = managedTrade.entryOrder)
				orderPlaced = True
			except PlaceOrderException as e:
				logger.error(f'Failed to place stop loss order: {e.reason}')
				orderPlaced = False

		if orderPlaced == True:
			logger.info(f'Stop Loss order for trade {managedTrade.trade.id} reestablished successfully.')

	async def _reestablishTakeProfitOrder(self, managedTrade: ManagedTrade):
		"""
		Reestablishes the take profit order for the given trade
		"""
		brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managedTrade.template.account)
		if brokerConnector == None:
			logger.error(f'No active broker connection found for account {managedTrade.template.account}. Unable to reestablish stop loss order')
			return
		
		managedTrade.takeProfitOrder.status = OrderStatus.OPEN
		managedTrade.takeProfitOrder.price = self._round_order_price(brokerConnector, managedTrade.takeProfitOrder, managedTrade.takeProfitOrder.price)
		try:
			await brokerConnector.prepareOrder(managedTrade.takeProfitOrder, False)
		except PrepareOrderException as e:
			logger.error(f'Failed to prepare take profit order. Reason: {e.reason}')
			return
		
		try:
			await brokerConnector.placeOrder(managedTrade, managedTrade.takeProfitOrder, parent_order = managedTrade.entryOrder)
			logger.info(f'Take Profit order for trade {managedTrade.trade.id} reestablished successfully.')
		except PlaceOrderException as e:
			logger.error(f'Failed to reestablish Take Profit order for trade {managedTrade.trade.id}. Reason: {e.reason}')
			return

	async def _reportExecutedTrade(self, managedTrade: ManagedTrade, contracts: int):
		"""
		Reports the filled amount of the executed trade to the OptraBot Hub
		It tries to report the event 3 times before giving up.
		"""
		from optrabot.tradinghubclient import TradinghubClient
		
		#executedContracts = 0
		#for leg in managedTrade.entryOrder.legs:
		#	executedContracts += abs(leg.quantity * filledAmount)

		additional_data = {
			'trade_id': managedTrade.trade.id,
			'account': managedTrade.template.account,
			'contracts': int(contracts)
		}
		reporterror = False
		tryCount = 0
		while tryCount < 3:
			try:
				await TradinghubClient().reportAction('CT', additional_data=json.dumps(additional_data))
				break
			except Exception as excp:
				reporterror = True
				tryCount += 1
		if reporterror == True:
			logger.error('Error reporting position open event to OptraBot Hub within 3 tries.')

	def _update_current_price_and_delta(self, managed_trade: ManagedTrade):
		"""
		Updates the current price and delta of the managed Trade based on the price data from the broker
		"""
		brokerConnector = BrokerFactory().getBrokerConnectorByAccount(managed_trade.template.account)
		if brokerConnector == None or brokerConnector.isConnected() == False:
			logger.error(f'No active broker connection found for account {managed_trade.template.account}. Unable to update current price')
			return
		
		total_price: float = 0
		total_delta: float = 0
		for leg in managed_trade.current_legs:
			current_leg_price_data = brokerConnector.get_option_strike_price_data(symbol=managed_trade.entryOrder.symbol, expiration=leg.expiration, strike=leg.strike)
			assert current_leg_price_data != None
			leg.midPrice = current_leg_price_data.getCallMidPrice() if leg.right == OptionRight.CALL else current_leg_price_data.getPutMidPrice()
			current_leg_delta = current_leg_price_data.callDelta if leg.right == OptionRight.CALL else current_leg_price_data.putDelta
			if leg.action == OrderAction.SELL:
				# If it was sell, price and delta have to be negated
				current_leg_delta *= -1
			leg.delta = current_leg_delta * leg.quantity
			leg.midPrice = leg.midPrice * leg.quantity
			
			total_price += leg.midPrice if leg.action == OrderAction.BUY else leg.midPrice * -1
			total_delta += leg.delta

		total_price = abs(total_price)
		managed_trade.current_price = total_price
		managed_trade.current_delta = total_delta
		logger.trace(f'Current price for trade {managed_trade.trade.id} is {managed_trade.current_price:.2f}')

		# securityStatus = {}
		# for element in managed_trade.transactions:
		# 	transaction: schemas.Transaction = element
		# 	security = transaction.sectype + str(transaction.expiration) + str(transaction.strike)
		# 	change = transaction.contracts
		# 	fees = transaction.fee + transaction.commission
		# 	if transaction.type == OrderAction.SELL or transaction.type == 'EXP':
		# 		change = change * -1
		# 	try:
		# 		statusData = securityStatus[security]
		# 		statusData.openContracts += change
		# 	except KeyError:
		# 		statusData = SecurityStatusData(securityId=security, sec_type=transaction.sectype, strike=transaction.strike, expiration=transaction.expiration, openContracts=change, fees=transaction.fee, unrealPNL=0, realPNL = 0)
		# 		securityStatus.update({security:statusData})
		# 	statusData.unrealPNL -= ((transaction.price * symbol_info.multiplier * change) + fees)
		
		# total_unreal_pnl = 0
		# for security, statusData in securityStatus.items():
		# 	if statusData.openContracts == 0:
		# 		# contract transactions are closed
		# 		statusData.realPNL = statusData.unrealPNL
		# 		statusData.unrealPNL = 0
		# 	else:
		# 		# Contract is still open. Get current price data and
		# 		# calculate the unrealized PNL
		# 		option_price_data = brokerConnector.get_option_strike_price_data(symbol=managed_trade.entryOrder.symbol, expiration=statusData.expiration, strike=statusData.strike)
		# 		assert option_price_data != None
		# 		current_price = option_price_data.getCallMidPrice() if statusData.sec_type == OptionRight.CALL else option_price_data.getPutMidPrice()
		# 		assert current_price != None
		# 		#original_cost = (transaction.price * symbol_info.multiplier * statusData.openContracts)
		# 		current_ta_price = current_price * statusData.openContracts
		# 		#current_cost = (current_price * symbol_info.multiplier * statusData.openContracts * -1)
		# 		#unreal_pnl = current_cost - original_cost
		# 		total_price
	async def _deleteTrade(self, managedTrade: ManagedTrade, reason: str):
		"""
		Deletes the trade from the database and the list of managed trades.
		
		Args:
			managedTrade: Trade to be deleted
			reason: Reason for deletion
		"""
		logger.debug(f"Deleting trade {managedTrade.trade.id} from database because {reason}")
		
		# Trade aus der Datenbank löschen
		with Session(get_db_engine()) as session:
			crud.delete_trade(session, managedTrade.trade)
		
		# Trade aus der Liste der verwalteten Trades entfernen
		if managedTrade in self._trades:
			self._trades.remove(managedTrade)
		
		logger.debug(f"Trade {managedTrade.trade.id} successfully removed")
