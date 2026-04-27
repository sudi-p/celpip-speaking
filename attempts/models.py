from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    companion_visibility = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Override PermissionsMixin's M2M fields to avoid clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ['date_joined']

    def __str__(self):
        return self.email


class Question(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    task_id    = models.IntegerField(db_index=True)
    task_name  = models.CharField(max_length=100)
    task_type  = models.CharField(max_length=20, default="speaking")  # speaking | writing
    text       = models.TextField()
    source     = models.CharField(max_length=20, default="ai")        # ai | manual

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task {self.task_id} ({self.task_type}) — {self.text[:70]}"


class Session(models.Model):
    created_at    = models.DateTimeField(auto_now_add=True, db_index=True)
    task_id       = models.IntegerField()
    task_name     = models.CharField(max_length=100)
    task_type     = models.CharField(max_length=20, default="speaking")
    name          = models.CharField(max_length=200)
    question      = models.TextField(blank=True, default="")
    question_ref  = models.ForeignKey(
        Question, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="sessions",
    )
    response_summary = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Attempt(models.Model):
    created_at    = models.DateTimeField(auto_now_add=True, db_index=True)
    task_id       = models.IntegerField()
    task_name     = models.CharField(max_length=100)
    task_type     = models.CharField(max_length=20, default="speaking")
    transcript    = models.TextField(blank=True)
    response_text = models.TextField(blank=True, default="")
    score         = models.IntegerField(null=True, blank=True)
    evaluation_json = models.JSONField(null=True, blank=True)
    duration_sec  = models.IntegerField(null=True, blank=True)
    question      = models.TextField(blank=True, default="")
    user_name     = models.CharField(max_length=100, blank=True, default="")
    audio_file    = models.FileField(upload_to="audio/", blank=True)
    session       = models.ForeignKey(
        Session, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="attempts",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task {self.task_id} — {self.score or '?'}/12 — {self.created_at:%Y-%m-%d %H:%M}"


class CompanionRequest(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sent_companion_requests'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='received_companion_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'pending'), ('accepted', 'accepted'), ('rejected', 'rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = [('from_user', 'to_user')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.email} → {self.to_user.email} ({self.status})"
