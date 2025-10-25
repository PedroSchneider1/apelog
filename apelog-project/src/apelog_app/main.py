from kivy.core.window import Window
Window.maximize()

from kivymd.app import MDApp
from kivy.lang import Builder

from pathlib import Path
import setproctitle

from apelog_app.controller.main_controller import MainController

class MyApp(MDApp):
    def build(self):
        window_icon = Path(__file__).parent.parent / "assets" / "apelog-logo2.1.png"
        kv_path = Path(__file__).parent / "view" / "app.kv"
        
        setproctitle.setproctitle("Apelog") # Muda o nome do processo no sistema
        
        self.icon = str(window_icon)
        self.title = "Apelog"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        Builder.load_file(str(kv_path))
        return MainController()  # Controller faz ponte entre model e view

def main():
    MyApp().run()

if __name__ == "__main__":
    main()