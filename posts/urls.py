# posts/urls.py

from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.home, name='home'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new/', views.post_create, name='post_create'),
    path('post/<int:pk>/update/', views.post_update, name='post_update'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    # path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    # path('post/<int:pk>/like/', views.like_toggle, name='like_toggle'),
    # path('follow/<str:username>/', views.follow_toggle, name='follow_toggle'),
    # path('following/', views.following_feed, name='following_feed'),
    path('load-more/', views.load_more_posts, name='load_more_posts'),
]
