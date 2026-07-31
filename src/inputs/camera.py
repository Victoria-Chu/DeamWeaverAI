import logging
from typing import Any

try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger(__name__)

class CameraCapture:
    """Handles video frame capture from a local hardware webcam device using OpenCV."""

    def __init__(self, device_id: int = 0) -> None:
        """
        Initializes the camera capture device.

        Args:
            device_id: The index of the video capture device to open.
        """
        self.device_id: int = device_id

    def capture_frame(self) -> tuple[bool, Any]:
        """
        Captures a single frame from the camera device.

        Returns:
            A tuple containing:
                - A boolean indicating if the capture was successful.
                - The captured frame (ndarray) or None if capture failed.
        """
        logger.info(f"Opening camera device {self.device_id}")
        if cv2 is None:
            logger.error("OpenCV is not installed. Cannot capture frame.")
            return False, None

        cap = cv2.VideoCapture(self.device_id, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.device_id)
            
        if not cap.isOpened():
            logger.error("Could not open camera device.")
            return False, None
        
        # Read a few warmup frames to allow auto-exposure to settle
        ret: bool = False
        frame: Any = None
        for _ in range(4):
            ret, frame = cap.read()
            if not ret:
                break

        cap.release()
        
        if not ret or frame is None:
            logger.error("Failed to grab frame.")
            return False, None
            
        logger.info("Successfully captured frame.")
        return True, frame

    def capture_jpeg_bytes(self) -> tuple[bool, bytes | None]:
        """
        Captures a single frame and encodes it to JPEG bytes.

        Returns:
            A tuple containing:
                - A boolean indicating if the capture and encoding was successful.
                - The encoded JPEG bytes, or None if failed.
        """
        success, frame = self.capture_frame()
        if not success or frame is None:
            return False, None

        if cv2 is None:
            return False, None

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            logger.error("Failed to encode frame to JPEG.")
            return False, None

        return True, buffer.tobytes()

