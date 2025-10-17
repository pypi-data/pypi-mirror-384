"""
dbbasic-admin: Auto-discovery admin interface for dbbasic modules
"""

__version__ = "0.1.0"

from .admin import discover_modules, build_nav, clear_cache

__all__ = ['discover_modules', 'build_nav', 'clear_cache']
