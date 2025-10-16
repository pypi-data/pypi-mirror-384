from sqlalchemy import TIMESTAMP, Boolean, Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class Account(Base):
	__tablename__ = "accounts"

	id = Column(String, primary_key=True)
	name = Column(String)
	broker = Column(String)
	pdt = Column(Boolean, default=False)

class Trade(Base):
	__tablename__ = "trades"

	id = Column(Integer, primary_key=True, autoincrement=True)
	account = Column(String, ForeignKey('accounts.id'))
	symbol = Column(String)
	strategy = Column(String)
	status = Column(String, default='NEW') # Status: OPEN or CLOSED
	realizedPNL = Column(Float, default=0.0)
	transactions = relationship("Transaction", back_populates="trade")

	def __str__(self) -> str:
		""" Returns a string representation of the Trade
		"""
		tradeString = ('ID: ' + str(self.id) + ' Account: ' + self.account + ' Strategy: ' + self.strategy + ' Symbol: ' + str(self.status) + ' RealizedPNL: ' + str(self.realizedPNL))
		return tradeString

class Transaction(Base):
	__tablename__ = 'transactions'

	tradeid = Column(Integer, ForeignKey('trades.id'), primary_key=True)
	id = Column(Integer, primary_key=True)
	type = Column(String) # SELL,BUY,EXP
	sectype = Column(String) # C, P, S
	timestamp = Column(TIMESTAMP, ) # Timestamp of transaction in UTC
	expiration = Column(Date)
	strike = Column(Float)
	contracts = Column(Integer, default=1)
	price = Column(Float, default=0)
	fee = Column(Float, default=0)
	commission = Column(Float, default=0)
	notes = Column(String, default='')

	trade = relationship("Trade", back_populates="transactions")

