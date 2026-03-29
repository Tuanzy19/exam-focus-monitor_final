let alertSound = new Audio("/static/alert.mp3");   // every 10
let buzzerSound = new Audio("/static/buzz.mp3");   // per distraction

let intervalID = null;
let isMonitoring = false;
let lastTotal = 0;
let lastAlertLevel = 0; // track 10,20,30...

function startMonitoring() {
    if (isMonitoring) return;

    document.getElementById("videoFeed").src = "/video";
    document.getElementById("videoFeed").style.display = "block";
    document.getElementById("placeholder").style.display = "none";

    // unlock audio
    alertSound.play().then(() => {
        alertSound.pause();
        alertSound.currentTime = 0;
    }).catch(() => {});

    buzzerSound.play().then(() => {
        buzzerSound.pause();
        buzzerSound.currentTime = 0;
    }).catch(() => {});

    intervalID = setInterval(checkStatus, 1000);
    isMonitoring = true;
}

function stopMonitoring() {
    document.getElementById("videoFeed").src = "";
    document.getElementById("videoFeed").style.display = "none";
    document.getElementById("placeholder").style.display = "block";

    clearInterval(intervalID);
    intervalID = null;

    isMonitoring = false;
    lastTotal = 0;
    lastAlertLevel = 0;

    document.getElementById("status").innerText = "Status: Stopped";
}

function resetMonitoring() {
    fetch('/reset', { method: 'POST' })
        .then(res => res.json())
        .then(() => {

            document.getElementById("status").innerText = "Status: Reset";
            document.getElementById("counter").innerText = "Total Distraction: 0";
            document.getElementById("phoneCounter").innerText = "Phone Detected: 0";
            document.getElementById("noFaceCounter").innerText = "No Face Detected: 0";

            // stop sounds
            alertSound.pause();
            alertSound.currentTime = 0;

            buzzerSound.pause();
            buzzerSound.currentTime = 0;

            lastTotal = 0;
            lastAlertLevel = 0;
        })
        .catch(err => console.log("Reset error:", err));
}

function checkStatus() {
    fetch('/status')
        .then(res => res.json())
        .then(data => {

            // UI
            document.getElementById("status").innerText =
                "Status: " + data.status;

            document.getElementById("counter").innerText =
                "Total Distraction: " + data.total;

            document.getElementById("phoneCounter").innerText =
                "Phone Detected: " + data.phone;

            document.getElementById("noFaceCounter").innerText =
                "No Face Detected: " + data.noface;

            //  buzzer per increase
            if (data.total > lastTotal) {
                buzzerSound.play().catch(() => {});
            }

            //  alert every 10 (ONLY ONCE)
            if (
                data.total % 10 === 0 &&
                data.total !== 0 &&
                data.total !== lastAlertLevel
            ) {
                alertSound.play().catch(() => {});
                lastAlertLevel = data.total;
            }

            lastTotal = data.total;
        })
        .catch(err => console.log("Fetch error:", err));
}