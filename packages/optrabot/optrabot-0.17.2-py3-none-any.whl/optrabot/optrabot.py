import array
from collections import OrderedDict
import asyncio
import datetime as dt
import json
from fastapi import FastAPI
from ib_async import *
import logging
import webbrowser
from loguru import logger
import pytz
from sqlalchemy.orm import Session
from optrabot.broker.brokerconnector import BrokerConnector
from optrabot import schemas
from optrabot.broker.brokerfactory import BrokerFactory
from optrabot.marketdatatype import MarketDataType
from optrabot.optionhelper import OptionHelper
import optrabot.config as optrabotcfg
from optrabot.trademanager import TradeManager
from optrabot.tradetemplate.templatefactory import Template
import optrabot.symbolinfo as symbolInfo
from optrabot.tradetemplate.templatetrigger import TriggerType
from optrabot.tradetemplate.processor.templateprocessor import TemplateProcessor
from optrabot.signaldata import SignalData
from .tradinghubclient import TradinghubClient
import pkg_resources
from .database import *
from . import crud
from apscheduler.schedulers.asyncio import AsyncIOScheduler

optrabot_dev_version = '0.17.1'

def get_version() -> str:
	"""
	Returns the version of the package
	"""
	environment = os.environ.get('OPTRABOT_ENV', 'PROD')
	if environment != 'DEV':
		try:
			return pkg_resources.get_distribution('optrabot').version
		except pkg_resources.DistributionNotFound:
			return optrabot_dev_version 
	else:
		return optrabot_dev_version

