// Handles turning on the webcam and capturing a frame to send to the backend.
// Reused by any kiosk page that needs the camera (currently: verify.html).

async function startCamera(videoElementId) {
    const video = document.getElementById(videoElementId);
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
    } catch (err) {
        console.error("Could not access camera:", err);
    }
}

function captureFrame(videoElementId, canvasElementId) {
    const video = document.getElementById(videoElementId);
    const canvas = document.getElementById(canvasElementId);
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    return canvas.toDataURL('image/jpeg'); // base64 image, ready to send to backend
}