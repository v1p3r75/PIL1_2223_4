from django.urls import path
from . import views

urlpatterns = [
    path("admin", views.adminDashboard, name="admin-dashboard"),
    path("", views.adminDashboard, name="student-dashboard"),
    path("admin/dash", views.adminDash, name="admin-dash"),
    path("admin/teachers", views.adminTeachers, name="admin-teachers"),
    path("admin/subjects", views.adminSubjects, name="admin-subjects"),
    path("admin/levels", views.adminLevels, name="admin-levels"),
    path("account", views.userAccount, name="user-account"),
]