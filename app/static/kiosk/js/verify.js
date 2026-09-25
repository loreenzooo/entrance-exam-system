// Logic specific to the verify.html page.
// Wires together: camera.js (turns on webcam, captures a still frame)
// and face-detector.js (live face/lighting feedback while camera runs).

document.addEventListener('DOMContentLoaded', async function () {
    await startCamera('camera-video');

    // Show "loading" while the detection model downloads (first time only)
    document.getElementById('face-status').textContent = 'Loading face detection...';

    await loadFaceDetectionModels();

    startFaceDetectionLoop(
        'camera-video',      // video element
        'brightness-canvas', // hidden canvas used just for brightness sampling
        'camera-frame',      // wrapper div that changes border color
        'face-status',       // text status message
        'capture-btn'        // capture button - only enabled when face looks good
    );

    document.getElementById('capture-btn').addEventListener('click', function () {
        const dataUrl = captureFrame('camera-video', 'camera-canvas');
        document.getElementById('photo_data').value = dataUrl;
        document.getElementById('verify-form').submit();
    });
});