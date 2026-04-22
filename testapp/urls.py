from django.urls import path
from . import views

urlpatterns = [
    # 🧠 Step 1: Select user type (entry point)
    path('', views.select_user_type, name='user_type'),

    # 🧠 Step 2: Quiz page
    path('test/', views.test_page, name='test'),

    # 📊 Step 3: Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]