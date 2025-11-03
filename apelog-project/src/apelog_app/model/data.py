# ---------------------------
# IMPORTS
# ---------------------------

import os

import numpy as np
import time
import threading
import soundfile as sf
import sounddevice as sd

import matplotlib
matplotlib.use('module://kivy_garden.matplotlib.backend_kivy')
import matplotlib.pyplot as plt

from kivy.utils import platform
from kivy.config import Config

# avoid conflict between mouse provider and touch (very important with touch device)
# no need for android platform
if platform != 'android':
    Config.set('input', 'mouse', 'mouse,disable_on_activity')
else:
    #for android, we remove mouse input to not get extra touch 
    Config.remove_option('input', 'mouse')

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
    'path.simplify': True,
    'path.simplify_threshold': 1.0,
    'agg.path.chunksize': 1000
})
matplotlib.font_manager._load_fontmanager(try_read_cache=True)

# ---------------------------
# AUDIO MODEL
# ---------------------------

class MediaModel:
    def __init__(self):
        self.y = None
        self.sr = None
        self.ts = None
        self.duration = 0.0

    def _librosa_load(self, file_path):
        """Carrega o arquivo de áudio usando librosa."""
        try:
            self.y, self.sr = sf.read(file_path)
            self.ts = np.arange(len(self.y)) / self.sr
            self.duration = len(self.y) / self.sr
            return True
        except Exception as e:
            print(f"Erro ao carregar áudio: {e}")
            return False

    def segment(self, start, duration):
        """Retorna um trecho do áudio em um intervalo de tempo específico."""
        start_sample = int(start * self.sr)
        end_sample = int((start + duration) * self.sr)
        end_sample = min(end_sample, len(self.y))
        
        seg = type("Segment", (), {})()  # objeto dinâmico simples
        seg.ys = self.y[start_sample:end_sample]
        seg.ts = np.arange(len(seg.ys)) / self.sr + start
        seg.framerate = self.sr
        seg.duration = len(seg.ys) / self.sr
        return seg

    def _estimate_fundamental_freq(self, peaks_points):
        """Estima a frequência fundamental usando autocorrelação em segmentos ao redor dos picos locais."""
        frequencies = []
        for peak in peaks_points:
            # Extract a segment around the peak (0.2s before and 0.2s after)
            start = max(0, peak[0] - 0.2)
            duration = 0.4
            if start + duration > self.duration:
                duration = self.duration - start

            segment = self.segment(start=start, duration=duration)
            if len(segment.ys) < 300:  # muito curto
                frequencies.append(0)
                continue

            # Compute autocorrelation
            corrs = np.correlate(segment.ys, segment.ys, mode='full')
            corrs = corrs[len(corrs)//2:]
            corrs /= np.max(np.abs(corrs))

            # Find first local maximum in a reasonable lag range
            lag = np.argmax(corrs[150:250]) + 150
            period = lag / segment.framerate
            frequency = 1 / period if period > 0 else 0
            frequencies.append(frequency)

        return frequencies

    def _auto_generate_markers(self, interval=5.0):
        """Gera marcadores automáticos a partir de intervalos de tempo fixos."""
        total_duration = self.duration
        num_slices = max(1, int(total_duration / interval))
        
        local_maxima_points = []

        # Thresholds
        std_dev = np.std(self.y)
        noise_factor = 15
        freq_threshold = 90
        amp_threshold = 0.05 + (std_dev * noise_factor)

        # Process each slice
        for i in range(num_slices):
            start_time = i * interval
            duration = min(interval, total_duration - start_time)
            segment = self.segment(start=start_time, duration=duration)

            # Find local max
            if len(segment.ys) == 0:
                continue

            result = np.argmax(segment.ys)
            if segment.ys[result] > amp_threshold:
                local_maxima_points.append((segment.ts[result], segment.ys[result]))

        # Filter by fundamental frequency
        frequencies = self._estimate_fundamental_freq(local_maxima_points)
        filtered_points = [
            point for i, point in enumerate(local_maxima_points)
            if frequencies[i] >= freq_threshold
        ]

        return filtered_points
        

class AudioFilesModel(MediaModel):
    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.is_paused = False
        self.play_start_time = 0.0
        self.current_time = 0.0
        self.start_sample = 0
        self.thread = None
        self.audio_extensions = (".mp3", ".wav", ".flac", ".ogg")
        self.fig = None
        self.ax = None
        self.markers = {}  # {file_path: [(time, amplitude), ...]}
        self.audio_analysis = False # Habilita/desabilita análise automática de marcadores

    def _playback_loop(self):
        """Thread interna para reprodução assíncrona."""
        self.start_sample = int(self.current_time * self.sr)
        self.play_start_time = time.time()  # tracking para o pause

        sd.play(self.y[self.start_sample:], self.sr, blocking=False)

        # Espera até o áudio terminar ou ser pausado
        while self.is_playing and not self.is_paused and sd.get_stream() is not None and sd.get_stream().active:
            time.sleep(0.1)

        # Quando o áudio termina
        if self.is_playing and not self.is_paused:
            self.is_playing = False
            self.current_time = 0.0
        print("Reprodução concluída.")

    # ---------------------------
    # PLAYBACK CONTROLS
    # ---------------------------

    def play(self, file_path=None):
        """Inicia a reprodução do áudio."""
        if file_path:
            self._librosa_load(file_path)

        if self.y is None or self.sr is None:
            print("Nenhum áudio carregado.")
            return

        if self.is_paused:
            print("Retomando reprodução...")
            self.is_paused = False
        else:
            print("Iniciando reprodução...")
            self.is_playing = True
            self.is_paused = False

        self.thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.thread.start()

    def pause(self):
        """Pausa a reprodução do áudio."""
        if not self.is_playing:
            print("Nada está sendo reproduzido.")
            return

        if self.is_paused:
            print("O áudio já está pausado.")
            return

        self.is_paused = True
        sd.stop()

        # Computa o tempo atual
        elapsed = time.time() - self.play_start_time
        self.current_time += elapsed
        print(f"Áudio pausado em {self.current_time:.2f} segundos.")

    def seek(self, time_position=0):
        """Seleciona uma posição específica no áudio e toca a partir."""
        if self.y is None or self.sr is None: # verifica se áudio está carregado
            return
        if time_position < 0 or time_position > self.duration:
            print("Posição inválida.")
            return
        self.current_time = time_position
        sd.stop()
        self.is_playing = False
        self.is_paused = False

    # ---------------------------
    # AUDIO FILE MANAGEMENT
    # ---------------------------

    def _audio_loader(self, directory, audio_files=[]):
        """Retorna lista de caminhos de áudios válidos no diretório."""
        if (not directory or not all(os.path.exists(p) for p in directory)):
            return audio_files
        for path in directory:
            if (os.path.isfile(path) and path.lower().endswith(self.audio_extensions)) and (os.path.abspath(path) not in audio_files):
                audio_files.append(os.path.abspath(path))
                
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

    def init_waveform_fig(self):
        """Cria a figura e o fig uma única vez."""
        if self.fig is None:
            self.fig, self.ax = plt.subplots(figsize=(10, 3), dpi=80)
            self.fig.patch.set_facecolor('#191919')
            self.ax.set_facecolor('#191919')
            self.ax.set_autoscale_on(False)
            self.ax.autoscale(enable=False)
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)

    def generate_waveform(self, file_path):
        """Gera e retorna a figura Matplotlib com marcadores automáticos."""
        if self.fig is None or self.ax is None:
            self.init_waveform_fig()

        try:
            # Carrega o áudio completo para análise
            self._librosa_load(file_path)

            # Reduz resolução só para exibir mais rápido
            y = self.y
            sr = self.sr
            MAX_POINTS = len(y) if len(y) < 100000 else 100000
            if len(y) > MAX_POINTS:
                downsample_factor = len(y) // MAX_POINTS
                y = y[::downsample_factor]
                sr_effective = sr / downsample_factor
            else:
                sr_effective = sr
            
            t = np.arange(len(y)) / sr_effective

            # Limpa e desenha waveform
            self.ax.clear()
            self.ax.set_facecolor('#111')

            for yline in [-1, -0.5, 0, 0.5, 1]:
                self.ax.axhline(y=yline, color='#333', linestyle='-', linewidth=0.8, alpha=0.5)
            
            self.ax.plot(t, y, color="#ca8c18", linewidth=0.8, antialiased=True, rasterized=True)

            self.ax.set_xlim(0, t[-1])
            self.ax.set_ylim(-1, 1)
            self.ax.set_title(os.path.basename(file_path), color='white', fontsize=10, pad=6)
            self.ax.tick_params(axis='x', colors='gray', labelsize=8)
            self.ax.tick_params(axis='y', colors='gray', labelsize=8)
            self.fig.tight_layout(pad=0.5)

            if self.audio_analysis:
                # Armazena e reutiliza marcadores
                if file_path not in self.markers:
                    markers = self._auto_generate_markers(interval=5.0)
                    self.markers[file_path] = markers  # guarda no dicionário
                    print(f"{len(markers)} marcadores detectados e armazenados.")
                else:
                    markers = self.markers[file_path]
                    print(f"Marcadores já existentes para {os.path.basename(file_path)} ({len(markers)}).")

                # Desenha marcadores na waveform
                for (time, amp) in markers:
                    self.ax.axvline(
                        x=time, color="#34f1ff", linestyle='--', linewidth=1.2, alpha=0.8
                    )

            return self.fig

        except Exception as e:
            print(f"Erro ao gerar waveform: {e}")
            return None

    def clear_markers(self, file_path=None):
        """Remove marcadores de um arquivo específico ou de todos."""
        if file_path:
            self.markers.pop(file_path, None)
        else:
            self.markers.clear()
