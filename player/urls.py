from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/', include('social_django.urls', namespace='social')),
    path('logout/', views.logout_view, name='logout'),
]