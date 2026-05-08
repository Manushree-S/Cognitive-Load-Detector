from django.db import models
from django.contrib.auth.models import User


class TestResult(models.Model):

    # 🧠 User Types
    USER_TYPES = [
        ('normal', 'Normal'),
        ('adhd', 'ADHD'),
        ('dyslexia', 'Dyslexia'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 👤 User Category
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='normal'
    )

    # 📊 Test Metrics
    time_taken = models.FloatField()

    errors = models.IntegerField()

    load_level = models.CharField(max_length=20)

    # 🖱 Raw Tracking
    cursor_movements = models.IntegerField(default=0)

    idle_time = models.FloatField(default=0)

    # 🔥 NEW REALISTIC METRICS
    movement_rate = models.FloatField(default=0)

    idle_rate = models.FloatField(default=0)

    # 🕒 Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.user_type} - "
            f"{self.load_level}"
        )