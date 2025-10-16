import copy
from datetime import datetime
from typing import List
from loguru import logger
from optrabot.broker.optionpricedata import OptionStrikeData
from optrabot.managedtrade import ManagedTrade
from optrabot.broker.order import Leg, OptionRight, Order, OrderAction, OrderType, PriceEffect
from optrabot.optionhelper import OptionHelper
from optrabot.signaldata import SignalData
from optrabot.tradetemplate.processor.templateprocessorbase import TemplateProcessorBase
from optrabot.tradetemplate.templatefactory import IronCondor, Template

class IronCondorProcessor(TemplateProcessorBase):
	def __init__(self, template: Template):
		"""
		Initializes the Iron Condor Processor with the given template
		"""
		super().__init__(template)
		self.credit_legs = None

	def composeEntryOrder(self, signalData: SignalData = None):
		"""
		Composes the entry order for the Iron Condor template
		"""
		super().composeEntryOrder(signalData)
		iron_condor_template :IronCondor = self._template
		short_strike_put = None
		short_strike_call = None
		premium = iron_condor_template.get_premium()

		# Short Strike Determination
		shortStrikeData = iron_condor_template.getShortStrikeData()
		if not shortStrikeData and not premium:
			raise ValueError('Configuration for Short Strike or premium is missing in template!')

		if iron_condor_template.wing == None:
				raise ValueError('Wing size has not been defined!')
		
		expiration_date = datetime.today().date()

		if shortStrikeData:
			if shortStrikeData.offset:
				logger.debug(f'Using Short Strike Offset: {shortStrikeData.offset}')
				short_strike_put =  OptionHelper.roundToStrikePrice(signalData.close - shortStrikeData.offset)
				short_strike_call =  OptionHelper.roundToStrikePrice(signalData.close + shortStrikeData.offset)
			elif shortStrikeData.delta:
				logger.debug(f'Using Short Strike Delta: {shortStrikeData.delta}')
				try:
					short_strike_put = self.get_short_strike_from_delta("SPX", OptionRight.PUT, shortStrikeData.delta)
					short_strike_call = self.get_short_strike_from_delta("SPX", OptionRight.CALL, shortStrikeData.delta)
				except ValueError as value_error:
					logger.error(f'Error while determining Short Strike by Delta: {value_error}')
					return None

			logger.debug(f'Using Wing Size: {iron_condor_template.wing}')
			long_strike_put = self.get_valid_strike(short_strike_put - iron_condor_template.wing, True)
			long_strike_call = self.get_valid_strike(short_strike_call + iron_condor_template.wing, False)

			# Now create the entry order with its legs as all required strikes are determined
			legs: List[Leg] = []
			legs.append(Leg(action=OrderAction.SELL, strike=short_strike_put, symbol=self._template.symbol, right=OptionRight.PUT, expiration=expiration_date, quantity=1))
			legs.append(Leg(action=OrderAction.SELL, strike=short_strike_call, symbol=self._template.symbol, right=OptionRight.CALL, expiration=expiration_date, quantity=1))
			legs.append(Leg(action=OrderAction.BUY, strike=long_strike_call, symbol=self._template.symbol, right=OptionRight.CALL, expiration=expiration_date, quantity=1))
			legs.append(Leg(action=OrderAction.BUY, strike=long_strike_put, symbol=self._template.symbol, right=OptionRight.PUT, expiration=expiration_date, quantity=1))
		elif premium:
			logger.debug(f'Trying to create an Iron Condor with premium: ${premium} and Wing Size: {iron_condor_template.wing}')
			self.credit_legs = None
			legs = self.compose_legs_with_min_premium(iron_condor_template.symbol, expiration_date, premium, iron_condor_template.wing)
			if not legs:
				raise ValueError('Unable to determine legs for Iron Condor based on premium and wing size!')

		entryOrder = Order(symbol=self._template.symbol, legs=legs, action=OrderAction.BUY_TO_OPEN, quantity=self._template.amount, type=OrderType.LIMIT)
		return entryOrder
	
	def calculate_position_delta_and_price(self, legs: List[Leg], option_strike_data: OptionStrikeData) -> float:
		"""
		Calculates the total delta of the given legs and the mid price of the legs
		"""
		leg_delta = 0.0
		position_delta = 0.0
		for leg in legs:
			if leg.right == OptionRight.CALL:
				leg_delta = option_strike_data.strikeData[leg.strike].get_call_delta() * leg.quantity
				leg.midPrice = option_strike_data.strikeData[leg.strike].getCallMidPrice()
			elif leg.right == OptionRight.PUT:
				leg_delta = option_strike_data.strikeData[leg.strike].get_put_delta() * leg.quantity
				leg.midPrice = option_strike_data.strikeData[leg.strike].getPutMidPrice()
			if leg.action == OrderAction.SELL:
				leg_delta *= -1
			position_delta += leg_delta
		return position_delta
	
	def calculate_position_price(self, legs: List[Leg], open: bool = True) -> float:
		"""
		Calculates the total price of the given legs.
		- Positive position prices indicate a net credit (income)
		- Negative position prices indicate a net debit (cost)
		"""
		total_price = 0.0
		for leg in legs:
			if leg.action == OrderAction.BUY:
				if open:
					total_price -= leg.midPrice * leg.quantity
				else:
					total_price += leg.midPrice * leg.quantity
			elif leg.action == OrderAction.SELL:
				if open:
					total_price += leg.midPrice * leg.quantity
				else:
					total_price -= leg.midPrice * leg.quantity
		return total_price
	
	def compose_legs_with_min_premium(self, symbol: str, expiration_date: datetime.date, min_premium: float, wing: float) -> List[Leg] | None:
		"""
		Composes the Iron Condor legs based on the given minimum premium and the wing size.
		"""
		from optrabot.broker.brokerfactory import BrokerFactory
		broker_connector = BrokerFactory().getBrokerConnectorByAccount(self._template.account)
		assert broker_connector != None

		atm_strike = broker_connector.get_atm_strike(self._template.symbol)
		if not atm_strike:
			return
		
		current_short_call_strike = atm_strike
		current_short_put_strike = atm_strike
		option_strike_data = broker_connector.get_option_strike_data(symbol, expiration_date)
		strikes = option_strike_data.strikeData.keys()
		next_short_call_strike = OptionHelper.get_next_strike(current_short_call_strike, strikes, True)
		next_short_put_strike = OptionHelper.get_next_strike(current_short_put_strike, strikes, False)
		logger.debug(f'ATM Strike: {atm_strike} - starting with Put Strike: {next_short_put_strike} Call Strike: {next_short_call_strike}')

		starting_legs: List[Leg] = []
		starting_legs.append(Leg(action=OrderAction.SELL, strike=next_short_put_strike, symbol=symbol, right=OptionRight.PUT, expiration=expiration_date, quantity=1))
		starting_legs.append(Leg(action=OrderAction.SELL, strike=next_short_call_strike, symbol=symbol, right=OptionRight.CALL, expiration=expiration_date, quantity=1))
		long_strike_put = self.get_valid_strike(next_short_put_strike - self._template.wing, True)
		long_strike_call = self.get_valid_strike(next_short_call_strike + self._template.wing, False)
		starting_legs.append(Leg(action=OrderAction.BUY, strike=long_strike_call, symbol=self._template.symbol, right=OptionRight.CALL, expiration=expiration_date, quantity=1))
		starting_legs.append(Leg(action=OrderAction.BUY, strike=long_strike_put, symbol=self._template.symbol, right=OptionRight.PUT, expiration=expiration_date, quantity=1))

		entry_order_legs = self.determine_order_legs(starting_legs, strikes, option_strike_data, min_premium)

		return entry_order_legs
	
	def determine_order_legs(self, legs: List[Leg], strikes: List[float], option_strike_data, min_premium: float) -> List[Leg] | None:	
		"""
		Determines the according order legs recursively.
		"""
		position_delta = round(self.calculate_position_delta_and_price(legs, option_strike_data) * 100, 2)
		logger.debug(f'Calculated Position Delta: {position_delta}')
		if position_delta < 2 and position_delta > -2:
			# Delta is OK, check if price is sufficient
			new_position_price = self.calculate_position_price(legs, True)
			logger.debug(f'Calculated Position Price: {new_position_price:.2f}. Required price: {min_premium:.2f}')
			if new_position_price >= min_premium:
				# Store the legs which are above the required premium
				self.credit_legs = copy.deepcopy(legs)
				# Try to adjust
				return self.adjust_legs(position_delta, legs, strikes, option_strike_data, min_premium)
			else:
				# Legs Premium is below minimum premium --> So we adjusted to much
				# return the previous stored legs
				return self.credit_legs
		else:
			# Legs need to be adjusted
			return self.adjust_legs(position_delta, legs, strikes, option_strike_data, min_premium)

	def adjust_legs(self, position_delta: float, legs: List[Leg], strikes: list[float], option_strike_data, min_premium: float) -> List[Leg] | None:
		if position_delta > 0:
			# Short Put leg need to be further OTM
			for leg in legs:
				if leg.right == OptionRight.PUT and leg.action == OrderAction.SELL:
					# Find next OTM Put Strike
					next_strike = OptionHelper.get_next_strike(leg.strike, strikes, False)
					if next_strike is not None:
						leg.strike = next_strike
						logger.debug(f'Adjusted Put Leg to Strike: {next_strike}')

						# Long Put Leg adjustment
						long_leg = next((l for l in legs if l.right == OptionRight.PUT and l.action == OrderAction.BUY), None)
						if long_leg is not None:
							long_leg.strike = self.get_valid_strike(next_strike - self._template.wing, True)
							logger.debug(f'Adjusted Long Leg to Strike: {long_leg.strike}')
					else:
						logger.error('No further OTM Put Strike found, cannot adjust position delta.')
						return None
		else:
			# Short Call leg need to be further OTM
			for leg in legs:
				if leg.right == OptionRight.CALL and leg.action == OrderAction.SELL:
					# Find next OTM Call Strike
					next_strike = OptionHelper.get_next_strike(leg.strike, strikes, True)
					if next_strike is not None:
						leg.strike = next_strike
						logger.debug(f'Adjusted Call Leg to Strike: {next_strike}')

						# Long Leg adjustment
						long_leg = next((l for l in legs if l.right == OptionRight.CALL and l.action == OrderAction.BUY), None)
						if long_leg is not None:
							long_leg.strike = self.get_valid_strike(next_strike + self._template.wing, False)
							logger.debug(f'Adjusted Long Leg to Strike: {long_leg.strike}')
					else:
						logger.error('No further OTM Call Strike found, cannot adjust position delta.')
						return None
		return self.determine_order_legs(legs, strikes, option_strike_data, min_premium)

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
		sl_order_legs = copy.deepcopy(managedTrade.entryOrder.legs)
		self.invert_leg_actions(sl_order_legs)
		logger.debug(f'Calculated stop loss price: {stopLossPrice}')
		stopLossOrder = Order(symbol=self._template.symbol, legs=sl_order_legs, action=OrderAction.SELL_TO_CLOSE, quantity=self._template.amount, type=OrderType.STOP, price=stopLossPrice)
		return stopLossOrder