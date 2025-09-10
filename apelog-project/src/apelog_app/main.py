from kivy.app import App
from kivy.lang import Builder
from pathlib import Path

from apelog_app.controller.main_controller import MainController

class MyApp(App):
    def build(self):
        kv_path = Path(__file__).parent / "view" / "app.kv"
        Builder.load_file(str(kv_path))
        return MainController()  # controller faz ponte entre model e view

def main():
    MyApp().run()

if __name__ == "__main__":
    main()