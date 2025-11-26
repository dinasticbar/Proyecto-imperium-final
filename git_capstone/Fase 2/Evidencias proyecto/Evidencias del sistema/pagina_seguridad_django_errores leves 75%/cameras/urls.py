from django.urls import path
from . import views

app_name = "cameras"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.registro_view, name="registro"),
    path("home/", views.camera_list, name="camera_list"),
    path("add_camera/", views.add_camera, name="add_camera"),
    path("generate_qr/<int:camera_id>/", views.generate_qr_for_camera, name="generate_qr"),
    path("stream/", views.camera_stream, name="camera_stream"),
    path("mjpeg_feed/", views.camera_mjpeg_feed, name="camera_mjpeg_feed"),
    path("capture/<int:camera_id>/", views.capture_frame, name="capture_frame"),
    path("captures/", views.captures_gallery, name="captures_gallery"),
]
