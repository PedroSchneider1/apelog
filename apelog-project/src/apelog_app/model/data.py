import os
import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use('module://kivy_garden.matplotlib.backend_kivy')
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

class LoadAudioFiles:
    def __init__(self):
        self.audio_extensions = (".mp3", ".wav", ".flac", ".ogg")

    def _load_from_directory(self, directory, audio_files=[]):
        """Retorna lista de caminhos de áudios válidos no diretório."""
        if (not directory or not all(os.path.exists(p) for p in directory)):
            return audio_files
        for path in directory:
            if (os.path.isfile(path) and path.lower().endswith(self.audio_extensions)) and (os.path.basename(path) not in audio_files):
                audio_files.append(os.path.abspath(path)) # Apenas o nome do arquivo
        return audio_files
    
    def _remove_from_app(self, file_name, audio_files):
        """Remove um arquivo de áudio da lista."""
        if file_name in audio_files:
            audio_files.remove(file_name)
        return audio_files
    
    def clear_audio_files(self):
        """Limpa a lista de arquivos de áudio carregados."""
        return []

    def generate_waveform(self, file_path):
        """Gera e retorna um widget Kivy com a waveform do áudio."""
        try:
            # Carrega o áudio
            y, sr = librosa.load(file_path, sr=None)

            # Cria eixo de tempo
            t = np.arange(len(y)) / sr

            # Cria figura
            fig, ax = plt.subplots()
            ax.plot(t, y, color='blue')
            ax.set_xlabel("Tempo (s)")
            ax.set_ylabel("Amplitude")
            ax.set_title(os.path.basename(file_path))
            ax.set_xlim(0, t[-1])

            # # Torna interativo — adiciona callback de clique
            # def onclick(event):
            #     if event.inaxes == ax:
            #         print(f"Marcador em {event.xdata:.2f}s")
            #         ax.axvline(event.xdata, color='red', linestyle='--')
            #         fig.canvas.draw_idle()

            # fig.canvas.mpl_connect('button_press_event', onclick)

            # Retorna o widget compatível com Kivy

            # Retorna widget Kivy
            return FigureCanvasKivyAgg(fig)

        except Exception as e:
            print(f"Erro ao gerar waveform: {e}")
            return None
