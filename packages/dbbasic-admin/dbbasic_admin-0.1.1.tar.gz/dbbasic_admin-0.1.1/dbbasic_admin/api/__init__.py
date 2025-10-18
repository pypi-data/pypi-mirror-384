"""Admin dashboard handler - /admin/"""
from dbbasic_web.responses import html
from dbbasic_admin.admin import build_nav
from dbbasic_admin.discover import discover_tsv_tables


def handle(request):
    """Render admin dashboard"""
    nav_items = build_nav()
    tables = discover_tsv_tables()

    total_rows = sum(t['rows'] for t in tables)

    # Build nav HTML
    nav_html = "".join(f'<li><a href="{item["href"]}">{item.get("icon", "")} {item["label"]}</a></li>' for item in nav_items)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; height: 100vh; background: #f5f5f5; }}
        .sidebar {{ width: 250px; background: #2c3e50; color: white; padding: 20px; overflow-y: auto; }}
        .sidebar h1 {{ font-size: 24px; margin-bottom: 30px; color: #ecf0f1; }}
        .sidebar ul {{ list-style: none; }}
        .sidebar li {{ margin-bottom: 10px; }}
        .sidebar a {{ color: #ecf0f1; text-decoration: none; display: block; padding: 10px; border-radius: 5px; transition: background 0.2s; }}
        .sidebar a:hover {{ background: #34495e; }}
        .content {{ flex: 1; padding: 40px; overflow-y: auto; }}
        .header {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .header h2 {{ color: #2c3e50; margin-bottom: 10px; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; margin-bottom: 5px; }}
    </style>
</head>
<body>
    <div class="sidebar"><h1>Admin</h1><ul>{nav_html}</ul></div>
    <div class="content">
        <div class="header"><h2>Dashboard</h2><p>Welcome to the admin interface</p></div>
        <div class="card"><h3>Quick Stats</h3><div class="stats">
            <div class="stat-card"><div class="stat-value">{len(tables)}</div><div>Tables</div></div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"><div class="stat-value">{total_rows}</div><div>Total Rows</div></div>
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);"><div class="stat-value">1</div><div>Active Users</div></div>
        </div></div>
        <div class="card"><h3>Tables</h3><ul>
            {"".join(f'<li><a href="/admin/database?table={t["name"]}">{t["name"]}</a> - {t["rows"]} rows</li>' for t in tables)}
        </ul></div>
    </div>
</body>
</html>"""

    return html(html_content)
