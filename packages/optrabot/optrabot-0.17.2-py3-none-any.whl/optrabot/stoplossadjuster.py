from loguru import logger

class StopLossAdjuster:
	def __init__(self, reverse: bool, trigger: int, stop: int, offset: float = 0) -> None:
		"""
		reverse: Wenn True, bedeutet es das tiefere aktuelle Preise einen Profit darstellen z.B. bei verkauften Optionen
		basePrice: Basispreis für die Berechnung - typicherweise der Einstiegpreis der Position. Der Basispreis ist immer positiv
		offset: $ Wert um den der neue Stop Loss näher an den aktuellen Preis (positiv) oder weiter weg vom aktuellen Preis (negativ) wird.
		"""
		self._reverse = reverse
		self._basePrice = None
		self._trigger = trigger
		self._stop = stop
		self._offset = offset
		self._triggered = False

		self._targetStopPrice = 0

	def isTriggered(self) -> bool:
		""" Returns True, if the Adjuster has triggered and adjusted a stop price already
		"""
		return self._triggered

	def execute(self, currentPrice: float) -> any:
		"""
		If the Stop Loss Adjuster has not been executed, if determines if the stoploss
		needs to be adjusted and returns the new stoploss price.
		None is returned, if the stoploss doesn't has to be adjusted

		currentPrice: Aktueller Preis der Position
		"""
		if self._triggered == True:
			return None
		
		assert self._basePrice != None
		
		currentPNLPerContract = 0
		if self._reverse == True:
			currentPNLPerContract = self._basePrice - currentPrice
		else:
			currentPNLPerContract = currentPrice - self._basePrice

		currentPNLPercent = round((currentPNLPerContract / self._basePrice) * 100, 2)
		logger.debug(f'Current trade price: {currentPrice:.2f} entry price: {self._basePrice:.2f} PnL (%): {currentPNLPercent:.2f}')

		if currentPNLPercent >= self._trigger:
			logger.debug('Profit level {} percent reached. Triggering Stop Loss adjustment.', self._trigger)
			self._triggered = True
			#stopDistance = self._basePrice * self._stop / 100
			if self._reverse == True:
				stop_calc_base = self._basePrice * (100 - self._trigger) / 100
			else:
				stop_calc_base = self._basePrice * (self._trigger + 100) / 100
			stopDistance = stop_calc_base * self._stop / 100
			offset = self._offset
			if self._reverse == True:
				stopDistance = stopDistance * -1
				offset = self._offset * -1
			newStopPrice = stop_calc_base - stopDistance + offset
			return newStopPrice

		return None
	
	def setBasePrice(self, basePrice: float):
		""" Sets the base price for the calculations of the stop loss adjuster
		"""
		self._basePrice = basePrice
		stopDistance = self._basePrice / 100 * self._stop
		if self._reverse == True:
			self._targetStopPrice = self._basePrice + stopDistance
	
	def resetTrigger(self):
		"""
		Reset the trigger
		"""
		self._triggered = False
	
	def toDict(self):
		""" Returns a dictionary representation of the adjusterwhich is used for
		the config file.
		"""
		returnDict = {'trigger': self._trigger, 'stop': self._stop, 'offset': self._offset }
		return returnDict
	
	def __str__(self):
		return ('Reverse: ' + str(self._reverse) + ' Trigger: ' + str(self._trigger) + ' Stop: ' + str(self._stop) + 
		' Offset: ' + str(self._offset) + ' Triggered: ' + str(self.isTriggered()) )





