#
# pyvider/components/data_sources/__init__.py
#

# pyvider/components/data_sources/__init__.py
"""
Pyvider Data Sources Components
==============================
This package contains all data source components that are automatically discovered
and registered by the Pyvider framework.

Components in this package must use the @register_data_source decorator.
"""

# This file intentionally contains no explicit imports.
# All data source components are discovered automatically by scanning this package.

__all__ = [
    # No explicit exports - autodiscovery handles registration
]

# Metadata for the autodiscovery system
__component_type__ = "data_source"
__autodiscovery__ = True

# 📦🚀🐍
