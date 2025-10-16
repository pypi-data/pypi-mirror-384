class MarketDataType:
	Undefined : int = 0
	Live : int = 1
	Delayed : int = 3
	
	def __init__(self, marketDataType: int = Undefined):
		self.Value: int = marketDataType
	
	def toString(self):
		match self.Value:
			case MarketDataType.Live:
				return 'Live'
			case MarketDataType.Delayed:
				return 'Delayed'
			case _:
				return 'Undefined'
			
	def byValue(self, marketDataType: int):
		if marketDataType != MarketDataType.Delayed and marketDataType != MarketDataType.Live:
			self._invalidValue(marketDataType)
		self.Value = marketDataType
	
	def byString(self, marketDataType: str):
		match marketDataType.upper():
			case 'LIVE':
				self.Value = MarketDataType.Live
			case 'DELAYED':
				self.Value = MarketDataType.Delayed
			case _:
				self._invalidValue(marketDataType)

	def _invalidValue(self, invalidValue):
		self.Value = MarketDataType.Undefined
		raise ValueError('Invalid Market Data type: ' + str(invalidValue))
