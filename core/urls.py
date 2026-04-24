from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/application/<int:app_id>/status/', views.update_application_status, name='update_app_status'),
    path('dashboard/application/<int:app_id>/hr/', views.hr_feedback_view, name='hr_feedback'),
    path('dashboard/user/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
]
