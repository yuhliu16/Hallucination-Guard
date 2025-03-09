from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import signup_view

urlpatterns = [
    path('', views.airesponse_list, name='airesponse_list'),
    path('airesponse/<int:pk>/', views.airesponse_detail, name='airesponse_detail'),
    path('airesponse/<int:pk>/review/', views.submit_review, name='submit_review'),
    path('reviews/', views.review_list, name='review_list'),
    path('debates/', views.debate_list, name='debate_list'),
    path('review/<int:review_id>/', views.review_detail, name='review_detail'),
    path('debate/<int:debate_id>/', views.debate_detail, name='debate_detail'),
    path('signup/', signup_view, name='signup'),
    # LOGIN
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    # LOGOUT
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
