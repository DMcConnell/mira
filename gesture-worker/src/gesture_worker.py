import os, cv2

ENV = os.getenv("MIRA_ENV", "mac")  # "mac" or "pi"


def open_capture(width=640, height=360, fps=30):
    if ENV == "pi":
        try:
            # Picamera2 path (preferred on Pi)
            from picamera2 import Picamera2
            import numpy as np

            picam = Picamera2()
            config = picam.create_preview_configuration(
                main={"size": (width, height), "format": "RGB888"}
            )
            picam.configure(config)
            picam.start()

            class PiCap:
                def read(self):
                    frame = picam.capture_array()
                    return True, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                def release(self):
                    picam.stop()

            return PiCap()
        except Exception:
            # Fallback: GStreamer → OpenCV
            pipeline = (
                "libcamerasrc ! video/x-raw, width=%d, height=%d, framerate=%d/1 ! "
                "videoconvert ! video/x-raw,format=BGR ! appsink" % (width, height, fps)
            )
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            return cap
    else:
        # macOS (and generic USB cams)
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        return cap
