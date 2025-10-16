import asyncio
from datetime import datetime
from datetime import timedelta
from eventkit import Event
from optrabot.broker.order import Execution, Order, OrderStatus
from optrabot import crud, schemas
from optrabot.broker.brokerconnector import BrokerConnector
from optrabot.broker.c2connector import C2Connector
from optrabot.broker.ibtwsconnector import IBTWSTConnector
from optrabot.broker.tastytradeconnector import TastytradeConnector
from optrabot.database import get_db_engine
import optrabot.config as optrabotcfg
from optrabot.models import Account
from optrabot.util.singletonmeta import SingletonMeta
import pandas_market_calendars as mcal
import pytz
from sqlalchemy.orm import Session
from loguru import logger
from typing import Dict, List

class BrokerFactory(metaclass=SingletonMeta):
	def __init__(self):
		self._connectors: Dict[str, BrokerConnector] = {}
		self.orderStatusEvent = Event('orderStatusEvent')
		self.commissionReportEvent = Event('commissionReportEvent')
		self.orderExecutionDetailsEvent = Event('orderExecutionDetailsEvent')
		self._symbols = ['SPX', 'VIX']
		self._shutingdown = False
		self._session_start : datetime = None
		self._session_end : datetime = None
		self._session_price_end : datetime = None
		self.update_trading_session_data()

	async def createBrokerConnectors(self):
		""" Creates broker connections from the given configuration
		"""
		twsConnector = IBTWSTConnector()
		if twsConnector.isInitialized():
			self._connectors[twsConnector.id] = twsConnector
		tastyConnector = TastytradeConnector()
		if tastyConnector.isInitialized():
			self._connectors[tastyConnector.id] = tastyConnector
		c2Connector = C2Connector()
		if c2Connector.isInitialized():
			self._connectors[c2Connector.id] = c2Connector
		
		for value in self._connectors.values():
			connector : BrokerConnector = value
			connector.connectedEvent += self._onBrokerConnected
			connector.commissionReportEvent += self._onCommissionReport
			connector.disconnectedEvent += self._onBrokerDisconnected
			connector.connectFailedEvent += self._onBrokerConnectFailed
			connector.orderStatusEvent += self._onOrderStatus
			connector.orderExecutionDetailsEvent += self._onOrderExecutionDetailsEvent
			await connector.connect()

	def check_accounts_after_all_brokers_connected(self):
		"""
		Checks if the accounts configured in the trade template are available in the broker connections.
		If not all connectors are connected yet, this method does nothing.
		"""
		config :optrabotcfg.Config = optrabotcfg.appConfig

		all_accounts = []
		for connector in self._connectors.values():
			if not connector.isConnected():
				return
			else:
				all_accounts += connector.getAccounts()

		tradeTemplates = config.getTemplates()	
		for template in tradeTemplates:
			if template.account:
				accountFound = False
				for account in all_accounts:
					if account.id == template.account:
						accountFound = True
						break
				if not accountFound:
					logger.error(f'Account {template.account} configured in Trade Template {template.name} is not available in any connected Broker!')

	async def check_price_data(self):
		"""
		Checks if the connected brokers are still delivering price data during the trading session
		"""
		now = datetime.now(pytz.timezone('US/Eastern'))
		if self._session_start and self._session_end:
			if now >= self._session_start and now <= self._session_price_end:
				logger.debug('Checking price data are up-to-date for the connected brokers')
				for connector in self.get_broker_connectors().values():
					if connector.isConnected():
						last_update_time = connector.get_last_option_price_update_time()
						if last_update_time is None or (now - last_update_time).total_seconds() > 30:
							from optrabot.tradinghubclient import TradinghubClient, NotificationType
							message = f'Price data for {connector.broker} is not up-to-date! Last update: {last_update_time}'
							await TradinghubClient().send_notification(NotificationType.WARN, f'⚠️ {message}')
							logger.warning(message)
						else:
							logger.debug(f'Price data for {connector.broker} is up-to-date. Last update: {last_update_time}')

	async def new_day_start(self):
		"""
		Called when a new day starts
		"""
		for value in self._connectors.values():
			connector : BrokerConnector = value
			# Request ticker data for the new day
			if connector.isConnected():
				await connector.requestTickerData(self._symbols)
			else:
				logger.warning(f'Broker {connector.broker} is not connected yet. Not requesting ticker data now.')

		self.update_trading_session_data()

	def get_broker_connectors(self) -> Dict[str, BrokerConnector]:
		"""
		Returns the broker connectors
		"""
		return self._connectors

	def getBrokerConnectorByAccount(self, account: str) -> BrokerConnector:
		""" Returns the broker connector for the given account
		"""
		for value in self._connectors.values():
			connector : BrokerConnector = value
			accounts = connector.getAccounts()
			for acc in accounts:
				if acc.id == account:
					return connector
		return None
	
	def get_connector_by_id(self, id: str) -> BrokerConnector:
		""" 
		Returns the broker connector for the given id
		"""
		return self._connectors.get(id)
	
	def get_trading_satus_info(self) -> str:
		""" 
		Returns a string with the status of the broker connectors
		"""
		status = ''
		for value in self._connectors.values():
			connector : BrokerConnector = value
			connector_trading_enabled = 'Yes' if connector.isTradingEnabled() == True else 'No'
			status += f'{connector.broker}: {connector_trading_enabled} '
		return status
	
	def is_market_open(self) -> bool:
		""" 
		Returns True if the market is open
		"""
		if self._session_start and self._session_end:
			now = datetime.now(pytz.timezone('America/New_York'))
			if now >= self._session_start and now <= self._session_end:
				return True
		return False
	
	def is_trading_day(self) -> bool:
		"""
		Returns True if today is a trading day
		"""
		if self._session_start == None and self._session_end == None:
			return False
		return True

	def is_shutting_down(self) -> bool:
		""" 
		Returns True if the BrokerFactory is shutting down
		"""
		return self._shutingdown

	def update_trading_session_data(self):
		try:
			cme = mcal.get_calendar('CBOE_Index_Options')
			now = datetime.now(pytz.timezone('America/New_York'))
			today_schedule = cme.schedule(start_date=now.date(), end_date=now.date())

			if today_schedule.empty:
				self._session_start = None
				self._session_end = None
				self._session_price_end = None
				logger.info('No trading session today.')
			else:
				self._session_start = today_schedule.iloc[0]['market_open']
				self._session_end = today_schedule.iloc[0]['market_close']
				self._session_price_end = self._session_end - timedelta(minutes=self._session_end.minute) if self._session_end.minute > 0 else self._session_end
				logger.info(f'Today trading - Session start: {self._session_start} Session end: {self._session_end}')
		except Exception as e:
			logger.error(f'Error while determining trading session start and end: {e}')

	async def _onBrokerConnected(self, brokerConnector: BrokerConnector):
		""" 
		Called when a broker connection has been established
		the BrokerConnector object is passed as parameter
		"""
		logger.info('Broker {} connected successfully.', brokerConnector.id)
		accounts = brokerConnector.getAccounts()
		self._updateAccountsInDatabase(accounts)

		self.check_accounts_after_all_brokers_connected()
		
		await brokerConnector.requestTickerData(self._symbols)

	def _onBrokerDisconnected(self, brokerConnector):
		""" 
		Called when a broker connection has been disconnected
		the BrokerConnector object is passed as parameter
		"""
		logger.warning('Broker {} disconnected, attempting to reconnect in 30 seconds ...', brokerConnector.id)
		asyncio.create_task(self._reconnect_broker_task(brokerConnector))

	def _onCommissionReport(self,  order: Order, execution_id: str, commission: float, fee: float):
		""" 
		Called when a commission report has been received
		"""
		self.commissionReportEvent.emit(order, execution_id, commission, fee)

	def _onOrderExecutionDetailsEvent(self, order: Order, execution: Execution):
		""" 
		Called when an order execution details event has been received
		"""
		self.orderExecutionDetailsEvent.emit(order, execution)

	def _onOrderStatus(self, order: Order, status: OrderStatus, filledAmount: int = 0):
		""" 
		Called when an order status has changed
		"""
		self.orderStatusEvent.emit(order, status, filledAmount)

	def _onBrokerConnectFailed(self, brokerConnector):
		""" 
		Called when a broker connection has failed to connect
		"""
		logger.error('Failed to connect to broker {}, attempting to reconnect in 30 seconds ...', brokerConnector.id)
		asyncio.create_task(self._reconnect_broker_task(brokerConnector))

	async def _reconnect_broker_task(self, brokerConnector: BrokerConnector):
		"""
		Asynchronous task to reconnect a broker after a disconnect
		"""
		await asyncio.sleep(30)
		await brokerConnector.connect()

	def _updateAccountsInDatabase(self, accounts: List[Account]):
		"""
		Updates the account information in the database if required
		"""
		with Session(get_db_engine()) as session:
			for account in accounts:
				logger.debug('Managed Account at {}: {}', account.broker, account.id)
				known_account = crud.get_account(session, account.id)
				if known_account == None:
					logger.debug('Account is new. Adding it to the Database')
					new_account = schemas.AccountCreate( id = account.id, name = account.name, broker = account.broker, pdt = account.pdt)
					crud.create_account(session, new_account)
					logger.debug('Account {} created in database.', account.id)
				else:
					if account.name != known_account.name or account.pdt != known_account.pdt:
						logger.debug('Account {} has changed. Updating it in the database.', account.id)
						known_account.name = account.name
						known_account.pdt = account.pdt
						crud.update_account(session, known_account)

	async def shutdownBrokerConnectors(self):
		""" Shuts down all broker connections
		"""
		self._shutingdown = True
		for value in self._connectors.values():
			connector : BrokerConnector = value
			connector.disconnectedEvent -= self._onBrokerDisconnected
			connector.connectFailedEvent -= self._onBrokerConnectFailed
			connector.connectedEvent -= self._onBrokerConnected
			connector.orderStatusEvent -= self._onOrderStatus
			if connector.isConnected():
				await connector.disconnect()
		
