from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class Exchange(ABC):
    @abstractmethod
    def get_base_currency(self) -> str:
        """Dapatkan mata uang dasar exchange (contoh: 'USDT', 'IDR')"""
        pass

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> float:
        """Ambil harga koin dalam mata uang dasar exchange"""
        pass

    @abstractmethod
    def fetch_balance(self) -> Dict[str, Dict[str, float]]:
        """Ambil seluruh saldo dalam format {asset: {'free': float, 'locked': float}}"""
        pass

    @abstractmethod
    def transfer_coin(
        self, 
        symbol: str, 
        amount: float, 
        address: str, 
        tag: Optional[str] = None,
        network: Optional[str] = None
    ) -> bool:
        """Transfer koin ke alamat tertentu"""
        pass