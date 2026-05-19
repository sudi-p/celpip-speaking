from django.urls import path
from . import views, auth_views

urlpatterns = [
    # Auth endpoints
    path("auth/register", auth_views.register),
    path("auth/login", auth_views.login_view),
    path("auth/logout", auth_views.logout_view),
    path("auth/me", auth_views.me),

    # Companion endpoints
    path("companions", auth_views.companions_list),
    path("companions/request", auth_views.send_companion_request),
    path("companions/<int:pk>/accept", auth_views.accept_companion),
    path("companions/<int:pk>/reject", auth_views.reject_companion),
    path("companions/<int:pk>", auth_views.remove_companion),


    # Session endpoints
    path("sessions", views.sessions_list_create),
    path("sessions/latest", views.latest_session),
    path("sessions/<int:pk>", views.session_detail),

    # Attempt endpoints
    path("transcribe", views.transcribe),
    path("generate-question", views.generate_question),
    path("evaluate", views.evaluate),
    path("submit", views.submit),
    path("submit-writing", views.submit_writing),
    path("attempts", views.list_attempts),
    path("attempts/<int:pk>", views.attempt_detail),
    path("attempts/<int:pk>/reevaluate", views.reevaluate_attempt),

    # Question bank
    path("questions", views.list_questions),

    # Activity log
    path("logs", views.activity_logs),

    # Vocab quiz
    path("vocab-quiz-count", views.vocab_quiz_count),

    # Dashboard
    path("dashboard/metrics", views.dashboard_metrics),
]
