from django.contrib import admin
from .models import Attempt, Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "task_id", "created_at")
    list_filter = ("task_id",)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "task_id", "score", "session")
    list_filter = ("task_id", "session")
