"""
Module to define the config of the application
"""
from collections import UserDict
from typing import List, OrderedDict
from ruyaml import YAML
from ruyaml.scanner import ScannerError
from loguru import logger
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import NumberValidator
from InquirerPy.validator import EmptyInputValidator
import os

from optrabot.tradetemplate.templatefactory import IronFly, PutSpread, Template, TemplateFactory, TemplateType
from optrabot.tradetemplate.templatetrigger import TemplateTrigger
from optrabot.tradetemplate.templatedata import LongStrikeData, ShortStrikeData

configFileName = "config.yaml"
defaultHubHost = 'wss://app.optrabot.com'

# Global variable to store the current configuration
appConfig = None

class Config(UserDict):
	def __init__(self, config_path=configFileName):
		self.config_path = os.path.expanduser(config_path)
		self._templates = []
		self.loaded = False
		self.load()

	def load(self):
		"""
        Loads configuration from configuration YAML file.
        """
		logger.debug("Try loading config file...")
		try:
			with open(os.path.expanduser(self.config_path), 'r') as f:
				try:
					self.data = YAML().load(f)
					logger.debug("Config loaded successfully.")
					self.loaded = True
				except Exception as e:
					logger.error("Error parsing yaml of configuration file '{}' :{}", e.problem_mark, e.problem)
		except FileNotFoundError:
			logger.error(
				 "Error opening configuration file {}".format(self.config_path)
			)
			self.createDefaultConfig()

	def createDefaultConfig(self):
		""" Create a default configuration 
		"""
		logger.info('Using a default configuration.')
		defaultDoc = 'general:\n'
		defaultDoc += '  instanceid: testagent\n'
		self.data = YAML().load(defaultDoc)

	def get(self, key):
		"""
		Fetch the configuration value for the specified key. If there are nested dictionaries, a dot
		notation can be used.

		So if the configuration contents are:

		self.data = {
			'first': {
				'second': 'value'
			},
		}

        self.data.get('first.second') == 'value'

		Arguments:
        	key(str): Configuration key to fetch
		"""
		keys = key.split('.')
		value = self.data.copy()

		for key in keys:
			value = value[key]
			if value == None:
				raise KeyError

		return value
	
	def save(self):
		"""
		Saves configuration in the configuration YAML file.
		"""
		with open(os.path.expanduser(self.config_path), 'w+') as f:
			yaml = YAML()
			yaml.default_flow_style = False
			yaml.dump(self.data, f)

	def logConfigurationData(self):
		"""
		Write Configuration data into the optrabot log file in Debug Mode
		"""
		logger.debug('Using following configuration data...')
		for key, value in self.data.items():
			logger.debug('Category {}:', key)
			if value == None:
				continue
			children = OrderedDict(value)
			for subkey, subvalue in children.items():
				if isinstance(subvalue, dict):
					logger.debug('Sub Category {}:', subkey)
					try:
						subChildren = OrderedDict(subvalue)
						for subsubkey, subsubvalue in subChildren.items():
							if isinstance(subsubvalue, dict):
								logger.debug('	{}', subsubkey)
								try:
									subsubChildren = OrderedDict(subsubvalue)
									for subsubsubkey, subsubsubvalue in subsubChildren.items():
										logger.debug('       	{}: {}', subsubsubkey, subsubsubvalue)
								except ValueError:
									continue
							else:
								logger.debug('       {}: {}', subsubkey, subsubvalue)
					except ValueError:
						continue
				else:
					logger.debug('   {}: {}', subkey, subvalue)

	def readTemplates(self):
		self._templates = []
		try:
			for key, data in self.get('templates').items():
				logger.debug('Reading Template: {}', key)
				template = TemplateFactory.createTemplate(name=key,data=data)
				if template != None:
					if template.validate():
						template_state = '' if template.is_enabled() else '(disabled)'
						logger.info(f'Loaded Trade Template: {template.name} {template_state}')
						self._templates.append(template)
					else:
						logger.error(f'Template {template.name} is not valid. Please check the configuration!')
		except KeyError as exc:
			logger.error('Missing key: {} --> No templates are configured!', exc)

	def getTemplates(self) -> List[Template]:
		""" Returns the configured templates
		"""
		return self._templates
	
	def getInstanceId(self) -> str:
		""" Returns the configured OptraBot Agent Id / Instance Id
		"""
		instanceId = ''
		try:
			instanceId = self.get('general.instanceid')
		except KeyError as exc:
			instanceId = self.get('general.agentid')
		return instanceId

