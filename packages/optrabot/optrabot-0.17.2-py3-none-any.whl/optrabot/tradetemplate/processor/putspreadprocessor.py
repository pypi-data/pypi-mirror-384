import copy
from datetime import datetime
from typing import List
from loguru import logger
from optrabot.broker.order import Leg, OptionRight, Order, OrderAction, OrderType, PriceEffect
from optrabot.optionhelper import OptionHelper
from optrabot.signaldata import SignalData
from optrabot.tradetemplate.processor.templateprocessorbase import TemplateProcessorBase
from optrabot.tradetemplate.templatefactory import PutSpread, Template
from optrabot.managedtrade import ManagedTrade


class PutSpreadProcessor(TemplateProcessorBase):
	
	def __init__(self, template: Template):
		"""
		Initializes the put spread processor with the given template
		"""
		super().__init__(template)

	def composeEntryOrder(self, signalData: SignalData = None):
		"""
		Composes the entry order for the put spread template
		"""
		super().composeEntryOrder(signalData)
		putSpreadTemplate :PutSpread = self._template
		shortStrike = None
		# Short Strike Determination
		if signalData and signalData.strike > 0:
			shortStrike = signalData.strike
		else:
			shortStrikeData = putSpreadTemplate.getShortStrikeData()
			if not shortStrikeData:
				raise ValueError('Configuration for Short Strike is missing in template!')
			if shortStrikeData.offset:
				logger.debug(f'Using Short Strike Offset: {shortStrikeData.offset}')
				shortStrike =  OptionHelper.roundToStrikePrice(signalData.close + shortStrikeData.offset)
			if shortStrikeData.delta:
				logger.debug(f'Using Short Strike Delta: {shortStrikeData.delta}')
				try:
					shortStrike = self.get_short_strike_from_delta("SPX", OptionRight.PUT, shortStrikeData.delta)
				except ValueError as value_error:
					logger.error(f'Error while determining Short Strike by Delta: {value_error}')
					return None
			if shortStrikeData.price:
				logger.debug(f'Using Short Strike price: {shortStrikeData.price}')
				try:
					shortStrike = self.get_strike_by_price("SPX", OptionRight.PUT, shortStrikeData.price)
				except ValueError as value_error:
					logger.error(f'Error while determining Short Strike by Price: {value_error}')
					return None
		
		if shortStrike == None:
			raise ValueError('Short Strike could not be determined!')
			
		logger.debug(f'Using Short Strike: {shortStrike}')

		# Long Strike Determination
		longStrikeData = putSpreadTemplate.getLongStrikeData()
		if not longStrikeData:
			raise ValueError('Configuration for Long Strike is missing in template!')
		
		if longStrikeData.width:
			longStrike = OptionHelper.roundToStrikePrice(shortStrike - longStrikeData.width)
			logger.debug(f'Using Long Strike: {longStrike}')
		elif longStrikeData.price:
			logger.debug(f'Using Long Strike price: {longStrikeData.price}')
			longStrike = self.get_strike_by_price("SPX", OptionRight.PUT, longStrikeData.price)

		if longStrikeData.max_width:
			if longStrikeData.max_width < abs(shortStrike - longStrike):
				raise ValueError(f'Strikes {shortStrike}/{longStrike} exceeds the defined maximum width {longStrikeData.max_width}')

		# Now create the entry order with its legs as all required strikes are determined
		legs: List[Leg] = []
		legs.append(Leg(action=OrderAction.SELL, strike=shortStrike, symbol=self._template.symbol, right=OptionRight.PUT, expiration=datetime.today().date(), quantity=1))
		legs.append(Leg(action=OrderAction.BUY, strike=longStrike, symbol=self._template.symbol, right=OptionRight.PUT, expiration=datetime.today().date(), quantity=1))
		
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
		tp_order_legs = copy.deepcopy(managedTrade.entryOrder.legs)
		self.invert_leg_actions(tp_order_legs)
		takeProfitOrder = Order(symbol=self._template.symbol, legs=tp_order_legs, action=OrderAction.SELL_TO_CLOSE, quantity=self._template.amount, type=OrderType.LIMIT, price=takeProfitPrice)
		return takeProfitOrder
	
	def composeStopLossOrder(self, managedTrade: ManagedTrade, fillPrice: float) -> Order:
		"""
		Composes the stop loss order based on the template and the given fill price
		"""
		super().composeStopLossOrder(managedTrade, fillPrice)
		logger.debug('Creating stop loss order for template {}', self._template.name)
		stopLossPrice = self._template.calculateStopLossPrice(fillPrice)
		logger.debug(f'Calculated stop loss price: {stopLossPrice}')
		sl_order_legs = copy.deepcopy(managedTrade.entryOrder.legs)
		self.invert_leg_actions(sl_order_legs)
		stopLossOrder = Order(symbol=self._template.symbol, legs=sl_order_legs, action=OrderAction.SELL_TO_CLOSE, quantity=self._template.amount, type=OrderType.STOP, price=stopLossPrice)
		return stopLossOrder