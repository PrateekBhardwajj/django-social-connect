from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='dashboard/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', auth_views.LoginView.as_view(template_name='dashboard/login.html')),

    # Facebook Integration
    path('facebook/callback/', views.facebook_callback, name='facebook_callback'),
    path('facebook/posts/', views.facebook_posts, name='facebook_posts'),

    # AJAX Facebook Like/Comment
    path('facebook/like/<str:post_id>/ajax/', views.facebook_like_ajax, name='facebook_like_ajax'),
    path('facebook/comment/<str:post_id>/ajax/', views.facebook_comment_ajax, name='facebook_comment_ajax'),

    # Instagram Integration
    path('instagram/posts/', views.instagram_posts, name='instagram_posts'),
    path('instagram/comment/<str:post_id>/', views.instagram_comment_ajax, name='instagram_comment_ajax'),
]
