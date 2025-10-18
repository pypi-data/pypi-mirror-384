"""Database browser handler - /admin/database"""
from dbbasic_web.responses import html
from dbbasic_admin.admin import build_nav
from dbbasic_admin.discover import discover_tsv_tables, read_tsv_data, format_file_size


def handle(request):
    """Render database browser"""
    nav_items = build_nav()
    tables = discover_tsv_tables()

    # Get selected table from query params
    selected_table = request.get('query', {}).get('table')
    table_data = []

    if selected_table:
        table_data = read_tsv_data(selected_table, limit=100)

    nav_html = "".join(f'<li><a href="{item["href"]}">{item.get("icon", "")} {item["label"]}</a></li>' for item in nav_items)

    # Build tables grid
    tables_html = ""
    for t in tables:
        tables_html += f'''<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
            <h3>{t["name"]}.tsv</h3>
            <p>{t["rows"]} rows • {format_file_size(t["size"])}</p>
            <p style="font-size: 12px; color: #666;">{", ".join(t["columns"][:5])}{" +"+str(len(t["columns"])-5)+" more" if len(t["columns"]) > 5 else ""}</p>
            <a href="/admin/database?table={t["name"]}" style="color: #0066cc;">View Data</a>
        </div>'''

    # Build data table if selected
    data_html = ""
    if selected_table and table_data:
        columns = list(table_data[0].keys()) if table_data else []
        data_html = f'<h3>Table: {selected_table}</h3><table style="width: 100%; border-collapse: collapse;"><thead><tr>'
        data_html += "".join(f'<th style="border: 1px solid #ddd; padding: 8px; background: #f5f5f5;">{col}</th>' for col in columns)
        data_html += '</tr></thead><tbody>'
        for row in table_data:
            data_html += '<tr>'
            data_html += "".join(f'<td style="border: 1px solid #ddd; padding: 8px;">{row.get(col, "")}</td>' for col in columns)
            data_html += '</tr>'
        data_html += '</tbody></table>'

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Database - Admin</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; height: 100vh; background: #f5f5f5; }}
        .sidebar {{ width: 250px; background: #2c3e50; color: white; padding: 20px; overflow-y: auto; }}
        .sidebar h1 {{ font-size: 24px; margin-bottom: 30px; color: #ecf0f1; }}
        .sidebar ul {{ list-style: none; }}
        .sidebar li {{ margin-bottom: 10px; }}
        .sidebar a {{ color: #ecf0f1; text-decoration: none; display: block; padding: 10px; border-radius: 5px; }}
        .content {{ flex: 1; padding: 40px; overflow-y: auto; }}
        .header {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
    </style>
</head>
<body>
    <div class="sidebar"><h1>Admin</h1><ul>{nav_html}</ul></div>
    <div class="content">
        <div class="header"><h2>🗄️ Database</h2><p>Browse TSV tables</p></div>
        <div class="card"><h3>Tables</h3><div class="grid">{tables_html}</div></div>
        {f'<div class="card">{data_html}</div>' if data_html else ''}
    </div>
</body>
</html>"""

    return html(html_content)
