from datetime import datetime
from loguru import logger
import pytz

class Common:

	@staticmethod
	def parse_with_timezone(timeStr: str) -> datetime.time:
		""" 
		Parses a time string like 11:00 EST to a datetime.time object
		"""
		if timeStr == None:
			return None
		
		parts = timeStr.split(' ')
		try:
			now = datetime.now()
			naive_time = datetime.strptime(parts[0], '%H:%M').replace(year=now.year, month=now.month, day=now.day)
			if len(parts) > 1:
				tzstr = parts[1]
			else:
				tzstr = 'EST'
			tzstr = "US/Eastern" if tzstr == 'EST' else tzstr
			tz = pytz.timezone(tzstr)
			localized_time = tz.localize(naive_time)
			return localized_time
		except ValueError and AttributeError as error:
			logger.error(f'Invalid time format: {timeStr} - Expecting HH:MM <Timezone>')
			return None