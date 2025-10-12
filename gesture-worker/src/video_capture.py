import cv2, time
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def list_available_cameras(max_index=10):
    """
    Test camera indices and return available ones with their info.
    """
    available = []
    print("\nScanning for available cameras...")
    print("-" * 60)

    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                backend = cap.getBackendName()

                print(f"✓ Camera {i}: {width}x{height} @ {fps}fps (backend: {backend})")
                available.append(
                    {
                        "index": i,
                        "width": width,
                        "height": height,
                        "fps": fps,
                        "backend": backend,
                    }
                )

                # Show a preview window
                cv2.imshow(f"Camera {i} Preview (press any key)", frame)
                cv2.waitKey(1000)  # Show for 1 second
                cv2.destroyAllWindows()
            cap.release()
        else:
            print(f"✗ Camera {i}: Not available")

    print("-" * 60)
    if available:
        print(f"\nFound {len(available)} available camera(s)")
        print("Use one of the available indices above in your code.")
    else:
        print("\nNo cameras found!")

    return available


# Uncomment the line below to scan for cameras
# list_available_cameras()

cap = cv2.VideoCapture(1)  # switch to Pi pipeline in prod
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 30)

with mp_hands.Hands(
    model_complexity=0,
    max_num_hands=2,
    min_detection_confidence=0.4,
    min_tracking_confidence=0.4,
) as hands:
    prev = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)
        if res.multi_hand_landmarks:
            for hand in res.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
        # FPS HUD
        now = time.time()
        fps = 1.0 / (now - prev)
        prev = now
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        cv2.imshow("gesture-dev", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break  # ESC to exit
cap.release()
cv2.destroyAllWindows()
