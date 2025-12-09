from pydub import AudioSegment
import os

class AudioProcessor:
    def __init__(self, audio_file):
        self.audio_file = audio_file
        self.audio_segment = None

    def load_audio(self):
        if os.path.exists(self.audio_file):
            self.audio_segment = AudioSegment.from_file(self.audio_file)
        else:
            raise FileNotFoundError(f"Audio file {self.audio_file} not found.")

    def play_audio(self):
        if self.audio_segment is not None:
            play(self.audio_segment)
        else:
            raise ValueError("Audio segment is not loaded. Please load an audio file first.")

    def convert_format(self, output_format):
        if self.audio_segment is not None:
            base = os.path.splitext(self.audio_file)[0]
            output_file = f"{base}.{output_format}"
            self.audio_segment.export(output_file, format=output_format)
            return output_file
        else:
            raise ValueError("Audio segment is not loaded. Please load an audio file first.")

    def get_duration(self):
        if self.audio_segment is not None:
            return len(self.audio_segment) / 1000  # duration in seconds
        else:
            raise ValueError("Audio segment is not loaded. Please load an audio file first.")