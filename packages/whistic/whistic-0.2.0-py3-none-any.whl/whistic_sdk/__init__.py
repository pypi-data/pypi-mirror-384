"""
Whistic SDK - Python SDK to interface with the Whistic API

This package provides a simple and intuitive way to interact with the Whistic API
for vendor management and third-party risk management operations.
"""

from .whistic import Whistic
from .vendors import Vendors
from .vendorintakeform import VendorIntakeForm

__version__ = "0.2.0"
__author__ = "Phil Massyn"
__email__ = "phil.massyn@icloud.com"
__description__ = "Python SDK to interface with the Whistic API"

__all__ = ["Whistic", "Vendors", "VendorIntakeForm"]