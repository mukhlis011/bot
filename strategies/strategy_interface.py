# strategies/strategy_interface.py
from abc import ABC, abstractmethod

class ArbitrageStrategy(ABC):
    @abstractmethod
    def find_opportunities(self, prices):
        """Cari peluang arbitrase"""
        pass