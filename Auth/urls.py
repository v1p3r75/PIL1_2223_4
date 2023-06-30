from django.urls import path
from . import views

urlpatterns = [
    path("login", views.index, name="login"),
    path("register", views.register, name="register"),
    path("forgot-password", views.forgotPassword, name="forgotPassword"),
    path("reset-password", views.resetPassword, name="resetPassword"),
    path("logout", views.logoutUser, name="logout"),
]