def captureTemplateData(template: Template):
	template.strategy = inquirer.text(message="Strategy:", default=template.strategy).execute()
	template.adjustmentStep = float(inquirer.number(message="Increment for limit price adjustments ($):",default=template.adjustmentStep, float_allowed=True, validate=EmptyInputValidator()).execute())
	#if template._type == TemplateType.IronFly:
	#	template.wing = int(inquirer.number(message="Wing Size (points):", default=template.wing, min_allowed=10).execute())
	if template._type == TemplateType.PutSpread:
		short_strike_data = template.getShortStrikeData()
		short_strike_data.offset = int(inquirer.number(message="Offset for the short strike ($):", default=short_strike_data.offset).execute())
		template.setShortStikeData(short_strike_data)
		long_strike_data = template.getLongStrikeData()
		long_strike_data.width = int(inquirer.number(message="Width of the Spread (points):", default=long_strike_data.width, min_allowed=1).execute())
		template.setLongStikeData(long_strike_data)
	template.account = inquirer.text(message="Account number to be used for trading:",default=template.account, validate=EmptyInputValidator()).execute()
	template.amount = int(inquirer.number(message="Number of contracts to be traded:", default=template.amount, min_allowed=1).execute())
	try:
		template.takeProfit = int(inquirer.number(message="Percentage of captured premium as profit target (%):", default=template.takeProfit, min_allowed=1, max_allowed=100).execute())
	except ValueError:
		template.takeProfit = None
	template.stopLoss = int(inquirer.number(message="Percentage of captured premium as stop loss level (%):", default=template.stopLoss, min_allowed=1).execute())
	if template._type == TemplateType.IronFly:
		template.minPremium = float(inquirer.number(message="Minimum premium for an Iron Fly trade ($):",default=template.minPremium, float_allowed=True, validate=EmptyInputValidator()).execute())
	try:
		template.maxOpenTrades = int(inquirer.number(message="Maximum number of parallel open positions:", default=template.maxOpenTrades, min_allowed=1).execute())
	except ValueError:
		template.maxOpenTrades = 0

