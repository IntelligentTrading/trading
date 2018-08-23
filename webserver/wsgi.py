"""
WSGI config for webserver project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

############################
import sys

root_file = os.path.join(os.path.dirname(__file__), "..", "..")
project_root = os.path.abspath(root_file)
sys.path.insert(1, project_root)
############################

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webserver.settings')

application = get_wsgi_application()
