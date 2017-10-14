import os

from django.core import management
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gtcollab.settings")
application = get_wsgi_application()

management.call_command('load_courses')