from kivy.app import App
from kivymd.app import MDApp
from kivy.lang import Builder
from pathlib import Path

from apelog_app.controller.main_controller import MainController

class MyApp(MDApp):
    def build(self):
        self.title = "Apelog"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        kv_path = Path(__file__).parent / "view" / "app.kv"
        Builder.load_file(str(kv_path))
        return MainController()  # controller faz ponte entre model e view

def main():
    MyApp().run()

if __name__ == "__main__":
    main()