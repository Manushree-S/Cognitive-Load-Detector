from django.urls import path
from . import views

urlpatterns = [

    # Landing Page
    path(
        '',
        views.landing_page,
        name='landing_page'
    ),

    # Student Details Page
    path(
        'student/',
        views.student_details,
        name='student_details'
    ),

    # Test Page
    path(
        'test/',
        views.test_page,
        name='test'
    ),

    # Result Page
    path(
        'result/',
        views.result_page,
        name='result'
    ),

    # Dashboard
    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

]
