from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attempts", "0006_session_response_summary"),
    ]

    operations = [
        migrations.AddField(
            model_name="attempt",
            name="user_name",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
