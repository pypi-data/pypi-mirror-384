from dataclasses import dataclass
from typing import Dict
import pytz

@dataclass
class SymbolInfo:
	"""
	The Symbol Info class is a data class that holds the information of a symbol.
	Broker Connectors can add their specific information to this class.
	"""
	symbol: str
	strike_interval: float
	quote_step: float
	option_symbol_suffix: str
	timezone: pytz.tzinfo

	def __init__(self, symbol: str, option_symbol_suffix: str, strike_interval: float, quote_step: float, multiplier: float, exchange: str, trading_class: str, timezone: str) -> None:
		self.symbol = symbol
		self.strike_interval = strike_interval
		self.quote_step = quote_step
		self.multiplier = multiplier
		self.option_symbol_suffix = option_symbol_suffix
		self.exchange = exchange
		self.trading_class = trading_class
		self.timezone = pytz.timezone(timezone)
		pass

def initialize_symbol_infos() -> Dict[str, SymbolInfo]:
	symbol_info_dict = {
		"SPX" : SymbolInfo("SPX", "W", 5, 0.05, 100, "SMART", "SPXW", "US/Eastern"),
		"VIX" : SymbolInfo("VIX", "W", 1, 0.05, 1000, "SMART", "VIXW", "US/Eastern"),
	}
	return symbol_info_dict

symbol_infos = initialize_symbol_infos()