from datetime import datetime
from typing import List
from optrabot.optionhelper import OptionHelper
from optrabot.broker.brokerconnector import BrokerConnector
import optrabot.config as optrabotcfg
from loguru import logger
from optrabot.broker.brokerfactory import BrokerFactory
from optrabot.broker.order import Leg, OptionRight, Order, OrderAction
from optrabot.config import Config
from optrabot.signaldata import SignalData
from optrabot.symbolinfo import symbol_infos
from optrabot.tradetemplate.templatefactory import Template
from optrabot.managedtrade import ManagedTrade

"""
Base class for all template processors
"""
class TemplateProcessorBase:
	broker_connector: BrokerConnector

	def __init__(self, template: Template):
		"""
		Initializes the template processor with the given template
		"""
		self._template = template
		self.broker_connector = BrokerFactory().getBrokerConnectorByAccount(self._template.account)
		assert self.broker_connector != None
		self._config: Config = optrabotcfg.appConfig

	def composeEntryOrder(self, signalData: SignalData = None) -> Order:
		"""
		Composes the entry order based on the template and the optional signal data
		"""
		logger.debug('Creating entry order for template {}', self._template.name)

	def composeTakeProfitOrder(self, managedTrade: ManagedTrade, fillPrice: float) -> Order:
		"""
		Composes the take profit order based on the template and the given fill price
		"""
		logger.debug('Creating take profit order for trade {}', managedTrade.trade.id)

	def composeStopLossOrder(self, managedTrade: ManagedTrade, fillPrice: float) -> Order:
		"""
		Composes the stop loss order based on the template and the given fill price
		"""
		logger.debug('Creating stop loss order for trade {}', managedTrade.trade.id)

	def hasTakeProfit(self) -> bool:
		"""
		Returns True if the template has a take profit defined
		"""
		return self._template.hasTakeProfit()
	
	def get_short_strike_from_delta(self, symbol: str, right: OptionRight, delta: int) -> float:
		"""
		Returns the short strike based on the given delta via the associated broker
		connector and the buffered price data
		"""
		return self.broker_connector.get_strike_by_delta(symbol, right, delta)
	
	def get_strike_by_price(self, symbol: str, right: OptionRight, price: float) -> float:
		"""
		Determines the strike based on a given premium price via the associated broker
		connector and the buffered price data
		"""
		return self.broker_connector.get_strike_by_price(symbol, right, price)
	
	def get_valid_strike(self, strike: float, higher: bool) -> float:
		"""
		Returns a valid strike price around the given strike. If the strike is not available,
		it will return the nearest higher or lower strike based on the 'higher' parameter.
		"""
		data = self.broker_connector.get_option_strike_data(self._template.symbol, datetime.today().date())
		try:
			strike_data= data.strikeData[strike]
			return strike
		except KeyError:
			strikes = data.strikeData.keys()
			return OptionHelper.get_next_strike(strike, strikes, higher)

	def check_conditions(self) -> bool:
		"""
		Checks the conditions of the template against the given 
		"""
		if self._template.vix_max or self._template.vix_min:
			logger.debug('Checking VIX conditions')
			broker = BrokerFactory().getBrokerConnectorByAccount(self._template.account)
			if broker == None:
				logger.error('No broker connection available for account {}', self._template.account)
				return False
			
			try:
				vixPrice = broker.getLastPrice(symbol_infos['VIX'].symbol)
			except Exception as e:
				logger.warning('No price data for VIX available!')
				return False
			logger.debug('VIX Price: {}', vixPrice)
			if vixPrice:
				if self._template.vix_max:
					if vixPrice > self._template.vix_max:
						logger.info(f'Max VIX condition (max: {self._template.vix_max} current: {vixPrice}) not met. Ignoring signal.')
						return False
				if self._template.vix_min:
					if vixPrice < self._template.vix_min:
						logger.info(f'Min VIX condition (min: {self._template.vix_min} current: {vixPrice}) not met. Ignoring signal.')
						return False
		return True
	
	def invert_leg_actions(self, legs: List[Leg]):
		"""
		Inverts the actions of the given legs (BUY <-> SELL)
		"""
		for leg in legs:
			if leg.action == OrderAction.BUY:
				leg.action = OrderAction.SELL
			elif leg.action == OrderAction.SELL:
				leg.action = OrderAction.BUY