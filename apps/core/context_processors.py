from django.conf import settings


def enterprise_theme(request):
    """
    Context processor injecting the Enterprise Hybrid Design System (V1.0)
    design tokens, product identity, and role-adaptive navigation.
    """
    is_manager = False
    if hasattr(request, 'user') and request.user.is_authenticated:
        is_manager = getattr(request.user, 'is_manager', False)

    nav_items = [
        {'id': 'overview', 'name': 'Overview', 'url': '/', 'icon': 'dashboard', 'manager_only': False},
        {'id': 'inventory', 'name': 'Inventory Intelligence', 'url': '/inventory/', 'icon': 'inventory_2', 'manager_only': False},
        {'id': 'forecasting', 'name': 'Demand Forecasting', 'url': '/forecasting/', 'icon': 'trending_up', 'manager_only': True},
        {'id': 'procurement', 'name': 'Procurement', 'url': '/procurement/', 'icon': 'shopping_cart', 'manager_only': False},
        {'id': 'suppliers', 'name': 'Supplier Management', 'url': '/suppliers/', 'icon': 'business', 'manager_only': False},
        {'id': 'logistics', 'name': 'Logistics Operations', 'url': '/logistics/', 'icon': 'local_shipping', 'manager_only': False},
        {'id': 'finance', 'name': 'Financial Intelligence', 'url': '/finance/', 'icon': 'account_balance', 'manager_only': True},
        {'id': 'intelligence', 'name': 'AI Operations', 'url': '/intelligence/', 'icon': 'psychology', 'manager_only': True},
        {'id': 'automation', 'name': 'Automation Control Centre', 'url': '/automation/', 'icon': 'smart_toy', 'manager_only': True},
        {'id': 'audit', 'name': 'Audit & Security', 'url': '/audit/', 'icon': 'shield', 'manager_only': True},
        {'id': 'reporting', 'name': 'Reporting Hub', 'url': '/reporting/', 'icon': 'description', 'manager_only': True},
        {'id': 'system_health', 'name': 'System Health', 'url': '/system-health/', 'icon': 'monitor_heart', 'manager_only': True},
    ]

    # Filter navigation items based on user authority
    filtered_nav = [item for item in nav_items if not item['manager_only'] or is_manager]

    return {
        'BRAND': {
            'NAME': 'SCALE.Core',
            'FULL_NAME': 'Supply Chain Analytics & Logistics Engine',
            'AUTHOR': 'Hemanth Kumar H A',
            'TAGLINE': 'One Operator. One Intelligent System. Complete Supply Chain Visibility.',
            'PHILOSOPHY': 'One human supervises. SCALE.Core operates.',
            'VERSION': '1.0.0-rc1',
        },
        'THEME': {
            'SIDEBAR_BG': '#18212B',
            'SIDEBAR_HOVER': '#222D39',
            'WORKSPACE_BG': '#F4F5F2',
            'SURFACE_PRIMARY': '#FFFFFF',
            'SURFACE_SECONDARY': '#F8F9F7',
            'BORDER_PRIMARY': '#E3E7E3',
            'BRAND_INDIGO': '#4F5FC7',
            'BRAND_INDIGO_HOVER': '#414FAF',
            'BRAND_INDIGO_LIGHT': '#EEF0FC',
            'TEXT_PRIMARY': '#202A33',
            'TEXT_SECONDARY': '#68737D',
            'CRITICAL_BG': '#FFF0F0',
            'CRITICAL_TEXT': '#C04444',
            'WARNING_BG': '#FFF6E7',
            'WARNING_TEXT': '#A66B18',
            'HEALTHY_BG': '#EDF6EF',
            'HEALTHY_TEXT': '#387B50',
            'INFO_BG': '#EEF2FA',
            'INFO_TEXT': '#4969A5',
        },
        'NAV_ITEMS': filtered_nav,
        'IS_MANAGER': is_manager,
    }
