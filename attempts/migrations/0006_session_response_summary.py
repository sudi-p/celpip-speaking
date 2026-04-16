from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attempts", "0005_seed_initial_session"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="response_summary",
            field=models.TextField(blank=True, default=""),
        ),
    ]
