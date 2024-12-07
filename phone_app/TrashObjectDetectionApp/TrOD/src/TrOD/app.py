"""
This app uses your camera to take a picture and detect trash objects.
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN
import requests
from PIL import Image as PILImage
from io import BytesIO
import cv2
import os


class TrOD(toga.App):
    def startup(self):
        """Construct and show the Toga application."""
        # Main layout box
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Button for capturing images
        self.capture_button = toga.Button(
            "Capture Image",
            on_press=self.capture_image,
            style=Pack(padding=10)
        )
        main_box.add(self.capture_button)

        # Button for sending images to the API
        self.process_button = toga.Button(
            "Send to API",
            on_press=self.process_image,
            style=Pack(padding=10)
        )
        main_box.add(self.process_button)

        # Status label to display messages
        self.status_label = toga.Label(
            "Status: Ready",
            style=Pack(padding=10)
        )
        main_box.add(self.status_label)

        # Placeholder for displaying the processed image
        self.image_view = toga.ImageView(style=Pack(height=300, padding=10))
        main_box.add(self.image_view)

        # Create the main window and add the main box
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    def capture_image(self, widget):
        """Capture an image using the laptop camera."""
        self.status_label.text = "Opening camera..."
        try:
            # Open the camera
            cap = cv2.VideoCapture(0)  # 0 is the default camera
            if not cap.isOpened():
                self.status_label.text = "Error: Cannot access the camera"
                return

            # Capture a single frame
            ret, frame = cap.read()
            cap.release()  # Release the camera
            
            if ret:
                self.status_label.text = "Image captured successfully!"
                # Convert the captured frame to PIL Image
                image = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                
                # Set the specific folder path
                folder_path = r"D:\GBC\Full Stack Data Science\Project\Trash_Detection_product\backend\data\inference_trash_images\images"
                os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
                
                # Save the image in the specific folder
                self.image_path = os.path.join(folder_path, "captured_image.png")
                image.save(self.image_path, format="PNG")
                
                # Update the ImageView with the saved image
                self.image_view.image = toga.Image(self.image_path)
            else:
                self.status_label.text = "Error: Unable to capture image"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

    def process_image(self, widget):
        """Send the image to the object detection API."""
        api_url = "http://127.0.0.1:11000/trash_image"  # Correct API endpoint
        self.status_label.text = "Sending image to API..."

        try:
            if not hasattr(self, "image_path") or not os.path.exists(self.image_path):
                self.status_label.text = "Error: No image available to send"
                return

            # Open the captured image file and send it to the API
            with open(self.image_path, "rb") as img_file:
                response = requests.post(api_url, files={"file": img_file})
                if response.status_code == 204:
                    self.status_label.text = "Image processed successfully!"
                    processed_img_url = response.url

                    # Optionally: Fetch and display the processed image
                    processed_img = requests.get(processed_img_url, stream=True)
                    if processed_img.status_code == 200:
                        processed_img_path = os.path.join(
                            os.path.dirname(self.image_path), "processed_image.png"
                        )
                        with open(processed_img_path, "wb") as f:
                            f.write(processed_img.content)
                        self.image_view.image = toga.Image(processed_img_path)
                    else:
                        self.status_label.text = f"Error: Unable to fetch processed image"
                else:
                    self.status_label.text = f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"



def main():
    return TrOD()
