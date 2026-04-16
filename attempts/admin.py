from django.contrib import admin
from .models import Attempt, Question, Session


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display  = ("id", "task_id", "task_name", "task_type", "source", "created_at", "short_text")
    list_filter   = ("task_id", "task_type", "source")
    search_fields = ("text",)
    ordering      = ("-created_at",)

    @admin.display(description="Question (preview)")
    def short_text(self, obj):
        return obj.text[:100] + ("…" if len(obj.text) > 100 else "")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "task_id", "task_type", "created_at")
    list_filter  = ("task_id", "task_type")


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "task_id", "task_type", "score", "session")
    list_filter  = ("task_id", "task_type", "session")
