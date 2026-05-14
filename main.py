import cv2
import mediapipe as mp
import time
import numpy as np
import win32api
import win32print
import os

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh()

# Landmark mata kiri & kanan (MediaPipe FaceMesh)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

EAR_THRESHOLD = 0.25      # makin kecil = makin ketat
CONSEC_FRAMES = 3         # harus tertutup beberapa frame (anti noise)

blink_frame_counter = 0
blink_count = 0
first_blink_time = 0
last_print_time = 0
cooldown = 2

status_text = "Menunggu..."

def print_file():
    file_path = os.path.abspath("blink_print.txt")
    win32api.ShellExecute(0, "print", file_path, None, ".", 0)

# hitung EAR
def calculate_ear(landmarks, eye_points):
    p = [(landmarks[i].x, landmarks[i].y) for i in eye_points]

    # rumus EAR
    A = np.linalg.norm(np.array(p[1]) - np.array(p[5]))
    B = np.linalg.norm(np.array(p[2]) - np.array(p[4]))
    C = np.linalg.norm(np.array(p[0]) - np.array(p[3]))

    ear = (A + B) / (2.0 * C)
    return ear

cap = cv2.VideoCapture(0)

print("Sistem EAR aktif... kedip 2x untuk print")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            landmarks = face_landmarks.landmark

            left_ear = calculate_ear(landmarks, LEFT_EYE)
            right_ear = calculate_ear(landmarks, RIGHT_EYE)
            ear = (left_ear + right_ear) / 2.0

            # ===== DETEKSI KEDIP =====
            if ear < EAR_THRESHOLD:
                blink_frame_counter += 1
            else:
                # mata buka kembali → dianggap 1 kedip valid
                if blink_frame_counter >= CONSEC_FRAMES:
                    current_time = time.time()

                    if blink_count == 0:
                        blink_count = 1
                        first_blink_time = current_time
                        status_text = "Kedip pertama"

                    elif blink_count == 1:
                        if current_time - first_blink_time <= 1:
                            if current_time - last_print_time > cooldown:
                                status_text = "PRINTING..."
                                print_file()
                                last_print_time = current_time
                            else:
                                status_text = "Cooldown..."
                        else:
                            status_text = "Terlalu lama"

                        blink_count = 0

                blink_frame_counter = 0

    # reset kalau terlalu lama
    if blink_count == 1 and (time.time() - first_blink_time > 1):
        blink_count = 0
        status_text = "Reset"

    # ===== VISUAL =====
    cv2.putText(frame, f"EAR: {ear:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.putText(frame, f"Blink Count: {blink_count}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    cv2.putText(frame, f"Status: {status_text}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

    cv2.imshow("EAR Blink Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()