from django.db import migrations


def forward(apps, schema_editor):
    Session = apps.get_model("attempts", "Session")
    Attempt = apps.get_model("attempts", "Attempt")

    orphans = Attempt.objects.filter(session__isnull=True).order_by("created_at")
    if not orphans.exists():
        return

    session = Session.objects.create(
        task_id=1,
        task_name="Giving Advice",
        name="Giving Advice — Session 1",
        question="",
    )
    # Back-date session to the earliest attempt so history looks correct
    earliest = orphans.first().created_at
    Session.objects.filter(pk=session.pk).update(created_at=earliest)

    orphans.update(session=session)


def reverse(apps, schema_editor):
    Session = apps.get_model("attempts", "Session")
    Attempt = apps.get_model("attempts", "Attempt")
    Attempt.objects.all().update(session=None)
    Session.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("attempts", "0004_session_model_and_fk"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
