"""
WSGI config for tata_evaluation project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tata_evaluation.settings')

application = get_wsgi_application()
