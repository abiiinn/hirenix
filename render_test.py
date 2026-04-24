import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hirenix_prj.settings")
django.setup()
from django.test import RequestFactory
from core.views import dashboard_view
from users.models import User

factory = RequestFactory()
request = factory.get('/dashboard/')
request.user = User.objects.get(username='AVA')

response = dashboard_view(request)
with open('/tmp/dj_rendered.html', 'w') as f:
    f.write(response.content.decode('utf-8'))
print("Done")
