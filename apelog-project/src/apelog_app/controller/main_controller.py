from kivy.uix.boxlayout import BoxLayout
from apelog_app.model.data import ExampleModel

class MainController(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = ExampleModel()

    def on_button_press(self):
        result = self.model.do_something()
        print(f"Resultado do model: {result}")
