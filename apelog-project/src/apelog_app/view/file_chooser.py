from tkinter import filedialog as fd
from pathlib import Path

def browse_files(controller_callback):
    """Abre um diálogo para seleção de múltiplos arquivos de áudio."""
    filetypes = (
        ('Audio files', '*.mp3 *.wav *.flac *.ogg'),
        ('All files', '*.*')
    )
    filenames = fd.askopenfilenames(
        title='Selecione os arquivos de áudio',
        initialdir=str(Path.home()),
        filetypes=filetypes
    )
    if filenames:
        controller_callback(filenames)