def ensureInitialConfig() -> bool:
	configPath = os.path.expanduser(configFileName)
	if os.path.exists(configPath):
		return True
	print("No config.yaml found. Let's answer some questions and generate the required configuration file.")
	configOK = False
	try:
		confAPIKey = inquirer.text(message="What's your OptraBot API Key:").execute()
		confInstanceId = inquirer.text(message="Give your OptraBot Instance an Id:", default="optrabot").execute()
		confWebPort = inquirer.number(message="Port number on which the OptraBot UI will be accessible:", default=8080).execute()
		confTWSHost = inquirer.text(message="Hostname of your TWS/IB Gateway machine:",default="127.0.0.1").execute()
		confTWSPort = inquirer.number(message="Port number of your TWS/IB Gateway:",default=7496, validate=NumberValidator()).execute()
		confTWSClientID = inquirer.number(message="Client ID to be used for TWS/IB Gateway connection:",default=21, validate=NumberValidator()).execute()
		confTWSMarketData = inquirer.select(
			message="Select a market data type:",
			choices=[
	            "Live",
	            "Delayed",
	            #Choice(value=None, name="Exit"),
	        ],
	        default="Live",
		).execute()

		templatesDict = {}
		addTemplate = True
		templCount = 0
		while addTemplate:
			templCount += 1
			if templCount == 1:
				templateDefault = PutSpread('0DTEMagickTrend10')
				templateDefault.strategy = 'Magick Trend 10'
				templateDefault._trigger = TemplateTrigger({'type': 'external', 'value': '0DTEMagickTrend10', 'excludetimefrom': '11:30 EST', 'excludetimeto': '12:00 EST'})
				templateDefault.adjustmentStep = 0.05
				short_strike_data = ShortStrikeData()
				short_strike_data.offset = -5
				templateDefault.setShortStikeData(short_strike_data)
				long_strike_data = LongStrikeData()
				long_strike_data.width = 70
				templateDefault.setLongStikeData(long_strike_data)
				templateDefault.account = ''
				templateDefault.amount = 1
				templateDefault.takeProfit = 50
				templateDefault.stopLoss = 200
				templateDefault.maxOpenTrades = None
				templateDefault.set_enabled(True)
				# templateDefault.minPremium = 14
			elif templCount == 2:
				templateDefault = PutSpread('0DTEMagickTrend30')
				templateDefault.strategy = 'Magick Trend 30'
				templateDefault._trigger = TemplateTrigger({'type': 'external', 'value': '0DTEMagickTrend30', 'timefrom': '11:00 EST', 'timeto': '15:00 EST'})
				templateDefault.adjustmentStep = 0.05
				short_strike_data = ShortStrikeData()
				short_strike_data.offset = -5
				templateDefault.setShortStikeData(short_strike_data)
				long_strike_data = LongStrikeData()
				long_strike_data.width = 70
				templateDefault.setLongStikeData(long_strike_data)
				templateDefault.account = ''
				templateDefault.amount = 1
				templateDefault.stopLoss = 200
				templateDefault.maxOpenTrades = None
				templateDefault.set_enabled(True)
			# elif templCount == 2:
			# 	templateDefault = IronFly('0DTELunchIF')
			# 	templateDefault.strategy = '0DTE Lunch Iron Fly'
			# 	templateDefault._trigger = TemplateTrigger({'type': 'external', 'value': '0DTELunchIF'})
			# 	templateDefault.adjustmentStep = 0.1
			# 	templateDefault.wing = 70
			# 	templateDefault.account = ''
			# 	templateDefault.amount = 1
			# 	templateDefault.takeProfit = 10
			# 	templateDefault.stopLoss = 20
			# 	templateDefault.minPremium = 0
			# elif templCount == 3:
			# 	templateDefault = IronFly('0DTEFOMCFly')
			# 	templateDefault.strategy = '0DTE FOMC Fly'
			# 	templateDefault._trigger = TemplateTrigger({'type': 'external', 'value': '0DTEFOMCFly'})
			# 	templateDefault.adjustmentStep = 0.1
			# 	templateDefault.wing = 100
			# 	templateDefault.account = ''
			# 	templateDefault.amount = 1
			# 	templateDefault.takeProfit = 10
			# 	templateDefault.stopLoss = 100
			# 	templateDefault.minPremium = 0
			else:
				break
			addTemplate = inquirer.confirm(message="Add a trade template '" +  templateDefault.name + "'", default=True).execute()
			if not addTemplate:
				break
			captureTemplateData(templateDefault)
			templatesDict.update({templateDefault.name:templateDefault.toDict()})

		# confTradingAccount = inquirer.text(message="Account number to be used for trading:",default="").execute()
		# confTradingContracts = inquirer.number(message="Number of IronFly contracts to be traded:", min_allowed=1).execute()
		# confTradingPriceIncement = inquirer.number(message="Increment for limit price adjustments ($):",default=0.1, float_allowed=True, validate=EmptyInputValidator()).execute()
		# confTradingMinimumPremium = inquirer.number(message="Minimum premium for an Iron Fly trade ($):",default=14, float_allowed=True, validate=EmptyInputValidator()).execute()
		# confTradingTakeProfit = inquirer.number(message="Percentage of captured premium as profit target (%):", default=8, min_allowed=1, max_allowed=100).execute()
		# confTradingStopLoss = inquirer.number(message="Percentage of captured premium as stop loss level (%):", default=16, min_allowed=1).execute()
		# confStopLossAdjust = inquirer.confirm(message="Automatic stop loss adjustment?",default=False).execute()
		# if confStopLossAdjust:
		# 	confSLATrigger = inquirer.number(message="Percentage of profit that triggers the stop loss adjustment (%):", default=10, min_allowed=1, validate=EmptyInputValidator()).execute()
		# 	confSLAStop = inquirer.number(message="Adjusted stop 'postive=below entry; negative=above entry' (%):", default=0, validate=EmptyInputValidator()).execute()
		# 	confSLAOffset = inquirer.number(message="Offset for the adjusted stop 'negtive=away from market; positive=closer to market' ($):", default=-0.2, float_allowed=True,validate=EmptyInputValidator()).execute()
		confirm = inquirer.confirm(message="Confirm?", default=True).execute()
	except KeyboardInterrupt as exc:
		print('Configuration has been aborted!')
		return False

	if not confirm:
		print("Configuration assistant abortet!")
		return

	data = dict(general=dict(port=int(confWebPort), apikey=confAPIKey, instanceid=confInstanceId, hub=defaultHubHost),
				tws=dict(host=confTWSHost, port=int(confTWSPort), clientid=int(confTWSClientID), marketdata=confTWSMarketData),templates=templatesDict)
	#if confStopLossAdjust:
	#	twsItems = dict(data["tws"].items())
	#	twsItems["adjuststop"] = dict(trigger=int(confSLATrigger), stop=int(confSLAStop), offset=float(confSLAOffset))
	#	data["tws"] = twsItems
		  
	configYAML = yaml=YAML()
	try:
		with open(configFileName, 'w') as configFile:
			configYAML.dump(data, configFile )
		print("Config file " + configFileName + " has been generated based on your answers.\nYou may modify the configuration file manually if required.")
		configOK = True
	except IOError as exc:
		print("Error generating the config file:", configFileName)
		print("I/O error({0}): {1}".format(exc.errno, exc.strerror))
		return
	
	return configOK