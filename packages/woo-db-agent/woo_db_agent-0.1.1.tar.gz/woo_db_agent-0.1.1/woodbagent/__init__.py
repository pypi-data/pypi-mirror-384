"""
WooCommerce Gemini Query Generator
A tool to generate and execute SQL queries for WooCommerce using Google Gemini API
"""

__version__ = "0.1.0"
__author__ = "iasamanrhzai"
__email__ = "iasaman.rhzai@gmail.com"

from .core import WooCommerceQueryGenerator
from .executor import execute_query, display_results

__all__ = [
    'WooCommerceQueryGenerator',
    'execute_query',
    'display_results'
]
