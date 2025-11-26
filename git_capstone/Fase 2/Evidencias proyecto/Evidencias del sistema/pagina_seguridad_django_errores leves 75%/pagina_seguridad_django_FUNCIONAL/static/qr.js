/**
 * 
 * @param {string} text 
 * @param {HTMLElement} qrElement 
 */
export function generateQR(text, qrElement) {
    if (!text || !qrElement) return;
    qrElement.innerHTML = '';
    new window.QRCode(qrElement, {
        text: text,
        width: 200,
        height: 200
    });
}

export function startScan(videoElement, canvasElement, resultCallback) {
    const ctx = canvasElement.getContext('2d');
    let scanning = true;

    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
        .then(function(stream) {
            videoElement.srcObject = stream;
            videoElement.setAttribute("playsinline", true);
            videoElement.play();
            requestAnimationFrame(tick);
        });

    function tick() {
        if (!scanning) return;
        if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
            canvasElement.height = videoElement.videoHeight;
            canvasElement.width = videoElement.videoWidth;
            ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            let imageData = ctx.getImageData(0, 0, canvasElement.width, canvasElement.height);
            let code = window.jsQR(imageData.data, imageData.width, imageData.height, { inversionAttempts: "dontInvert" });
            if (code) {
                scanning = false;
                videoElement.srcObject.getTracks().forEach(track => track.stop());
                if (typeof resultCallback === 'function') {
                    resultCallback(code.data);
                }
            } else {
                requestAnimationFrame(tick);
            }
        } else {
            requestAnimationFrame(tick);
        }
    }

    return () => { scanning = false; };
}

/**
 * Genera automáticamente un QR con el texto dado y lo muestra en el elemento especificado.
 * @param {string} text - Texto a codificar.
 * @param {HTMLElement} qrElement - Elemento donde mostrar el QR.
 */
export function autoGenerateQR(text, qrElement) {
    generateQR(text, qrElement);
}