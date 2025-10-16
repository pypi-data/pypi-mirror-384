
from typing import List
from optrabot.deltaadjuster import DeltaAdjuster
from optrabot.models import Trade
from optrabot.tradetemplate.templatefactory import Template
from optrabot.broker.order import Execution, Leg, OptionRight, Order, OrderAction
from optrabot.stoplossadjuster import StopLossAdjuster
import copy

class ManagedTrade:
	"""
	ManagedTrade is representing a trade which is currently managed by the TradeManager.
	"""
	adjustment_orders: List[Order]

	def __init__(self, trade: Trade, template: Template, entryOrder: Order, account: str = ''): 
		self.trade = trade
		self.entryOrder = entryOrder
		self.template = template
		self.account = account
		self.takeProfitOrder: Order = None
		self.stopLossOrder: Order = None
		self.closing_order: Order = None
		self.status = 'NEW'
		self.realizedPNL = 0.0
		self.transactions = []
		self.expired = False
		self.entry_price = None					# Holds the entry price for the trade
		self.current_price: float = None		# Holds the current price of the trade
		self.current_delta: float = None		# Holds the current delta of the position
		self.current_legs: List[Leg] = []		# Holds the current legs of the trade (filled after entry order is excuted)
		self.stoploss_adjusters: List[StopLossAdjuster] = []
		self.delta_adjusters: List[DeltaAdjuster] = []
		self.long_legs_removed = False			# will be set to true for credit_trades if the long legs are no longer available
		self.adjustment_orders = []				# Holds orders which are created by delta adjusters

	def isActive(self) -> bool:
		"""
		Returns True if the trade is active
		"""
		return self.status == 'OPEN'
	
	def setup_stoploss_adjusters(self):
		""" 
		Copies the stop loss adjusters from the template to the managed trade and sets the
		base price for earch of the adjusters
		"""
		for adjuster in self.template.get_stoploss_adjusters():
			adjuster_copy = copy.copy(adjuster)
			adjuster_copy.setBasePrice(self.entry_price)
			self.stoploss_adjusters.append(adjuster_copy)

	def setup_delta_adjusters(self):
		"""
		Copies the delta adjusters from the template to the managed trade
		"""
		for adjuster in self.template.get_delta_adjusters():
			adjuster_copy = copy.copy(adjuster)
			self.delta_adjusters.append(adjuster_copy)

	def update_current_legs(self, adjustment_order: Order):
		"""
		Updates the current legs of the trade from the execution of the adjustment order.
		"""
		for leg in adjustment_order.legs:
			opposite_action = OrderAction.SELL if leg.action == OrderAction.BUY else OrderAction.BUY
			existing_leg = next((l for l in self.current_legs if l.strike == leg.strike and l.right == leg.right and l.action != opposite_action), None)
			if existing_leg:
				# If an existing leg was found, remove it from the current legs, because it has been closed
				self.current_legs.remove(existing_leg)
			else:
				# Otherwise it is a new leg added by execution of the adjustment order
				self.current_legs.append(copy.copy(leg))