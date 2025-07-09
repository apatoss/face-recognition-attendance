import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import os
import mysql.connector
import csv
from datetime import datetime, time

# MySQL DB connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="_Alfath23",
    database="attendancesystem"
)
cursor = conn.cursor()

# Mediapipe face detection
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.7)

# Load known faces (face_recognition only)
known_faces = []
known_names = []

face_dir = "faces"
if not os.path.exists(face_dir):
    os.makedirs(face_dir)

for filename in os.listdir(face_dir):
    img_path = os.path.join(face_dir, filename)
    image = face_recognition.load_image_file(img_path)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        known_faces.append(encodings[0])
        known_names.append(os.path.splitext(filename)[0])

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Determine attendance status
def get_attendance_status():
    now = datetime.now().time()
    if time(8, 0) <= now <= time(9, 30): return "On Time"
    elif time(9, 30) < now < time(17, 30): return "Late"
    elif time(17, 30) <= now <= time(22, 0): return "Punch Out"
    else: return "Outside Allowed Time"

csv_file = "attendance.csv"
if not os.path.exists(csv_file):
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Day", "Time", "Status"])

recorded_names = set()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detection.process(rgb_frame)

    if results.detections:
        face_locations = []
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = frame.shape
            x1, y1 = int(bbox.xmin * w), int(bbox.ymin * h)
            x2, y2 = int((bbox.xmin + bbox.width) * w), int((bbox.ymin + bbox.height) * h)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            face_locations.append((y1, x2, y2, x1))

        encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        for encoding, (y1, x2, y2, x1) in zip(encodings, face_locations):
            matches = face_recognition.compare_faces(known_faces, encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                match_index = np.argmin(face_recognition.face_distance(known_faces, encoding))
                name = known_names[match_index]

            if name != "Unknown" and name not in recorded_names:
                now = datetime.now()
                status = get_attendance_status()
                day = now.strftime("%A")
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("INSERT INTO attendance (name, day, timestamp, status) VALUES (%s, %s, %s, %s)", (name, day, timestamp, status))
                conn.commit()

                with open(csv_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([name, day, timestamp, status])

                recorded_names.add(name)

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    else:
        print("No face detected")

    cv2.imshow('Face Recognition Attendance', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
conn.close()