import asyncio
from enum import Enum
from optrabot import config, crud, schemas
from optrabot.config import Config
import certifi
from contextlib import suppress
import datetime as dt
from datetime import datetime, timedelta
from ib_async import *
import json
from loguru import logger
import httpx
from typing import Any, List
from fastapi import status
from sqlalchemy.orm import Session
import optrabot.config as optrabotcfg
from optrabot.database import get_db_engine
from optrabot.signaldata import SignalData
from optrabot.tradehelper import TradeHelper
from optrabot.optionhelper import OptionHelper
from optrabot.stoplossadjuster import StopLossAdjuster
from optrabot.tradetemplate.processor.templateprocessor import TemplateProcessor
from optrabot.tradetemplate.templatefactory import Template
from optrabot.tradetemplate.templatetrigger import TriggerType
from optrabot.util.singletonmeta import SingletonMeta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import ssl
import websockets

class NotificationType(str, Enum):
	"""
	Represents the type of an order
	"""
	ERROR = "E"
	INFO = "I"
	WARN = "W"
	

class TradinghubClient(metaclass=SingletonMeta):
	def __init__(self, optraBot):
		logger.debug("TradinghubClient Init")
		self._lastAnswerReceivedAt = None
		self._config = optrabotcfg.appConfig
		self.optraBot = optraBot
		if self.optraBot:
			self._config : Config = self.optraBot['config']
		else:
			self._config = Config()
		self._instanceId = ''
		self.hub_host = ''
		self._contracts: int = 0
		try:
			self._contracts = int(self._config.get('tws.contracts'))
		except KeyError as keyErr:
			self._contracts = 1

		try:
			self.hub_host = self._config.get('general.hub')
		except KeyError as keyError:
			self.hub_host = config.defaultHubHost
			logger.warning("No Hub URL is configured in config.yaml. Using the default.")

		try:
			self._apiKey = self._config.get('general.apikey')
		except KeyError as keyError:
			logger.error("No API Key is configured in config.yaml. Stopping here!")
			self._apiKey = None

		try:
			self._instanceId = self._config.getInstanceId()
			logger.info("Running with Instance ID '{}'.", self._instanceId)
		except KeyError as keyError:
			self._instanceId = None

		self._entryTrade = None
		self._entryTradeContract = None
		self._currentTemplate = None
		self._currentTrade = None
		self._slShortTrade = None
		self._tpTrade = None
		self._ironFlyAskPrice = 0.0
		self._ironFlyComboContract = None
		self._ironFlyContracts = None
		self._ironFlyLongLegContracts = None
		self._ironFlyShortComboContract = None
		self._longLegFillsPrice = 0.0
		self._longLegFillsReceived = 0
		self._previousIronFlyPrice = 0.0
		self._unchangedIronFlyPriceCounter = 0
		self._shuttingdown = False
		self._position = False
		self._closingLongLegs = False
		self._fillTransactionMap = {}
		self._entryOrderFilled = 0   # Number of fills for the entry order
		self._task_web_socket = None
		self._web_socket = None
		self._last_keepalive: datetime = datetime.now()

	async def _monitor_keepalive(self):
		"""
		Monitor the keepalive status and reconnect if necessary
		"""
		while not self._shuttingdown:
			if self._last_keepalive < datetime.now() - timedelta(seconds=30):
				logger.warning('No keep alive received from OptraBot Hub since more than 30 seconds. Reconnecting ...')
				await self._web_socket.close()
			await asyncio.sleep(30)

	async def connect(self, additional_data):
		""" Connects to the OptraBot Hub and reports the livecycle action.
		"""
		logger.info('Connecting to OptraBot Hub ...')
		if not self._use_websocket():
			await self.reportAction(action='SU', additional_data=json.dumps(additional_data))
		else:
			self._task_web_socket = asyncio.create_task(self._connect_websocket(additional_data))

	async def _connect_websocket(self, additional_data):
		"""
		Connects to the OptraBot Hub using a websocket and keeps the connection open. 
		"""
		if self.hub_host.startswith('wss'):
			ssl_context = ssl.create_default_context(cafile=certifi.where())
		else:
			ssl_context = None
	
		keep_alive_task = asyncio.create_task(self._monitor_keepalive())

		while not self._shuttingdown:
			try:
				async with websockets.connect(
					self.hub_host + '/ws', 
					additional_headers=[('X-API-Key', self._apiKey), ('X-Version', self.optraBot.Version)],
					ssl=ssl_context
					) as self._web_socket:
					
					# Send Account Numbers to Hub
					await self._web_socket.send(json.dumps(additional_data))

					# Wait for message that connection has been accepted
					response = await self._web_socket.recv()
					json_data = json.loads(response)
					if json_data.get('message') != 'CONNECTION_ACCEPTED':
						logger.error('Connection to OptraBot Hub failed!')
						return
					
					logger.info('Connected to OptraBot Hub successfully.')

					asyncio.create_task(self._websocket_keepalive())

					while True:
						response = await self._web_socket.recv()
						#logger.debug('Received data from Hub: {}', response)
						try:
							data = json.loads(response)
						except json.JSONDecodeError as jsonExcp:
							logger.error('Received invalid JSON data from Hub: {}', response)

						try:
							action = data['action']
							if action == 'KA':
								#logger.debug('Received Keepalive from Hub.')
								self._last_keepalive = datetime.now()
								continue
						except Exception as excp:
							pass

						try:
							data = json.loads(data)
						except json.JSONDecodeError as jsonExcp:
							logger.error('Received invalid JSON data from Hub: {}', response)
						
						# Check if the recieved data is a signal to be processed
						try:
							signal_data = data["signal"]
							await self._process_signal_data(signal_data)
						except KeyError as keyExcp:
							pass

				logger.info('Connection to OptraBot Hub closed.')

			except websockets.ConnectionClosedError as closedExcp:
				if closedExcp.reason:
					logger.error(f'Connection Closed by OptraBot Hub. Reason: {closedExcp.reason}')
				else:
					logger.error('Connection Closed by OptraBot Hub.')
				if closedExcp.code == 4001:
					break
			except websockets.ConnectionClosedOK as closedExcp:
				logger.info('Connection to OptraBot Hub closed.')
			except Exception as excp:
				logger.error(f'Error connecting to OptraBot Hub: {excp}')
			finally:
				if not self._shuttingdown:
					self._web_socket = None
					logger.info('Reconnecting in 10 seconds ...')
					await asyncio.sleep(10)
		keep_alive_task.cancel()

	async def shutdown(self):
		logger.debug('Shutting down Trading Hub Client.')
		self._shuttingdown = True

		# Disconnect from OptraBot Hub
		if not self._use_websocket():
			try:
				logger.info('Disconnecting from OptraBot Hub ...')
				additional_data = {
		 			'instance_id': self._config.getInstanceId()
				}
				await self.reportAction(action='SD', additional_data=json.dumps(additional_data))
			except Exception as excp:
				logger.error('Problem on Shutdown: {}', excp)
		else:
			# Close Websocket connection
			if self._web_socket:
				if self._task_web_socket:
					logger.debug('Stopping Websocket Task.')
					self._task_web_socket.cancel()
				logger.debug('Closing Websocket Connection.')
				try:
					await self._web_socket.send(json.dumps({'action': 'SD', 'instance_id': self._instanceId}))
					await self._web_socket.close()
				except Exception as excp:
					pass
		#self._stopPositionMonitoring()

	async def reportAction(self, action: str, additional_data: str = '') -> bool:
		"""
		Reports a livecycle action and relevant details to the OptraBot Hub and check if it is allowed.
		- Instance with the same id must not be running already
		- A subscription must be active
		- The configured account numbers must not be used by another registered user already

		Returns true if the action was reported successfully, otherwise false.
		"""
		data = {
			'action': action,
			'instance_id': self._instanceId,
			'additional_data': additional_data
		}
		headers = {'X-API-Key': self._apiKey, 'X-Version': self.optraBot.Version, "Content-Type": "application/json"}
		if not self._use_websocket():
			try:
				response = httpx.post(self.hub_host + '/report_action', json=data, headers=headers)
			except Exception as excp:
				raise excp
			
			if response.status_code != status.HTTP_200_OK:
				jsonData = response.json()
				if jsonData['detail']:
					errorMessage = jsonData['detail']
				else:
					errorMessage = response.reason_phrase
				raise Exception(errorMessage)
		else:
			# Send the data via Websocket
			if self._web_socket:
				await self._web_socket.send(json.dumps(data))
			else:
				logger.warning('Unable to send notification. WebSocket connection to OptraBot server is broken!')

	async def send_notification(self, notification_type: NotificationType, message: str):
		"""
		Send a Telegram notification via OptraBot Server
		"""
		additional_data = {
		 	'instance_id': self._config.getInstanceId(),
			'type': notification_type,
			'message': message
		}
		await self.reportAction(action='NT', additional_data=json.dumps(additional_data))


	async def _poll(self):
		try:
			fetch_url = self.hub_host + '/fetch_signal'
			url_params = {'instanceid': self._instanceId}
			headers = {'X-API-Key': self._apiKey, 'X-Version': self.optraBot.Version}
			if self._shuttingdown:
				logger.debug("Client Session closed. Stop polling.")
				return
			
			logger.debug('Checking for Signal from Hub.')
			response = httpx.get(fetch_url, params=url_params, follow_redirects=True, headers=headers)
			logger.debug('Answer received ({}).', response.status_code)
			self._pollTimeouts = 0
			if response.status_code != status.HTTP_200_OK:
				if response.status_code == status.HTTP_401_UNAUTHORIZED:
					logger.error("Error requesting signal from OptraBot Hub: {}", response.json()['detail'])
				else:
					logger.error("Error on HTTP request: {}", response.reason_phrase)
				return
			
			self._lastAnswerReceivedAt = datetime.now()
			if response.text != '\"\"' and response.text != '':
				logger.debug("Response {}", response.content )

				try:
					response_data = json.loads(response.content)
				except json.JSONDecodeError as jsonExcp:
					logger.error("Didn't receive JSON data!")
					return
				
				await self._process_signal_data(response_data)
				
		except httpx.TimeoutException as timeoutException:
			logger.debug("Timeout while fetching Signal from Hub: {}", timeoutException)
			self._pollTimeouts += 1
			if self._pollTimeouts > 3:
				logger.error("Too many timeouts while fetching Signal from Hub. Please check the connection!")
				return
		except Exception as anyEcxp:
			logger.error("Exception occured during poll: {}", anyEcxp)

	async def _process_signal_data(self, signal_data: dict):
		"""
		Process signal data received from the OptraBot hub
		"""
		signalStrategy = signal_data['strategy']
		logger.debug('Received Signal: {}', signal_data['strategy'])
		templateProcessor = TemplateProcessor()
		triggeredTemplates = templateProcessor.determineTemplates(signalStrategy)
		if len(triggeredTemplates) == 0:
			logger.info('No active template matched external trigger value {}!', signal_data['strategy'])
			return
				
		signalData = SignalData(timestamp=self._parseTimestamp(signal_data['time']), close=signal_data['close'], strike=0 )
		
		# Use the VWAP target as strike price for the Iron Fly and the Lunch Iron Fly
		if signalStrategy == '0DTEIronFly' or signalStrategy == '0DTELunchIF':
			signalData.strike = signal_data['vwaptarget']
		else:
			signalData.strike = signal_data['shortstrike']
		
		# Obtain the Template Processor and schedule a job to process the signals
		job_scheduler : AsyncIOScheduler = self.optraBot._backgroundScheduler
		for triggeredTemplate in triggeredTemplates:
			job_id = 'processtemplate' + str(triggeredTemplate.name)
			job_scheduler.add_job(templateProcessor.processTemplate, args=[triggeredTemplate, signalData], id=job_id, max_instances=10, misfire_grace_time=None)
		return	

	# async def excuteTradeTemplate(self, template: Template, response_data: dict):
	# 	""" This method is called via Job Scheduler for executing the given Trade Template in the background.
	# 	"""
	# 	logger.debug(f"Excuting Trade Template {template.name}")
	# 	try:
	# 		ib: IB = self.optraBot['ib']
	# 		if not ib.isConnected():
	# 			logger.error("Interactive Brokers is not connected. Unable to process received signal!")
	# 			return
			
	# 		if not self.optraBot.isTradingEnabled():
	# 			logger.error("Trading is not enabled. Looks like your Market Data Subscription is wrong. Skippimg this Trade!")
	# 			return
			
	# 		spx = Index('SPX', 'SMART')
	# 		qualifiedContracts = await ib.qualifyContractsAsync(spx) 
	# 		[ticker] = await ib.reqTickersAsync(spx)
	# 		spxValue = ticker.marketPrice()
	# 		#self.app['SPXPrice'] = spxValue
	# 		logger.debug("SPX Market Price {}", spxValue)

	# 		chains = await ib.reqSecDefOptParamsAsync(spx.symbol, '', spx.secType, spx.conId)
	# 		chain = next(c for c in chains if c.tradingClass == 'SPXW' and c.exchange == 'SMART')
	# 		if chain == None:
	# 			logger.error("No Option Chain for SPXW and SMART found! Doing no trade!")
	# 			return
			
			
	# 		# Options Kontrakte ermitteln
	# 		nan = float('nan')
	# 		self._currentTemplate = template
	# 		self._currentTemplate.resetStopLossAdjuster()
	# 		if not self._currentTemplate.wing:
	# 			wingSize = 70
	# 		else:
	# 			wingSize = self._currentTemplate.wing
	# 		amount = self._currentTemplate.amount
	# 		accountNo = self._currentTemplate.account
	# 		current_date = dt.date.today()
	# 		expiration = current_date.strftime('%Y%m%d')
	# 		shortLegStrike = float(response_data['vwaptarget'])
	# 		longPutStrike = shortLegStrike - wingSize
	# 		longCallStrike = shortLegStrike + wingSize
	# 		logger.info("Building Iron Fly combo with Short strike {}, Long Put strike {} and Long Call strike {}", shortLegStrike, longPutStrike, longCallStrike)
			
	# 		# Überprüfen das auf den geplanten Legs keine anderen Orders liegen
	# 		logger.debug('Checking for open Trades if Combo Legs are colliding')
	# 		contractsWithOpenOrders = await self._getAllOpenOrderContracts(accountNo, spx.symbol)

	# 		shortPutContract = Option(spx.symbol, expiration, shortLegStrike, 'P', 'SMART', tradingClass = 'SPXW')
	# 		await ib.qualifyContractsAsync(shortPutContract)
	# 		if not OptionHelper.checkContractIsQualified(shortPutContract):
	# 			return
	# 		if shortPutContract.conId in contractsWithOpenOrders:
	# 			logger.error('Existing open order at stike price {}. Trade cannot be placed!', shortLegStrike)
	# 			return

	# 		shortCallContract = Option(spx.symbol, expiration, shortLegStrike, 'C', 'SMART', tradingClass = 'SPXW')				
	# 		await ib.qualifyContractsAsync(shortCallContract)
	# 		if not OptionHelper.checkContractIsQualified(shortCallContract):
	# 			return
	# 		if shortCallContract.conId in contractsWithOpenOrders:
	# 			logger.error('Existing open order at strike price {}. Trade cannot be placed!', shortLegStrike)
	# 			return
			
	# 		longPutContract = await self._DetermineValidLongOption(spx.symbol, expiration, longPutStrike, 'P', contractsWithOpenOrders)
	# 		if longPutContract == None or not OptionHelper.checkContractIsQualified(longPutContract):
	# 			logger.error('Unable to determine a valid Long Put option for the trade!')
	# 			return
	# 		if longPutContract.strike != longPutStrike:
	# 			logger.warning('Using different Long Put strike {}, because of existing open orders on desired strike {}.', longPutContract.strike, longPutStrike)

	# 		longCallContract = await self._DetermineValidLongOption(spx.symbol, expiration, longCallStrike, 'C', contractsWithOpenOrders)
	# 		if longCallContract == None or not OptionHelper.checkContractIsQualified(longCallContract):
	# 			logger.error('Unable to determine a valid Long Call option for the trade!')
	# 			return
	# 		if longCallContract.strike != longCallStrike:
	# 			logger.warning('Using different Long Call strike {}, because of existing open orders on desired strike {}.', longCallContract.strike, longCallStrike)

	# 		self._ironFlyLongLegContracts = [longCallContract, longPutContract]
	# 		self._ironFlyContracts = [shortPutContract, shortCallContract, longPutContract, longCallContract]
	# 		self._ironFlyComboContract = Contract(symbol=spx.symbol, secType='BAG', exchange='SMART', currency='USD', comboLegs=[])
	# 		self._ironFlyShortComboContract = Contract(symbol=spx.symbol, secType='BAG', exchange='SMART', currency='USD', comboLegs=[])
	# 		ironFlyMidPrice = None
	# 		for i in range(5):
	# 			tickers = await ib.reqTickersAsync(*self._ironFlyContracts)
	# 			logger.debug("Tickers {}", tickers)
	# 			ironFlyMidPrice = self._calculateIronFlyMidPrice(tickers, ironFlyComboContract=self._ironFlyComboContract, 
	# 										   ironFlyShortComboContract=self._ironFlyShortComboContract, 
	# 										   shortPutContract=shortPutContract,
	# 										   shortCallContract=shortCallContract,
	# 										   longPutContract=longPutContract,
	# 										   longCallContract=longCallContract)
	# 			if ironFlyMidPrice != None:
	# 				break
	# 			await asyncio.sleep(1)
			
	# 		#if util.isNan(ironFlyMidPrice):
	# 		if ironFlyMidPrice == None:
	# 			logger.error("No Mid Price for combo could be calculated!")
	# 			return

	# 		limitPrice = ironFlyMidPrice

	# 		logger.info("IronFly Combo Mid Price: {} Ask Price: {}", ironFlyMidPrice, self._ironFlyAskPrice)

	# 		if not self._meetsMinimumPremium(limitPrice):
	# 			logger.info('Premium below configured minimum premium of ${}. Trade is not executed!', self._currentTemplate.minPremium)
	# 			return
			
	# 		order = LimitOrder('BUY', amount, limitPrice)
	# 		with Session(get_db_engine()) as session:
	# 			newTrade = schemas.TradeCreate(account=accountNo, symbol='SPX', strategy=self._currentTemplate.strategy)
	# 			self._currentTrade = crud.create_trade(session, newTrade)
	# 			order.orderRef = 'OTB (' + str(self._currentTrade.id) + '): ' + template.name + ' - Open'
	# 		order.account = accountNo
	# 		order.outsideRth = True
	# 		self._fillTransactionMap.clear()
	# 		self._entryTrade = ib.placeOrder(self._ironFlyComboContract, order)
	# 		self._entryTradeContract = self._ironFlyComboContract
	# 		self._ironFlyAskPrice = 0.0
	# 		self._longLegFillsPrice = 0.0
	# 		self._previousIronFlyPrice = 0.0
	# 		self._unchangedIronFlyPriceCounter = 0
	# 		self._longLegFillsReceived = 0
	# 		self._slShortTrade = None
	# 		self._tpTrade = None
	# 		self._entryOrderFilled = 0
	# 		self._closingLongLegs = False
	# 		logger.debug("Account: {} Trade placed: {} Number of contracts: {}", order.account, self._entryTrade, amount)
	# 		self.optraBot._backgroundScheduler.add_job(self._trackEntryOrder, 'interval', seconds=5, id='TrackEntryOrder')

	# 	except Exception as excp:
	# 					logger.error("Exception: {}", excp)

	# def _calculateIronFlyMidPrice(self, tickers: List[Ticker], ironFlyComboContract: Contract, ironFlyShortComboContract: Contract, shortPutContract: Option, shortCallContract: Option, longPutContract: Option, longCallContract: Option) -> float:
	# 	"""
	# 	Calculate the Iron Fly Mid Price based on the given tickers. It returns
	# 	None if one of the legs got no valid price.
	# 	"""
	# 	ironFlyMidPrice = 0
	# 	self._ironFlyAskPrice = 0
	# 	ironFlyComboContract.comboLegs.clear()
	# 	ironFlyShortComboContract.comboLegs.clear()
	# 	for ticker in tickers:
	# 		tickerContract = ticker.contract
	# 		if tickerContract.conId == shortPutContract.conId:
	# 			midPrice = (ticker.ask + ticker.bid) / 2
	# 			if util.isNan(midPrice) or (ticker.ask == -1.00 and ticker.bid == -1.00):
	# 				return None
	# 			ironFlyMidPrice -= midPrice
	# 			if not util.isNan(ticker.bid):
	# 				self._ironFlyAskPrice -= ticker.bid
	# 				ironFlyComboContract.comboLegs.append(ComboLeg(conId=shortPutContract.conId, ratio=1, action='SELL', exchange='CBOE'))
	# 				ironFlyShortComboContract.comboLegs.append(ComboLeg(conId=shortPutContract.conId, ratio=1, action='BUY', exchange='CBOE'))
	# 		if tickerContract.conId == shortCallContract.conId:
	# 			midPrice = (ticker.ask + ticker.bid) / 2
	# 			if util.isNan(midPrice) or (ticker.ask == -1.00 and ticker.bid == -1.00):
	# 				return None
	# 			ironFlyMidPrice -= midPrice
	# 			if not util.isNan(ticker.bid):
	# 				self._ironFlyAskPrice -= ticker.bid
	# 				ironFlyComboContract.comboLegs.append(ComboLeg(conId=shortCallContract.conId, ratio=1, action='SELL', exchange='CBOE'))
	# 				ironFlyShortComboContract.comboLegs.append(ComboLeg(conId=shortCallContract.conId, ratio=1, action='BUY', exchange='CBOE'))
	# 		if tickerContract.conId == longPutContract.conId:
	# 			midPrice = (ticker.ask + ticker.bid) / 2
	# 			if util.isNan(midPrice) or (ticker.ask == -1.00 and ticker.bid == -1.00):
	# 				midPrice = 0.05
	# 			ironFlyMidPrice += midPrice
	# 			if not util.isNan(ticker.ask):
	# 				self._ironFlyAskPrice += ticker.ask
	# 				ironFlyComboContract.comboLegs.append(ComboLeg(conId=longPutContract.conId, ratio=1, action='BUY', exchange='CBOE'))
	# 		if tickerContract.conId == longCallContract.conId:
	# 			midPrice = (ticker.ask + ticker.bid) / 2
	# 			if util.isNan(midPrice) or (ticker.ask == -1.00 and ticker.bid == -1.00):
	# 				midPrice = 0.05
	# 			ironFlyMidPrice += midPrice
	# 			if not util.isNan(ticker.ask):
	# 				self._ironFlyAskPrice += ticker.ask
	# 				ironFlyComboContract.comboLegs.append(ComboLeg(conId=longCallContract.conId, ratio=1, action='BUY', exchange='CBOE'))
	# 	self._ironFlyAskPrice = OptionHelper.roundToTickSize(self._ironFlyAskPrice)
	# 	return OptionHelper.roundToTickSize(ironFlyMidPrice)

	# async def _trackEntryOrder(self):
	# 	ib: IB = self.optraBot['ib']
	# 	if self._entryTrade == None:
	# 		logger.debug("Stopping Entry Order Tracking")
	# 		self.optraBot._backgroundScheduler.remove_job('TrackEntryOrder')
	# 		return
		
	# 	if self._entryTrade.orderStatus.status == OrderStatus.Cancelled or self._entryTrade.orderStatus.status == OrderStatus.Inactive:
	# 		self._onEntryOrderCanceled()
	# 	elif self._entryTrade.orderStatus.status == OrderStatus.Filled:
	# 		logger.info("Entry Order has been filled already. No adjustment required")
	# 		logger.debug("Stopping Entry Order Tracking")
	# 		self.optraBot._backgroundScheduler.remove_job('TrackEntryOrder')
	# 	elif self._entryTrade.orderStatus.status == OrderStatus.PreSubmitted or self._entryTrade.orderStatus.status == OrderStatus.PendingSubmit:
	# 		logger.info("Entry Order is still in PreSubmitted state. Waiting for it to be submitted...")
	# 	elif self._entryTrade.orderStatus.status == OrderStatus.Submitted:
	# 		currentLimitPrice = self._entryTrade.order.lmtPrice
	# 		adjustedLimitPrice = currentLimitPrice + self._currentTemplate.adjustmentStep
	# 		logger.info("Entry Order status ({}). Entry price will be adjusted. Current Limit Price: ${}", self._entryTrade.orderStatus.status, currentLimitPrice)
	# 		if self._meetsMinimumPremium(adjustedLimitPrice) and adjustedLimitPrice <= self._ironFlyAskPrice:
	# 			self._entryTrade.order.lmtPrice = adjustedLimitPrice
	# 			try:
	# 				ib.placeOrder(self._entryTradeContract, self._entryTrade.order)
	# 			except Exception as excp:
	# 				logger('Exception beim Anpassen der Order')
	# 			return
	# 		else:
	# 			if adjustedLimitPrice > -15:
	# 				logger.info("Entry order limit price reached minimum premium. No entry.")
	# 			if adjustedLimitPrice > self._ironFlyAskPrice:
	# 				logger.info("Entry order limit price exceeded initial ask price. No entry.")
	# 			ib.cancelOrder(self._entryTrade.order)
	# 	else:
	# 		logger.error("Entry Order status is not considered: {}", self._entryTrade.orderStatus.status)

	# async def onOrderStatusEvent(self, trade: Trade):
	# 	if trade == self._entryTrade:
	# 		logger.debug('Order Status Event has been raised. Status: {}', trade.orderStatus.status)
	# 		if trade.orderStatus.status == OrderStatus.Cancelled:
	# 			logEntry: TradeLogEntry = None
	# 			for logEntry in trade.log:
	# 				if logEntry.status != 'Cancelled':
	# 					continue
	# 			if logEntry == None:
	# 				logger.error('No log entry found for Entry order cancellation!')
	# 			if logEntry.errorCode == 103:
	# 				# Error 103, reqId 10292: Doppelt vorhandene Order-ID
	# 				logger.info('Adjustment of entry order has been rejected, because Duplicate Order-ID. Entry Order still active.')
	# 			elif logEntry.errorCode == 0:
	# 				self._onEntryOrderCanceled()
	# 		elif trade.orderStatus.status == OrderStatus.Filled:
	# 			if self._position == False:
	# 				logger.info('Entry Order has been filled at ${} (Qty: {}) and trade is running now.', trade.orderStatus.avgFillPrice, trade.orderStatus.filled)
	# 				self._position = True
	# 				if self._currentTemplate.stopLossAdjuster:
	# 					self._currentTemplate.stopLossAdjuster.setBasePrice(round(self._entryTrade.orderStatus.avgFillPrice * -1, 2))
	# 				asyncio.create_task(self._placeTakeProfitAndStop(trade)).add_done_callback(self.optraBot.handleTaskDone)
	# 				#Run 1. Position Monitoring with delay
	# 				#asyncio.create_task(self._monitorPositionDelayed()).add_done_callback(self.optraBot.handleTaskDone)
	# 				self.optraBot._backgroundScheduler.add_job(self._monitorPosition, 'interval', seconds=5, id='MonitorPosition')
	# 			elif self._position == True:
	# 				logger.debug('Additionally fill quantity (Qty: {}) for the entry order...depending orders need to be adjusted.', trade.orderStatus.filled)
	# 				asyncio.create_task(self._adjustTakeProfitAndStop(trade)).add_done_callback(self.optraBot.handleTaskDone)

	# 			if trade.orderStatus.remaining > 0:
	# 				logger.warning('Partial fill for entry order. Remaining: {}', trade.orderStatus.remaining)
	# 			executedAmount = trade.orderStatus.filled - self._entryOrderFilled
	# 			logger.debug('Executed amount for entry trade: {}', executedAmount)
	# 			if executedAmount > 0:
	# 				asyncio.create_task(self._reportExecutedTrade(trade, executedAmount)).add_done_callback(self.optraBot.handleTaskDone)
	# 			self._entryOrderFilled = self._entryTrade.order.totalQuantity - trade.orderStatus.remaining

	# 	elif self._tpTrade and trade.order.orderId == self._tpTrade.order.orderId:
	# 		logger.debug('TP Order Status has been raised. Status: {}', trade.orderStatus.status)
	# 		if trade.orderStatus.status == OrderStatus.Cancelled:
	# 			logger.info('TP Order has been cancelled!')

	# 		elif trade.orderStatus.status == OrderStatus.Filled:
	# 			logger.success('TP Order has been filled. Trade finished')
	# 			self._tpTrade = None
	# 			self._slShortTrade = None
	# 			self._onPositionClose()

	# 	elif self._slShortTrade and trade.order.orderId == self._slShortTrade.order.orderId:
	# 		logger.debug('SL order for Short Legs status has been changed. Status: {}', trade.orderStatus.status)
	# 		if trade.orderStatus.status == OrderStatus.Cancelled:
	# 			logEntry: TradeLogEntry = None
	# 			for logEntry in trade.log:
	# 				if logEntry.status != 'Cancelled':
	# 					continue
	# 			if logEntry == None:
	# 				logger.error('No log entry found for SL order cancellation!')
	# 				return
	# 			if logEntry.errorCode == 201:
	# 				# 201: Order rejected - reason:Stop price revision is disallowed after order has triggered
	# 				logger.info('Adjustment of SL order has been rejected, because Stop Order was triggered or cancelled already.')
	# 			elif logEntry.errorCode == 0:
	# 				logger.info('SL Order for Short Legs has been cancelled.')
	# 			else:
	# 				logger.error('SL order for Short legs has been cancelled with error code {} and message: {}', logEntry.errorCode, logEntry.message)					

	# 		elif trade.orderStatus.status == OrderStatus.Filled:
	# 			logger.info('SL order for Short Legs has been filled. Trade finished')
	# 			logger.info('Now....Long Legs need to be closed if possible')
	# 			if self._closingLongLegs == False:
	# 				asyncio.create_task(self._close_long_legs(self._entryTrade.orderStatus.filled, self._currentTemplate.name, self._currentTemplate.account, tradeId=self._currentTrade.id )).add_done_callback(self.optraBot.handleTaskDone)
	# 				self._onPositionClose()

	# def _onEntryOrderCanceled(self):
	# 	""" Performs final steps after a entry order was canceled
	# 	"""
	# 	logger.info('Entry Order has been cancelled!')
	# 	self._entryTrade = None
	# 	logger.debug('Deleting trade {} from database...', self._currentTrade.id )
	# 	with Session(get_db_engine()) as session:
	# 		crud.delete_trade(session, self._currentTrade)
	# 	self._currentTrade = None

	# async def _DetermineValidLongOption(self, symbol, expiration, desiredStrike, right, contractsWithOpenOrders):
	# 	""" Determines the next possible Long Leg Option on the given Strike price and right ensuring that
	# 		there are no open orders.
	# 	"""
	# 	ib: IB = self.optraBot['ib']
	# 	strike = desiredStrike
	# 	validOption: Option = None
	# 	tryCount = 0
	# 	while tryCount < 5:
	# 		tryCount += 1
	# 		logger.debug('Checking Long {} Strike {}', right, strike)
	# 		option = Option(symbol, expiration, strike, right, 'CBOE', tradingClass = 'SPXW')
	# 		await ib.qualifyContractsAsync(option)
	# 		if not OptionHelper.checkContractIsQualified(option):
	# 			break
	# 		if not option.conId in contractsWithOpenOrders:
	# 			validOption = option
	# 			break
	# 		if right == 'P':
	# 			strike -= 5
	# 		else:
	# 			strike += 5
	# 	return validOption


	# async def onExecDetailsEvent(self, trade: Trade, fill: Fill):
	# 	""" This eventhandler is called on trade execution
	# 	"""
	# 	# First we need to check if Execution is related to an OptraBot Trade
	# 	# If so, the transaction needs to be recorded in the database
	# 	logger.debug('Exec Detail for trade {}', trade)
	# 	logger.debug('Fill: {}', fill)
	# 	tradeId = TradeHelper.getTradeIdFromOrderRef(fill.execution.orderRef)
	# 	if tradeId == 0:
	# 		logger.debug('Fill not from OptraBot trade...ignoring it.')
	# 		return
	# 	if fill.contract.secType == 'BAG':
	# 		# Do not store information on combo executions
	# 		return
	# 	with Session(get_db_engine()) as session:
	# 		max_transactionid = crud.getMaxTransactionId(session, tradeId)
	# 		dbTrade = crud.getTrade(session,tradeId)
	# 		if max_transactionid == 0:
	# 			# Opening Transaction of the trade
	# 			dbTrade.status = 'OPEN'
	# 		max_transactionid += 1
	# 		transactionType = ''
	# 		if fill.execution.side == 'BOT':
	# 			transactionType = 'BUY'
	# 		else:
	# 			transactionType = 'SELL'
	# 		expirationDate = datetime.strptime(fill.contract.lastTradeDateOrContractMonth, '%Y%m%d')
	# 		newTransaction = schemas.TransactionCreate(tradeid=tradeId, id=max_transactionid, type=transactionType, sectype=fill.contract.right, timestamp=fill.execution.time, expiration=expirationDate, strike=fill.contract.strike, contracts=fill.execution.shares, price=fill.execution.avgPrice, fee=0, commission=0, notes='')
	# 		self._fillTransactionMap[fill.execution.execId] = newTransaction.id # Memorize Execution ID of the fill for later commission report
	# 		crud.createTransaction(session, newTransaction)

	# 		# Check if trade is closed with all these transactions
	# 		TradeHelper.updateTrade(dbTrade)
	# 		session.commit()
	
	async def onCommissionReportEvent(self, trade: Trade, fill: Fill, report: CommissionReport):
		"""
		Handles the Commission Report Event
		"""
		logger.debug('Commission Report order id {} and fill {}', trade.order.orderId, fill)
		logger.debug('Commission Report: {}', report)
		tradeId = TradeHelper.getTradeIdFromOrderRef(fill.execution.orderRef)
		if tradeId == 0:
			logger.debug('Fill not from OptraBot trade...ignoring it.')
			return
		
		# Get Transaction ID for the fills execution id
		try:
			transactionId = self._fillTransactionMap[fill.execution.execId]
		except KeyError as keyError:
			logger.error('No trade transaction found for fill execution id {}', fill.execution.execId)
			return
		
		with Session(get_db_engine()) as session:
			transaction = crud.getTransactionById(session, tradeId, transactionId)
			if transaction == None:
				logger.error('Transaction with id {} for trade {} not found in database!', transactionId, tradeId)
				return
			transaction.commission = report.commission
			session.commit()

	async def _reportExecutedTrade(self, trade: Trade, executedAmount: int):
		"""
		Report the entry trade execution to Optrabot Hub
		"""
		try:
			executedContracts = 0
			if trade.contract.secType == 'BAG':
				for leg in trade.contract.comboLegs:
					executedContracts += leg.ratio * executedAmount
			else:
				executedContracts = executedAmount
					
			additional_data = {
				'trade_id': self._currentTrade.id,
				'account': self._currentTemplate.account,
				'contracts': int(executedContracts)
			}
			await self.reportAction('CT', additional_data=json.dumps(additional_data))
		except Exception as excp:
			logger.error('Error reporting position open event: {}', excp)

	async def _close_long_legs(self, positionSize: int, templatename: str, account: str, tradeId: int):
		logger.debug("Closing long legs of trade")
		self._closingLongLegs = True
		ib: IB = self.optraBot['ib']
		tickers = await ib.reqTickersAsync(*self._ironFlyLongLegContracts)
		for ticker in tickers:
			logger.debug("Long Leg {} {} Bid Price: {}", ticker.contract.right, ticker.contract.strike, ticker.bid)
			if ticker.bid >= 0.05:
				logger.debug('Creating limit sell order on bid price')
				order = LimitOrder('SELL', positionSize, ticker.bid)
				order.outsideRth = True
				order.account = account
				order.orderRef = 'OTB (' + str(tradeId) + '): ' + templatename + ' - Close Long Leg'
				closeTrade = ib.placeOrder(ticker.contract, order)
				logger.debug('Placed Long Leg closing order with id: {}', closeTrade.order.orderId)
			else:
				logger.info('Long leg {} {} is worthless and will be kept open till expiration.', ticker.contract.right, ticker.contract.strike)
				with Session(get_db_engine()) as session:
					max_transactionid = crud.getMaxTransactionId(session, tradeId)
					dbTrade = crud.getTrade(session,tradeId)
					assert(max_transactionid > 0)
					# Create expiration transaction for this leg
					max_transactionid += 1
					transactionType = 'EXP'
					expirationDate = datetime.strptime(ticker.contract.lastTradeDateOrContractMonth, '%Y%m%d')
					newTransaction = schemas.TransactionCreate(tradeid=tradeId, id=max_transactionid, type=transactionType, sectype=ticker.contract.right, timestamp=expirationDate, expiration=expirationDate, strike=ticker.contract.strike, contracts=positionSize, price=0.0, fee=0, commission=0.0, notes='')
					crud.createTransaction(session, newTransaction)
					TradeHelper.updateTrade(dbTrade)
					session.commit()

		logger.debug('exit _close_long_legs()')

	def _onPositionClose(self):
		logger.debug('_onPositionClose()')
		self._tpTrade = None
		self._slShortTrade = None
		self._entryTrade = None
		self._ironFlyComboContract = None
		self._ironFlyContracts = None
		self._position = False
		self._closingLongLegs = False
		self._currentTemplate = None
		self._currentTrade = None
		self._stopPositionMonitoring()

	async def _monitorPosition(self):
		logger.debug('Enter Monitor position()')
		if self._position == False:
			logger.debug('Position has been closed. Stopping Position-Monitoring now.')
			#self._positionMonitorTask = None
			self._stopPositionMonitoring()
			return

		#asyncio.create_task(self._monitorPositionDelayed()).add_done_callback(self.optraBot.handleTaskDone)

		ib: IB = self.optraBot['ib']
		if not ib.isConnected() or self.optraBot.isTradingEnabled() == False:
			logger.error('Interactive Brokers is not connected. Unable to monitor position!')
			return
		
		try:
			if self._position == False:
				logger.debug('Position has been closed. Stopping Position-Monitoring now.')
				return

			tickers = await ib.reqTickersAsync(*self._ironFlyContracts)
			longLegsValue = 0
			currentIronFlyAskPrice = 0
			currentIronFlyBidPrice = 0
			adjustedStopLossPrice = None
			for ticker in tickers:
				if ticker.contract in self._ironFlyLongLegContracts:
					if ticker.bid >= 0:
						longLegsValue += ticker.bid
						currentIronFlyBidPrice -= ticker.bid
						currentIronFlyAskPrice += ticker.ask
				else:
					# Für Short Legs müssen die Ask Preise addiert werden
					currentIronFlyBidPrice += ticker.ask
					currentIronFlyAskPrice -= ticker.bid
		
			if self._position == False:
				logger.debug('Position has been closed. Stopping Position-Monitoring now.')
				return

			currentIronFlyAskPrice = abs(currentIronFlyAskPrice)
			currentIronFlyPrice = OptionHelper.calculateMidPrice(currentIronFlyBidPrice, currentIronFlyAskPrice)
			if currentIronFlyPrice == self._previousIronFlyPrice:
				self._unchangedIronFlyPriceCounter += 1
			else:
				self._unchangedIronFlyPriceCounter = 0
			self._previousIronFlyPrice = currentIronFlyPrice
			if self._unchangedIronFlyPriceCounter > 10:
				logger.warning('Price of Iron Fly has not changed for 10 times. There is a problem with price data from TWS probably.')
				self._unchangedIronFlyPriceCounter = 0

			if self._currentTemplate.stopLossAdjuster:
				if not self._currentTemplate.stopLossAdjuster.isTriggered():
					adjustedStopLossPrice = self._currentTemplate.stopLossAdjuster.execute(currentIronFlyPrice)
					if adjustedStopLossPrice == None:
						logger.debug('No need to adjust stop loss now.')
					else:
						self._ironFlyStopPrice = adjustedStopLossPrice
						logger.info('Performing stop loss adjustment. New Stop Loss price: {}', self._ironFlyStopPrice)
				else:
					logger.debug('Stoploss adjustment has been performed already.')
			else:
				logger.debug('No StopLoss adjustment configured.')
			desiredStopPrice = OptionHelper.roundToTickSize(self._ironFlyStopPrice + longLegsValue)
			currentStopPrice = OptionHelper.roundToTickSize(self._slShortTrade.order.auxPrice)
			logger.debug('Long Legs value {} Current Short SL Price: {} Desired Short SL Pice: {}', round(longLegsValue,2), currentStopPrice, desiredStopPrice)
			openOrders = ib.openOrders()

			if self._position == False:
				logger.debug('Position has been closed. Stopping Position-Monitoring now.')
				return
			if any(order.orderId == self._slShortTrade.order.orderId for order in openOrders):
			#if self._slShortTrade.order in openOrders:
				if self._slShortTrade.isActive():
					if currentStopPrice != desiredStopPrice:
						self._slShortTrade.order.auxPrice = desiredStopPrice
						logger.info('Adjusting Stop Loss price to ${}', desiredStopPrice)
						ib.placeOrder(self._slShortTrade.contract, self._slShortTrade.order)
						logger.debug('Updated SL order with id: {}', self._slShortTrade.order.orderId)
					else:
						logger.debug('No adjustment of Stop Loss price required.')
				else:
					logger.debug('SL Order is not active anymore.')
			else:
				logger.warning('Caution: Stop Loss order for Short Strikes is missing. Trying to reestablish the Stop Loss order now!')
				await self._reestablishStopLossOrder(desiredStopPrice)
		except ConnectionError as connError:
			logger.error('Connection to TWS lost during Position Monitoring. Unable to monitor position!')

		logger.debug('Leave Monitor position()')

	async def _monitorPositionDelayed(self):
		logger.debug('Waiting 10 seconds for next position monitoring.')
		await asyncio.sleep(10)
		if self._position == True:
			asyncio.create_task(self._monitorPosition(), name='MonitorPosition').add_done_callback(self.optraBot.handleTaskDone)

	def _meetsMinimumPremium(self, premium: float) -> bool:
		""" Checks if given premium meets minimum premium

		Parameters
		----------
		premium : float
			As premium is a typically a credit, a negative number is expected.
		
		Returns
		-------
		bool
			Returns True, if the received premium is more than the configured minimum premium
		"""
		if self._currentTemplate.minPremium == None:
			return True
		if premium > (self._currentTemplate.minPremium * -1):
			return False
		return True

	def _parseTimestamp(self, timestamp: str) -> datetime:
		""" Parses the given timestamp into a `datetime`object

		Parameters
		----------
		timestamp : str
    		Timestamp as string with timezone info e.g. 2023-11-07T14:10:00Z.
		"""
		try:
			parsedTime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
		except Exception as excpt:
			logger.error("Timestamp {} got unexpected format.", timestamp)
			return None
		return parsedTime

	async def _scheduleNextPoll(self):
		await asyncio.sleep(5)
		asyncio.create_task(self._poll()).add_done_callback(self.optraBot.handleTaskDone)
		
	def start_polling(self, scheduler):
		"""
		Tradinghub Polling runner
		"""
		logger.debug("start_polling")
		if self._use_websocket():
			logger.debug("Websocket connection is used. Stop polling.")
			return
		else:
			logger.warning("You're using legacy long polling connection to OptraBot Hub. Please consider using Websocket connection.")
		
		if self._apiKey == None:
			logger.debug("No API Key configured. Stop polling.")
			return

		if self._instanceId == None:
			logger.error("No Instance ID configured in config.yaml. Stop polling!")
			return

		scheduler.add_job(self._poll, 'interval', seconds=5)

	def _stopPositionMonitoring(self):
		self.optraBot._backgroundScheduler.remove_job('MonitorPosition')
	
	def _use_websocket(self):
		""" Returns True if the OptraBot Hub should be accessed via Websocket
		"""
		if self.hub_host.startswith('ws'):
			return True
		return False
	
	async def _websocket_keepalive(self):
		"""
		Asynchronous Task sending a keepalive message to the OptraBot Hub every 20 seconds
		"""
		try:
			while self._web_socket:
				await self._web_socket.send('{"action":"KA"}')
				self._lastAnswerReceivedAt = datetime.now()
				await asyncio.sleep(20)
		except websockets.ConnectionClosedError as closedError:
			pass
		except websockets.ConnectionClosedOK as closedError:
			pass
		logger.error("Websocket connection is not established. Stop keepalive.")

	def isHubConnectionOK(self) -> bool:
		""" Returns True if the last request to the OptraBot Hub was responed 
		30 seconds ago or less.
		"""
		if self._lastAnswerReceivedAt == None or self._last_keepalive == None:
			return False
		timeDelta_ka_send = datetime.now() - self._lastAnswerReceivedAt
		timeDelta_ka_received = datetime.now() - self._last_keepalive
		if timeDelta_ka_send.total_seconds() > 30 or timeDelta_ka_received.total_seconds() > 30:
			return False
		else:
			return True