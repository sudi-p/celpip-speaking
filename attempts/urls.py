from django.urls import path
from . import views

urlpatterns = [
    # Session endpoints
    path("sessions", views.sessions_list_create),
    path("sessions/latest", views.latest_session),
    path("sessions/<int:pk>", views.session_detail),

    # Attempt endpoints
    path("transcribe", views.transcribe),
    path("generate-question", views.generate_question),
    path("evaluate", views.evaluate),
    path("submit", views.submit),
    path("attempts", views.list_attempts),
    path("attempts/<int:pk>", views.attempt_detail),
    path("attempts/<int:pk>/reevaluate", views.reevaluate_attempt),

    # Activity log
    path("logs", views.activity_logs),
]
