from typing import Dict
import datetime as dt
import pytz

class OptionStrikePriceData:
	def __init__(self) -> None:
		self.callBid: float = None
		self.callAsk: float = None
		self.callDelta: float = None
		self.putBid: float = None
		self.putAsk: float = None
		self.putDelta: float = None
		self.brokerSpecific = {}  # Broker specific data
		self.lastUpdated: dt.datetime =None  # Last time the data was updated

	def getPutMidPrice(self) -> float:
		"""
		Returns the mid price of the put option
		"""
		if self.putBid == None:
			bidPrice = 0
		else:
			bidPrice = self.putBid
		
		if self.putAsk == None:
			askPrice = 0
		else:
			askPrice = self.putAsk
		return (bidPrice + askPrice) / 2
	
	def getCallMidPrice(self) -> float:
		"""
		Returns the mid price of the call option
		"""
		if self.callBid == None:
			bidPrice = 0
		else:
			bidPrice = self.callBid
		
		if self.callAsk == None:
			askPrice = 0
		else:
			askPrice = self.callAsk
		return (bidPrice + askPrice) / 2

	def get_call_delta(self) -> float:
		"""
		Returns the delta of the call option
		"""
		if self.callDelta == None:
			return 0
		return self.callDelta
	
	def get_put_delta(self) -> float:
		"""
		Returns the delta of the put option
		"""
		if self.putDelta == None:
			return 0
		return self.putDelta

	def is_outdated(self) -> bool:
		"""
		Returns true if the data is outdated
		"""
		if self.lastUpdated == None:
			return True
		delta = dt.datetime.now(pytz.timezone('US/Eastern')) - self.lastUpdated
		return delta.total_seconds() > 30

class OptionStrikeData:
	def __init__(self) -> None:
		self.strikeData: Dict[float, OptionStrikePriceData] = {}