# dbbasic-admin

Auto-discovery admin interface for dbbasic modules.

## Philosophy

> Admin interfaces should auto-generate from installed modules, not require manual configuration.

## Features

- **Auto-discovery** - Installing a dbbasic module automatically adds its admin panels
- **Zero configuration** - Modules just need `admin.py` and `templates/admin/`
- **Filesystem routing** - Admin routes follow file paths (like CGI/PHP)
- **Dynamic sidebar** - Built from core + discovered modules
- **Auto-CRUD** - Generates admin UI for TSV tables
- **Search & filters** - Built-in for all tables

## Installation

```bash
pip install dbbasic-admin
```

## Quick Start

### 1. Install dbbasic-admin

```bash
pip install dbbasic-admin
```

### 2. Access Admin Interface

```
http://localhost:8000/admin/
```

That's it! The admin interface is ready.

### 3. Install Modules with Admin Panels

```bash
pip install dbbasic-blog
```

The "Posts" tab automatically appears in the admin sidebar.

## Creating a Module with Admin

### 1. Export ADMIN_CONFIG

```python
# your_module/admin.py
ADMIN_CONFIG = [
    {
        "icon": "📝",
        "label": "Posts",
        "href": "/admin/posts",
        "order": 20,
        "table": "posts",  # Auto-generates CRUD
    }
]
```

### 2. Create Templates (Optional)

For custom admin pages:

```
your_module/
└── templates/
    └── admin/
        └── posts/
            ├── list.html    # /admin/posts/list
            ├── new.html     # /admin/posts/new
            └── [id].html    # /admin/posts/123
```

### 3. Install Your Module

```bash
pip install your-module
```

Your admin tab appears automatically!

## How It Works

1. **Auto-discovery** - Scans installed `dbbasic_*` packages
2. **Finds ADMIN_CONFIG** - Loads nav items from each module's `admin.py`
3. **Builds sidebar** - Combines core + module nav items
4. **Filesystem routing** - Uses dbbasic-web's routing for admin pages

## Core Admin Pages

- **Dashboard** - System overview, quick actions
- **Code** - File browser and editor
- **Database** - TSV table browser
- **Jobs** - Background job queue
- **Logs** - System and application logs
- **Settings** - Configuration management

## ADMIN_CONFIG Reference

```python
ADMIN_CONFIG = [
    {
        # Required
        'label': 'Posts',           # Display name
        'href': '/admin/posts',     # URL path

        # Optional
        'icon': '📝',              # Emoji or icon class
        'order': 20,               # Sort order (0-99)
        'badge': '3',              # Notification badge
        'table': 'posts',          # Auto-generate CRUD
        'fields': {...},           # Field configuration for CRUD
    }
]
```

## Documentation

Full specification: https://dbbasic.com/admin-spec

## License

MIT

## Links

- PyPI: https://pypi.org/project/dbbasic-admin/
- GitHub: https://github.com/askrobots/dbbasic-admin
- Documentation: https://dbbasic.com/admin-spec
