import os
import sys
import django

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webserver.settings")
django.setup()
