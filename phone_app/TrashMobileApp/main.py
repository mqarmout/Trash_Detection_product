import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.button import Button as PopupButton
import cv2
import requests
from PIL import Image as PILImage
import os
import threading

kivy.require('2.3.0')

class TrODApp(App):
    def build(self):
        self.main_layout = BoxLayout(orientation='vertical', padding=10)
        
        # Status label
        self.status_label = Label(text="Status: Ready", size_hint=(1, None), height=40)
        self.main_layout.add_widget(self.status_label)

        # Image display widget
        self.image_view = Image(size_hint=(1, 1))
        self.main_layout.add_widget(self.image_view)

        # Capture button
        self.capture_button = Button(text="Capture Image", size_hint=(1, None), height=50)
        self.capture_button.bind(on_press=self.capture_image)
        self.main_layout.add_widget(self.capture_button)

        # Send to API button
        self.process_button = Button(text="Send to API", size_hint=(1, None), height=50)
        self.process_button.bind(on_press=self.process_image)
        self.main_layout.add_widget(self.process_button)

        # Capture again button
        self.capture_again_button = Button(text="Capture Again", size_hint=(1, None), height=50)
        self.capture_again_button.bind(on_press=self.capture_again)
        self.capture_again_button.disabled = True  # Initially disabled
        self.main_layout.add_widget(self.capture_again_button)

        # Start streaming thread
        self.is_streaming = True
        self.is_capturing = False
        threading.Thread(target=self.start_stream, daemon=True).start()

        return self.main_layout

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
                    Clock.schedule_once(lambda dt: self.update_image_view(image))

                except Exception as e:
                    Clock.schedule_once(lambda dt: self.update_status(f"Error: {str(e)}"))

    def update_image_view(self, image):
        """Update the ImageView with a new image."""
        self.image_view.texture = self.convert_pil_to_texture(image)

    def convert_pil_to_texture(self, image):
        """Convert a PIL image to Kivy texture."""
        from kivy.graphics.texture import Texture
        data = image.tobytes()
        texture = Texture.create(size=image.size, colorfmt='rgb')
        texture.blit_buffer(data, colorfmt='rgb', bufferfmt='ubyte')
        return texture

    def capture_image(self, instance):
        """Capture an image using the laptop camera."""
        self.status_label.text = "Capturing image..."
        try:
            self.is_capturing = True
            ret, frame = self.cap.read()
            if ret:
                self.status_label.text = "Image captured successfully!"
                # Convert frame to PIL Image
                image = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                # Freeze the image and display it
                self.is_streaming = False  # Stop streaming
                self.capture_again_button.disabled = False  # Enable "Capture Again" button

                # Display the captured image
                Clock.schedule_once(lambda dt: self.update_image_view(image))

                # Store image for further processing
                self.image_path = os.path.join(os.getcwd(), "captured_image.png")
                image.save(self.image_path, format="PNG")
            else:
                self.status_label.text = "Error: Unable to capture image"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

    def process_image(self, instance):
        """Send the image to the object detection API and fetch the processed image."""
        base_url = "http://34.46.17.218:5000"  # For local test http://127.0.0.1:11000
        api_url = f"{base_url}/trash_image"
        
        # Show processing message
        Clock.schedule_once(lambda dt: self.update_status("Processing image..."))

        try:
            if not hasattr(self, "image_path") or not os.path.exists(self.image_path):
                Clock.schedule_once(lambda dt: self.update_status("Error: No image available to send"))
                return

            # Open the captured image file and send it to the API
            with open(self.image_path, "rb") as img_file:
                response = requests.post(api_url, files={"file": img_file}, allow_redirects=False)

                if response.status_code == 302:  # Successful response with redirect
                    # Extract the redirect URL for the processed image
                    redirect_url = response.headers.get("Location")
                    if not redirect_url:
                        Clock.schedule_once(lambda dt: self.update_status("Error: No redirect URL provided by the API"))
                        return

                    # Full URL to fetch the processed image
                    processed_img_url = f"{base_url}{redirect_url}"

                    # Fetch the processed image
                    processed_img = requests.get(processed_img_url, stream=True)
                    if processed_img.status_code == 200:
                        processed_img_path = os.path.join(
                            os.path.dirname(self.image_path), "processed_image.png"
                        )
                        with open(processed_img_path, "wb") as f:
                            f.write(processed_img.content)

                        # Display the processed image (apply flip for display)
                        image = PILImage.open(processed_img_path)
                        flipped_image = image.transpose(PILImage.FLIP_TOP_BOTTOM)  # Flip vertically

                        # Display the flipped image
                        Clock.schedule_once(lambda dt: self.update_image_view(flipped_image))
                        Clock.schedule_once(lambda dt: self.update_status("Image processed successfully!"))

                        # Disable the "Send to API" button and enable "Capture Again" button
                        Clock.schedule_once(self.disable_process_button)
                        Clock.schedule_once(self.enable_capture_again_button)
                    else:
                        Clock.schedule_once(lambda dt: self.update_status(f"Error: Unable to fetch processed image (status {processed_img.status_code})"))
                elif response.status_code == 204:
                    Clock.schedule_once(lambda dt: self.update_status("Error: API did not process the image (status 204)"))
                else:
                    Clock.schedule_once(lambda dt: self.update_status(f"Error: API returned status {response.status_code} - {response.text}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"Error: {str(e)}"))

    def capture_again(self, instance):
        """Allow the user to capture a new image again."""
        self.status_label.text = "Ready for next capture..."
        self.capture_again_button.disabled = True  # Disable the "Capture Again" button
        self.is_streaming = True  # Restart streaming
        threading.Thread(target=self.start_stream, daemon=True).start()

    def update_status(self, text):
        """Update the status label text."""
        self.status_label.text = text

    def disable_process_button(self, dt):
        """Disable the process button."""
        self.process_button.disabled = True

    def enable_capture_again_button(self, dt):
        """Enable the capture again button."""
        self.capture_again_button.disabled = False

    def on_stop(self):
        """Cleanup on application exit."""
        self.is_streaming = False  # Stop the streaming thread
        if hasattr(self, 'cap'):
            self.cap.release()  # Release the camera
        cv2.destroyAllWindows()  # Close any OpenCV windows


if __name__ == "__main__":
    TrODApp().run()