class OptraBot():
	def __init__(self, app: FastAPI):
		self.app = app
		self._apiKey = None
		self.thc : TradinghubClient = None
		self._marketDataType : MarketDataType = None
		self.Version = get_version()
		self._backgroundScheduler = AsyncIOScheduler()
		self._backgroundScheduler.start()
			
	def __setitem__(self, key, value):
		setattr(self, key, value)

	def __getitem__(self, key):
		return getattr(self, key)
	
	async def startup(self):
		logger.info('OptraBot {version}', version=self.Version)
		# Read Config
		conf = optrabotcfg.Config("config.yaml")
		optrabotcfg.appConfig = conf
		self['config'] = conf
		conf.logConfigurationData()
		conf.readTemplates()
		updateDatabase()
		self.thc = TradinghubClient(self)
		if self.thc._apiKey == None:
			return

		try:
			additional_data = {
				'instance_id': conf.getInstanceId(),
				'accounts': self._getConfiguredAccounts()
			}
			await self.thc.connect(additional_data)
		except Exception as excp:
			logger.error('Problem on Startup: {}', excp)
			logger.error('OptraBot halted!')
			return
		
		logger.info('Sucessfully connected to OptraBot Hub')
		await BrokerFactory().createBrokerConnectors()
		self.thc.start_polling(self._backgroundScheduler)
		TradeManager()
		self._backgroundScheduler.add_job(self._statusInfo, 'interval', minutes=5, id='statusInfo', misfire_grace_time=None)
		self._backgroundScheduler.add_job(self._new_day_start, 'cron', hour=0, minute=0, second=0, timezone=pytz.timezone('US/Eastern'), id='day_change', misfire_grace_time=None)
		self._backgroundScheduler.add_job(self._check_price_data, 'interval', seconds=30, id='check_price_data', misfire_grace_time=None)
		self._scheduleTimeTriggers()

		environment = os.environ.get('OPTRABOT_ENV', 'PROD')
		if environment == 'DEV':
			logger.warning('Run the UI by command: npm start')
		else:
			webPort = conf.get('general.port')
			url = f"http://localhost:{webPort}/ui/optrabot.html"
			webbrowser.open(url)

	async def shutdown(self):
		logger.info('Shutting down OptraBot')
		await self.thc.shutdown()
		TradeManager().shutdown()
		await BrokerFactory().shutdownBrokerConnectors()
		self._backgroundScheduler.shutdown()

	async def _check_price_data(self):
		"""
		Checks if the connected brokers are still delivering price data during the trading session
		"""
		await BrokerFactory().check_price_data()

	async def _new_day_start(self):
		"""
		Perform operations on start of a new day
		"""
		logger.debug('Performing Day Change operations')
		await BrokerFactory().new_day_start()
		self._scheduleTimeTriggers()

	def _statusInfo(self):
		siHubConnection = 'OK' if self.thc.isHubConnectionOK() == True else 'Problem!'

		managedTrades = TradeManager().getManagedTrades()
		activeTrades = 0
		for managedTrade in managedTrades:
			if managedTrade.isActive():
				activeTrades += 1

		logger.info(f'Broker Trading enabled: {BrokerFactory().get_trading_satus_info()}')
		logger.info(f'Status Info: Hub Connection: {siHubConnection} - Active Trades: {activeTrades}')

	def _scheduleTimeTriggers(self):
		"""
		Schedules the time triggers for the relevant templates with the time trigger
		"""
		conf: Config = self['config']
		now = dt.datetime.now().astimezone(pytz.UTC)
		for item in conf.getTemplates():
			template : Template = item
			trigger = template.getTrigger()
			if trigger.type == TriggerType.Time:
				if template.is_enabled() == False:
					logger.debug(f'Template {template.name} is disabled. Not scheduling time trigger.')
					continue
				if trigger._weekdays:
					if now.weekday() not in trigger._weekdays:
						logger.debug(f'Template {template.name} is not scheduled for today')
						continue
				if trigger._blackout_days:
					if now.date() in trigger._blackout_days:
						logger.debug(f'Template {template.name} is in blackout days for today')
						continue
				if not BrokerFactory().is_trading_day():
					logger.debug(f'Market is not open. Not scheduling time trigger for template {template.name}')
					continue
				if trigger._trigger_time.time() < now.time():
					logger.debug(f'Trigger time {trigger._trigger_time} for template {template.name} is in the past. Not scheduling it.')
					continue

				trigger_time_today = dt.datetime.combine(now.date(), trigger._trigger_time.time(), tzinfo=trigger._trigger_time.tzinfo)
				logger.debug(f'Scheduling one-time trigger for template {template.name} at {trigger_time_today}')
				#self._backgroundScheduler.add_job(self._triggerTemplate, 'cron', hour=trigger._trigger_time.hour, minute=trigger._trigger_time.minute, second=0, timezone=trigger._trigger_time.tzinfo, args=[template], id=f'time_trigger_{template.name}', misfire_grace_time=None)
				self._backgroundScheduler.add_job(
					self._triggerTemplate,
					'date',
					run_date=trigger_time_today,
					timezone=trigger._trigger_time.tzinfo,
					args=[template],
					id=f'time_trigger_{template.name}',
					misfire_grace_time=None
				)

	async def _triggerTemplate(self, template: Template):
		logger.info(f'Executing Time Trigger for template {template.name}')
		job_id = 'processtemplate' + str(template.name)
		signal_data = SignalData(timestamp=dt.datetime.now().astimezone(pytz.UTC), close=0, strike=0 )
		templateProcessor = TemplateProcessor()
		self._backgroundScheduler.add_job(templateProcessor.processTemplate, args=[template, signal_data], id=job_id, max_instances=10, misfire_grace_time=None)

	def getMarketDataType(self) -> MarketDataType:
		""" Return the configured Market Data Type
		"""
		if self._marketDataType is None:
			config: Config = self['config']
			try:
				confMarketData = config.get('tws.marketdata')
			except KeyError as keyError:
				confMarketData = 'Delayed'
			self._marketDataType = MarketDataType()
			self._marketDataType.byString(confMarketData)
		return self._marketDataType

	def _getConfiguredAccounts(self) -> list:
		""" 
		Returns a list of configured accounts
		"""
		#conf: Config = self['config']
		conf: Config = optrabotcfg.appConfig
		configuredAccounts = None
		for item in conf.getTemplates():
			template : Template = item
			if configuredAccounts == None:
				configuredAccounts = [template.account]
			else:
				if not template.account in configuredAccounts:
					configuredAccounts.append(template.account)
		return configuredAccounts

	@logger.catch
	def handleTaskDone(self, task: asyncio.Task):
		if not task.cancelled():
			taskException = task.exception()
			if taskException != None:
				logger.error('Task Exception occured!')
				raise taskException