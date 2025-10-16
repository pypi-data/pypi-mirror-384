from abc import ABC, abstractmethod
from datetime import date
import datetime as dt
from typing import List
from eventkit import Event
from loguru import logger

from optrabot.broker.optionpricedata import OptionStrikeData, OptionStrikePriceData
from optrabot.broker.order import Execution, Order as GenericOrder, OrderStatus
from optrabot.config import Config
from optrabot.models import Account
import optrabot.symbolinfo as symbolInfo
from optrabot.tradetemplate.templatefactory import Template
from optrabot.managedtrade import ManagedTrade
from optrabot.exceptions import PlaceOrderException

class BrokerConnector(ABC):
	# Constants for Events
	EVENT_CONNECTED = 'connectedEvent'
	EVENT_CONNECT_FAILED = 'connectFailedEvent'
	EVENT_COMMISSION_REPORT = 'commissionReportEvent'
	EVENT_DISCONNECTED = 'disconnectedEvent'
	EVENT_ORDER_STATUS = 'orderStatusEvent'
	EVENT_ORDER_EXEC_DETAILS = 'orderExecutionDetailsEvent'

	def __init__(self) -> None:
		self._initialized = False
		self._createEvents()
		self.id = None		# ID of the connector
		self.broker = None	# ID of the broker
		self._tradingEnabled = False
		self._managedAccounts: List[Account] = []
		self._last_option_price_update_time: dt.datetime = None
		pass
	
	@abstractmethod
	async def cancel_order(self, order: GenericOrder):
		"""
		Cancels the given order
		"""
		pass

	@abstractmethod
	async def connect(self):
		""" 
		Establishes a connection to the broker
		"""
		logger.info('Connecting with broker {}', self.id)

	@abstractmethod
	async def disconnect(self):
		""" 
		Disconnects from the broker
		"""
		logger.info('Disconnecting from broker {}', self.id)

	@abstractmethod
	def isConnected(self) -> bool:
		""" 
		Returns True if the broker is connected
		"""
		pass

	@abstractmethod
	def getAccounts(self) -> List[Account]:
		""" 
		Returns the accounts managed by the broker connection
		"""
		pass

	def get_atm_strike(self, symbol:str) -> float:
		""" 
		Returns the ATM strike price for the given symbol based on the buffered option price data.
		If no data is available, it returns None.
		"""
		symbolData = self._symbolData[symbol]
		return symbolData.lastAtmStrike
	
	@abstractmethod
	async def prepareOrder(self, order: GenericOrder, need_valid_price_data: bool = True) -> None:
		"""
		Prepares the given order for execution.
		- Retrieve current market data for order legs

		Raises:
			PrepareOrderException: If the order preparation fails with a specific reason.
		"""

	def oco_as_complex_order(self) -> bool:
		""" 
		Returns True if the broker connection supports OCO orders in form of one complex order
		instead of two single orders
		"""
		return False

	@abstractmethod
	async def placeOrder(self, managed_trade: ManagedTrade, order: GenericOrder, parent_order: GenericOrder = None) -> None:
		""" 
		Places the given order for a managed account via the broker connection.
		
		Raises:
			PlaceOrderException: If the order placement fails with a specific reason.
		"""
		pass

	@abstractmethod
	async def place_complex_order(self, take_profit_order: GenericOrder, stop_loss_order: GenericOrder, template: Template) -> bool:
		""" 
		Places Take Profit and Stop Loss Order as single complex order
		"""
		pass

	@abstractmethod
	async def adjustOrder(self, managed_trade: ManagedTrade, order: GenericOrder, price: float) -> bool:
		""" 
		Adjusts the given order with the given new price
		"""
		pass

	@abstractmethod
	async def requestTickerData(self, symbols: List[str]):
		""" 
		Request ticker data for the given symbols and their options
		"""
		pass

	@abstractmethod
	def getFillPrice(self, order: GenericOrder) -> float:
		""" 
		Returns the fill price of the given order if it is filled
		"""
		pass

	def getLastPrice(self, symbol: str) -> float:
		""" 
		Returns the last price of the given symbol
		"""
		pass

	@abstractmethod
	def get_option_strike_data(self, symbol: str, expiration: date) -> OptionStrikeData:
		""" 
		Returns the option strike data for the given symbol and expiration. It is including
		prices and greeks.
		"""
		pass

	@abstractmethod
	def get_option_strike_price_data(self, symbol: str, expiration: date, strike: float) -> OptionStrikePriceData:
		""" 
		Returns the option strike price data for the given symbol, expiration, strike and right
		"""
		pass

	def get_last_option_price_update_time(self) -> dt.datetime:
		"""
		Returns the last update time of the option price data
		"""
		return self._last_option_price_update_time

	@abstractmethod
	def get_strike_by_delta(self, symbol: str, right: str, delta: int) -> float:
		""" 
		Returns the strike price based on the given delta based on the buffered option price data
		"""
		raise NotImplementedError()
	
	@abstractmethod
	def get_strike_by_price(self, symbol: str, right: str, price: float) -> float:
		""" 
		Returns the strike price based on the given premium price based on the buffered option price data
		"""
		raise NotImplementedError()

	def get_min_price_increment(self, price: float) -> float:
		""" 
		Returns the minimum price increment for the given option based on the given price.
		It's based on the information from Tastytrade Help Center article: https://support.tastytrade.com/support/s/solutions/articles/43000435374
		"""
		if price < 3:
			return 0.05
		else:
			return 0.1

	async def eod_settlement_tasks(self):
		"""
		Perform End of Day settlement tasks
		"""
		pass

	def uses_oco_orders(self) -> bool:
		""" 
		Returns True if the broker connection supports and uses OCO orders for managing take profit and stop loss
		"""
		return False

	def _createEvents(self):
		""" 
		Creates the events for the broker connection
		"""
		self.connectedEvent = Event(self.EVENT_CONNECTED)
		self.disconnectedEvent = Event(self.EVENT_DISCONNECTED)
		self.commissionReportEvent = Event(self.EVENT_COMMISSION_REPORT)
		self.connectFailedEvent = Event(self.EVENT_CONNECT_FAILED)
		self.orderStatusEvent = Event(self.EVENT_ORDER_STATUS)
		self.orderExecutionDetailsEvent = Event(self.EVENT_ORDER_EXEC_DETAILS)

	def _emitConnectedEvent(self):
		""" 
		Emits the connected event
		"""
		self.connectedEvent.emit(self)

	def _emitDisconnectedEvent(self):
		""" 
		Emits the disconnected event
		"""
		self._managedAccounts = []
		self.disconnectedEvent.emit(self)

	def _emitConnectFailedEvent(self):
		""" 
		Emits the broker connect failed event
		"""
		self.connectFailedEvent.emit(self)

	def _emitCommissionReportEvent(self, order: GenericOrder, execution_id: str, commission: float = 0, fee: float = 0):
		"""
		Emits the commission report event if commission and fee information are delivered
		for a execution which previously has been reported with the according execution_id.
		"""
		self.commissionReportEvent.emit(order, execution_id, commission, fee)

	def _emitOrderExecutionDetailsEvent(self, order: GenericOrder, execution: Execution):
		""" 
		Emits the order execution details event
		"""
		self.orderExecutionDetailsEvent.emit(order, execution)

	def _emitOrderStatusEvent(self, order: GenericOrder, status: OrderStatus, filledAmount: int = 0):
		""" 
		Emits the order status event. Filled amount holds the amount that has been filled with this
		order status change, if the status event is a "Filled" event.
		"""
		self.orderStatusEvent.emit(order, status, filledAmount)

	def isInitialized(self) -> bool:
		""" 
		Returns True if the broker connector is initialized
		"""
		return self._initialized

	def isTradingEnabled(self) -> bool:
		""" 
		Returns True if trading is enabled
		"""
		return self._tradingEnabled
	
	async def set_trading_enabled(self, enabled: bool, reason: str = None):
		""" 
		Sets the trading enabled flag with an optional reason which is being logged
		"""
		from optrabot.broker.brokerfactory import BrokerFactory
		self._tradingEnabled = enabled
		if reason:
			logger.debug('Trading enabled: {} - Reason: {}', enabled, reason)
			if enabled == False and not BrokerFactory().is_shutting_down() and BrokerFactory().is_market_open():
				from optrabot.tradinghubclient import TradinghubClient, NotificationType
				notification_message = '‼️ Trading with broker ' + self.broker + ' has been disabled'
				if reason:
					notification_message += ' due to: ' + reason 
				notification_message += '!'
				await TradinghubClient().send_notification(NotificationType.WARN, notification_message) 
				logger.error('Trading has been disabled: {}', reason)
		else:
			logger.debug('Trading enabled: {}', enabled)