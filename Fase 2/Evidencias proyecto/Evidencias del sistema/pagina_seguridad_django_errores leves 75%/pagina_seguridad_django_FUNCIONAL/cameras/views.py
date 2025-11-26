import io
import os

import cv2
import qrcode

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, StreamingHttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from .models import Camera, SecurityCode, Capture


def login_view(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("cameras:camera_list")
        error = "Usuario o contraseña incorrectos."
    return render(request, "cameras/login.html", {"error": error})


def registro_view(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")
        if not username or not email or not password:
            error = "Todos los campos son obligatorios."
        elif password != confirm:
            error = "Las contraseñas no coinciden."
        elif User.objects.filter(username=username).exists():
            error = "Usuario ya registrado."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("cameras:camera_list")
    return render(request, "cameras/registro.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("cameras:login")


@login_required
def camera_list(request):
    cameras = Camera.objects.all()
    # adjuntar última captura (si existe) a cada cámara
    for cam in cameras:
        from .models import Capture
        last = Capture.objects.filter(camera=cam).order_by("-created_at").first()
        cam.last_capture = last.image.url if last else ""
    return render(request, "cameras/home.html", {"cameras": cameras})


@login_required
def add_camera(request):
    camera = None
    error = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        rtsp_url = request.POST.get("rtsp_url", "").strip()
        description = request.POST.get("description", "").strip()
        if name and rtsp_url:
            camera = Camera.objects.create(
                name=name,
                rtsp_url=rtsp_url,
                description=description or ""
            )
            # Ir directo a pantalla de QR
            return redirect("cameras:generate_qr", camera_id=camera.id)
        else:
            error = "Nombre y URL son obligatorios."
    return render(request, "cameras/add_camera.html", {"camera": camera, "error": error})


@login_required
def generate_qr_for_camera(request, camera_id):
    camera = get_object_or_404(Camera, pk=camera_id)
    lifetime = int(request.GET.get("lifetime_seconds", 300))
    code = SecurityCode.create_for_camera(camera, lifetime_seconds=lifetime)

    stream_url = request.build_absolute_uri(
        reverse("cameras:camera_stream") + f"?camera={camera.id}&token={code.token}"
    )

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(stream_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    qr_dir = settings.MEDIA_ROOT / "access_qr"
    os.makedirs(qr_dir, exist_ok=True)
    filename = f"access_{camera.id}_{code.token}.png"
    file_path = qr_dir / filename
    img.save(file_path)

    qr_url = f"{settings.MEDIA_URL}access_qr/{filename}"

    return render(
        request,
        "cameras/qr_access.html",
        {
            "camera": camera,
            "qr_url": qr_url,
            "stream_url": stream_url,
            "expires_at": code.expires_at,
        },
    )


def gen_camera_frames(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        ok, jpeg = cv2.imencode(".jpg", frame)
        if not ok:
            continue
        frame_bytes = jpeg.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
    cap.release()


@login_required
def camera_mjpeg_feed(request):
    camera_id = request.GET.get("camera")
    token = request.GET.get("token")
    if not camera_id or not token:
        return HttpResponseForbidden("Falta cámara o token.")
    camera = get_object_or_404(Camera, pk=camera_id)
    try:
        code = SecurityCode.objects.get(camera=camera, token=token)
    except SecurityCode.DoesNotExist:
        return HttpResponseForbidden("Token inválido.")
    if not code.is_valid():
        return HttpResponseForbidden("Token expirado o ya usado.")
    return StreamingHttpResponse(
        gen_camera_frames(camera.rtsp_url),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )


@login_required
def camera_stream(request):
    camera_id = request.GET.get("camera")
    token = request.GET.get("token")
    if not camera_id or not token:
        return HttpResponseForbidden("Falta cámara o token.")
    camera = get_object_or_404(Camera, pk=camera_id)
    try:
        code = SecurityCode.objects.get(camera=camera, token=token)
    except SecurityCode.DoesNotExist:
        return HttpResponseForbidden("Token inválido.")
    if not code.is_valid():
        return HttpResponseForbidden("Token expirado o ya usado.")
    stream_url = request.build_absolute_uri(
        reverse("cameras:camera_mjpeg_feed") + f"?camera={camera.id}&token={token}"
    )
    return render(
        request,
        "cameras/camera_stream.html",
        {"camera": camera, "stream_url": stream_url},
    )


@login_required
def capture_frame(request, camera_id):
    camera = get_object_or_404(Camera, pk=camera_id)
    cap = cv2.VideoCapture(camera.rtsp_url)
    success, frame = cap.read()
    cap.release()
    if not success:
        return HttpResponse("No se pudo capturar la imagen", status=500)
    ok, jpeg = cv2.imencode(".jpg", frame)
    if not ok:
        return HttpResponse("Error al codificar la imagen", status=500)
    image_bytes = jpeg.tobytes()
    captures_dir = settings.MEDIA_ROOT / "captures"
    os.makedirs(captures_dir, exist_ok=True)
    filename = f"capture_camera_{camera.id}_{SecurityCode.objects.count()}.jpg"
    filepath = captures_dir / filename
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    Capture.objects.create(camera=camera, image=f"captures/{filename}")
    return redirect("cameras:captures_gallery")


@login_required
def captures_gallery(request):
    captures = Capture.objects.select_related("camera").order_by("-created_at")
    return render(request, "cameras/captures.html", {"captures": captures})

@login_required
def delete_camera(request, camera_id):
    camera = get_object_or_404(Camera, pk=camera_id)
    camera.delete()
    return redirect("cameras:camera_list")
