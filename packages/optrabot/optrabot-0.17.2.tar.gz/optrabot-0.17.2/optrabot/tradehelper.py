from dataclasses import dataclass
from datetime import date
from loguru import logger
from ib_async import Fill
import re
from optrabot.broker.order import OrderAction
from optrabot import models

@dataclass
class SecurityStatusData:
	securityId: str
	sec_type: str
	strike: float
	expiration: date
	openContracts: int
	fees: float
	unrealPNL: float
	realPNL: float

class TradeHelper:

	@staticmethod
	def getTradeIdFromOrderRef(orderRef: str) -> int:
		""" Extracts the OptraBot Trade Id from the order reference of a fill
		"""
		tradeId = 0
		pattern = r'^OTB\s\((?P<tradeid>[0-9]+)\):[\s0-9A-Za-z]*'
		compiledPattern = re.compile(pattern)
		match = compiledPattern.match(orderRef)
		if match:
			tradeId = int(match.group('tradeid'))
		return tradeId
	
	@staticmethod
	def isTransactionsComplete(trade: models.Trade, adjustExpired: bool = False) -> bool:
		""" Checks if the transactions of the trade with the given Id are complete,
		which means everything liquidated or expired.
		If 'adjustExpired' is True, then missing EXP transactions are created if the contract is expired already
		"""
		securityStatus = {}
		isComplete = True
		for ta in trade.transactions:
			# Dictionary aus Security-String und dem aktuellen Bestand
			# Am Ende müssen die Bestände 0 sein, damit der Trade Complete ist
			security = ta.sectype + str(ta.expiration) + str(ta.strike)
			change = ta.contracts
			if ta.type == 'SELL':
				change = change * -1
			try:
				currentStatus = securityStatus[security]
				securityStatus[security] = currentStatus+change
			except KeyError:
				securityStatus.update({security:change})
		
		for security, status in securityStatus.items():
			if status != 0:
				isComplete = False
		
		return isComplete
	
	@staticmethod
	def updateTrade(trade: models.Trade):
		""" Analyzes the transactions of the given trade and 
			- updates the status of the trade
			- calculates the realized PNL
		"""
		securityStatus = {}
		isComplete = True
		for ta in trade.transactions:
			security = ta.sectype + str(ta.expiration) + str(ta.strike)
			change = ta.contracts
			taFee = ta.fee + ta.commission
			if ta.type == OrderAction.SELL or ta.type == 'EXP':
				change = change * -1
			try:
				statusData = securityStatus[security]
				statusData.openContracts += change
			except KeyError:
				statusData = SecurityStatusData(securityId=security, sec_type=ta.sectype, strike=ta.strike, expiration=ta.expiration, openContracts=change, fees=ta.fee, unrealPNL=0, realPNL = 0)
				securityStatus.update({security:statusData})
			statusData.fees += taFee
			statusData.realPNL -= taFee
			statusData.unrealPNL -= ((ta.price * 100 * change) + taFee)
		
		trade.realizedPNL = 0
		for security, statusData in securityStatus.items():
			if statusData.openContracts == 0:
				# contract transactions are closed
				statusData.realPNL = statusData.unrealPNL
				statusData.unrealPNL = 0
			else:
				# Trade is not complete yet
				isComplete = False
			trade.realizedPNL += statusData.realPNL
		if isComplete == True:
			trade.realizedPNL = round(trade.realizedPNL, 2)
			trade.status = 'CLOSED'
			
				