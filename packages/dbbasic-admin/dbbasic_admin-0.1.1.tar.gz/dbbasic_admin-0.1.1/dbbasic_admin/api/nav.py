"""
API endpoint for navigation items.

Route: /admin/api/nav
Returns: JSON array of navigation items
"""

import json
from dbbasic_web.responses import json as json_response
from dbbasic_admin.admin import build_nav


def handle(request):
    """
    Return navigation items as JSON.

    This endpoint is called by the admin UI to dynamically
    build the sidebar navigation from core + discovered modules.

    Returns:
        JSON response with nav items array
    """
    nav_items = build_nav()

    # Return as JSON using dbbasic_web's json response helper
    return json_response(json.dumps(nav_items, indent=2))
