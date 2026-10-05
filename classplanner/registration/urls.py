from django.urls import path
from .views import ProfileView, ProfileUpdateView
from . import views

urlpatterns = [
    path('', views.CustomLoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile_update/<int:pk>/', ProfileUpdateView.as_view(), name='profile_update'),
    path('auth/changepasswordgenered/', views.changePasswordGenered, name='changepasswordgenered'),
    path('auth/changepassword/<int:uid>/<str:token>/', views.changePassword, name='changepassword'),
]