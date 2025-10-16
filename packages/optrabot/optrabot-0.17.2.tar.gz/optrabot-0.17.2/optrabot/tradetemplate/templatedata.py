
class ShortStrikeData:
	"""
	Data class which holds configuration of the short strike of a template
	"""
	def __init__(self):
		self.offset :float = None
		self.delta :int = None
		self.price :float = None

	def toDict(self):
		""" Returns a dictionary representation of the Short Strke Data which is used for
		the config file.
		"""
		returnDict = {'offset': self.offset}
		return returnDict

class LongStrikeData:
	"""
	Data class which holds configuration of the long strike of a template
	"""
	def __init__(self):
		self.width :float = None
		self.max_width :float = None
		self.offset: float = None
		self.delta :int = None
		self.price :float = None

	def toDict(self):
		""" Returns a dictionary representation of the Long Strke Data which is used for
		the config file.
		"""
		returnDict = {}
		if self.width:
			returnDict['width'] = self.width
		if self.offset:
			returnDict['offset'] = self.offset
		if self.price:
			returnDict['price'] = self.price
		if self.max_width:
			returnDict['max_width'] = self.max_width
		return returnDict