from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty

from apelog_app.model.data import LoadAudioFiles
from apelog_app.view.file_chooser import FileChooserPopup

class MainController(BoxLayout):
    audio_files = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loader = LoadAudioFiles()
        self.audio_files = []
        self.dialog = None
        self.bind(audio_files=self.update_audio_list)

    # ---------------------------
    # VIEW CALLBACKS
    # ---------------------------

    def on_kv_post(self, base_widget):
        """Chamado após o carregamento do .kv"""
        self.update_audio_list()

    def on_add_button_pressed(self):
        """Chamado quando o usuário clica em '+'"""
        self.open_directory_selector()

    def on_audio_select(self, filename):
        """Chamado quando o usuário clica num item da lista"""
        print(f"🎵 Áudio selecionado: {filename}")

    # ---------------------------
    # LÓGICA DE CONTROLE
    # ---------------------------

    def open_directory_selector(self):
        """Abre o seletor de diretório (view auxiliar)"""
        popup = FileChooserPopup(controller_callback=self._load_from_directory)
        popup.open()

    def _load_from_directory(self, directory_path):
        """Carrega áudios via loader e atualiza a view"""
        loaded_files = self.loader._load_from_directory(directory_path, audio_files=self.audio_files)
        self.audio_files = loaded_files if loaded_files else ["Erro ao carregar arquivos"]

    # ---------------------------
    # VIEW UPDATE
    # ---------------------------

    def update_audio_list(self, *args):
        rv = self.ids.get("audio_list_view")
        if rv:
            rv.data = [{"text": name} for name in self.audio_files]