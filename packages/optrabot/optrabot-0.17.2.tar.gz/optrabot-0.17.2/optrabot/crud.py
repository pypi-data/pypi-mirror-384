from sqlalchemy.orm import Session
from sqlalchemy import func, select
from . import models, schemas
from loguru import logger

#########################################
#### Acount							 ####
#########################################
def create_account(session: Session, account: schemas.AccountCreate) -> models.Account:
	""" Create a new account in the database
	"""
	db_account = models.Account(id=account.id, name=account.name, broker=account.broker, pdt=account.pdt)
	session.add(db_account)
	session.commit()
	return db_account

def update_account(session: Session, account: models.Account) -> models.Account:
	""" Updates the account in the database
	"""
	session.merge(account)
	session.commit()
	return account

def get_account(session: Session, id: str) -> models.Account:
	""" Fetches the data of the given account based on the ID.
	"""
	statement = select(models.Account).filter_by(id=id)
	account = session.scalars(statement).first()
	return account

def get_accounts(session: Session, skip: int = 0, limit: int = 100):
	stmnt = select(models.Account)
	accounts = session.scalars(stmnt).all()
	
	return accounts

#########################################
#### Trade							 ####
#########################################
def create_trade(session: Session, newTrade: schemas.TradeCreate) -> models.Trade:
	""" Create a new trade in the database
	"""
	dbTrade = models.Trade(account=newTrade.account, symbol=newTrade.symbol, strategy=newTrade.strategy)
	session.add(dbTrade)
	session.commit()
	session.flush()
	logger.debug('Created new trade: {}', dbTrade)
	return dbTrade

def getTrade(session: Session, tradeId: int) -> models.Trade:
	""" Get a trade by it's id
	"""
	return session.get(models.Trade, tradeId)

def update_trade(session: Session, trade: models.Trade) -> models.Trade:
	""" Updates the trade in the database
	"""
	session.merge(trade)
	session.commit()
	session.flush()
	logger.debug('Updated trade: {}', trade)
	return trade

def delete_trade(session: Session, deleteTrade: models.Trade):
	""" Deletes the trade from the database
	"""
	session.delete(deleteTrade)
	session.commit()
	session.flush()
	logger.debug('Deleted trade: {}', deleteTrade)
	return

#########################################
#### Transaction					 ####
#########################################
def getMaxTransactionId(session: Session, tradeId: int) -> int:
	statement = select(func.max(models.Transaction.id)).filter_by(tradeid=tradeId)
	maxId = session.scalar(statement)
	if maxId == None:
		maxId = 0
	return maxId

def getTransactionById(session: Session, tradeId: int, transactionId: int) -> models.Transaction:
	""" Fetches the transaction based on the Trade ID and Transaction ID
	"""
	statement = select(models.Transaction).filter_by(tradeid=tradeId, id=transactionId)
	transaction = session.scalars(statement).first()
	return transaction

def createTransaction(session: Session, newTransaction: schemas.TransactionCreate) -> models.Transaction:
	""" Creates a new transaction record for the given trade
	"""
	dbTransaction = models.Transaction(tradeid=newTransaction.tradeid, id=newTransaction.id,
									type=newTransaction.type,
									sectype=newTransaction.sectype,
									timestamp=newTransaction.timestamp,
									expiration=newTransaction.expiration,
									strike=newTransaction.strike,
									contracts=newTransaction.contracts,
									price=newTransaction.price,
									fee=newTransaction.fee,
									commission=newTransaction.commission,
									notes=newTransaction.notes)
	session.add(dbTransaction)
	session.commit()
	return dbTransaction