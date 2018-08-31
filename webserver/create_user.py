import uuid
import pytz
from datetime import datetime

import os
import sys
import django

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webserver.settings")
django.setup()


from webserver.models import User  # noqa


api_key = ''.join(str(uuid.uuid4()).split('-'))
user = User.objects.create(api_key=api_key,
                           date_created=datetime.now(tz=pytz.utc))
user.save()

print("User with {} key created".format(api_key))
