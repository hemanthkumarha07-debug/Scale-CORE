import os

apps = [
    'core', 'accounts', 'audit', 'notifications', 'inventory', 'sales',
    'suppliers', 'procurement', 'logistics', 'forecasting', 'finance',
    'intelligence', 'automation', 'system_health', 'reporting'
]

for app in apps:
    app_dir = os.path.join('apps', app)
    os.makedirs(app_dir, exist_ok=True)
    init_file = os.path.join(app_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass
    
    apps_file = os.path.join(app_dir, 'apps.py')
    class_name = "".join(x.title() for x in app.split("_")) + "Config"
    with open(apps_file, 'w') as f:
        f.write(f'''from django.apps import AppConfig


class {class_name}(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app}'
    verbose_name = '{app.replace("_", " ").title()}'
''')

print("All Django apps scaffolded successfully.")
