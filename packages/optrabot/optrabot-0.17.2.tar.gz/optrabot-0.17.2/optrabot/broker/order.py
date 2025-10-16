from datetime import datetime
from enum import Enum
from optrabot.optionhelper import OptionHelper
from typing import Optional

class OrderAction(str, Enum):
    """
    Represents actions of an order or order le
    """

    BUY_TO_OPEN = "Buy to Open"
    BUY_TO_CLOSE = "Buy to Close"
    SELL_TO_OPEN = "Sell to Open"
    SELL_TO_CLOSE = "Sell to Close"
    BUY = "Buy"
    SELL = "Sell"

class OrderType(str, Enum):
	"""
	Represents order types
	"""
	LIMIT = "Limit"
	MARKET = "Market"
	STOP = "Stop"
	STOP_LIMIT = "Stop Limit"

class OrderStatus(str, Enum):
	"""
	Represents the status of an order
	"""
	OPEN = "Open"
	FILLED = "Filled"
	CANCELLED = "Cancelled"

class OptionRight(str, Enum):
	"""
	Represents the right of an option
	"""
	CALL = "Call"
	PUT = "Put"

class Leg():
	"""
	Represents a leg of an order.
	"""
	action: OrderAction
	quantity: Optional[int]
	symbol: str
	strike: float
	right: OptionRight
	expiration: datetime
	askPrice: float = None
	bidPrice: float = None
	midPrice: float = None
	delta: float = None
	brokerSpecific = {}
     
	def __init__(self, action: OrderAction, symbol: str, quantity: Optional[int] = 0, strike: float = None, right: OptionRight = None, expiration: datetime = None):
		self.action = action
		self.quantity = quantity
		self.symbol = symbol
		self.right = right
		self.strike = strike
		self.expiration = expiration
		self.delta = 0

class PriceEffect(str, Enum):
    """
    This is an :class:`~enum.Enum` that shows the sign of a price effect.
    """
    CREDIT = "Credit"
    DEBIT = "Debit"
    NONE = "None"

class Order():
	"""
	Represents an order. A order can have multiple legs
	"""
	
	def __init__(self, symbol: str = '', action: OrderAction = None, type: OrderType = None, legs: list[Leg] = None, quantity: int = 1, price: float = None):
		self.symbol = symbol
		self.action = action
		self.legs: list[Leg] = legs
		self.type = type
		self.quantity = quantity
		self.price: float = price
		self.averageFillPrice: float = None
		self.ocaGroup = None
		self.status: OrderStatus = None
		self.orderReference: str = ''
		self.brokerSpecific = {}
		self.broker_order_id = ''
		self.price_effect = PriceEffect.NONE

	def determine_price_effect(self):
		""" 
		Determines the price effect of the order based on its legs and the price data
		"""
		total_price = self.calculate_price()
		self.price_effect = PriceEffect.CREDIT if total_price < 0 else PriceEffect.DEBIT if total_price > 0 else PriceEffect.NONE

	def calculate_price(self) -> float:
		"""
		Calculates the total price of the order based on its legs and their prices
		"""
		total_price = 0.0
		for leg in self.legs:
			if leg.strike is None or leg.right is None:
				continue  # Skip legs without strike or right
			if leg.midPrice is None:
				leg.midPrice = self.calculate_mid_price(leg.askPrice, leg.bidPrice)
			
			if leg.action in [OrderAction.BUY_TO_OPEN, OrderAction.BUY_TO_CLOSE, OrderAction.BUY]:
				total_price += leg.midPrice * (leg.quantity if leg.quantity else 1)
			elif leg.action in [OrderAction.SELL_TO_OPEN, OrderAction.SELL_TO_CLOSE, OrderAction.SELL]:
				total_price -= leg.midPrice * (leg.quantity if leg.quantity else 1)
		
		return total_price

	def calculate_mid_price(self, ask_price: float, bid_price: float) -> float:
		"""
		Calculates the mid price based on the given ask and bid prices
		"""
		int_ask_price = ask_price if not OptionHelper.isNan(ask_price) and ask_price >= 0 else 0
		int_bid_price = bid_price if not OptionHelper.isNan(bid_price) and bid_price >= 0 else 0
		return (int_ask_price + int_bid_price) / 2

class Execution():
	"""
	Represents a fill information of an order execution
	"""
	def __init__(self, id: str, action: OrderAction, sec_type: str, strike: float, amount: int, price: float, timestamp: datetime, expiration: datetime):
		self.id: str = id
		self.action: OrderAction =action
		self.sec_type: str = sec_type
		self.strike: float = strike
		self.timestamp: datetime = timestamp
		self.expiration: datetime = expiration
		self.amount: int = amount
		self.price: float = price