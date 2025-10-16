"""
OpenGeode-Stochastic Python binding
"""
from __future__ import annotations
__all__: list[str] = ['StochasticLibrary', 'hello_world']
class StochasticLibrary:
    @staticmethod
    def initialize() -> None:
        ...
def hello_world() -> bool:
    ...
