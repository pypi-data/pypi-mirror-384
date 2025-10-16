from typing import OrderedDict
from datetime import datetime
from loguru import logger
class EarlyExitTriggerType:
	Breakeven: str = 'breakeven'
	Time: str = 'time'

class EarlyExitTrigger:
	_trigger_time: datetime = None
	type: EarlyExitTriggerType = None

	def __init__(self, triggerdata: OrderedDict) -> None:
		type = triggerdata['type']
		assert type in [EarlyExitTriggerType.Breakeven, EarlyExitTriggerType.Time]
		self.type = type
		try:
			self.value = triggerdata['value']
		except KeyError:
			self.value = None
			pass