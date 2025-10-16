from dataclasses import dataclass
import datetime


@dataclass
class SignalData:
	"""
	Class for holding signal data especially from external signals
	"""
	
	timestamp: datetime
	"""
	Timestamp of the signal
	"""

	close: float
	"""
	Close price of the underlying asset at signal time
	"""

	strike: float
	"""
	Defined strike price of the signal. It may be empty
	"""
	

