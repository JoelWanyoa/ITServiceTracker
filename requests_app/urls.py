from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'requests_app'

urlpatterns = [
    path('', views.home, name='home'),
    # UI routes at root-level
    path('dashboard/', views.ui_dashboard, name='ui_dashboard'),
    path('login/', views.ui_login, name='login'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='account_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('requests/example/', views.ui_request_detail, name='request_detail_example'),
    path('submit/', views.submit_request, name='submit_request'),
    path('success/', views.submit_success, name='submit_success'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('requests/', views.list_requests, name='list_requests'),
    path('requests/<int:pk>/', views.detail_request, name='detail_request'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]
