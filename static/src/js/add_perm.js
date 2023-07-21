form.submit(function (e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.

    const form = $(this);

    const actionUrl = form.attr('action');
    overlay.style.display = 'block';
    const fd = new FormData(this)
    $.ajax({
        type: "POST",
        url: actionUrl,
        data: fd, // Use FormData object to include file data
        processData: false,
        contentType: false,
        success: function (data) {
            //se data è "errore" vuol dire che c'è stato un errore
            //if (data === "error") {
            //    alert(data);
            //} else {
            alert(data);
            //redirect to gestione permessi
            window.location.href = "/dashboard/gest_perm";

            //}
        }
    });

})


function choseImage() {
    fromCamera = false;
    document.getElementById('image-input').click();
}

document.addEventListener("DOMContentLoaded", function () {
    const imageBox = document.getElementById('image-box');
    const imageButtons = document.getElementById('image-buttons');

    imageBox.appendChild(imageButtons);
});


const videoElement = document.getElementById('videoElement');
let mediaStream = null;

function startCamera() {
    navigator.mediaDevices.getUserMedia({video: true}).then(gotMedia).catch(error =>
        console.error('getUserMedia() error:', error));
    const vid = document.getElementById('videoElement');
    vid.style.display = 'block';
    const scatta = document.getElementById('scatta');
    scatta.style.display = 'block';
    const startcamera = document.getElementById('startcamera');
    startcamera.style.display = 'none';
    const preview = document.getElementById('preview');
    if (preview.style.display === 'block') {
        preview.style.display = 'none';
    }
}

function gotMedia(stream) {
    mediaStream = stream;
    videoElement.srcObject = mediaStream;
    videoElement.addEventListener('loadedmetadata', function () {
        videoElement.play();
    });
}

function capture() {
    const canvasElement = document.createElement('canvas');
    const context = canvasElement.getContext('2d');
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;

    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    const imageData = canvasElement.toDataURL('image/png');
    const img = document.getElementById("preview");
    // Pause the video and display the current frame as an image
    // #videoElement.pause();

    videoElement.style.display = 'none';
    img.style.display = 'block';
    img.src = imageData;

    // Leggi la stringa di codifica in base64 come un blob e avvia la lettura del file
    const blob = b64toBlob(imageData);
    const file = new File([blob], "image.png", {type: "image/png"});
    const input = document.getElementById('image-input');

    // Crea un oggetto DataTransfer
    const dataTransfer = new DataTransfer();

    // Aggiungi il file all'oggetto DataTransfer
    dataTransfer.items.add(file);

    // Imposta la proprietà 'files' dell'elemento input utilizzando l'oggetto DataTransfer
    input.files = dataTransfer.files;
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

const overlay = document.getElementById('overlay');
