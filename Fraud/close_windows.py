#!/usr/bin/env python3
"""
Close all OpenCV windows and camera processes
"""

import cv2
import sys
import os
import signal
import subprocess
import time

def close_all_windows():
    """Close all OpenCV windows and camera processes"""
    try:
        # Close all OpenCV windows
        cv2.destroyAllWindows()
        cv2.waitKey(1)  # Process any pending events

        # Force close any remaining windows
        for i in range(10):
            cv2.destroyAllWindows()
            cv2.waitKey(1)

        print("✅ OpenCV windows closed!")

        # Try to kill any Python processes that might be holding camera
        try:
            # Kill any Python processes with camera/opencv
            subprocess.run(['pkill', '-f', 'visual_pos'], check=False)
            subprocess.run(['pkill', '-f', 'photo_preview'], check=False)
            subprocess.run(['pkill', '-f', 'face_detection'], check=False)
            print("✅ Camera processes terminated!")
        except Exception as e:
            print(f"⚠️ Could not kill processes: {e}")

        # Try to release camera explicitly
        try:
            camera = cv2.VideoCapture(0)
            camera.release()
            print("✅ Camera released!")
        except Exception as e:
            print(f"⚠️ Could not release camera: {e}")

        print("🧹 All cleanup completed!")

    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")

if __name__ == "__main__":
    close_all_windows()
