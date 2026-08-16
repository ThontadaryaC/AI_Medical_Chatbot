import gtts
import threading
import time
import logging
import os
import tempfile
import pygame
from typing import Optional

class TTSManager:
    """Text-to-Speech manager using gTTS and pygame"""

    def __init__(self):
        self.lock = threading.Lock()
        self.is_available_flag = True
        self.logger = logging.getLogger(__name__)
        self.temp_files = []  # Keep track of temp files for cleanup
        # Initialize pygame mixer
        try:
            pygame.mixer.init()
        except Exception as e:
            self.logger.error(f"Failed to initialize pygame mixer: {str(e)}")
            self.is_available_flag = False

    def speak(self, text: str) -> bool:
        """Speak the given text using gTTS and pygame"""
        if not text or not text.strip():
            self.logger.warning("Empty text provided to TTS")
            return False

        if not self.is_available_flag:
            self.logger.error("TTS not available")
            return False

        try:
            with self.lock:
                # Create a temporary file for the audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_path = temp_file.name
                    self.temp_files.append(temp_path)

                # Generate speech using gTTS
                tts = gtts.gTTS(text.strip(), lang='en', slow=False)
                tts.save(temp_path)

                # Play the audio in a separate thread to avoid blocking
                play_thread = threading.Thread(target=self._play_audio, args=(temp_path,))
                play_thread.daemon = True
                play_thread.start()

                self.logger.info(f"Successfully initiated speech for text: {text[:50]}...")
                return True

        except Exception as e:
            self.logger.error(f"Error during TTS: {str(e)}")
            return False

    def _play_audio(self, file_path: str):
        """Play the audio file and clean up"""
        try:
            # Load and play the audio
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error playing audio: {str(e)}")
        finally:
            # Clean up the temp file
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                if file_path in self.temp_files:
                    self.temp_files.remove(file_path)
            except Exception as e:
                self.logger.error(f"Error cleaning up temp file: {str(e)}")

    def stop(self):
        """Stop current speech and cleanup all temp files"""
        try:
            with self.lock:
                pygame.mixer.music.stop()
                for temp_file in self.temp_files[:]:
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                        self.temp_files.remove(temp_file)
                    except Exception as e:
                        self.logger.error(f"Error cleaning up temp file during stop: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error stopping TTS: {str(e)}")

    def is_available(self) -> bool:
        """Check if TTS is available"""
        return self.is_available_flag

# Global TTS manager instance
tts_manager = TTSManager()

def speak_text(text: str) -> bool:
    """Convenience function to speak text"""
    return tts_manager.speak(text)

def speak_text_async(text: str) -> bool:
    """Speak text asynchronously (same as speak_text since it's already async)"""
    return speak_text(text)

def cleanup_tts():
    """Cleanup TTS resources"""
    tts_manager.stop()
