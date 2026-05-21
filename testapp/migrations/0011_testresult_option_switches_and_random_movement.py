from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("testapp", "0010_testresult_accuracy_testresult_attention_score_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="testresult",
            name="option_switch_rate",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="testresult",
            name="option_switches",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="testresult",
            name="random_movement_rate",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="testresult",
            name="random_movements",
            field=models.IntegerField(default=0),
        ),
    ]
