from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from kivymd.uix.menu import MDDropdownMenu

from apelog_app.model.data import LoadAudioFiles
from apelog_app.view.file_chooser import FileChooserPopup

import os

class MainController(BoxLayout):
    audio_files = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.loader = LoadAudioFiles()
        self.audio_files = []
        self.file_menu = None
        self.tools_menu = None
        self.help_menu = None
        self.bind(audio_files=self.update_audio_list)

    # ---------------------------
    # VIEW CALLBACKS
    # ---------------------------

    def on_kv_post(self, base_widget):
        """Chamado após o carregamento do .kv"""
        self.update_audio_list()

    def on_upload_button_pressed(self):
        """Chamado quando o usuário clica em 'upload'"""
        self.open_directory_selector()

    def on_audio_select(self, filename):
        """Chamado quando o usuário clica num item da lista"""
        print(f"Selecionado: {filename}")

        if not filename:
            print("Arquivo não encontrado.")
            return

        # Gera o espectrograma via model
        spectrogram_widget = self.loader.generate_waveform(filename)
        if not spectrogram_widget:
            print("Falha ao gerar espectrograma.")
            return

        # Atualiza o container na view
        container = self.ids.spectrogram_container
        container.clear_widgets()
        container.add_widget(spectrogram_widget)

    # ---------------------------
    # MENU METHODS
    # ---------------------------

    def open_file_menu(self):
        """Abre o menu File"""
        menu_items = [
            {
                "viewclass": "OneLineIconListItem",
                "icon": "upload",
                "text": "Upload Audio",
                "on_release": lambda x="upload": self.on_menu_item_selected(x),
            },
            {
                "viewclass": "OneLineIconListItem", 
                "icon": "download",
                "text": "Download Audio",
                "on_release": lambda x="download": self.on_menu_item_selected(x),
            },
        ]
        
        self.file_menu = MDDropdownMenu(
            caller=self.ids.file_menu_button,
            items=menu_items,
            width_mult=4,
        )
        self.file_menu.open()
    
    def open_tools_menu(self):
        """Abre o menu Tools"""
        menu_items = [
            {
                "viewclass": "OneLineIconListItem",
                "icon": "chart-bar",
                "text": "Audio Analysis",
                "on_release": lambda x="analysis": self.on_menu_item_selected(x),
            },
            {
                "viewclass": "OneLineIconListItem",
                "icon": "playlist-check", 
                "text": "Batch Processing",
                "on_release": lambda x="batch": self.on_menu_item_selected(x),
            },
        ]
        
        self.tools_menu = MDDropdownMenu(
            caller=self.ids.tools_menu_button,
            items=menu_items,
            width_mult=4,
        )
        self.tools_menu.open()
    
    def open_help_menu(self):
        """Abre o menu Help"""
        menu_items = [
            {
                "viewclass": "OneLineIconListItem",
                "icon": "help-circle",
                "text": "Documentation", 
                "on_release": lambda x="docs": self.on_menu_item_selected(x),
            },
            {
                "viewclass": "OneLineIconListItem",
                "icon": "information",
                "text": "About",
                "on_release": lambda x="about": self.on_menu_item_selected(x),
            },
        ]
        
        self.help_menu = MDDropdownMenu(
            caller=self.ids.help_menu_button,
            items=menu_items,
            width_mult=4,
        )
        self.help_menu.open()
    
    def on_menu_item_selected(self, action):
        """Processa a seleção de itens do menu"""
        # Fecha todos os menus
        if self.file_menu:
            self.file_menu.dismiss()
        if self.tools_menu:
            self.tools_menu.dismiss() 
        if self.help_menu:
            self.help_menu.dismiss()
        
        # Executa a ação
        if action == "upload":
            self.open_directory_selector()
        elif action == "download":
            self.on_download_button_pressed()
        elif action == "analysis":
            print("Audio analysis functionality")
        elif action == "batch":
            print("Batch processing functionality")
        elif action == "docs":
            print("Open documentation")
        elif action == "about":
            print("Show about dialog")

    # ---------------------------
    # LÓGICA DE CONTROLE
    # ---------------------------

    def on_download_button_pressed(self):
        """Chamado quando o usuário clica em 'download'"""
        print("Download functionality - implementar")

    def open_directory_selector(self):
        """Abre o seletor de diretório (view auxiliar)"""
        popup = FileChooserPopup(controller_callback=self._load_from_directory)
        popup.open()

    def _load_from_directory(self, directory_path):
        """Carrega áudios via loader e atualiza a view"""
        loaded_files = self.loader._load_from_directory(directory_path, audio_files=self.audio_files)
        self.audio_files = loaded_files

    # ---------------------------
    # VIEW UPDATE
    # ---------------------------

    def update_audio_list(self, *args):
        rv = self.ids.get("audio_list_view")
        if rv:
            rv.data = [{"text": name} for name in self.audio_files]