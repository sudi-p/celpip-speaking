from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("attempts.urls")),

    # Auth pages
    path("login.html", TemplateView.as_view(template_name="login.html")),
    path("register.html", TemplateView.as_view(template_name="register.html")),

    # Frontend HTML pages — served through Django's template engine
    path("", TemplateView.as_view(template_name="index.html", extra_context={"active_page": "tasks"}), name="index"),
    path("index.html", TemplateView.as_view(template_name="index.html", extra_context={"active_page": "tasks"})),
    path("record.html", TemplateView.as_view(template_name="record.html", extra_context={"active_page": "record"})),
    path("history.html", TemplateView.as_view(template_name="history.html", extra_context={"active_page": "history"})),
    path("detail.html", TemplateView.as_view(template_name="detail.html", extra_context={"active_page": "record"})),
    path("logs.html", TemplateView.as_view(template_name="logs.html", extra_context={"active_page": "logs"})),
    path("write.html", TemplateView.as_view(template_name="write.html", extra_context={"active_page": "write"})),
    path("questions.html", TemplateView.as_view(template_name="questions.html", extra_context={"active_page": "questions"})),
    path("vocab.html", TemplateView.as_view(template_name="vocab.html", extra_context={"active_page": "vocab"})),
    path("settings.html", TemplateView.as_view(template_name="settings.html", extra_context={"active_page": "settings"})),

    # Study notes
    path("notes", TemplateView.as_view(template_name="notes.html", extra_context={"active_page": "notes"})),

    # CELPIP task study guides
    path("speaking-task-1", TemplateView.as_view(template_name="speaking task 1.html", extra_context={"active_page": "task_1"})),
    path("speaking-task-2", TemplateView.as_view(template_name="speaking task 2.html", extra_context={"active_page": "task_2"})),
    path("speaking-task-3", TemplateView.as_view(template_name="speaking task 3.html", extra_context={"active_page": "task_3"})),
    path("speaking-task-4", TemplateView.as_view(template_name="speaking task 4.html", extra_context={"active_page": "task_4"})),
    path("speaking-task-5", TemplateView.as_view(template_name="speaking task 5.html", extra_context={"active_page": "task_5"})),
    path("speaking-task-6", TemplateView.as_view(template_name="speaking task 6.html", extra_context={"active_page": "task_6"})),
    path("speaking-task-7", TemplateView.as_view(template_name="speaking task 7.html", extra_context={"active_page": "task_7"})),
    path("speaking-task-8", TemplateView.as_view(template_name="speaking task 8.html", extra_context={"active_page": "task_8"})),
    path("writing-task-1", TemplateView.as_view(template_name="writing task 1.html", extra_context={"active_page": "writing_task_1"})),
    path("writing-task-2", TemplateView.as_view(template_name="writing task 2.html", extra_context={"active_page": "writing_task_2"})),

    # Media files (audio recordings) — must come BEFORE the catch-all
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),

    # Frontend static assets (CSS, JS) — catch-all, must be last
    re_path(r"^(?P<path>.*)$", serve, {"document_root": settings.FRONTEND_DIR}),
]
