
from django.db import models
from django.contrib.auth.models import User


class TestResult(models.Model):

    LOAD_CHOICES = [

        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    USER_TYPES = [

        ('normal', 'Normal'),
        ('adhd', 'ADHD'),
        ('dyslexia', 'Dyslexia'),
    ]

    # ==========================================
    # USER
    # ==========================================

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # ==========================================
    # BASIC TEST DATA
    # ==========================================

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='normal'
    )

    subject = models.CharField(
        max_length=50,
        default='3-5'
    )

    load_level = models.CharField(
        max_length=10,
        choices=LOAD_CHOICES
    )

    # ==========================================
    # PERFORMANCE
    # ==========================================

    accuracy = models.FloatField(
        default=0
    )

    attention_score = models.FloatField(
        default=0
    )

    errors = models.IntegerField(
        default=0
    )

    time_taken = models.FloatField(
        default=0
    )

    # ==========================================
    # BEHAVIORAL ANALYTICS
    # ==========================================

    cursor_movements = models.IntegerField(
        default=0
    )

    random_movements = models.IntegerField(
        default=0
    )

    option_switches = models.IntegerField(
        default=0
    )

    idle_time = models.FloatField(
        default=0
    )

    movement_rate = models.FloatField(
        default=0
    )

    random_movement_rate = models.FloatField(
        default=0
    )

    option_switch_rate = models.FloatField(
        default=0
    )

    idle_rate = models.FloatField(
        default=0
    )

    # ==========================================
    # TIMESTAMP
    # ==========================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==========================================
    # STRING
    # ==========================================

    def __str__(self):

        return (

            f"{self.user.username} - "
            f"{self.load_level}"
        )


class StudentFeedback(models.Model):

    EMOJI_CHOICES = [
        ("very_happy", "Very Happy"),
        ("happy", "Happy"),
        ("okay", "Okay"),
        ("confused", "Confused"),
        ("tired", "Tired"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    student_name = models.CharField(
        max_length=100
    )

    grade_level = models.CharField(
        max_length=20
    )

    emoji = models.CharField(
        max_length=30,
        choices=EMOJI_CHOICES
    )

    comment = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.student_name} - {self.grade_level} - {self.emoji}"
