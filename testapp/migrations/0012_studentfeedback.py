from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("testapp", "0011_testresult_option_switches_and_random_movement"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "student_name",
                    models.CharField(max_length=100),
                ),
                (
                    "grade_level",
                    models.CharField(max_length=20),
                ),
                (
                    "emoji",
                    models.CharField(
                        choices=[
                            ("very_happy", "Very Happy"),
                            ("happy", "Happy"),
                            ("okay", "Okay"),
                            ("confused", "Confused"),
                            ("tired", "Tired"),
                        ],
                        max_length=30,
                    ),
                ),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
