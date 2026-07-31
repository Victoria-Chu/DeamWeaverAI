import asyncio
import logging
import sys
import threading
from pathlib import Path
from typing import Any

# Configure console logging output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Ensure project root is in sys.path for direct script execution
root_dir: Path = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    import customtkinter as ctk
    from PIL import Image
except ImportError:
    ctk = None
    Image = None

try:
    import pygame
except ImportError:
    pygame = None

from config.settings import settings
from src.core.orchestrator import BedtimeStoryOrchestrator

logger = logging.getLogger(__name__)

class DreamWeaverApp:
    """The main desktop interface class for the DreamWeaver AI digital storybook application."""

    def __init__(self) -> None:
        """Initializes GUI windows, binds events, and configures hardware camera/audio settings."""
        if ctk is None or Image is None:
            raise ImportError("customtkinter and Pillow are required to run this desktop application.")
        
        # Configure customtkinter settings
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Root Window
        self.root: ctk.CTk = ctk.CTk()
        self.root.title("DreamWeaver AI 🪄")
        self.root.geometry("1024x720")
        self.root.resizable(True, True)
        self.root.configure(fg_color="#131326")

        self.webcam_active: bool = True
        self.current_story_data: dict[str, Any] | None = None
        self.current_slide_index: int = 0
        self.audio_playing: bool = False
        self.audio_process: Any | None = None
        self.last_voice_transcript: str | None = None
        self.last_image_bytes: bytes | None = None

        # Initialize pygame mixer for audio playback
        if pygame is not None:
            try:
                pygame.mixer.init()
                logger.info("Successfully initialized Pygame mixer.")
            except Exception as e:
                logger.error(f"Failed to initialize Pygame mixer: {e}")

        # Bind window close event to clean up audio playing processes
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # UI Layout Setup
        self._setup_ui()
        
        # Start camera preview loop
        self.root.after(100, self._update_camera_loop)

    def _setup_ui(self) -> None:
        """Sets up grid weight and configures layouts for all UI widgets."""
        # Configure grid weight (Lock sidebar to minsize=280 and allow output panel to resize)
        self.root.grid_columnconfigure(0, weight=0, minsize=280)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # ----------------- Left Sidebar (Config Panel) -----------------
        self.sidebar: ctk.CTkFrame = ctk.CTkFrame(
            self.root, 
            width=280, 
            corner_radius=20,
            fg_color="#1e1e38",
            border_width=2,
            border_color="#2b2b52"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)

        # Title
        self.title_label: ctk.CTkLabel = ctk.CTkLabel(
            self.sidebar, 
            text="DreamWeaver AI 🪄", 
            font=ctk.CTkFont(family="Comic Sans MS", size=24, weight="bold"),
            text_color="#ffeaa7"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Child Name Entry
        self.name_label: ctk.CTkLabel = ctk.CTkLabel(
            self.sidebar, 
            text="Protagonist's Name:",
            font=("Comic Sans MS", 12, "bold"),
            text_color="#a29bfe"
        )
        self.name_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.name_entry: ctk.CTkEntry = ctk.CTkEntry(
            self.sidebar, 
            placeholder_text="Name",
            fg_color="#2b2b52",
            text_color="#ffeaa7",
            border_color="#5f27cd",
            corner_radius=10
        )
        self.name_entry.insert(0, settings.default_child_name)
        self.name_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Child Age Slider
        self.age_label: ctk.CTkLabel = ctk.CTkLabel(
            self.sidebar, 
            text=f"Protagonist's Age: {settings.default_child_age}",
            font=("Comic Sans MS", 12, "bold"),
            text_color="#a29bfe"
        )
        self.age_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        self.age_slider: ctk.CTkSlider = ctk.CTkSlider(
            self.sidebar, 
            from_=1, 
            to=12, 
            number_of_steps=11, 
            progress_color="#fd79a8",
            button_color="#ff7675",
            button_hover_color="#e66767",
            command=self._on_age_slider_move
        )
        self.age_slider.set(settings.default_child_age)
        self.age_slider.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Duration Slider
        self.duration_label: ctk.CTkLabel = ctk.CTkLabel(
            self.sidebar, 
            text=f"Story Duration: {settings.default_duration_minutes} mins",
            font=("Comic Sans MS", 12, "bold"),
            text_color="#a29bfe"
        )
        self.duration_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")
        self.duration_slider: ctk.CTkSlider = ctk.CTkSlider(
            self.sidebar, 
            from_=3, 
            to=20, 
            number_of_steps=17, 
            progress_color="#74b9ff",
            button_color="#00cec9",
            button_hover_color="#00b894",
            command=self._on_duration_slider_move
        )
        self.duration_slider.set(settings.default_duration_minutes)
        self.duration_slider.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Input Spark Mode Choice
        self.mode_label: ctk.CTkLabel = ctk.CTkLabel(
            self.sidebar, 
            text="Input Spark Mode:",
            font=("Comic Sans MS", 12, "bold"),
            text_color="#a29bfe"
        )
        self.mode_label.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")
        self.mode_combo: ctk.CTkComboBox = ctk.CTkComboBox(
            self.sidebar, 
            values=["Voice Spark", "Image Spark"],
            fg_color="#2b2b52",
            button_color="#5f27cd",
            button_hover_color="#341f97",
            text_color="#ffeaa7",
            border_color="#5f27cd",
            corner_radius=10,
            command=self._on_mode_change
        )
        self.mode_combo.set("Voice Spark")
        self.mode_combo.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Output options toggles Sub-Frame
        self.toggles_frame: ctk.CTkFrame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.toggles_frame.grid(row=9, column=0, padx=20, pady=5, sticky="ew")
        self.toggles_frame.grid_columnconfigure((0, 1), weight=1)

        self.audio_toggle: ctk.CTkCheckBox = ctk.CTkCheckBox(
            self.toggles_frame, 
            text="Voice", 
            onvalue=True, 
            offvalue=False,
            text_color="#ffeaa7",
            fg_color="#5f27cd",
            hover_color="#341f97",
            font=("Comic Sans MS", 11, "bold")
        )
        self.audio_toggle.select()
        self.audio_toggle.grid(row=0, column=0, sticky="w", padx=(0, 5))

        self.images_toggle: ctk.CTkCheckBox = ctk.CTkCheckBox(
            self.toggles_frame, 
            text="Illustrations", 
            onvalue=True, 
            offvalue=False,
            text_color="#ffeaa7",
            fg_color="#5f27cd",
            hover_color="#341f97",
            font=("Comic Sans MS", 11, "bold")
        )
        self.images_toggle.select()
        self.images_toggle.grid(row=0, column=1, sticky="w", padx=(5, 0))

        # Camera preview frame (Compact height=110)
        self.cam_preview_frame: ctk.CTkFrame = ctk.CTkFrame(
            self.sidebar, 
            height=110, 
            fg_color="black",
            border_width=2,
            border_color="#2b2b52",
            corner_radius=10
        )
        self.cam_preview_frame.grid(row=10, column=0, padx=20, pady=5, sticky="ew")
        self.cam_preview_frame.grid_propagate(False)
        self.cam_preview_label: ctk.CTkLabel = ctk.CTkLabel(self.cam_preview_frame, text="Live Camera Feed", text_color="grey")
        self.cam_preview_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Hide webcam preview frame by default since the default mode is Voice Spark
        self.cam_preview_frame.grid_remove()

        # Status and Action Buttons
        self.status_label: ctk.CTkLabel = ctk.CTkLabel(
            self.sidebar, 
            text="Status: Ready", 
            text_color="#55efc4",
            font=("Comic Sans MS", 11, "bold")
        )
        self.status_label.grid(row=11, column=0, padx=20, pady=5, sticky="w")

        # Flexible spacer gridded row
        self.sidebar.grid_rowconfigure(12, weight=1)

        self.spark_btn: ctk.CTkButton = ctk.CTkButton(
            self.sidebar, 
            text="🎤 Record Voice Spark", 
            fg_color="#5f27cd",
            hover_color="#341f97",
            text_color="#ffffff",
            text_color_disabled="#718093",
            corner_radius=15,
            font=("Comic Sans MS", 12, "bold"),
            command=self._trigger_spark
        )
        self.spark_btn.grid(row=13, column=0, padx=20, pady=8, sticky="ew")

        self.generate_btn: ctk.CTkButton = ctk.CTkButton(
            self.sidebar, 
            text="✨ Create Bedtime Storybook", 
            fg_color="#ff7675",
            hover_color="#d63031",
            text_color="#131326",
            text_color_disabled="#718093",
            corner_radius=15,
            font=("Comic Sans MS", 14, "bold"),
            command=self._generate_storybook
        )
        self.generate_btn.grid(row=14, column=0, padx=20, pady=(8, 20), sticky="ew")

        # ----------------- Right Content Panel (Viewer) -----------------
        self.content: ctk.CTkFrame = ctk.CTkFrame(self.root, fg_color="#131326")
        self.content.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        # Story Title
        self.story_title_label: ctk.CTkLabel = ctk.CTkLabel(
            self.content, 
            text="Snuggle up and prepare for bedtime adventures...", 
            font=ctk.CTkFont(family="Comic Sans MS", size=20, weight="bold"),
            text_color="#ffeaa7"
        )
        self.story_title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Storybook Slide Canvas
        self.slide_frame: ctk.CTkFrame = ctk.CTkFrame(
            self.content, 
            fg_color="#1e1e38",
            corner_radius=25,
            border_width=3,
            border_color="#ffbe76"
        )
        self.slide_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.slide_frame.grid_columnconfigure(0, weight=1)
        self.slide_frame.grid_rowconfigure(0, weight=1)
        
        self.slide_image_label: ctk.CTkLabel = ctk.CTkLabel(
            self.slide_frame, 
            text="Your Bedtime Storybook Will Appear Here", 
            text_color="#a29bfe",
            font=("Comic Sans MS", 14, "bold")
        )
        self.slide_image_label.grid(row=0, column=0, sticky="nsew")

        # Scrollable Text Narration Box
        self.textbox: ctk.CTkTextbox = ctk.CTkTextbox(
            self.content, 
            height=130, 
            wrap="word",
            fg_color="#1e1e38",
            text_color="#ffeaa7",
            font=("Comic Sans MS", 13, "bold"),
            corner_radius=15,
            border_width=2,
            border_color="#5f27cd"
        )
        self.textbox.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.textbox.insert("0.0", "Choose a character, target duration, select inputs, and click generate to weave a custom story...")

        # Playback Nav Controls
        self.control_frame: ctk.CTkFrame = ctk.CTkFrame(
            self.content, 
            height=50,
            fg_color="#1e1e38",
            corner_radius=15
        )
        self.control_frame.grid(row=3, column=0, padx=20, pady=(10, 15), sticky="ew")
        self.control_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.prev_btn: ctk.CTkButton = ctk.CTkButton(
            self.control_frame, 
            text="◀ Previous", 
            state="disabled", 
            fg_color="#2b2b42",
            hover_color="#341f97",
            text_color="#718093",
            text_color_disabled="#718093",
            corner_radius=12,
            font=("Comic Sans MS", 11, "bold"),
            command=self._prev_slide
        )
        self.prev_btn.grid(row=0, column=0, padx=10, pady=10)

        self.play_btn: ctk.CTkButton = ctk.CTkButton(
            self.control_frame, 
            text="▶ Play Narration", 
            state="disabled", 
            fg_color="#2b2b42",
            hover_color="#00b894",
            text_color="#718093",
            text_color_disabled="#718093",
            corner_radius=12,
            font=("Comic Sans MS", 11, "bold"),
            command=self._play_narration
        )
        self.play_btn.grid(row=0, column=1, padx=10, pady=10)

        self.stop_btn: ctk.CTkButton = ctk.CTkButton(
            self.control_frame, 
            text="■ Stop", 
            state="disabled", 
            fg_color="#2b2b42",
            hover_color="#c0392b",
            text_color="#718093",
            text_color_disabled="#718093",
            corner_radius=12,
            font=("Comic Sans MS", 11, "bold"),
            command=self._stop_narration
        )
        self.stop_btn.grid(row=0, column=2, padx=10, pady=10)

        self.next_btn: ctk.CTkButton = ctk.CTkButton(
            self.control_frame, 
            text="Next ▶", 
            state="disabled", 
            fg_color="#2b2b42",
            hover_color="#341f97",
            text_color="#718093",
            text_color_disabled="#718093",
            corner_radius=12,
            font=("Comic Sans MS", 11, "bold"),
            command=self._next_slide
        )
        self.next_btn.grid(row=0, column=3, padx=10, pady=10)

    def _on_age_slider_move(self, value: float) -> None:
        """Handles slider moves to adjust age preferences."""
        self.age_label.configure(text=f"Protagonist's Age: {int(value)}")

    def _on_duration_slider_move(self, value: float) -> None:
        """Handles slider moves to adjust bedtime durations."""
        self.duration_label.configure(text=f"Story Duration: {int(value)} mins")

    def _on_mode_change(self, choice: str) -> None:
        """Changes widgets depending on Voice or Vision capture selection."""
        if choice == "Image Spark":
            self.spark_btn.configure(text="📷 Capture Toy Vision")
            self.webcam_active = True
            self.cam_preview_frame.grid()
        else:
            self.spark_btn.configure(text="🎤 Record Voice Spark")
            self.webcam_active = False
            self.cam_preview_label.configure(image="", text="Live Camera Feed")
            self.cam_preview_frame.grid_remove()

    def _update_camera_loop(self) -> None:
        """Periodically pulls low-res preview feeds from local camera interface."""
        if self.mode_combo.get() == "Image Spark" and self.webcam_active:
            try:
                import cv2

                from src.inputs.camera import CameraCapture
                cam: CameraCapture = CameraCapture(0)
                success, frame = cam.capture_frame()
                if success and frame is not None:
                    # Convert BGR (OpenCV) to RGB (PIL)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    resized = pil_img.resize((240, 110))
                    
                    ctk_img: ctk.CTkImage = ctk.CTkImage(light_image=resized, dark_image=resized, size=(240, 110))
                    self.cam_preview_label.configure(image=ctk_img, text="")
                    self.cam_preview_label.image = ctk_img
            except Exception as e:
                logger.debug(f"Webcam frame preview loop warning: {e}")
        
        # Schedule check every 800 milliseconds to preserve system resources
        self.root.after(800, self._update_camera_loop)

    def _trigger_spark(self) -> None:
        """Launches a daemon worker to record sound clip or capture toy vision photo."""
        mode: str = self.mode_combo.get()
        self.status_label.configure(text="Status: Recording/Capturing input...", text_color="yellow")
        
        def run() -> None:
            if "Voice" in mode:
                orchestrator: BedtimeStoryOrchestrator = BedtimeStoryOrchestrator(
                    child_name=self.name_entry.get(),
                    child_age=int(self.age_slider.get()),
                    duration_minutes=int(self.duration_slider.get()),
                    mode="Voice"
                )
                transcript: str = orchestrator.voice_handler.record_and_transcribe()
                self.last_voice_transcript = transcript
                self.last_image_bytes = None
                self.root.after(0, lambda: self._update_status(f"Captured Speech: {transcript[:45]}...", "lightgreen"))
            else:
                # Pause live preview briefly during high-res capture to avoid hardware locks
                self.webcam_active = False
                from src.inputs.camera import CameraCapture
                cam_cap: CameraCapture = CameraCapture(0)
                success, jpeg_bytes = cam_cap.capture_jpeg_bytes()
                self.webcam_active = True
                
                if success and jpeg_bytes:
                    self.last_image_bytes = jpeg_bytes
                    self.last_voice_transcript = None
                    self.root.after(0, lambda: self._update_status("Webcam photo captured successfully! 📷", "lightgreen"))
                else:
                    self.root.after(0, lambda: self._update_status("Capture failed.", "red"))

        threading.Thread(target=run, daemon=True).start()

    def _update_status(self, text: str, color: str) -> None:
        """Updates the status status text bar color dynamically."""
        self.status_label.configure(text=f"Status: {text}", text_color=color)

    def _set_btn_state(self, btn: ctk.CTkButton, state: str, active_fg: str, active_text: str) -> None:
        """Convenience utility to enable/disable button widgets cleanly."""
        if state == "disabled":
            btn.configure(state="disabled", fg_color="#2b2b42", text_color="#718093")
        else:
            btn.configure(state="normal", fg_color=active_fg, text_color=active_text)

    def _generate_storybook(self) -> None:
        """Main action command parsing setup values and weaving storybook details on an async worker."""
        name: str = self.name_entry.get().strip()
        if not name:
            self._update_status("Please input a child name.", "red")
            return

        self._update_status("Weaving Bedtime Storybook...", "yellow")
        self._set_btn_state(self.generate_btn, "disabled", "#ff7675", "#131326")

        # Setup inputs
        age: int = int(self.age_slider.get())
        duration: int = int(self.duration_slider.get())
        mode: str = "Image" if "Image" in self.mode_combo.get() else "Voice"
        enable_audio: bool = self.audio_toggle.get()
        enable_images: bool = self.images_toggle.get()

        orchestrator: BedtimeStoryOrchestrator = BedtimeStoryOrchestrator(
            child_name=name,
            child_age=age,
            duration_minutes=duration,
            mode=mode
        )

        def worker() -> None:
            loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Trigger pipeline async
                result: dict[str, Any] = loop.run_until_complete(
                    orchestrator.run_pipeline(
                        "Forest cozy bedroom", 
                        enable_audio, 
                        enable_images,
                        pre_captured_transcript=self.last_voice_transcript,
                        pre_captured_image_bytes=self.last_image_bytes
                    )
                )
                self.root.after(0, lambda: self._on_generation_complete(result))
            except Exception as e:
                logger.error(f"Generation worker failed: {e}")
                self.root.after(0, lambda: self._update_status("Generation failed.", "red"))
                self.root.after(0, lambda: self._set_btn_state(self.generate_btn, "normal", "#ff7675", "#131326"))
            finally:
                loop.close()

        threading.Thread(target=worker, daemon=True).start()

    def _on_generation_complete(self, result: dict[str, Any]) -> None:
        """Callback handling successful generation results."""
        self._set_btn_state(self.generate_btn, "normal", "#ff7675", "#131326")
        self._update_status("Storybook created successfully!", "lightgreen")

        self.current_story_data = result
        self.current_slide_index = 0
        
        # Set controls active
        has_audio: bool = bool(result["audio_paths"])
        self._set_btn_state(self.play_btn, "normal" if has_audio else "disabled", "#00cec9", "#131326")
        self._set_btn_state(self.stop_btn, "normal" if has_audio else "disabled", "#d63031", "#ffffff")
        self._set_btn_state(self.prev_btn, "normal", "#5f27cd", "#ffffff")
        self._set_btn_state(self.next_btn, "normal", "#5f27cd", "#ffffff")

        # Render cover/first slide
        self._render_current_slide()

    def _render_current_slide(self) -> None:
        """Updates main canvas and narrative box elements to match the current slide index."""
        if not self.current_story_data:
            return

        story: dict[str, Any] = self.current_story_data["story"]
        self.story_title_label.configure(text=story["title"])

        # Display image illustration using pathlib.Path
        image_paths: list[Path] = self.current_story_data["image_paths"]
        if image_paths and len(image_paths) > self.current_slide_index:
            img_path: Path = image_paths[self.current_slide_index]
            if img_path.exists() and img_path.stat().st_size > 0:
                try:
                    pil_img: Image.Image = Image.open(img_path)
                    # Resize to fit content canvas
                    resized: Image.Image = pil_img.resize((500, 400))
                    ctk_img: ctk.CTkImage = ctk.CTkImage(light_image=resized, dark_image=resized, size=(500, 400))
                    self.slide_image_label.configure(image=ctk_img, text="")
                    self.slide_image_label.image = ctk_img
                except Exception as e:
                    self.slide_image_label.configure(image="", text=f"Image Error: {e}")
            else:
                self.slide_image_label.configure(image="", text="Placeholder Illustration (Generating)")
        else:
            self.slide_image_label.configure(image="", text="No Illustrations Enabled")

        # Display text content
        self.textbox.delete("0.0", "end")
        if self.current_slide_index == 0:
            self.textbox.insert("0.0", f"Cover Slide: {story['title']}\n\nVisual theme: {story['cover_art_prompt']}")
        else:
            ep: dict[str, Any] = story["episodes"][self.current_slide_index - 1]
            self.textbox.insert("0.0", f"Chapter {ep['chapter']}: {ep['title']}\n\n{ep['narration_text']}")

    def _prev_slide(self) -> None:
        """Triggers page turn transition backward."""
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self._render_current_slide()

    def _next_slide(self) -> None:
        """Triggers page turn transition forward."""
        if self.current_story_data:
            episodes_count: int = len(self.current_story_data["story"]["episodes"])
            if self.current_slide_index < episodes_count:
                self.current_slide_index += 1
                self._render_current_slide()

    def _play_narration(self) -> None:
        """Launches local media player to stream generated TTS audio narration."""
        if not self.current_story_data or "audio_paths" not in self.current_story_data:
            return
        audio_paths: list[Path] = self.current_story_data["audio_paths"]
        if not audio_paths:
            return
            
        audio_path: Path = audio_paths[0]
        if not audio_path.exists():
            self._update_status("Error: Narration file not found.", "red")
            return

        # Normalize backslashes to forward slashes for Windows MCI parser using pathlib
        audio_path_str: str = audio_path.resolve().as_posix()

        self._update_status("Playing bedtime narration track...", "lightgreen")
        logger.info(f"Play narration button clicked. Audio path: {audio_path_str}")
        
        # Stop any currently playing audio first
        self._stop_narration()

        if pygame is not None:
            try:
                logger.info("Loading audio into Pygame mixer...")
                pygame.mixer.music.load(audio_path_str)
                logger.info("Starting Pygame music playback...")
                pygame.mixer.music.play()
                logger.info("Successfully started audio playback.")
                self.audio_playing = True
            except Exception as e:
                logger.error(f"Failed to play audio via Pygame: {e}")
                self._update_status("Error playing narration.", "red")
        else:
            # Fallback to shell player if pygame is missing (e.g. on macOS / Linux)
            if sys.platform == "darwin": # macOS
                try:
                    import subprocess
                    self.audio_process = subprocess.Popen(["afplay", audio_path_str])
                    self.audio_playing = True
                except Exception as e:
                    logger.error(f"Failed to play audio via afplay: {e}")
            else: # Linux or other
                try:
                    import subprocess
                    self.audio_process = subprocess.Popen(["mpg123", audio_path_str], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.audio_playing = True
                except Exception as e:
                    logger.error(f"Failed to play audio via mpg123: {e}")
                    self._update_status("Narrator playback not supported on this platform.", "yellow")

    def _stop_narration(self) -> None:
        """Stops Pygame or subprocess audio playback streams."""
        if pygame is not None:
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.music.unload() # unlocks the file handle
            except Exception as e:
                logger.debug(f"Pygame stop warning: {e}")
        
        if hasattr(self, "audio_process") and self.audio_process:
            try:
                self.audio_process.terminate()
                self.audio_process.wait(timeout=1)
            except Exception as e:
                logger.debug(f"Process stop warning: {e}")
            self.audio_process = None
        
        self.audio_playing = False
        self._update_status("Audio playback stopped.", "yellow")

    def _on_close(self) -> None:
        """Cleans up audio tasks before exiting main program flow."""
        self._stop_narration()
        self.root.destroy()

    def start(self) -> None:
        """Spins up the main CustomTkinter frame layout thread."""
        logger.info("Launching CustomTkinter Bedtime storybook UI window loop.")
        self.root.mainloop()

if __name__ == "__main__":
    app: DreamWeaverApp = DreamWeaverApp()
    app.start()
