import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirenix_prj.settings')
django.setup()

from assessments.mcq_generator import generate_mcq_for_domain

print("Generating MCQ for Python...")
q = generate_mcq_for_domain("Python")
print(q)

