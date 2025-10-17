"""
API endpoint for navigation items.

Route: /admin/api/nav
Returns: JSON array of navigation items
"""

import json
from dbbasic_admin.admin import build_nav


def GET(request):
    """
    Return navigation items as JSON.

    This endpoint is called by the admin UI to dynamically
    build the sidebar navigation from core + discovered modules.

    Returns:
        JSON response with nav items array
    """
    nav_items = build_nav()

    # Return as JSON
    return {
        'status': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Cache-Control': 'max-age=60'  # Cache for 60 seconds
        },
        'body': json.dumps(nav_items, indent=2)
    }
