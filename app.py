from flask import Flask, render_template, Response, jsonify
import cv2
from ultralytics import YOLO

app = Flask(__name__)

# Camera
camera = cv2.VideoCapture(0)

# Load models
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

model = YOLO("yolov8n.pt")

# Variables
current_status = "FOCUSED"
distraction_count = 0
phone_count = 0
noface_count = 0
last_warning = False


def generate_frames():
    global current_status, distraction_count, phone_count, noface_count, last_warning

    while True:
        success, frame = camera.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        status_text = "Focused"
        color = (0, 255, 0)

        # YOLO DETECTION
        results = model(frame, stream=True)
        phone_detected = False

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = model.names[cls]

                if label == "cell phone":
                    phone_detected = True

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(frame, "PHONE DETECTED", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        # DISTRACTION LOGIC
        if phone_detected:
            status_text = "DISTRACTED (PHONE)"
            color = (255, 0, 0)
            current_status = "PHONE"

            if not last_warning:
                distraction_count += 1
                phone_count += 1
                last_warning = True

        elif len(faces) == 0:
            status_text = "DISTRACTED (NO FACE)"
            color = (0, 0, 255)
            current_status = "NO_FACE"

            if not last_warning:
                distraction_count += 1
                noface_count += 1
                last_warning = True

        else:
            status_text = "Focused"
            color = (0, 255, 0)
            current_status = "FOCUSED"
            last_warning = False

        # Draw face boxes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Display status
        cv2.putText(frame, status_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, color, 2)

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status')
def status():
    return jsonify({
        "status": current_status,
        "total": distraction_count,
        "phone": phone_count,
        "noface": noface_count
    })


# RESET ROUTE (MUST BE ABOVE app.run)
@app.route('/reset', methods=['POST'])
def reset():
    global distraction_count, phone_count, noface_count, current_status, last_warning

    distraction_count = 0
    phone_count = 0
    noface_count = 0
    current_status = "FOCUSED"
    last_warning = False

    return jsonify({"message": "reset successful"})


if __name__ == "__main__":
    app.run(debug=True)