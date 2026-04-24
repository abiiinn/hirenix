import django
from django.conf import settings
from django.template import Template, Context

settings.configure(TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates'}])
django.setup()

tpl = """
{% if app.voice_fluency_score > 0 or app.status == 'LEVEL3_PENDING' or
      app.status == 'LEVEL2_FAILED' or app.status == 'HIRED' or
      app.status == 'REJECTED' %}
HELLO
{% else %}
WORLD
{% endif %}
"""

try:
    print(Template(tpl).render(Context({'app': {}})))
except Exception as e:
    print("ERROR:", e)
