from typing import OrderedDict
from datetime import datetime
import calendar as cal
import pytz

from loguru import logger
class TriggerType:
	External: str = 'external'
	Time: str = 'time'

class TemplateTrigger:
	_trigger_time: datetime = None
	type: TriggerType = None
	_weekdays: list = None
	_blackout_days: list = None

	def __init__(self, triggerdata: OrderedDict) -> None:
		type = triggerdata['type']
		assert type in [TriggerType.External, TriggerType.Time]
		self.type = type
		self.value = triggerdata['value']
		assert self.value != '' and self.value != None
		
		if self.type == TriggerType.Time:
			# Check the time 
			try:
				self._trigger_time = self.parseTimeWithTimezone(self.value).astimezone(pytz.utc)
			except ValueError as valError:
				logger.error(f'Invalid time format for parameter "value"! Expecting HH:MM <Timezone>')
				self._trigger_time = None

			# Extract weekdays from the trigger data
			try:
				weekdays = triggerdata['weekdays']
				self._weekdays = self.extractWeekdays(weekdays)
			except KeyError:
				pass
			pass

		try:
			blackout_days = triggerdata['blackout_days']
			self._blackout_days = self.extract_blackout_days(blackout_days)
		except KeyError as keyError:
			pass

		try:
			timefrom = triggerdata['timefrom']
			self.fromTimeUTC = self.parseTimeWithTimezone(timefrom).astimezone(pytz.utc)
		except KeyError:
			self.fromTimeUTC = None
		except ValueError as valError:
			logger.error(f'Invalid time format for parameter "timefrom"!')

		try:
			timeto = triggerdata['timeto']
			self.toTimeUTC = self.parseTimeWithTimezone(timeto).astimezone(pytz.utc)
		except KeyError:
			self.toTimeUTC = None
		except ValueError as valError:
			logger.error(f'Invalid time format for parameter "timeto"!')

		try:
			excludeTimeFrom = triggerdata['excludetimefrom']
			self.excludeFromTimeUTC = self.parseTimeWithTimezone(excludeTimeFrom).astimezone(pytz.utc)
		except KeyError:
			self.excludeFromTimeUTC = None
		except ValueError as valError:
			logger.error(f'Invalid time format for parameter "excludetimefrom"!')

		try:
			excludeTimeTo = triggerdata['excludetimeto']
			self.excludeToTimeUTC = self.parseTimeWithTimezone(excludeTimeTo).astimezone(pytz.utc)
		except KeyError:
			self.excludeToTimeUTC = None
		except ValueError as valError:
			logger.error(f'Invalid time format for parameter "excludetimeto"!')
		
	def extract_blackout_days(self, blackout_days: list) -> list:
		"""
		Extracts the blackout days from the yaml dictionary and stores them in a list.
		"""
		extracted_blackout_days = []
		for value in blackout_days:
			try:
				date = datetime.strptime(value, '%Y-%m-%d').date()
				extracted_blackout_days.append(date)
			except ValueError as valError:
				logger.error(f'Invalid date format "{value}" for parameter "blackout_days"! Expecting YYYY-MM-DD')
				continue

		return extracted_blackout_days if len(extracted_blackout_days) > 0 else None

	def extractWeekdays(self, weekdays: list) -> list:
		"""
		Extracts the weekdays from the yaml dictionary and stores them in a list using the 
		calendar weekday constants.
		"""
		weekdaysList = []
		for value in weekdays:
			uppercase_weekday = value.upper()
			match uppercase_weekday:
				case 'MONDAY':
					weekdaysList.append(cal.MONDAY)
				case 'TUESDAY':
					weekdaysList.append(cal.TUESDAY)
				case 'WEDNESDAY':
					weekdaysList.append(cal.WEDNESDAY)
				case 'THURSDAY':
					weekdaysList.append(cal.THURSDAY)
				case 'FRIDAY':
					weekdaysList.append(cal.FRIDAY)
				case _:
					logger.error(f'Invalid weekday "{value}" in weekdays list! Expecting MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY')

		return weekdaysList if len(weekdaysList) > 0 else None

	def parseTimeWithTimezone(self, timeStr: str) -> datetime.time:
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

	def toDict(self):
		""" Returns a dictionary representation of the Trigger which is used for
		the config file.
		"""
		returnDict = {'type': self.type, 'value': self.value}
		eastern = pytz.timezone('US/Eastern')
		if self.fromTimeUTC != None:
			returnDict['timefrom'] = self.fromTimeUTC.astimezone(eastern).strftime('%H:%M %Z')
		if self.toTimeUTC != None:
			returnDict['timeto'] = self.toTimeUTC.astimezone(eastern).strftime('%H:%M %Z')
		if self.excludeFromTimeUTC != None:
			returnDict['excludetimefrom'] = self.excludeFromTimeUTC.astimezone(eastern).strftime('%H:%M %Z')
		if self.excludeToTimeUTC != None:
			returnDict['excludetimeto'] = self.excludeToTimeUTC.astimezone(eastern).strftime('%H:%M %Z')	
		return returnDict