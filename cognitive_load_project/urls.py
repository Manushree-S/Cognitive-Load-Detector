
from django.contrib import admin
from django.urls import path, include

urlpatterns = [

    path(
        'admin/',
        admin.site.urls
    ),

    # LOGIN/REGISTER APP
    path(
        '',
        include('accounts.urls')
    ),

    # QUIZ APP
    path(
        'quiz/',
        include('testapp.urls')
    ),
]

