from django.urls import path
from . import views

urlpatterns = [
    path('api/weights/', views.portfolio_weights, name='portfolio_weights'),
    path('api/values/', views.portfolio_values, name='portfolio_values'),
    path('api/test/data/', views.test_data, name='test_data'),
    path('api/test/ports/', views.test_ports, name='test_ports'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='home'),
]
