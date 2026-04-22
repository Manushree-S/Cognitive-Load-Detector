from django.contrib import admin
from .models import TestResult

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'user_type',        # 🔥 NEW
        'time_taken',
        'errors',
        'load_level',
        'cursor_movements', # 🔥 NEW
        'idle_time'         # 🔥 NEW
    )

    list_filter = ('user_type', 'load_level')

    search_fields = ('user__username',)