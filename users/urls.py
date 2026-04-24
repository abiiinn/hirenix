from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('hr/create/', views.create_hr_view, name='create_hr'),
    path('profile/', views.profile_view, name='profile'),
]
