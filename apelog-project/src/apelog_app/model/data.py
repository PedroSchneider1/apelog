import os

import numpy as np
import librosa
import sounddevice as sd

import matplotlib
matplotlib.use('module://kivy_garden.matplotlib.backend_kivy')
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING) # Suprime warnings do matplotlib

# Configurações globais do matplotlib para evitar score das fontes
matplotlib.use("module://kivy_garden.matplotlib.backend_kivy")  # Usa o backend certo
matplotlib.rcParams.update({
    'font.family': 'DejaVu Sans',
    'text.usetex': False,
    'figure.autolayout': True,
    'axes.unicode_minus': False,
    'animation.embed_limit': 0,   # Não gera base64 temporário
    'interactive': False,
})
matplotlib.font_manager._load_fontmanager(try_read_cache=True)

class MediaController:
    def __init__(self):
        self.y = None
        self.sr = None
        self.duration = 0.0

    def _librosa_load(self, file_path):
        """Carrega o arquivo de áudio usando librosa."""
        try:
            self.y, self.sr = librosa.load(file_path, sr=None)
            self.duration = librosa.get_duration(y=self.y, sr=self.sr)
            return True
        except Exception as e:
            print(f"Erro ao carregar áudio: {e}")
            return False

class AudioFilesController(MediaController):
    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.current_time = 0.0
        self.audio_extensions = (".mp3", ".wav", ".flac", ".ogg")
        self.fig = None
        self.ax = None
        self.canvas = None

    # ---------------------------
    # PLAYBACK CONTROLS
    # ---------------------------

    def play(self, file_path):
        """Inicia a reprodução do áudio."""
        self._librosa_load(file_path)
        if not os.path.exists(file_path) or (self.y is None or self.sr is None):
            print("Erro ao carregar arquivo.")
            return
        self.is_playing = True
        sd.play(self.y, self.sr, blocking=False) # Blocking permite reprodução assíncrona


    def pause(self):
        """Pausa a reprodução do áudio."""
        if self.is_playing:
            self.is_playing = False
            sd.stop()
        else:
            print("O áudio já está pausado.")

    # def seek(self, time_position):
    #     """Busca para uma posição específica no áudio."""
    #     if 0 <= time_position <= self.duration:
    #         self.current_time = time_position
    #         print(f"Buscando para: {time_position} segundos.")
    #     else:
    #         print("Posição inválida.")

    # ---------------------------
    # AUDIO FILE MANAGEMENT
    # ---------------------------

    def _audio_loader(self, directory, audio_files=[]):
        """Retorna lista de caminhos de áudios válidos no diretório."""
        if (not directory or not all(os.path.exists(p) for p in directory)):
            return audio_files
        for path in directory:
            if (os.path.isfile(path) and path.lower().endswith(self.audio_extensions)) and (os.path.basename(path) not in audio_files):
                audio_files.append(os.path.abspath(path)) # Apenas o nome do arquivo
                
        self.generate_waveform(audio_files[0])  # Gera a waveform do primeiro arquivo (cache para performance)
        return audio_files
    
    def _remove_from_app(self, file_name, audio_files):
        """Remove um arquivo de áudio da lista."""
        if file_name in audio_files:
            audio_files.remove(file_name)
        return audio_files
    
    def clear_audio_files(self):
        """Limpa a lista de arquivos de áudio carregados."""
        return []
    
    # ---------------------------
    # WAVEFORM GENERATION
    # ---------------------------

    def init_waveform_canvas(self):
        """Cria a figura e o canvas uma única vez."""
        if self.fig is None:
            self.fig, self.ax = plt.subplots(figsize=(10, 3), dpi=150)
            self.fig.patch.set_facecolor('#191919')
            self.ax.set_facecolor('#191919')
            self.ax.set_autoscale_on(False)
            self.ax.autoscale(enable=False)
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)

            self.canvas = FigureCanvasKivyAgg(self.fig)

        return self.canvas

    def generate_waveform(self, file_path):
        """Atualiza a waveform do áudio dentro da mesma figura."""
        if self.fig is None or self.ax is None:
            self.init_waveform_canvas()

        try:
            y, sr = librosa.load(file_path, sr=None)
            t = np.arange(len(y)) / sr

            self.ax.clear()

            # Fundo e linhas horizontais (estilo Audacity)
            self.ax.set_facecolor('#111')
            for yline in [-1, -0.5, 0, 0.5, 1]:
                self.ax.axhline(y=yline, color='#333', linestyle='-', linewidth=0.8, alpha=0.5)

            self.ax.plot(t, y, color="#ca8c18", linewidth=0.8, antialiased=True)
            self.ax.set_xlim(0, t[-1])
            self.ax.set_ylim(-1, 1)
            self.ax.set_title(os.path.basename(file_path), color='white', fontsize=10, pad=6)
            self.ax.tick_params(axis='x', colors='gray', labelsize=8)
            self.ax.tick_params(axis='y', colors='gray', labelsize=8)
            self.ax.set_autoscale_on(False)

            self.fig.tight_layout(pad=0.5)
            self.canvas.draw_idle()

            return self.canvas

        except Exception as e:
            print(f"Erro ao gerar waveform: {e}")
            return None