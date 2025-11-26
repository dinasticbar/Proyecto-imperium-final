from django.db import models
from django.utils import timezone
import secrets
from datetime import timedelta


class Camera(models.Model):
    name = models.CharField(max_length=150)
    rtsp_url = models.URLField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SecurityCode(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="codes")
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    @classmethod
    def create_for_camera(cls, camera, lifetime_seconds=300):
        token = secrets.token_urlsafe(24)
        now = timezone.now()
        expires = now + timedelta(seconds=lifetime_seconds)
        return cls.objects.create(camera=camera, token=token, expires_at=expires)

    def is_valid(self):
        return (not self.used) and (self.expires_at > timezone.now())

    def mark_used(self):
        self.used = True
        self.save(update_fields=["used"])


class Capture(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="captures")
    image = models.ImageField(upload_to="captures/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Captura {self.id} - {self.camera.name} ({self.created_at:%Y-%m-%d %H:%M:%S})"
