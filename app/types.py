from dataclasses import dataclass
from typing import List

@dataclass
class CandleData:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int
    

class FyersHistoryResponse:
    s: str
    candles: List[List[CandleData]]