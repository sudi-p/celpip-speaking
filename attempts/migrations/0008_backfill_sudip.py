from django.db import migrations


def backfill_user_name(apps, schema_editor):
    Attempt = apps.get_model("attempts", "Attempt")
    Attempt.objects.filter(user_name="").update(user_name="Sudip")


class Migration(migrations.Migration):

    dependencies = [
        ("attempts", "0007_attempt_user_name"),
    ]

    operations = [
        migrations.RunPython(backfill_user_name, migrations.RunPython.noop),
    ]
