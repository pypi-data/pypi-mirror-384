import argparse
from contextlib import asynccontextmanager
import inspect
import os
import ssl
import certifi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi.staticfiles import StaticFiles
from loguru import logger
import urllib.request, urllib.error
from packaging.version import Version
from InquirerPy import inquirer
import optrabot.config as optrabotcfg
import optrabot.api.template
from .optrabot import OptraBot, get_version
import re
import sys
import uvicorn

ValidLogLevels = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR']

@asynccontextmanager
async def lifespan(app: FastAPI):
	app.optraBot = OptraBot(app)
	await app.optraBot.startup()
	yield
	await app.optraBot.shutdown()

"""fix yelling at me error"""
from functools import wraps
 
from asyncio.proactor_events import _ProactorBasePipeTransport
 
def silence_event_loop_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except RuntimeError as e:
            if str(e) != 'Event loop is closed':
                raise
    return wrapper
 
_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)
"""fix yelling at me error end"""

def	get_frontend_dir() -> StaticFiles:
	current_file_path = os.path.abspath(__file__)
	current_dir = os.path.dirname(current_file_path)
	frontend_dist_dir = os.path.join(current_dir, 'ui')
	environment = os.environ.get('OPTRABOT_ENV', 'PROD')
	if environment == 'DEV':
		logger.info("Running in DEV mode")
		frontend_dist_dir = os.path.join(current_dir, '..', 'frontend', 'webapp')
	return StaticFiles(directory=frontend_dist_dir)

app = FastAPI(lifespan=lifespan)

# CORS-Konfiguration
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Erlaube spezifische Ursprünge
    allow_origins=["*"],  # Erlaube alle Ursprünge
	allow_credentials=True,
    allow_methods=["*"],  # Erlaube alle HTTP-Methoden
    allow_headers=["*"],  # Erlaube alle Header
)

import optrabot.api.template

app.mount("/ui", get_frontend_dir() , name="frontend")

class InterceptHandler(logging.Handler):
	def emit(self, record: logging.LogRecord) -> None:
		if not record.name.startswith('apscheduler'):
			return
			#logger.debug(record.getMessage())
		# Get corresponding Loguru level if it exists.
		level: str | int
		try:
			level = logger.level(record.levelname).name
		except ValueError:
			level = record.levelno

		# Find caller from where originated the logged message.
		frame, depth = inspect.currentframe(), 0
		while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
			frame = frame.f_back
			depth += 1
		level = 'DEBUG' if level == 'INFO' else level
		logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def configureLogging(requestedLogLevel, logScheduler):
	loglevel = 'INFO'
	if requestedLogLevel not in ValidLogLevels and requestedLogLevel != None:
		print(f'Log Level {requestedLogLevel} is not valid!')
	elif requestedLogLevel != None:
		loglevel = requestedLogLevel
	
	logFormat = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> |"
	if loglevel == 'DEBUG':
		logFormat += "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
	logFormat += "<level>{message}</level>"

	log_directory = "logs"
	if not os.path.exists(log_directory):
		os.makedirs(log_directory)
	log_file_name = os.path.join(log_directory, "optrabot_{time:YYYY-MM-DD}.log")

	logger.remove()
	logger.add(sys.stderr, level=loglevel, format = logFormat)
	#logger.add("optrabot.log", level='DEBUG', format = logFormat, rotation="5 MB", retention="10 days")
	logger.add(
        log_file_name,
        level='DEBUG',
        format=logFormat,
        rotation="00:00",  # Täglich um Mitternacht rotieren
        retention="10 days"  # Log-Dateien für 10 Tage aufbewahren
    )

	if logScheduler:
		logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
	#logging.basicConfig(level=logging.ERROR)  # Stummschalten aller Standard-Logger
		apscheduler_logger = logging.getLogger('apscheduler')
		apscheduler_logger.setLevel(loglevel)
	#handler = logging.StreamHandler(sys.stdout)
	#handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
	#apscheduler_logger.addHandler(handler)

def perform_update():
	"""
	Performs the update of the OptraBot package
	"""
	logger.info("Updating OptraBot")
	python_executable = os.path.basename(sys.executable)
	arguments = [python_executable, '-m pip install -U', 'optrabot']
	cmd = ' '.join(arguments)
	logger.debug(f"Executing update command: {cmd}")
	os.system(cmd)

	# OptraBot neustarten
	logger.info("Restarting OptraBot")
	args = []
	args.append(python_executable)
	args.append("-m")
	args.append("optrabot.main")
	skip_first = True
	for arg in sys.argv:
		if skip_first:
			skip_first = False
			continue
		args.append(arg)
	try:
		os.execvp(args[0], args )
		exit(0)
	except Exception as excp:
		logger.error("Problem restarting OptraBot: {}", excp)

def check_for_update():
	"""
	Check for an updated version of the OptraBot package
	"""
	try:
		installed_version = get_version()
		ssl_context = ssl.create_default_context(cafile=certifi.where())
		content = str(urllib.request.urlopen('{}/simple/{}/'.format('https://pypi.org', 'optrabot'), context=ssl_context).read())
		# Versionen mit Vorabversionen Pattern: '([^-<>]+).tar.gz'
		# Versionen ohne Vorabversionen Pattern: r'(\d+\.\d+\.\d+)\.tar\.gz'
		versions = re.findall(r'(\d+\.\d+\.\d+)\.tar\.gz', content) 
		latest_version = versions[-1]
		if Version(latest_version) > Version(installed_version):
			logger.info(f"You're running OptraBot version {installed_version}. New version of OptraBot is available: {latest_version}")
			try:
				if inquirer.confirm(message="Do you want to Update now?", default=True).execute():
					perform_update()
			except KeyboardInterrupt as excp:
				exit(0)

	except Exception as excp:
		logger.error("Problem checking for updates: {}", excp)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--loglevel", help="Log Level", choices=ValidLogLevels)
	parser.add_argument("--logscheduler", help="Log Job Scheduler", action="store_true")
	args = parser.parse_args()
	configureLogging(args.loglevel, args.logscheduler)
	check_for_update()
	if optrabotcfg.ensureInitialConfig()	== True:
		# Get web port from config
		configuration = optrabotcfg.Config("config.yaml")
		if configuration.loaded == False:
			print("Configuration error. Unable to run OptraBot!")
			sys.exit(1)
		webPort: int
		try:
			webPort = configuration.get('general.port')
		except KeyError as keyErr:
			webPort = 8080
		uvicorn_log_level = args.loglevel.lower() if args.loglevel else 'error'
		uvicorn.run("optrabot.main:app", port=int(webPort), host="0.0.0.0", log_level=uvicorn_log_level)
	else:
		print("Configuration error. Unable to run OptraBot!")