import os
from pathlib import Path

class LoadAudioFiles:
    def __init__(self):
        self.audio_extensions = (".mp3", ".wav", ".flac", ".ogg")

    def _load_from_directory(self, directory, audio_files=None):
        """Retorna lista de caminhos de áudios válidos no diretório."""
        if not directory or not all(os.path.exists(p) for p in directory):
            return []
        for path in directory:
            if os.path.isfile(path) and path.lower().endswith(self.audio_extensions):
                audio_files.append(os.path.basename(path)) # Apenas o nome do arquivo
        return audio_files