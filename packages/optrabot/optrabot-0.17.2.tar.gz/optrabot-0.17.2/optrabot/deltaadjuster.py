import copy
from datetime import datetime
from typing import List
from loguru import logger

from optrabot.optionhelper import OptionHelper
from optrabot.broker.optionpricedata import OptionStrikeData
from optrabot.broker.order import Leg, OptionRight, Order, OrderAction, OrderType, PriceEffect

class DeltaAdjuster:
	from_time: datetime
	credit_legs: List[Leg]
	wing_size: int
	adjustment_orders: List[Order]

	def __init__(self, from_time: datetime, threshold: int) -> None:
		self.from_time = from_time
		self.threshold = threshold
		self.credit_legs = []
		self.wing_size = None
		self.adjustment_orders = []


	def execute(self, trade) -> List[Order] | None:
		"""
		Execute the delta adjustment for the given trade and returns a list of orders to be executed
		to perform the adjustment on the trade.
		"""
		from optrabot.managedtrade import ManagedTrade
		from optrabot.broker.brokerfactory import BrokerFactory
		managed_trade: ManagedTrade = trade
		broker_connector = BrokerFactory().getBrokerConnectorByAccount(trade.template.account)
		assert broker_connector != None

		atm_strike = broker_connector.get_atm_strike(managed_trade.trade.symbol)
		if not atm_strike:
			return
		
		starting_legs: List[Leg] = []
		# Start with current Long legs
		closing_costs = self.calculate_position_price(managed_trade.current_legs, False)
		for leg in managed_trade.current_legs:
			if leg.action == OrderAction.BUY:
				starting_legs.append(copy.copy(leg))
		logger.debug(f'Closing costs for Legs: {closing_costs:.2f}')

		current_short_call_strike = atm_strike
		current_short_put_strike = atm_strike
		option_strike_data = broker_connector.get_option_strike_data(managed_trade.trade.symbol, managed_trade.current_legs[0].expiration)
		strikes = option_strike_data.strikeData.keys()
		
		next_short_call_strike = OptionHelper.get_next_strike(current_short_call_strike, strikes, True)
		next_short_put_strike = OptionHelper.get_next_strike(current_short_put_strike, strikes, False)
		logger.debug(f'ATM Strike: {atm_strike} - starting with Put Strike: {next_short_put_strike} Call Strike: {next_short_call_strike}')
		for leg in managed_trade.current_legs:
			if leg.action == OrderAction.SELL:
				if leg.right == OptionRight.CALL:
					short_call_leg = Leg(action=leg.action, symbol=leg.symbol, quantity=leg.quantity, strike=next_short_call_strike, right=leg.right, expiration=leg.expiration)
					starting_legs.append(short_call_leg)
				elif leg.right == OptionRight.PUT:
					short_put_leg = Leg(action=leg.action, symbol=leg.symbol, quantity=leg.quantity, strike=next_short_put_strike, right=leg.right, expiration=leg.expiration)
					starting_legs.append(short_put_leg)

		# Jetzt den eigentlichen Delta Adjustment Prozess starten.
		self.wing_size = managed_trade.template.get_wing()
		delta_adjusted_legs = self.adjust_delta(starting_legs, strikes, option_strike_data, closing_costs)
		if delta_adjusted_legs == None:
			logger.info(f'Delta adjustment not possible for a credit currently!')
			return

		# Ajdust Long legs if necessary for machting the wing size
		if self.wing_size is not None:
			# Call side
			short_call_leg = next((leg for leg in delta_adjusted_legs if leg.right == OptionRight.CALL and leg.action == OrderAction.SELL), None)
			long_call_leg = next((leg for leg in delta_adjusted_legs if leg.right == OptionRight.CALL and leg.action == OrderAction.BUY), None)
			if long_call_leg.strike - short_call_leg.strike > self.wing_size:
				long_call_leg.strike = short_call_leg.strike + self.wing_size

			# Put side
			short_put_leg = next((leg for leg in delta_adjusted_legs if leg.right == OptionRight.PUT and leg.action == OrderAction.SELL), None)
			long_put_leg = next((leg for leg in delta_adjusted_legs if leg.right == OptionRight.PUT and leg.action == OrderAction.BUY), None)
			if short_put_leg.strike - long_put_leg.strike > self.wing_size:
				long_put_leg.strike = short_put_leg.strike - self.wing_size

		# Compose order operations for performing the adjustment
		strikes_string = ''
		for leg in delta_adjusted_legs:
			if strikes_string != '':
				strikes_string += '/'
			strikes_string += str(leg.strike)
		logger.debug(f'Adjusted Legs to Strikes: {strikes_string}')

		# Detect changes
		original_legs = copy.copy(managed_trade.current_legs)
		original_legs = sorted(original_legs, key=lambda x: (x.action.value, x.right.value))
		long_legs_for_adjustment_order: List[Leg] = []
		short_legs_for_adjustment_order: List[Leg] = []
		for original_leg in original_legs:
			if original_leg.action == OrderAction.BUY:
				# Detect changes in Long Legs
				delta_leg = next((leg for leg in delta_adjusted_legs if leg.right == original_leg.right and leg.action == OrderAction.BUY), None)
				if delta_leg and delta_leg.strike != original_leg.strike:
					logger.info(f'Long Leg Adjusted: {original_leg.strike} -> {delta_leg.strike}')
					if original_leg.bidPrice > 0:
						leg_for_closing = copy.copy(original_leg)
						leg_for_closing.action = OrderAction.SELL
						long_legs_for_adjustment_order.append(leg_for_closing)	# First close the original leg
					else:
						logger.debug(f'Long Leg at strike {original_leg.strike} has no bid price...it will left orphan.')
						continue
					# Obtain price data for opening legs
					strike_price_data =  option_strike_data.strikeData[delta_leg.strike]
					delta_leg.askPrice = strike_price_data.putAsk if delta_leg.right == OptionRight.PUT else strike_price_data.callAsk
					delta_leg.bidPrice = strike_price_data.putBid if delta_leg.right == OptionRight.PUT else strike_price_data.callBid
					long_legs_for_adjustment_order.append(copy.copy(delta_leg))
			elif original_leg.action == OrderAction.SELL:
				# Detect changes in Short Legs
				delta_leg = next((leg for leg in delta_adjusted_legs if leg.right == original_leg.right and leg.action == OrderAction.SELL), None)
				if delta_leg and delta_leg.strike != original_leg.strike:
					logger.info(f'Short Leg Adjusted: {original_leg.strike} -> {delta_leg.strike}')
					leg_for_closing = copy.copy(original_leg)
					leg_for_closing.action = OrderAction.BUY
					short_legs_for_adjustment_order.append(leg_for_closing)

					# Obtain price data for opening legs
					strike_price_data =  option_strike_data.strikeData[delta_leg.strike]
					delta_leg.askPrice = strike_price_data.putAsk if delta_leg.right == OptionRight.PUT else strike_price_data.callAsk
					delta_leg.bidPrice = strike_price_data.putBid if delta_leg.right == OptionRight.PUT else strike_price_data.callBid
					
					short_legs_for_adjustment_order.append(copy.copy(delta_leg))
		if len(long_legs_for_adjustment_order) > 0:
			long_leg_adjustment_order = Order(symbol=managed_trade.trade.symbol, legs=long_legs_for_adjustment_order, action=OrderAction.BUY_TO_OPEN, quantity=managed_trade.template.amount, type=OrderType.LIMIT)
			self.adjustment_orders.append(long_leg_adjustment_order)
		if len(short_legs_for_adjustment_order) > 0:
			short_leg_adjustment_order = Order(symbol=managed_trade.trade.symbol, legs=short_legs_for_adjustment_order, action=OrderAction.BUY_TO_OPEN, quantity=managed_trade.template.amount, type=OrderType.LIMIT)
			self.adjustment_orders.append(short_leg_adjustment_order)

		if len(self.adjustment_orders) > 0:
			return self.adjustment_orders
		else:
			return None

	def adjust_delta(self, legs: List[Leg], strikes: list[float], option_strike_data, closing_costs: float) -> List[Leg]:
		"""
		Performs the adjustment of the positions delta recursively.
		"""
		position_delta = self.calculate_position_delta_and_price(legs, option_strike_data) * 100
		if position_delta < 2 and position_delta > -2:
			# Delta is OK, check if price is sufficient
			new_position_price = self.calculate_position_price(legs, True)
			adjustment_cost = closing_costs + new_position_price
			logger.debug(f'Adjusted position opening price: {new_position_price:.2f}')
			logger.debug(f'Adjustment price: {adjustment_cost:.2f}')
			if adjustment_cost >= 0:
				# Store legs which gave a credit
				self.credit_legs = copy.deepcopy(legs)
				# Try to adjust
				return self.adjust_legs(position_delta, legs, strikes, option_strike_data, closing_costs)
			else:
				# Adjustment for a debit --> So we adjusted to much
				return self.credit_legs
		else:
			# Legs need to be adjusted
			return self.adjust_legs(position_delta, legs, strikes, option_strike_data, closing_costs)

	def adjust_legs(self, position_delta: float, legs: List[Leg], strikes: list[float], option_strike_data, closing_costs: float) -> List[Leg]:
		if position_delta > 0:
			# Short Put leg need to be further OTM
			for leg in legs:
				if leg.right == OptionRight.PUT and leg.action == OrderAction.SELL:
					# Find next OTM Put Strike
					next_strike = OptionHelper.get_next_strike(leg.strike, strikes, False)
					if next_strike is not None:
						leg.strike = next_strike
						logger.debug(f'Adjusted Put Leg to Strike: {next_strike}')
					else:
						logger.error('No further OTM Put Strike found, cannot adjust position delta.')
						return legs
		else:
			# Short Call leg needs to be further OTM
			for leg in legs:
				if leg.right == OptionRight.CALL and leg.action == OrderAction.SELL:
					# Find next OTM Call Strike
					next_strike = OptionHelper.get_next_strike(leg.strike, strikes, True)
					if next_strike is not None:
						leg.strike = next_strike
						logger.debug(f'Adjusted Call Leg to Strike: {next_strike}')
					else:
						logger.error('No further OTM Call Strike found, cannot adjust position delta.')
						return legs
		return self.adjust_delta(legs, strikes, option_strike_data, closing_costs)

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
