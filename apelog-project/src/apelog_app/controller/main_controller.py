from kivy.uix.boxlayout import BoxLayout
from apelog_app.model.data import ExampleModel

class MainController(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = ExampleModel()

    def on_button_press(self):
        result = self.model.do_something()
        print(f"Resultado do model: {result}")


# pra implementar o controller de áudios, apenas uma sugestao:
'''
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty

class MainController(BoxLayout):
    audio_files = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Simulação de áudios — depois você pode preencher dinamicamente
        self.audio_files = ["voz1.wav", "voz2.wav", "musica.mp3", "teste.ogg"]
        self.bind(audio_files=self.update_audio_list)

    def on_kv_post(self, base_widget):
        # Atualiza lista ao carregar a interface
        self.update_audio_list()

    def update_audio_list(self, *args):
        """Atualiza o RecycleView com os nomes dos áudios"""
        rv = self.ids.get("audio_list_view")
        if rv:
            rv.data = [{"text": name} for name in self.audio_files]

    def on_audio_select(self, filename):
        """Chamado quando o usuário clica num áudio"""
        print(f"🎵 Áudio selecionado: {filename}")


'''