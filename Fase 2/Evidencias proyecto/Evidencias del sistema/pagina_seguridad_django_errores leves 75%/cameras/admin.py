from django.contrib import admin
from .models import Camera, SecurityCode
@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ("id","name","rtsp_url","created_at")
@admin.register(SecurityCode)
class SecurityCodeAdmin(admin.ModelAdmin):
    list_display = ("id","camera","token","created_at","expires_at","used")
    readonly_fields = ("created_at",)