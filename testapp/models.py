from django.db import models
from django.contrib.auth.models import User


class TestResult(models.Model):

    # 🧠 User types for adaptive system
    USER_TYPES = [
        ('normal', 'Normal'),
        ('adhd', 'ADHD'),
        ('dyslexia', 'Dyslexia'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 👤 User category
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='normal'
    )

    # 📊 Quiz metrics
    time_taken = models.FloatField()
    errors = models.IntegerField()
    load_level = models.CharField(max_length=20)

    # 🖱 Behavioral tracking
    cursor_movements = models.IntegerField(default=0)
    idle_time = models.FloatField(default=0)

    # 🕒 Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.created_at:
            return f"{self.user.username} ({self.user_type}) - {self.load_level} at {self.created_at.strftime('%d-%m-%Y %H:%M')}"
        return f"{self.user.username} ({self.user_type}) - {self.load_level}"