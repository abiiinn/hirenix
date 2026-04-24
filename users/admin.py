from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CandidateProfile, CompanyProfile

admin.site.register(User, UserAdmin)
admin.site.register(CandidateProfile)
admin.site.register(CompanyProfile)
