from kivy.metrics import dp
from kivy.clock import Clock

from kivy.properties import ListProperty
from kivy_matplotlib_widget.uix.graph_widget import MatplotFigure
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton

import numpy as np
import os

import apelog_app.model.data as model
from apelog_app.view.file_chooser import browse_files
from tkinter import Tk, Listbox, Toplevel, Button

# TODO: consertar bugs ao remover, exportar csv

class TableController:
    """Controlador da tabela de eventos."""
    def __init__(self, main_controller):
        self.main_controller = main_controller
        self.dialog = None
        self.data_tables = None
        self.events = []
        self.selected_row_index = None

    def create_table(self):
        """Cria ou atualiza a tabela de eventos na view."""
        self.data_tables = MDDataTable(
            size_hint=(0.8, 0.8),
            use_pagination=True,
            check=False,
            column_data=[
                ("No.", dp(20)),
                ("Timestamp", dp(30)),
                ("Title", dp(50)),
                ("Description", dp(60)),
                ("Audio name", dp(50)),
            ],
        )

        self.data_tables.row_data = self.events

        # Vincula evento de clique na linha
        self.data_tables.bind(on_row_press=self.on_row_press)

        container = self.main_controller.ids.events_table_container
        container.clear_widgets()
        container.add_widget(self.data_tables)
        print('Tabela de eventos criada.')

    def update_events(self, events, audio_name="audio.mp3"):
        """Atualiza os eventos na tabela."""
        ts = events[-1]
        title = f"Event at {ts:.3f}s"
        desc = "Marked manually"
        name = os.path.basename(audio_name)
        self.events.append((f"{ts:.3f}s", title, desc, name))
            
        print(f'Atualizando eventos: {self.events}')

    def update_table(self):
        """Atualiza visualmente a tabela com os eventos atuais."""
        if self.data_tables:
            self.data_tables.row_data = [
                (i+1, t[0], t[1], t[2], t[3])
                for i, t in enumerate(self.events)
            ]
            print('Eventos na tabela atualizados.')

    def add_row(self):
        """Adiciona uma nova linha à tabela."""
        self.data_tables.add_row((len(self.events),
                                  self.events[-1][0],
                                  self.events[-1][1],
                                  self.events[-1][2],
                                  self.events[-1][3]))
        print(f'Linha adicionada: {self.events[-1]}')

    def remove_selected(self):
        """Remove os eventos selecionados na tabela e retorna os índices dos selecionados."""
        if not self.data_tables:
            return []

        # Cria a janela principal do Tkinter
        root = Tk()
        root.withdraw()  # Oculta a janela principal

        # Cria um diálogo de nível superior
        dialog = Toplevel(root)
        dialog.title("Lista de Eventos")

        # Cria uma Listbox para exibir os índices e timestamps (multiselecionável)
        listbox = Listbox(dialog, width=50, height=20, selectmode="multiple")
        for i, row in enumerate(self.data_tables.row_data):
            listbox.insert("end", f"({i+1:02}) - Title: {row[2]} | Timestamp: {row[1]}")
        listbox.pack(padx=10, pady=10)

        selected_indices = []

        # Função para capturar os índices selecionados e fechar o diálogo
        def on_remove():
            nonlocal selected_indices
            selected_indices = [int(idx) for idx in listbox.curselection()]
            root.destroy()

        # Botão para remover os eventos selecionados
        remove_button = Button(dialog, text="Remover Selecionados", command=on_remove)
        remove_button.pack(pady=5)

        # Botão para fechar o diálogo sem remover
        close_button = Button(dialog, text="Fechar", command=lambda: root.destroy())
        close_button.pack(pady=5)

        # Configura o evento de fechamento da janela nativa
        dialog.protocol("WM_DELETE_WINDOW", lambda: root.destroy())

        # Mantém o diálogo aberto
        root.mainloop()

        # Remove os eventos selecionados da tabela e da lista de eventos
        for i in sorted(selected_indices, reverse=True):
            del self.events[i]

        return selected_indices

    def on_row_press(self, instance_table, instance_row):
        """Chamado ao clicar numa linha da tabela."""
        try:
            num_cols = len(self.data_tables.column_data)
            cell_index = instance_row.index
            row_index = cell_index // num_cols  # converte para índice de linha real

            print(f"Linha clicada: {row_index} (coluna {cell_index % num_cols})")
            self.selected_row_index = row_index

            if cell_index % num_cols != 0:
                row_data = self.data_tables.row_data[row_index]
                self.open_edit_dialog(row_data)

        except Exception as e:
            print(f"Erro ao abrir diálogo de edição: {e}")
            return

    def open_edit_dialog(self, row_data):
        """Abre o diálogo de edição da linha."""
        no, timestamp, title, desc, file = row_data

        self.dialog = MDDialog(
            title=f"Editar evento #{no}",
            type="custom",
            content_cls=self._create_dialog_content(title, desc),
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda *x: self.dialog.dismiss()),
                MDFlatButton(text="Salvar", on_release=self.save_edit),
            ],
        )
        self.dialog.open()

    def save_edit(self, *args):
        """Salva a edição da linha e atualiza a tabela."""
        new_title = self.title_field.text
        new_desc = self.desc_field.text

        index = self.selected_row_index
        no, timestamp, _, _, file = self.data_tables.row_data[index]
        self.data_tables.row_data[index] = (no, timestamp, new_title, new_desc, file)
        self.events[index] = (no, timestamp, new_title, new_desc, file)

        # Atualiza visualmente a tabela
        self.data_tables.update_row_data(
            self.data_tables,
            self.data_tables.row_data
        )

        print(f"Linha {no} atualizada: {new_title}, {new_desc}")

        self.dialog.dismiss()

    def _create_dialog_content(self, title, desc):
        """Cria o conteúdo do diálogo."""
        layout = MDBoxLayout(orientation="vertical", spacing=10, adaptive_height=True)
        self.title_field = MDTextField(text=title, hint_text="Título")
        self.desc_field = MDTextField(text=desc, hint_text="Descrição")
        layout.add_widget(self.title_field)
        layout.add_widget(self.desc_field)
        return layout

