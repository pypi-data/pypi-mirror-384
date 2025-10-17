"""
Core auto-discovery and navigation building for dbbasic-admin
"""

import importlib
import pkgutil
from typing import List, Dict, Any
from functools import lru_cache
import time

# Core admin navigation (always present)
CORE_NAV = [
    {'icon': '📊', 'label': 'Dashboard', 'href': '/admin/', 'order': 0},
    {'icon': '💻', 'label': 'Code', 'href': '/admin/code', 'order': 10},
    {'icon': '🗄️', 'label': 'Database', 'href': '/admin/database', 'order': 11},
]

# System navigation (always at bottom)
SYSTEM_NAV = [
    {'icon': '⏰', 'label': 'Jobs', 'href': '/admin/jobs', 'order': 90},
    {'icon': '📋', 'label': 'Logs', 'href': '/admin/logs', 'order': 91},
    {'icon': '🚀', 'label': 'Deploy', 'href': '/admin/deploy', 'order': 92},
    {'icon': '💾', 'label': 'Backup', 'href': '/admin/backup', 'order': 93},
    {'icon': '⚙️', 'label': 'Settings', 'href': '/admin/settings', 'order': 99},
]


@lru_cache(maxsize=1)
def discover_modules() -> List[Dict[str, Any]]:
    """
    Auto-discover admin modules from installed packages.

    Scans all installed packages for those starting with 'dbbasic_'
    and looks for an 'admin.py' module with 'ADMIN_CONFIG' export.

    Returns:
        List of dicts with 'name' and 'config' keys

    Example:
        [
            {
                'name': 'dbbasic_blog',
                'config': [
                    {'icon': '📝', 'label': 'Posts', 'href': '/admin/posts', 'order': 20}
                ]
            }
        ]
    """
    modules = []

    for pkg in pkgutil.iter_modules():
        # Only scan dbbasic_* packages, excluding ourselves
        if pkg.name.startswith('dbbasic_') and pkg.name != 'dbbasic_admin':
            try:
                # Try to import the module's admin.py
                admin_mod = importlib.import_module(f'{pkg.name}.admin')

                # Check if it exports ADMIN_CONFIG
                if hasattr(admin_mod, 'ADMIN_CONFIG'):
                    config = admin_mod.ADMIN_CONFIG

                    # Validate config is a list
                    if isinstance(config, list):
                        modules.append({
                            'name': pkg.name,
                            'config': config,
                            'discovered_at': time.time()
                        })

            except (ImportError, AttributeError):
                # Module doesn't have admin interface, skip it
                continue
            except Exception as e:
                # Log error but don't break discovery
                print(f"Warning: Error discovering {pkg.name}: {e}")
                continue

    return modules


def build_nav() -> List[Dict[str, Any]]:
    """
    Build complete navigation from core + discovered modules + system.

    Returns:
        Sorted list of nav items with all required fields

    Example:
        [
            {'icon': '📊', 'label': 'Dashboard', 'href': '/admin/', 'order': 0},
            {'icon': '📝', 'label': 'Posts', 'href': '/admin/posts', 'order': 20},
            {'icon': '⚙️', 'label': 'Settings', 'href': '/admin/settings', 'order': 99},
        ]
    """
    nav_items = []

    # Add core navigation
    nav_items.extend(CORE_NAV)

    # Add discovered module navigation
    for module in discover_modules():
        nav_items.extend(module['config'])

    # Add system navigation
    nav_items.extend(SYSTEM_NAV)

    # Sort by order (default to 50 if not specified)
    nav_items.sort(key=lambda x: x.get('order', 50))

    return nav_items


def clear_cache():
    """
    Clear the discovery cache.

    Call this after installing or uninstalling a module to force
    re-discovery on the next build_nav() call.
    """
    discover_modules.cache_clear()


def get_module_info(module_name: str) -> Dict[str, Any]:
    """
    Get information about a specific admin module.

    Args:
        module_name: Name of the module (e.g., 'dbbasic_blog')

    Returns:
        Module info dict or None if not found
    """
    for module in discover_modules():
        if module['name'] == module_name:
            return module
    return None
