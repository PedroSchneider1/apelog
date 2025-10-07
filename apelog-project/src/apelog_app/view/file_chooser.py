from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivymd.uix.button import MDFlatButton
from pathlib import Path

class FileChooserPopup(ModalView):
    def __init__(self, controller_callback, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.8, 0.8)  # redimensionável com a janela principal
        self.auto_dismiss = False

        box = BoxLayout(orientation="vertical", spacing=10, padding=10)

        self.chooser = FileChooserIconView(
            path=str(Path.home()),
            filters=["*.mp3", "*.wav", "*.flac", "*.ogg"],
            size_hint=(1, 1),
            multiselect=True
        )

        buttons = BoxLayout(size_hint_y=None, height="48dp", spacing=10)
        buttons.add_widget(MDFlatButton(text="Cancelar", on_release=lambda x: self.dismiss()))
        buttons.add_widget(MDFlatButton(
            text="Selecionar",
            on_release=lambda x: (
                self.dismiss(),
                controller_callback(self.chooser.selection)
            )
        ))

        box.add_widget(self.chooser)
        box.add_widget(buttons)
        self.add_widget(box)