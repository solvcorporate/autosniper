"""
Scrapers package for AutoSniper.
This package contains scrapers for different car listing sites.
"""
from .base import BaseScraper
from .autotrader import AutoTraderScraper
from .gumtree import GumtreeScraper

__all__ = ['BaseScraper', 'AutoTraderScraper', 'GumtreeScraper']