class CanvasController():
    """Controlador do canvas de desenho."""
    def __init__(self, main_controller):
        self.main_controller = main_controller
        self.audio_controller = main_controller.audio_controller
        
        self.audio_selected = main_controller.audio_selected
        self.touch_mode = 'cursor'
        self.selected_audio_x_pos = 0.0
        self.markers_pos = []  # lista de marcadores criados
        self.figure_widget = None  # guardará a referência para o gráfico atual

    def draw_waveform(self):
        """Desenha a waveform do áudio selecionado"""
        # {file_path: [(time, amplitude), ...]}
        for m in self.main_controller.audio_controller.markers.get(self.audio_selected, []):
            self.main_controller.table_controller.update_events([m[0]], self.audio_selected)
        self.main_controller.table_controller.update_table()

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
            bbox=dict(boxstyle='round,pad=0.3', fc='#ca8c18', ec='white', alpha=0.95)
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

    def create_marker(self, time_position: float):
        """Cria um marcador visual no gráfico"""
        print(f"Criando marcador em {time_position:.3f} s")
        if not self.figure_widget or not self.figure_widget.waveform_data:
            return
        ax = self.figure_widget.figure.axes[0]
        ax.axvline(
            x=time_position,
            color="#5ff033",
            linewidth=1.5,
            linestyle='--',
            zorder=9
        )
        self.markers_pos.append(time_position) if time_position not in self.markers_pos else None
        self.figure_widget.figure.canvas.draw_idle()

        print(f"Marcadores atuais: {self.markers_pos}")
        
        self.main_controller.table_controller.update_events(self.markers_pos, self.audio_selected)
        self.main_controller.table_controller.add_row()

    def delete_marker(self):
        """Remove um marcador visual do gráfico"""
        if not self.figure_widget or not self.figure_widget.waveform_data:
            return
        markers_id = self.main_controller.table_controller.remove_selected()
        ax = self.figure_widget.figure.axes[0]
        for marker_time in sorted([self.markers_pos[i] for i in markers_id], reverse=True):
            print(f"Removendo marcador em {marker_time:.3f} s")
            # Remove a linha do marcador
            for line in ax.get_lines():
                if line.get_xdata()[0] == marker_time and line.get_linestyle() == '--':
                    line.remove()
                    break
            # Remove da lista de marcadores
            self.markers_pos.remove(marker_time)
        self.figure_widget.figure.canvas.draw_idle()
        self.main_controller.table_controller.update_table()
        
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
        self.table_controller = TableController(self)

        self.bind(audio_files=self.update_audio_list)

    # ---------------------------
    # VIEW CALLBACKS
    # ---------------------------

    def on_kv_post(self, base_widget):
        """Chamado após o carregamento do .kv"""
        Clock.schedule_once(lambda dt: self.update_audio_list())
        Clock.schedule_once(lambda dt: self.update_events_table())

    # ---------------------------
    # MENU METHODS
    # ---------------------------

    def open_file_menu(self):
        """Abre o menu File"""
        menu_items = [
            {
                "viewclass": "OneLineIconListItem",
                "text": "Upload Audio",
                "on_release": lambda x="upload": self.on_menu_item_selected(x),
            },
            {
                "viewclass": "OneLineIconListItem", 
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
                "text": "Auto Marker",
                "on_release": lambda x="analysis": self.on_menu_item_selected(x),
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
                "text": "Documentation", 
                "on_release": lambda x="docs": self.on_menu_item_selected(x),
            },
            {
                "viewclass": "OneLineIconListItem",
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
            print("Download audio")
        elif action == "analysis":
            if self.audio_controller.audio_analysis:
                self.audio_controller.audio_analysis = False
                self.dialog = MDDialog(
                    title="Análise Automática Desativada",
                    text="Análise automática do áudio foi desativada.\nMarcadores automáticos não serão mais gerados.",
                    buttons=[
                        MDFlatButton(
                            text="OK",
                            on_release=lambda x: self.dialog.dismiss()
                        )
                    ],
                )
                self.dialog.open()
            else:
                self.audio_controller.audio_analysis = True
                self.dialog = MDDialog(
                    title="Análise Automática Ativada",
                    text="Análise automática do áudio foi ativada.\nMarcadores automáticos serão gerados ao carregar novos áudios.",
                    buttons=[
                        MDFlatButton(
                            text="OK",
                            on_release=lambda x: self.dialog.dismiss()
                        )
                    ],
                )
                self.dialog.open()
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

    # ---------------------------
    # MEDIA BUTTONS
    # ---------------------------

    def on_previous_button_pressed(self):
        """Chamado quando o usuário clica em 'previous'"""
        try:
            if not self.audio_selected:
                print("Nenhum áudio selecionado.")
                return
            if self.audio_files:
                if self.audio_controller.is_playing:
                    self.audio_controller.pause()
                    self.audio_controller.current_time = 0.0
                    self.ids.play_btn.icon = "play"
                current_index = self.audio_files.index(self.audio_selected)
                previous_index = (current_index - 1) % len(self.audio_files) # usando modulo para comportamento circular
                self.on_audio_select(self.audio_files[previous_index])
        except Exception as e:
            print(f"Erro ao reproduzir áudio: {e}")
            return

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
    
    def on_next_button_pressed(self):
        """Chamado quando o usuário clica em 'next'"""
        try:
            if not self.audio_selected:
                print("Nenhum áudio selecionado.")
                return
            if self.audio_files:
                if self.audio_controller.is_playing:
                    self.audio_controller.pause()
                    self.audio_controller.current_time = 0.0
                    self.ids.play_btn.icon = "play"
                current_index = self.audio_files.index(self.audio_selected)
                next_index = (current_index + 1) % len(self.audio_files) # usando modulo para comportamento circular
                self.on_audio_select(self.audio_files[next_index])
        except Exception as e:
            print(f"Erro ao reproduzir áudio: {e}")
            return

    def on_plus_button_pressed(self):
        """Chamado quando o usuário clica em 'plus' para adicionar marcadores"""
        try:
            if not self.audio_selected:
                print("Nenhum áudio selecionado.")
                return
            self.canvas_controller.create_marker(self.canvas_controller.selected_audio_x_pos)
        except Exception as e:
            print(f"Erro ao criar marcador: {e}")
            return
        
    def on_minus_button_pressed(self):
        """Chamado quando o usuário clica em 'minus' para remover marcadores"""
        try:
            if not self.audio_selected:
                print("Nenhum áudio selecionado.")
                return
            self.canvas_controller.delete_marker()
        except Exception as e:
            print(f"Erro ao remover marcador: {e}")
            return

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

    def update_events_table(self, events=[]):
        """Atualiza a tabela de eventos na view"""
        self.table_controller.create_table()