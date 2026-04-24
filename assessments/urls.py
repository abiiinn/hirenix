from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('level1/<int:app_id>/', views.take_mcq_test, name='mcq_test'),
    path('level1/<int:app_id>/submit/', views.submit_mcq_test, name='mcq_submit'),
    path('level2/<int:app_id>/', views.take_voice_test, name='voice_test'),
    path('level2/<int:app_id>/submit/', views.submit_voice_test, name='voice_submit'),
    path('level2/<int:app_id>/detail/', views.voice_detail, name='voice_detail'),
]
