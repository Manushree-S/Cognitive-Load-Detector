from django.db import models
from django.contrib.auth.models import User

class TestResult(models.Model):
    # User types for adaptive system
    USER_TYPES = [
        ('normal', 'Normal'),
        ('adhd', 'ADHD'),
        ('dyslexia', 'Dyslexia'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # User category
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='normal'
    )

    # Quiz metrics
    time_taken = models.FloatField()
    errors = models.IntegerField()
    load_level = models.CharField(max_length=20)

    # 🔥 NEW FIELDS (for behavioral tracking)
    cursor_movements = models.IntegerField(default=0)
    idle_time = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username} ({self.user_type}) - {self.load_level}"