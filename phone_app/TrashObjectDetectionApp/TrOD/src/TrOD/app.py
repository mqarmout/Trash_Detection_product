import toga
from toga.style import Pack
from toga.style.pack import COLUMN
import requests
from PIL import Image as PILImage
import cv2
import os
import threading

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

        # Button for capturing again and returning to streaming
        self.capture_again_button = toga.Button(
            "Capture Again",
            on_press=self.capture_again,
            style=Pack(padding=10)
        )
        self.capture_again_button.enabled = False  # Disabled initially
        main_box.add(self.capture_again_button)

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

        # Start streaming
        self.is_streaming = True
        threading.Thread(target=self.start_stream, daemon=True).start()

    def start_stream(self):
        """Continuously stream frames from the camera."""
        self.cap = cv2.VideoCapture(0)  # Open the default camera
        if not self.cap.isOpened():
            self.status_label.text = "Error: Cannot access the camera"
            return

        while self.is_streaming:
            ret, frame = self.cap.read()  # Capture frame-by-frame
            if ret:
                try:
                    # Convert frame to RGB for PIL compatibility
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Convert to PIL Image
                    image = PILImage.fromarray(frame_rgb)

                    # Update the ImageView with the current frame directly
                    self.image_view.image = toga.Image(image)

                except Exception as e:
                    self.status_label.text = f"Error: {str(e)}"
            else:
                self.status_label.text = "Error: Unable to capture frame"

    def capture_image(self, widget):
        """Capture an image using the laptop camera."""
        self.status_label.text = "Capturing image..."
        try:
            ret, frame = self.cap.read()
            if ret:
                self.status_label.text = "Image captured successfully!"
                # Convert frame to PIL Image
                image = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                # Freeze the image and display it
                self.is_streaming = False  # Stop streaming
                self.capture_again_button.enabled = True  # Enable "Capture Again" button

                # Display the captured image
                self.image_view.image = toga.Image(image)

                # Store image for further processing
                self.image_path = os.path.join(os.getcwd(), "captured_image.png")
                image.save(self.image_path, format="PNG")
            else:
                self.status_label.text = "Error: Unable to capture image"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

    def process_image(self, widget):
        """Send the image to the object detection API and fetch the processed image."""
        api_url = "http://127.0.0.1:11000/trash_image"
        self.status_label.text = "Sending image to API..."

        try:
            if not hasattr(self, "image_path") or not os.path.exists(self.image_path):
                self.status_label.text = "Error: No image available to send"
                return

            # Open the captured image file and send it to the API
            with open(self.image_path, "rb") as img_file:
                response = requests.post(api_url, files={"file": img_file}, allow_redirects=False)

                if response.status_code == 302:  # Successful response with redirect
                    # Extract the redirect URL for the processed image
                    redirect_url = response.headers.get("Location")
                    if not redirect_url:
                        self.status_label.text = "Error: No redirect URL provided by the API"
                        return

                    # Full URL to fetch the processed image
                    processed_img_url = f"http://127.0.0.1:11000{redirect_url}"

                    # Fetch the processed image
                    processed_img = requests.get(processed_img_url, stream=True)
                    if processed_img.status_code == 200:
                        processed_img_path = os.path.join(
                            os.path.dirname(self.image_path), "processed_image.png"
                        )
                        with open(processed_img_path, "wb") as f:
                            f.write(processed_img.content)

                        # Display the processed image
                        self.image_view.image = toga.Image(processed_img_path)
                        self.status_label.text = "Image processed successfully!"
                    else:
                        self.status_label.text = f"Error: Unable to fetch processed image (status {processed_img.status_code})"
                elif response.status_code == 204:
                    self.status_label.text = "Error: API did not process the image (status 204)"
                else:
                    self.status_label.text = f"Error: API returned status {response.status_code} - {response.text}"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

    def capture_again(self, widget):
        """Allow the user to capture a new image again."""
        self.status_label.text = "Ready for next capture..."
        self.capture_again_button.enabled = False  # Disable the "Capture Again" button
        self.is_streaming = True  # Restart streaming
        threading.Thread(target=self.start_stream, daemon=True).start()

    def on_close(self):
        """Cleanup on application exit."""
        self.is_streaming = False  # Stop the streaming thread
        if hasattr(self, 'cap'):
            self.cap.release()  # Release the camera
        cv2.destroyAllWindows()  # Close any OpenCV windows

        super().on_close()


def main():
    return TrOD()
