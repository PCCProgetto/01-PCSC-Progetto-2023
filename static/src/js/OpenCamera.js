let camera_start = false;

function startCamera() {
    camera_start = true;
    navigator.mediaDevices.getUserMedia({video: true}).then(gotMedia).catch(error =>
        console.error('getUserMedia() error:', error));
    const vid = document.getElementById('videoElement');
    vid.style.display = 'block';
    // const scatta = document.getElementById('scatta');
    // scatta.style.display = 'block';
    const startcamera = document.getElementById('startcamera');
    startcamera.style.display = 'none';
}

function gotMedia(mediaStream) {
    const videoElement = document.getElementById('videoElement');
    videoElement.srcObject = mediaStream;
    videoElement.addEventListener('loadedmetadata', function () {
        videoElement.play();
    });
}

function capture() {
    if (!camera_start) {
        startCamera()
    }
    const canvasElement = document.createElement('canvas');
    const context = canvasElement.getContext('2d');
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;

    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    const imageData = canvasElement.toDataURL('image/png');
    const img = document.getElementById("camera");
    // Pause the video and display the current frame as an image
    // #videoElement.pause();

    videoElement.style.display = 'none';
    img.style.display = 'block';
    img.src = imageData;

    // Leggi la stringa di codifica in base64 come un blob e avvia la lettura del file
    const blob = b64toBlob(imageData);
    const file = new File([blob], "image.png", {type: "image/png"});
    const fd = new FormData();

    fd.append('file', file);

    $.ajax({
        type: 'POST',
        url: '/upload',
        data: fd,
        processData: false,
        contentType: false
    }).done(function (data) {
        $('#result').text(data);
        console.log(data);
        document.getElementById("result").style.display = "block";
    });
}

// Converti una stringa di codifica in base64 in un oggetto Blob
function b64toBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], {type: mimeString});
}

function openCamera() {

    navigator.mediaDevices.getUserMedia({video: true}).then(gotMedia).catch(error =>
        console.error('getUserMedia() error:', error));

    function gotMedia(mediaStream) {
        const videoElement = document.createElement('video');
        videoElement.srcObject = mediaStream;

        videoElement.addEventListener('loadedmetadata', function () {
            videoElement.play();

            const canvasElement = document.createElement('canvas');
            const context = canvasElement.getContext('2d');
            canvasElement.width = videoElement.videoWidth;
            canvasElement.height = videoElement.videoHeight;

            function capture() {
                context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
                const imageData = canvasElement.toDataURL('image/png');

                let img = document.getElementById("camera");
                img.src = imageData;

                const fd = new FormData();
                fd.append('file', b64toBlob(imageData), 'screenshot.png');

                $.ajax({
                    type: 'POST',
                    url: '/upload',
                    data: fd,
                    processData: false,
                    contentType: false
                }).done(function (data) {
                    $('#result').text(data);
                    console.log(data);                
                });

                // window.setTimeout(capture, 100000);
            }

            capture();
        });
    }
}
