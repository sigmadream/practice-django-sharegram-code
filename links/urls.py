from django.urls import path
from . import views

app_name = 'links'

urlpatterns = [
    path('', views.link_list, name='link_list'),
    path('<int:pk>/', views.link_detail, name='link_detail'),
    path('new/', views.link_create, name='link_create'),
    path('<int:pk>/delete/', views.link_delete, name='link_delete'),
]