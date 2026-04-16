from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("attempts.urls")),

    # Frontend HTML pages — served through Django's template engine
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
    path("index.html", TemplateView.as_view(template_name="index.html")),
    path("record.html", TemplateView.as_view(template_name="record.html")),
    path("history.html", TemplateView.as_view(template_name="history.html")),
    path("detail.html", TemplateView.as_view(template_name="detail.html")),
    path("logs.html", TemplateView.as_view(template_name="logs.html")),

    # Frontend static assets (CSS, JS) — must come after HTML routes
    re_path(r"^(?P<path>.*)$", serve, {"document_root": settings.FRONTEND_DIR}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
