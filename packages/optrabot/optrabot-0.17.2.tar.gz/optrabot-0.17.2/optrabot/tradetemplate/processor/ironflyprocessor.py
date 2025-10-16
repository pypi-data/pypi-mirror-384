from datetime import datetime
from typing import List
from loguru import logger
from optrabot.broker.order import Leg, OptionRight, Order, OrderAction, OrderType
from optrabot.signaldata import SignalData
from optrabot.tradetemplate.processor.templateprocessorbase import TemplateProcessorBase
from optrabot.tradetemplate.templatefactory import IronFly, Template
from optrabot.managedtrade import ManagedTrade

class IronFlyProcessor(TemplateProcessorBase):
	
	def __init__(self, template: Template):
		"""
		Initializes the Iron Fly Processor with the given template
		"""
		super().__init__(template)
	
	def composeEntryOrder(self, signalData: SignalData = None):
		"""
		Composes the entry order for the put spread template
		"""
		super().composeEntryOrder(signalData)
		iron_fly_template :IronFly = self._template
		short_strike = None
		# Short Strike Determination
		if signalData and signalData.strike > 0:
			short_strike = signalData.strike

		if short_strike == None:
			raise ValueError('Short Strike could not be determined!')
		
		logger.debug(f'Using Short Strike: {short_strike}')

		if iron_fly_template.wing == None:
			raise ValueError('Wing size has not been defined!')
		logger.debug(f'Using Wing Size: {iron_fly_template.wing}')

		long_strike_upper = short_strike + iron_fly_template.wing
		long_strike_lower = short_strike - iron_fly_template.wing

		# Now create the entry order with its legs as all required strikes are determined
		legs: List[Leg] = []
		legs.append(Leg(action=OrderAction.SELL, strike=short_strike, symbol=self._template.symbol, right=OptionRight.PUT, expiration=datetime.today().date(), quantity=1))
		legs.append(Leg(action=OrderAction.SELL, strike=short_strike, symbol=self._template.symbol, right=OptionRight.CALL, expiration=datetime.today().date(), quantity=1))
		legs.append(Leg(action=OrderAction.BUY, strike=long_strike_upper, symbol=self._template.symbol, right=OptionRight.CALL, expiration=datetime.today().date(), quantity=1))
		legs.append(Leg(action=OrderAction.BUY, strike=long_strike_lower, symbol=self._template.symbol, right=OptionRight.PUT, expiration=datetime.today().date(), quantity=1))

		entryOrder = Order(symbol=self._template.symbol, legs=legs, action=OrderAction.BUY_TO_OPEN, quantity=self._template.amount, type=OrderType.LIMIT)
		return entryOrder

	def composeTakeProfitOrder(self, managedTrade: ManagedTrade, fillPrice: float) -> Order:
		"""
		Composes the take profit order based on the template and the given fill price
		"""
		super().composeTakeProfitOrder(managedTrade, fillPrice)
		logger.debug('Creating take profit order for template {}', self._template.name)
		takeProfitPrice = self._template.calculateTakeProfitPrice(fillPrice)
		logger.debug(f'Calculated take profit price: {takeProfitPrice}')

		takeProfitOrder = Order(symbol=self._template.symbol, legs=managedTrade.entryOrder.legs, action=OrderAction.SELL_TO_CLOSE, quantity=self._template.amount, type=OrderType.LIMIT, price=takeProfitPrice)
		return takeProfitOrder
	
	def composeStopLossOrder(self, managedTrade: ManagedTrade, fillPrice: float) -> Order:
		"""
		Composes the stop loss order based on the template and the given fill price
		"""
		super().composeStopLossOrder(managedTrade, fillPrice)
		logger.debug('Creating stop loss order for template {}', self._template.name)
		stopLossPrice = self._template.calculateStopLossPrice(fillPrice)
		logger.debug(f'Calculated stop loss price: {stopLossPrice}')
		
		stopLossOrder = Order(symbol=self._template.symbol, legs=managedTrade.entryOrder.legs, action=OrderAction.SELL_TO_CLOSE, quantity=self._template.amount, type=OrderType.STOP, price=stopLossPrice)
		return stopLossOrder