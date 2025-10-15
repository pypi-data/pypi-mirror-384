"""

Table Generator Module for Toy API (Backward Compatibility Wrapper)

This module provides backward compatibility by wrapping the unified
dummy_data_generator module. All new code should import from
dummy_data_generator directly.

License: BSD 3-Clause

"""

#
# IMPORTS
#
from toy_api.dummy_data_generator import create_table


#
# PUBLIC
#
__all__ = ['create_table']
