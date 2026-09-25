// Real-time face detection running in the browser, using face-api.js.
// This is SEPARATE from the backend's face_recognition check - this
// only gives live feedback (face count, lighting) while the camera
// is on, so the applicant can fix issues BEFORE clicking Capture.
// The backend still does its own real check after capture.

const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';

let detectionInterval = null;

async function loadFaceDetectionModels() {
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
}

function getAverageBrightness(videoElementId, sampleCanvasId) {
    const video = document.getElementById(videoElementId);
    const canvas = document.getElementById(sampleCanvasId);
    const context = canvas.getContext('2d');

    // Small sample size is enough for a brightness estimate - keeps this fast
    canvas.width = 50;
    canvas.height = 50;
    context.drawImage(video, 0, 0, 50, 50);

    const pixels = context.getImageData(0, 0, 50, 50).data;
    let total = 0;
    for (let i = 0; i < pixels.length; i += 4) {
        // Average of R, G, B for each pixel = rough brightness
        total += (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
    }
    return total / (pixels.length / 4); // 0 (black) to 255 (white)
}

function setFrameStatus(frameId, statusId, captureBtnId, state, message) {
    const frame = document.getElementById(frameId);
    const status = document.getElementById(statusId);
    const captureBtn = document.getElementById(captureBtnId);

    frame.classList.remove('frame-good', 'frame-warning', 'frame-bad');
    frame.classList.add('frame-' + state);
    status.textContent = message;

    // Only allow capture when everything looks good
    captureBtn.disabled = (state !== 'good');
}

async function startFaceDetectionLoop(videoElementId, sampleCanvasId, frameId, statusId, captureBtnId) {
    const video = document.getElementById(videoElementId);

    detectionInterval = setInterval(async () => {
        const brightness = getAverageBrightness(videoElementId, sampleCanvasId);

        if (brightness < 60) {
            setFrameStatus(frameId, statusId, captureBtnId, 'bad', 'Too dark - move to better lighting.');
            return;
        }
        if (brightness > 150) {
            setFrameStatus(frameId, statusId, captureBtnId, 'bad', 'Too bright - reduce glare or backlight.');
            return;
        }

        const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions());

        if (detections.length === 0) {
            setFrameStatus(frameId, statusId, captureBtnId, 'bad', 'No face detected - center your face in frame.');
        } else if (detections.length > 1) {
            setFrameStatus(frameId, statusId, captureBtnId, 'warning', 'Multiple faces detected - only one person at a time.');
        } else {
            setFrameStatus(frameId, statusId, captureBtnId, 'good', 'Face detected clearly - ready to capture.');
        }
    }, 400); // check about twice a second - fast enough to feel live, cheap enough not to lag
}

function stopFaceDetectionLoop() {
    if (detectionInterval) {
        clearInterval(detectionInterval);
    }
}