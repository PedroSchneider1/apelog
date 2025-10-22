from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from kivymd.uix.menu import MDDropdownMenu
from kivy_matplotlib_widget.uix.graph_widget import MatplotFigure

import numpy as np

import apelog_app.model.data as model
from apelog_app.view.file_chooser import browse_files

class CanvasController():
    """Controlador do canvas de desenho."""
    def __init__(self, main_controller):
        self.main_controller = main_controller
        self.audio_controller = main_controller.audio_controller
        
        self.audio_selected = main_controller.audio_selected
        self.touch_mode = 'cursor'  # 'pan' ou 'cursor'
        self.selected_audio_x_pos = 0.0
        self.figure_widget = None  # guardará a referência para o gráfico atual

    def draw_waveform(self):
        """Desenha a waveform do áudio selecionado"""
        # Gera a figura do waveform
        fig = self.audio_controller.generate_waveform(self.audio_selected)

        # Cria o widget Matplotlib
        figure_widget = MatplotFigure()
        figure_widget.figure = fig
        figure_widget.fast_draw = True

        # Atualiza o container da view
        container = self.main_controller.ids.waveform_container
        container.clear_widgets()
        container.add_widget(figure_widget)

        ax = fig.axes[0]
        figure_widget.register_lines(list(ax.get_lines()))
        self.figure_widget = figure_widget

        # --- CONFIGURAÇÕES INICIAIS ---
        figure_widget.waveform_data = None
        figure_widget.selected_marker = None
        figure_widget.selected_annotation = None
        figure_widget._dragging_bar = False

        # Captura dados do waveform principal
        lines = ax.get_lines()
        waveform_lines = [line for line in lines if line.get_color() == '#ca8c18']
        if waveform_lines:
            line = waveform_lines[0]
            figure_widget.waveform_data = {
                'xdata': line.get_xdata(),
                'ydata': line.get_ydata(),
                'xlim': ax.get_xlim(),
                'ylim': ax.get_ylim()
            }

        # --- BARRA DE POSIÇÃO (tipo DAW) ---
        # Cria a barra vertical inicial no tempo 0
        figure_widget.position_value = 0.0
        figure_widget.position_line = ax.axvline(
            x=0.0,
            color='#d42912',
            linewidth=2.0,
            zorder=10
        )

        # Cria anotação (texto) que mostra o tempo
        figure_widget.position_annotation = ax.annotate(
            "0.000 s",
            xy=(0.0, 1.02),  # um pouco acima do gráfico
            xycoords=('data', 'axes fraction'),
            ha='center',
            va='bottom',
            fontsize=9,
            color='white',
            bbox=dict(boxstyle='round,pad=0.3', fc='#ca8c18', ec='white', alpha=0.9)
        )

        # --- FUNÇÃO AUXILIAR PARA MOVER A BARRA ---
        def update_bar_position(instance, touch):
            """Atualiza posição da barra conforme toque/arraste"""
            if not instance.waveform_data:
                return

            xlim = instance.waveform_data['xlim']

            # Calcula posição relativa do toque dentro do gráfico
            rel_x = (touch.x - instance.x) / instance.width
            self.selected_audio_x_pos = np.clip(xlim[0] + rel_x * (xlim[1] - xlim[0]), xlim[0], xlim[1])

            # Atualiza posição da linha
            instance.position_line.set_xdata([self.selected_audio_x_pos, self.selected_audio_x_pos])
            instance.position_value = self.selected_audio_x_pos

            # Atualiza anotação de tempo
            if hasattr(instance, 'position_annotation'):
                instance.position_annotation.set_position((self.selected_audio_x_pos, 1.02))
                instance.position_annotation.set_text(f"{self.selected_audio_x_pos:.3f} s")

            try:
                self.audio_controller.seek(self.selected_audio_x_pos)
                self.main_controller.ids.play_btn.icon = "play"
                instance.figure.canvas.draw_idle()
            except:
                instance.figure.canvas.draw()
            instance._draw_bitmap()

        # --- EVENTOS DE TOQUE / ARRASTE ---
        def on_touch_down(instance, touch):
            if not instance.collide_point(*touch.pos):
                return False
            if instance.touch_mode != 'cursor':
                return False

            instance._dragging_bar = True
            update_bar_position(instance, touch)
            return True

        def on_touch_move(instance, touch):
            if getattr(instance, '_dragging_bar', False):
                update_bar_position(instance, touch)
                return True
            return False

        def on_touch_up(instance, touch):
            instance._dragging_bar = False
            return True

        # Faz o bind dos eventos
        figure_widget.bind(
            on_touch_down=on_touch_down,
            on_touch_move=on_touch_move,
            on_touch_up=on_touch_up
        )

        figure_widget.touch_mode = self.touch_mode

    def update_position(self, new_time: float):
        """Atualiza visualmente a barra conforme o tempo atual do áudio."""
        if not self.figure_widget or not self.figure_widget.waveform_data:
            return

        xlim = self.figure_widget.waveform_data['xlim']
        self.selected_audio_x_pos = np.clip(new_time, xlim[0], xlim[1])

        # Atualiza linha e anotação
        self.figure_widget.position_line.set_xdata(
            [self.selected_audio_x_pos, self.selected_audio_x_pos]
        )
        self.figure_widget.position_annotation.set_position(
            (self.selected_audio_x_pos, 1.02)
        )
        self.figure_widget.position_annotation.set_text(f"{self.selected_audio_x_pos:.3f} s")

        try:
            self.figure_widget.figure.canvas.draw_idle()
        except:
            self.figure_widget.figure.canvas.draw()
        self.figure_widget._draw_bitmap()

