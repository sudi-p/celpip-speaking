from django.db import models


class Session(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    task_id = models.IntegerField()
    task_name = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    question = models.TextField(blank=True, default="")
    response_summary = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Attempt(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    task_id = models.IntegerField()
    task_name = models.CharField(max_length=100)
    transcript = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True)
    evaluation_json = models.JSONField(null=True, blank=True)
    duration_sec = models.IntegerField(null=True, blank=True)
    question = models.TextField(blank=True, default="")
    user_name = models.CharField(max_length=100, blank=True, default="")
    audio_file = models.FileField(upload_to="audio/", blank=True)
    session = models.ForeignKey(
        Session, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="attempts",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task {self.task_id} — {self.score or '?'}/12 — {self.created_at:%Y-%m-%d %H:%M}"