class MainController(BoxLayout):
    """Controlador principal que faz a ponte entre Model e View."""
    audio_files = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
    
        self.audio_files = []
        self.audio_selected = None
        
        self.file_menu = None
        self.tools_menu = None
        self.help_menu = None

        self.audio_controller = model.AudioFilesModel()
        self.canvas_controller = CanvasController(self)

        self.bind(audio_files=self.update_audio_list)

    # ---------------------------
    # VIEW CALLBACKS
    # ---------------------------

    def on_kv_post(self, base_widget):
        """Chamado após o carregamento do .kv"""
        self.update_audio_list()

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

    def on_download_button_pressed(self):
        """Chamado quando o usuário clica em 'download'"""
        print("Download functionality - implementar")
    
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
    # UPLOAD / SELECT AUDIO
    # ---------------------------

    def on_upload_button_pressed(self):
        """Chamado quando o usuário clica em 'upload'"""
        self.open_directory_selector()

    def on_audio_select(self, filename):
        """Chamado quando o usuário clica num item da lista"""
        if filename == self.audio_selected:
            return
        print(f"Selecionado: {filename}")
        self.audio_selected = filename
        self.canvas_controller.audio_selected = filename

        if not filename:
            print("Arquivo não encontrado.")
            return

        self.canvas_controller.draw_waveform()

    def change_touch_mode(self, mode):
        """Muda o modo de interação do gráfico"""
        print(f"Changing touch mode to: {mode}")
        self.canvas_controller.touch_mode = mode
        
        container = self.ids.waveform_container
        if container.children:
            figure_widget = container.children[0]
            figure_widget.touch_mode = mode
            
        # Atualiza o estilo dos botões
        if self.touch_mode == 'cursor':
            self.ids.mode_cursor.text_color = (0.118, 0.314, 0.784, 1)
            self.ids.mode_pan.text_color = (1, 1, 1, 1)
        elif self.touch_mode == 'pan':
            self.ids.mode_pan.text_color = (0.118, 0.314, 0.784, 1)
            self.ids.mode_cursor.text_color = (1, 1, 1, 1)

    # ---------------------------
    # MEDIA BUTTONS
    # ---------------------------

    def on_play_button_pressed(self):
        """Chamado quando o usuário clica em 'play'"""
        try:
            if not self.audio_selected:
                print("Nenhum áudio selecionado.")
                return
            if self.ids.play_btn.icon == "play":
                self.audio_controller.play(self.audio_selected)
                self.ids.play_btn.icon = "pause"
            else:
                self.audio_controller.pause()
                self.canvas_controller.update_position(self.audio_controller.current_time)
                self.ids.play_btn.icon = "play"
        except Exception as e:
            print(f"Erro ao reproduzir áudio: {e}")
            self.ids.play_btn.icon = "play"
            return
        
    def on_previous_button_pressed(self):
        """Chamado quando o usuário clica em 'previous'"""
        print("Previous button pressed - implementar")
    
    def on_next_button_pressed(self):
        """Chamado quando o usuário clica em 'next'"""
        print("Next button pressed - implementar")

    # ---------------------------
    # DIRECTORY SELECTOR
    # ---------------------------

    def open_directory_selector(self):
        """Abre o seletor de diretório (view auxiliar)"""
        browse_files(self._load_from_directory)

    def _load_from_directory(self, filenames):
        """Carrega áudios via audio_controller e atualiza a view"""
        loaded_files = self.audio_controller._audio_loader(filenames, audio_files=self.audio_files)
        self.audio_files = loaded_files

    # ---------------------------
    # VIEW UPDATE
    # ---------------------------

    def update_audio_list(self, *args):
        """Atualiza a lista de áudios na view"""
        rv = self.ids.get("audio_list_view")
        if rv:
            rv.data = [{"text": f} for f in self.audio_files]