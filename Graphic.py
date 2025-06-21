# main.py with enhanced UI

import os
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, BorderImage
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ListProperty
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.image import AsyncImage
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.uix.widget import Widget

INTRO_BACKGROUND = "assets/intro.jpg"  # Tạo file này hoặc dùng ảnh có sẵn
RULES_BACKGROUND = "assets/rule.jpg"  # Tạo file này hoặc dùng ảnh có sẵn

# --- Import logic game from file game_logic.py ---
from logic4 import (
    Player, Deck, GameRound, Card,
    CARD_PROTOTYPES, CARDS_DATA_RAW,
    CARD_FOLDER, CARD_BACK_IMAGE, ELIMINATED_IMAGE
)

# Set window size and title
Window.size = (1000, 800)
Window.clearcolor = (0.1, 0.1, 0.2, 1)

# --- Kivy UI and Game Session Management ---

class IntroScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Tạo background cho màn hình intro
        with self.canvas.before:
            Color(0.1, 0.1, 0.2, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Logo và tên game
        logo_box = BoxLayout(orientation='vertical', size_hint=(1, 0.6))
        
        # Kiểm tra xem có file intro_background không, nếu có thì dùng
        if os.path.exists(INTRO_BACKGROUND):
            game_logo = AsyncImage(source=INTRO_BACKGROUND, allow_stretch=True, keep_ratio=True)
        else:
            # Nếu không có file, tạo hiển thị text logo
            game_logo = BoxLayout(orientation='vertical')
            with game_logo.canvas.before:
                Color(0.15, 0.15, 0.3, 1)
                RoundedRectangle(pos=game_logo.pos, size=game_logo.size, radius=[20,])
            game_logo.bind(pos=self._update_logo_bg, size=self._update_logo_bg)
            
            title = StyledLabel(
                text="LOVE LETTER", 
                font_size=48, 
                color=(1, 0.8, 0.8, 1),
                bold=True,
                outline_width=2,
                outline_color=(0.5, 0, 0.2, 1)
            )
            subtitle = StyledLabel(
                text="Board Game", 
                font_size=24,
                color=(1, 0.9, 0.7, 1)
            )
            game_logo.add_widget(Widget(size_hint_y=0.3))  # Padding
            game_logo.add_widget(title)
            game_logo.add_widget(subtitle)
            game_logo.add_widget(Widget(size_hint_y=0.3))  # Padding
            
        logo_box.add_widget(game_logo)
        self.layout.add_widget(logo_box)
        
        # Thông tin ngắn về game
        intro_text = (
            "Chinh phục trái tim của Công chúa bằng lá thư tình!\n\n"
            "Love Letter là trò chơi thẻ bài chiến thuật nhanh gọn,\n"
            "nơi bạn cố gắng đưa thư tình của mình đến tay Công chúa."
        )
        intro_label = StyledLabel(
            text=intro_text,
            font_size=18,
            halign='center',
            valign='center',
            size_hint_y=0.2
        )
        intro_label.bind(size=intro_label.setter('text_size'))
        self.layout.add_widget(intro_label)
        
        # Nút next để chuyển tới màn hình luật chơi
        button_box = BoxLayout(size_hint_y=0.2, padding=[dp(100), dp(10)])
        next_button = Button(
            text="Xem Luật Chơi", 
            size_hint=(0.5, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0.6, 0.4, 0.8, 1),
            font_size=20,
            bold=True
        )
        next_button.bind(on_press=self.go_to_rules)
        button_box.add_widget(next_button)
        self.layout.add_widget(button_box)
        
        self.add_widget(self.layout)
        
        # Animation khi màn hình xuất hiện
        self.opacity = 0
        anim = Animation(opacity=1, duration=1)
        Clock.schedule_once(lambda dt: anim.start(self), 0.1)
        
    def _update_bg(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size
        
    def _update_logo_bg(self, instance, value):
        for child in instance.canvas.before.children:
            if isinstance(child, RoundedRectangle):
                child.pos = instance.pos
                child.size = instance.size
                
    def go_to_rules(self, instance):
        # Transition to rules screen
        self.manager.current = 'rules'


class RulesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Tạo background cho màn hình rules
        with self.canvas.before:
            Color(0.1, 0.1, 0.2, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Tiêu đề luật chơi
        title = StyledLabel(
            text="Luật Chơi", 
            font_size=32, 
            color=(1, 0.8, 0.2, 1),
            size_hint_y=0.1
        )
        self.layout.add_widget(title)
        
        # Luật chơi trong ScrollView để cuộn được
        scroll_view = ScrollView(size_hint=(1, 0.7))
        rules_content = BoxLayout(orientation='vertical', 
                                 size_hint_y=None, 
                                 spacing=15,
                                 padding=[15, 15])
        rules_content.bind(minimum_height=rules_content.setter('height'))
        
        # Thêm các quy tắc game
        rules_text = [
            ("Mục Tiêu:", "Giành được nhiều tokens nhất bằng cách tồn tại đến cuối vòng hoặc loại bỏ đối thủ."),
            ("Số Token Cần Thắng:", "2 người chơi: 7 tokens\n3 người chơi: 5 tokens\n4 người chơi: 4 tokens\n5+ người chơi: 3 tokens"),
            ("Cách Chơi:", "Mỗi lượt, người chơi rút 1 lá bài, sau đó chơi 1 trong 2 lá đang có."),
            ("Thứ Tự Lá Bài:", "1-Guard: Đoán lá bài của đối thủ (trừ Guard). Nếu đúng, đối thủ bị loại.\n"
             "2-Priest: Xem lá bài của đối thủ.\n"
             "3-Baron: So sánh lá bài với đối thủ, người có lá thấp hơn bị loại.\n"
             "4-Handmaid: Bảo vệ bạn khỏi hiệu ứng của người khác đến lượt sau.\n"
             "5-Prince: Buộc người chơi (có thể là bản thân) bỏ lá hiện tại và rút lá mới.\n"
             "6-King: Tráo đổi lá bài với người chơi khác.\n"
             "7-Countess: Phải đánh nếu có King hoặc Prince trên tay.\n"
             "8-Princess: Bị loại nếu bạn bỏ lá này vì bất kỳ lý do gì.")
        ]
        
        for title, desc in rules_text:
            rule_box = BoxLayout(orientation='vertical', 
                                size_hint_y=None)
            rule_box.bind(minimum_height=rule_box.setter('height'))
            
            # Tiêu đề quy tắc
            rule_title = StyledLabel(
                text=title, 
                font_size=18, 
                bold=True,
                color=(1, 0.7, 0.4, 1),
                size_hint_y=None,
                height=dp(30)
            )
            rule_box.add_widget(rule_title)
            
            # Mô tả quy tắc
            rule_desc = StyledLabel(
                text=desc,
                font_size=16,
                size_hint_y=None,
                text_size=(None, None)
            )
            rule_desc.bind(texture_size=rule_desc.setter('size'))
            rule_box.add_widget(rule_desc)
            
            # Thêm padding
            rule_box.add_widget(Widget(size_hint_y=None, height=10))
            
            rules_content.add_widget(rule_box)
        
        scroll_view.add_widget(rules_content)
        self.layout.add_widget(scroll_view)
        
        # Nút để bắt đầu game
        button_box = BoxLayout(size_hint_y=0.2, padding=[dp(100), dp(10)])
        start_button = Button(
            text="Bắt Đầu Game", 
            size_hint=(0.5, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0.3, 0.6, 0.3, 1),
            font_size=20,
            bold=True
        )
        start_button.bind(on_press=self.start_game)
        button_box.add_widget(start_button)
        self.layout.add_widget(button_box)
        
        self.add_widget(self.layout)
        
    def _update_bg(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size
        
    def start_game(self, instance):
        # Chuyển tới màn hình game chính
        self.manager.current = 'game'
        
        # Sau khi chuyển màn hình, khởi tạo thiết lập game
        game_screen = self.manager.get_screen('game')
        game = game_screen.children[0]  # LoveLetterGame là widget con duy nhất của game_screen
        Clock.schedule_once(lambda dt: game.initialize_game_setup(), 0.5)  # Delay nhỏ để đảm bảo màn hình đã chuyển

class ImageButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True
        
    def on_press(self):
        # Add slight scale effect on press
        self.opacity = 0.8
        
    def on_release(self):
        self.opacity = 1.0

class StyledLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = (0.9, 0.9, 1, 1)
        self.bold = True
        self.outline_width = 1
        self.outline_color = (0, 0, 0, 1)

class CardDisplay(BoxLayout):
    def __init__(self, card_source="", name="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 5
        self.size_hint_y = None
        self.height = 180
        
        # Add background with rounded corners
        with self.canvas.before:
            Color(0.2, 0.2, 0.3, 0.7)
            self.bg = RoundedRectangle(radius=[10,])
            
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Card image with border
        self.card_image = Image(source=card_source, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.card_image)
        
        # Name label
        self.name_label = StyledLabel(text=name, size_hint_y=0.2, font_size='12sp')
        self.add_widget(self.name_label)
        
    def _update_rect(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size

class LoveLetterGame(BoxLayout):  # Kivy Main Widget
    def __init__(self, **kwargs):
        # Khởi tạo các thuộc tính cần thiết TRƯỚC khi gọi super().__init__
        self.game_log = ["Welcome to Love Letter Kivy!"]
        self.num_players_session = 0
        self.players_session_list = []
        self.human_player_id = 0
        self.current_round_manager = None
        self.tokens_to_win_session = 0
        self.game_over_session_flag = True
        self.active_popup = None
        self.waiting_for_input = False
        self.opponent_widgets_map = {}
        self.animated_widget_details = {}
        
        # Bây giờ gọi super().__init__
        super().__init__(**kwargs)
        
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        
        # Add a subtle gradient background
        with self.canvas.before:
            Color(0.15, 0.15, 0.25, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Vô hiệu hóa sự kiện on_kv_post tự động và sử dụng Clock thay thế
        # Setup game when added to the window
        Clock.schedule_once(self._delayed_setup, 0.5)
        
    def _delayed_setup(self, dt):
        """Hàm khởi tạo được gọi sau khi widget đã được thêm vào cửa sổ"""
        self._load_card_prototypes_and_images()
        self.setup_ui_placeholders()
        # self.prompt_player_count()
        
    def initialize_game_setup(self):
        """Được gọi khi người dùng nhấn Bắt Đầu Game từ màn hình Rules"""
        self.prompt_player_count()
        
    # Ghi đè phương thức on_kv_post để nó không làm gì cả
    def on_kv_post(self, *args, **kwargs):
        pass
        
    def _force_show_player_count_popup(self, dt):
        if hasattr(self, 'active_popup') and self.active_popup:
            self.active_popup.dismiss()
        self.prompt_player_count()
        
    def _update_bg(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def _load_card_prototypes_and_images(self):
        # NOTE: This function modifies the global CARD_PROTOTYPES imported from game_logic
        global CARD_PROTOTYPES
        CARD_PROTOTYPES.clear()

        missing_card_back = False
        if not os.path.exists(CARD_BACK_IMAGE):
            self.log_message(f"CRITICAL ERROR: Card back image not found at {CARD_BACK_IMAGE}", permanent=True)
            missing_card_back = True

        for eng_name, data in CARDS_DATA_RAW.items():
            viet_name = data['vietnamese_name']
            path_jpg = os.path.join(CARD_FOLDER, f"{viet_name}.jpg")
            path_png = os.path.join(CARD_FOLDER, f"{viet_name}.png")
            actual_path = next((p for p in [path_jpg, path_png] if os.path.exists(p)), None)

            if not actual_path:
                self.log_message(f"Warning: Image for '{eng_name}' ({viet_name}) not found. Using card back.",
                                 permanent=True)
                actual_path = CARD_BACK_IMAGE if not missing_card_back else ""

            CARD_PROTOTYPES[eng_name] = Card(
                name=eng_name,
                value=data['value'],
                description=data['description'],
                image_path=actual_path,
                vietnamese_name=viet_name,
                count_classic=data['count_classic'],
                count_large=data['count_large']
            )
        self.log_message(f"Card prototypes and images loaded. {len(CARD_PROTOTYPES)} card types found.", permanent=True)

    def setup_ui_placeholders(self):
        self.clear_widgets()
        
        # Tạo màn hình chờ đẹp hơn
        welcome_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Logo hoặc tiêu đề game
        title_label = StyledLabel(
            text="Love Letter Board Game", 
            font_size=32,
            color=(0.9, 0.7, 0.8, 1),
            size_hint_y=0.3
        )
        welcome_layout.add_widget(title_label)
        
        # Hình ảnh minh họa
        image_box = BoxLayout(size_hint_y=0.4)
        if os.path.exists(CARD_BACK_IMAGE):
            welcome_image = Image(source=CARD_BACK_IMAGE, size_hint_max_x=0.7)
            welcome_image.pos_hint = {'center_x': 0.5}
            image_box.add_widget(welcome_image)
        welcome_layout.add_widget(image_box)
        
        # Thông điệp chờ
        waiting_label = StyledLabel(
            text="Đang chờ bắt đầu trò chơi...", 
            font_size=24, 
            size_hint_y=0.3
        )
        welcome_layout.add_widget(waiting_label)
        
        self.add_widget(welcome_layout)

    def prompt_player_count(self):
        self.game_log = ["Welcome to Love Letter Kivy!", "Please select number of players (2-8)."]
        if hasattr(self, 'message_label'): self.log_message("", permanent=False)

        popup_layout = BoxLayout(orientation='vertical', spacing="15dp", padding="20dp")
        
        # Add styling to the popup
        title_label = StyledLabel(
            text="Select Number of Players (2-8):", 
            font_size=22,
            size_hint_y=None, 
            height="50dp"
        )
        popup_layout.add_widget(title_label)
        
        options_layout = GridLayout(cols=4, spacing="10dp", size_hint_y=None)
        options_layout.bind(minimum_height=options_layout.setter('height'))
        
        for i in range(2, 9):
            btn = Button(
                text=str(i), 
                size_hint_y=None, 
                height="60dp",
                background_color=(0.3, 0.4, 0.8, 1),
                font_size=20,
                bold=True
            )
            btn.player_count = i
            btn.bind(on_press=self.initialize_game_with_player_count)
            options_layout.add_widget(btn)
            
        popup_layout.add_widget(options_layout)
        
        self.active_popup = Popup(
            title="Love Letter - Player Count", 
            content=popup_layout,
            size_hint=(0.6, 0.4), 
            auto_dismiss=False,
            title_color=(1, 0.9, 0.8, 1),
            title_size='20sp',
            title_align='center',
            background="atlas://data/images/defaulttheme/button_pressed"
        )
        self.active_popup.open()

    def initialize_game_with_player_count(self, instance):
        if self.active_popup:
            self.active_popup.dismiss()
            self.active_popup = None
        self.num_players_session = instance.player_count
        self.log_message(f"Number of players set to: {self.num_players_session}")

        if self.num_players_session == 2:
            self.tokens_to_win_session = 7
        elif self.num_players_session == 3:
            self.tokens_to_win_session = 5
        elif self.num_players_session == 4:
            self.tokens_to_win_session = 4
        else:
            self.tokens_to_win_session = 3
        self.log_message(f"Tokens needed to win: {self.tokens_to_win_session}")

        self.players_session_list = [Player(id_num=0, name="Player 1 (You)")]
        self.human_player_id = self.players_session_list[0].id
        for i in range(1, self.num_players_session):
            self.players_session_list.append(Player(id_num=i, name=f"CPU {i}", is_cpu=True))

        self.setup_main_ui()
        self.start_new_game_session()

    def setup_main_ui(self):
        self.clear_widgets()
        
        # Top section with scores and game log
        top_section = BoxLayout(size_hint_y=0.25, orientation='vertical', spacing=5)
        
        # Info bar with improved styling
        info_bar = BoxLayout(size_hint_y=None, height=40, padding=5)
        with info_bar.canvas.before:
            Color(0.2, 0.3, 0.5, 0.8)
            RoundedRectangle(pos=info_bar.pos, size=info_bar.size, radius=[10,])
        info_bar.bind(pos=self._update_info_bar_bg, size=self._update_info_bar_bg)
            
        self.score_label = StyledLabel(
            text="Scores:", 
            size_hint_x=0.7, 
            halign='left', 
            valign='middle', 
            font_size=16
        )
        self.score_label.bind(size=self.score_label.setter('text_size'))
        
        self.turn_label = StyledLabel(
            text="Game Over", 
            size_hint_x=0.3, 
            halign='right', 
            valign='middle', 
            color=(1, 0.8, 0.2, 1),
            font_size=16
        )
        self.turn_label.bind(size=self.turn_label.setter('text_size'))
        
        info_bar.add_widget(self.score_label)
        info_bar.add_widget(self.turn_label)
        top_section.add_widget(info_bar)
        
        # Game log with improved styling
        log_container = BoxLayout(size_hint_y=1, padding=5)
        with log_container.canvas.before:
            Color(0.1, 0.1, 0.2, 0.7)
            RoundedRectangle(pos=log_container.pos, size=log_container.size, radius=[10,])
        log_container.bind(pos=self._update_log_container_bg, size=self._update_log_container_bg)
        
        log_scroll_view = ScrollView(size_hint_y=1)
        self.message_label = Label(
            text="\n".join(self.game_log), 
            size_hint_y=None, 
            halign='left', 
            valign='top',
            color=(0.9, 0.9, 0.9, 1),
            font_size=14,
            padding=(10, 10)
        )
        self.message_label.bind(texture_size=self.message_label.setter('size'))
        log_scroll_view.add_widget(self.message_label)
        log_container.add_widget(log_scroll_view)
        top_section.add_widget(log_container)
        self.add_widget(top_section)

        # Game area with better layout
        game_area = BoxLayout(orientation='vertical', spacing=15, size_hint_y=0.7)
        
        # Opponents area with title
        opponents_header = BoxLayout(size_hint_y=None, height=30)
        opponents_header.add_widget(StyledLabel(
            text="Opponents", 
            size_hint_y=None, 
            height=30, 
            font_size=18,
            color=(0.9, 0.7, 0.3, 1)
        ))
        game_area.add_widget(opponents_header)
        
        # Improved opponents display
        self.opponents_area_scrollview = ScrollView(size_hint=(1, 0.4))
        self.opponents_grid = GridLayout(
            cols=max(1, min(4, self.num_players_session - 1) if self.num_players_session > 1 else 1),
            size_hint_x=None if self.num_players_session - 1 > 3 else 1, 
            size_hint_y=None,
            spacing=10,
            padding=5
        )
        self.opponents_grid.bind(minimum_width=self.opponents_grid.setter('width'))
        self.opponents_grid.bind(minimum_height=self.opponents_grid.setter('height'))
        self.opponents_area_scrollview.add_widget(self.opponents_grid)
        game_area.add_widget(self.opponents_area_scrollview)
        
        # Deck area with improved styling
        deck_container = BoxLayout(size_hint_y=0.2, spacing=15, padding=5)
        with deck_container.canvas.before:
            Color(0.2, 0.25, 0.3, 0.6)
            RoundedRectangle(pos=deck_container.pos, size=deck_container.size, radius=[10,])
        deck_container.bind(pos=self._update_deck_container_bg, size=self._update_deck_container_bg)
        
        # Deck display with shadow effect
        deck_display = BoxLayout(orientation='vertical', size_hint_x=0.3)
        self.deck_image = Image(
            source=CARD_BACK_IMAGE, 
            allow_stretch=True,
            keep_ratio=True
        )
        deck_display.add_widget(self.deck_image)
        
        deck_info = BoxLayout(orientation='vertical', size_hint_x=0.7)
        self.deck_count_label = StyledLabel(
            text="Deck: 0", 
            font_size=18,
            color=(0.9, 0.8, 0.5, 1)
        )
        deck_info.add_widget(self.deck_count_label)
        
        deck_container.add_widget(deck_display)
        deck_container.add_widget(deck_info)
        game_area.add_widget(deck_container)
        
        # Player hand area with improved styling
        self.human_player_display_wrapper = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)
        
        player_header = BoxLayout(size_hint_y=None, height=30)
        player_header.add_widget(StyledLabel(
            text="Your Hand (Click to Play)", 
            size_hint_y=None, 
            height=30, 
            font_size=18,
            color=(0.3, 0.8, 0.6, 1)
        ))
        self.human_player_display_wrapper.add_widget(player_header)
        
        player_hand_container = BoxLayout(size_hint_y=0.7)
        with player_hand_container.canvas.before:
            Color(0.15, 0.25, 0.2, 0.6)
            RoundedRectangle(pos=player_hand_container.pos, size=player_hand_container.size, radius=[10,])
        player_hand_container.bind(pos=self._update_player_hand_bg, size=self._update_player_hand_bg)
        
        self.player_hand_area = BoxLayout(orientation='horizontal', spacing=20, padding=10)
        player_hand_container.add_widget(self.player_hand_area)
        self.human_player_display_wrapper.add_widget(player_hand_container)
        
        discard_container = BoxLayout(orientation='vertical', size_hint_y=0.3)
        discard_title = StyledLabel(text="Your Discard", size_hint_y=None, height=20, font_size=14)
        discard_container.add_widget(discard_title)
        self.player_discard_display = Image(source="", allow_stretch=True, keep_ratio=True)
        discard_container.add_widget(self.player_discard_display)
        self.human_player_display_wrapper.add_widget(discard_container)
        
        game_area.add_widget(self.human_player_display_wrapper)
        self.add_widget(game_area)

        # Bottom action button with improved styling
        self.action_button = Button(
            text="Start New Game Session", 
            size_hint_y=None, 
            height=60,
            background_color=(0.4, 0.6, 0.9, 1),
            font_size=18,
            bold=True
        )
        self.action_button.bind(on_press=self.on_press_action_button)
        self.add_widget(self.action_button)
        
        self.update_ui_full()
    
    def _update_info_bar_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.2, 0.3, 0.5, 0.8)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10,])
    
    def _update_log_container_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.1, 0.1, 0.2, 0.7)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10,])
    
    def _update_deck_container_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.2, 0.25, 0.3, 0.6)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10,])
    
    def _update_player_hand_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.15, 0.25, 0.2, 0.6)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10,])

    def log_message(self, msg, permanent=True):
        print(msg)
        if permanent:
            self.game_log.append(msg)
            if len(self.game_log) > 100: self.game_log = self.game_log[-100:]
        if hasattr(self, 'message_label'):
            self.message_label.text = "\n".join(self.game_log)
            if self.message_label.parent and isinstance(self.message_label.parent, ScrollView):
                self.message_label.parent.scroll_y = 0

    def update_ui_full(self):
        if not hasattr(self, 'score_label'): return

        # Update score display with colored tokens
        score_texts = []
        for p in self.players_session_list:
            token_display = "★" * p.tokens + "☆" * (self.tokens_to_win_session - p.tokens)
            score_texts.append(f"{p.name}: {token_display}")
        self.score_label.text = " | ".join(score_texts)

        # Update turn info
        current_player_name_round = "N/A"
        is_round_active_for_ui = False
        if self.current_round_manager and self.current_round_manager.round_active:
            is_round_active_for_ui = True
            current_player_name_round = self.players_session_list[self.current_round_manager.current_player_idx].name

        if self.game_over_session_flag:
            self.turn_label.text = "Game Over!"
            self.action_button.text = "Start New Game Session"
            self.action_button.background_color = (0.4, 0.6, 0.9, 1)
        elif not is_round_active_for_ui:
            self.turn_label.text = "Round Over"
            self.action_button.text = "Start Next Round"
            self.action_button.background_color = (0.5, 0.7, 0.3, 1)
        else:
            self.turn_label.text = f"Turn: {current_player_name_round}"
            self.action_button.text = "Forfeit Round (DEBUG)"
            self.action_button.background_color = (0.8, 0.3, 0.3, 1)

        # Update deck display
        if self.current_round_manager and self.current_round_manager.deck:
            self.deck_count_label.text = f"Cards Remaining: {self.current_round_manager.deck.count()}"
            self.deck_image.source = CARD_BACK_IMAGE if not self.current_round_manager.deck.is_empty() else ""
        else:
            self.deck_count_label.text = "Deck: N/A"
            self.deck_image.source = ""

        # Update opponent displays with enhanced styling
        self.opponents_grid.clear_widgets()
        self.opponent_widgets_map.clear()
        if self.num_players_session > 1:
            # Set columns based on player count for better layout
            max_cols = 4
            self.opponents_grid.cols = min(max_cols, max(1, self.num_players_session - 1))
            self.opponents_grid.size_hint_x = None if self.num_players_session - 1 > max_cols else 1

            for p_opponent in self.players_session_list:
                if p_opponent.id == self.human_player_id: continue

                # Create styled opponent display
                opponent_container = BoxLayout(orientation='vertical', size_hint_y=None, height=200, width=150, padding=5)
                
                # Add background with border and status color
                with opponent_container.canvas.before:
                    if p_opponent.is_eliminated:
                        Color(0.5, 0.1, 0.1, 0.7)  # Red for eliminated
                    elif p_opponent.is_protected:
                        Color(0.2, 0.5, 0.2, 0.7)  # Green for protected
                    else:
                        Color(0.2, 0.2, 0.3, 0.7)  # Default blue
                    RoundedRectangle(pos=opponent_container.pos, size=opponent_container.size, radius=[15,])
                
                opponent_container.bind(pos=self._update_opponent_bg, size=self._update_opponent_bg)
                
                # Name with token count
                name_box = BoxLayout(size_hint_y=0.15)
                token_text = f"{p_opponent.name} {'★' * p_opponent.tokens}"
                status_text = " [E]" if p_opponent.is_eliminated else " [P]" if p_opponent.is_protected else ""
                name_label = StyledLabel(
                    text=token_text + status_text, 
                    font_size='12sp',
                    color=(1, 1, 0.8, 1) if not p_opponent.is_eliminated else (1, 0.7, 0.7, 1)
                )
                name_box.add_widget(name_label)
                opponent_container.add_widget(name_box)
                
                # Card display
                card_img_src = CARD_BACK_IMAGE
                if p_opponent.is_eliminated:
                    card_img_src = ELIMINATED_IMAGE
                elif not p_opponent.hand:
                    card_img_src = ""
                
                card_box = BoxLayout(size_hint_y=0.55)
                card_image = Image(source=card_img_src, allow_stretch=True, keep_ratio=True)
                card_box.add_widget(card_image)
                opponent_container.add_widget(card_box)
                
                # Discard pile display
                discard_box = BoxLayout(orientation='vertical', size_hint_y=0.3)
                discard_label = StyledLabel(text="Discard", font_size='10sp', size_hint_y=0.3)
                discard_box.add_widget(discard_label)
                
                discard_img_src = ""
                if p_opponent.discard_pile:
                    discard_img_src = p_opponent.discard_pile[-1].image_path
                
                discard_image = Image(source=discard_img_src, allow_stretch=True, keep_ratio=True, size_hint_y=0.7)
                discard_box.add_widget(discard_image)
                opponent_container.add_widget(discard_box)
                
                self.opponents_grid.add_widget(opponent_container)
                self.opponent_widgets_map[p_opponent.id] = opponent_container

        # Update human player hand display with enhanced styling
        human_player = self.players_session_list[self.human_player_id]
        self.player_hand_area.clear_widgets()
        
        if human_player.is_eliminated:
            self.player_hand_area.add_widget(Image(source=ELIMINATED_IMAGE, allow_stretch=True))
            self.player_hand_area.add_widget(StyledLabel(text="Eliminated!", color=(1, 0.5, 0.5, 1), font_size=24))
        elif human_player.hand:
            is_player_turn_active_ui = (self.current_round_manager and
                                       self.current_round_manager.round_active and
                                       self.current_round_manager.current_player_idx == self.human_player_id and
                                       not self.waiting_for_input)

            for card_obj in human_player.hand:
                # Create card container with styling
                card_container = BoxLayout(
                    orientation='vertical',
                    size_hint=(1 / len(human_player.hand) if len(human_player.hand) > 0 else 1, 1),
                    padding=5
                )
                
                # Card button with shadow effect when active
                card_button = ImageButton(source=card_obj.image_path)
                card_button.card_name = card_obj.name
                card_button.bind(on_press=self.on_player_card_selected)
                card_button.disabled = not is_player_turn_active_ui
                card_button.opacity = 1.0 if is_player_turn_active_ui else 0.7
                
                # Add card value indicator
                card_value_box = BoxLayout(size_hint_y=None, height=20)
                card_value_label = StyledLabel(
                    text=f"{card_obj.name} ({card_obj.value})", 
                    font_size='12sp',
                    color=(1, 1, 0.8, 1)
                )
                card_value_box.add_widget(card_value_label)
                
                card_container.add_widget(card_button)
                card_container.add_widget(card_value_box)
                self.player_hand_area.add_widget(card_container)

        # Update player discard display
        self.player_discard_display.source = human_player.discard_pile[-1].image_path if human_player.discard_pile else ""
        
        self.log_message("", permanent=False)
    
    def _update_opponent_bg(self, instance, value):
        if hasattr(instance, 'canvas') and hasattr(instance, 'canvas.before'):
            for child in instance.canvas.before.children:
                if isinstance(child, RoundedRectangle):
                    child.pos = instance.pos
                    child.size = instance.size

    # The rest of your methods remain unchanged...
    # Here I'll include just a sample of the UI display popup methods to show styling improvements

    def ui_display_target_selection_popup(self, acting_player_obj, card_played_obj, valid_targets_list,
                                        continuation_callback_in_gameround):
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        
        popup_layout = BoxLayout(orientation='vertical', spacing="15dp", padding="20dp")
        
        # Add card image and info
        header_box = BoxLayout(size_hint_y=0.3, spacing=10)
        card_image = Image(
            source=card_played_obj.image_path, 
            size_hint_x=0.3, 
            allow_stretch=True, 
            keep_ratio=True
        )
        header_box.add_widget(card_image)
        
        info_box = BoxLayout(orientation='vertical', size_hint_x=0.7)
        info_box.add_widget(StyledLabel(
            text=f"{card_played_obj.name} (Value: {card_played_obj.value})", 
            font_size=18,
            color=(1, 0.9, 0.7, 1)
        ))
        info_box.add_widget(StyledLabel(
            text=card_played_obj.description, 
            font_size=14,
            color=(0.9, 0.9, 1, 1)
        ))
        header_box.add_widget(info_box)
        popup_layout.add_widget(header_box)
        
        # Title
        popup_layout.add_widget(StyledLabel(
            text=f"Choose target for {acting_player_obj.name}:",
            font_size=16,
            color=(1, 1, 0.8, 1),
            size_hint_y=None,
            height=30
        ))
        
        # Target selection
        scroll_view = ScrollView(size_hint=(1, 0.6))
        target_grid = GridLayout(cols=1, spacing="8dp", size_hint_y=None)
        target_grid.bind(minimum_height=target_grid.setter('height'))
        
        for target in valid_targets_list:
            btn_text = f"{target.name}"
            if target == acting_player_obj: btn_text += " (Yourself)"
            
            btn = Button(
                text=btn_text, 
                size_hint_y=None, 
                height="50dp",
                background_color=(0.3, 0.5, 0.8, 1) if target != acting_player_obj else (0.5, 0.5, 0.3, 1),
                font_size=16
            )
            btn.target_player_id = target.id
            btn.bind(on_press=lambda instance, ap=acting_player_obj, tid=target.id:
                    (self.dismiss_active_popup(), continuation_callback_in_gameround(ap, tid)))
            target_grid.add_widget(btn)
        
        scroll_view.add_widget(target_grid)
        popup_layout.add_widget(scroll_view)
        
        self.active_popup = Popup(
            title=f"{card_played_obj.name} Target Selection", 
            content=popup_layout,
            size_hint=(0.8, 0.8), 
            auto_dismiss=False,
            title_color=(1, 0.9, 0.7, 1),
            title_size='20sp',
            title_align='center',
            background="atlas://data/images/defaulttheme/button_pressed"
        )
        self.active_popup.open()

    # Remaining methods would be the same but with styling updates
    # Include all your original methods here, but I've provided this sample to show how to style popups
    def _get_player_widget_by_id(self, player_id):
        if player_id == self.human_player_id:
            return self.human_player_display_wrapper
        return self.opponent_widgets_map.get(player_id)

    def _update_anim_rect_pos_size(self, instance, value):
        if hasattr(instance, 'canvas_anim_bg_rect'):
            instance.canvas_anim_bg_rect.pos = instance.pos
            instance.canvas_anim_bg_rect.size = instance.size

    def ui_animate_effect(self, effect_details, duration=1.0, on_complete_callback=None):
        self.dismiss_active_popup()
        processed_animation = False
        anim_type = effect_details.get('type')
        if anim_type == 'highlight_player':
            player_ids = effect_details.get('player_ids', [])
            color_type = effect_details.get('color_type', 'target')
            actor_id = effect_details.get('actor_id')

            if color_type == 'target':
                highlight_color_rgba = (0.5, 0.8, 1, 0.6)
            elif color_type == 'elimination':
                highlight_color_rgba = (1, 0.2, 0.2, 0.7)
            elif color_type == 'protection':
                highlight_color_rgba = (0.2, 1, 0.2, 0.7)
            elif color_type == 'actor_action':
                highlight_color_rgba = (1, 0.8, 0.2, 0.6)
            else:
                highlight_color_rgba = (0.7, 0.7, 0.7, 0.5)

            widgets_to_animate_this_call = []
            if actor_id is not None and effect_details.get('highlight_actor', False):
                actor_widget = self._get_player_widget_by_id(actor_id)
                if actor_widget:
                    widgets_to_animate_this_call.append({'widget': actor_widget, 'color': (1, 0.8, 0.2, 0.5)})

            for p_id in player_ids:
                widget = self._get_player_widget_by_id(p_id)
                if widget:
                    widgets_to_animate_this_call.append({'widget': widget, 'color': highlight_color_rgba})

            for item in widgets_to_animate_this_call:
                widget_to_animate = item['widget']
                color_rgba = item['color']
                processed_animation = True
                if widget_to_animate not in self.animated_widget_details:
                    with widget_to_animate.canvas.before:
                        widget_to_animate.canvas_anim_bg_color = Color(*color_rgba)
                        widget_to_animate.canvas_anim_bg_rect = Rectangle(size=widget_to_animate.size,
                                                                          pos=widget_to_animate.pos)
                    widget_to_animate.bind(pos=self._update_anim_rect_pos_size, size=self._update_anim_rect_pos_size)
                    self.animated_widget_details[widget_to_animate] = {
                        'widget': widget_to_animate,
                        'instruction_color': widget_to_animate.canvas_anim_bg_color,
                        'instruction_rect': widget_to_animate.canvas_anim_bg_rect,
                        'original_bound_pos_size': True
                    }
                else:
                    widget_to_animate.canvas_anim_bg_color.rgba = color_rgba
                    widget_to_animate.canvas_anim_bg_rect.size = widget_to_animate.size
                    widget_to_animate.canvas_anim_bg_rect.pos = widget_to_animate.pos

        if processed_animation:
            Clock.schedule_once(lambda dt: self._clear_animations_and_proceed(on_complete_callback), duration)
        elif on_complete_callback:
            on_complete_callback()


    def _clear_animations_and_proceed(self, on_complete_callback):
        for widget, details in list(self.animated_widget_details.items()):
            w = details['widget']
            if hasattr(w, 'canvas_anim_bg_color'):
                w.canvas_anim_bg_color.rgba = (0, 0, 0, 0)
        self.animated_widget_details.clear()
        if on_complete_callback:
            on_complete_callback()

    def on_press_action_button(self, instance):
        if self.game_over_session_flag:
            self.prompt_player_count()
        elif self.current_round_manager and not self.current_round_manager.round_active:
            self.start_new_round()
        else:
            if self.current_round_manager and self.current_round_manager.round_active and \
                    self.current_round_manager.players[
                        self.current_round_manager.current_player_idx].id == self.human_player_id:
                self.log_message(f"{self.players_session_list[self.human_player_id].name} forfeits the round.")
                self.log_message("DEBUG: Forfeit currently complex to reimplement cleanly. Ignored.")
            else:
                self.log_message("Cannot forfeit now.")

    def start_new_game_session(self):
        self.log_message(f"--- Starting New Game Session with {self.num_players_session} players ---")
        for p in self.players_session_list: p.tokens = 0
        self.game_over_session_flag = False
        self.start_new_round()

    def start_new_round(self):
        self.log_message("--- UI: Preparing New Round ---")
        if self.game_over_session_flag:
            self.log_message("Game is over. Cannot start new round until new game session.")
            self.update_ui_full()
            return
        game_deck = Deck(self.num_players_session, self.log_message)
        game_deck.burn_one_card(self.num_players_session)
        min_cards_needed = self.num_players_session
        if game_deck.count() < min_cards_needed:
            self.log_message(
                f"Error: Not enough cards in deck ({game_deck.count()}) for {self.num_players_session} players. Needs {min_cards_needed}.")
            self.game_over_session_flag = True
            self.update_ui_full()
            return

        ui_callbacks = {
            'update_ui_full_callback': self.update_ui_full,
            'set_waiting_flag_callback': self.set_waiting_for_input_flag,
            'get_active_popup_callback': lambda: self.active_popup,
            'dismiss_active_popup_callback': self.dismiss_active_popup,
            'request_target_selection_callback': self.ui_display_target_selection_popup,
            'request_guard_value_popup_callback': self.ui_display_guard_value_popup,
            'request_bishop_value_popup_callback': self.ui_display_bishop_value_popup,
            'request_bishop_redraw_choice_popup_callback': self.ui_display_bishop_redraw_choice_popup,
            'request_cardinal_first_target_popup_callback': self.ui_display_cardinal_first_target_popup,
            'request_cardinal_second_target_popup_callback': self.ui_display_cardinal_second_target_popup,
            'request_cardinal_look_choice_popup_callback': self.ui_display_cardinal_look_choice_popup,
            'award_round_tokens_callback': self.award_round_tokens_and_check_game_over,
            'check_game_over_token_callback': self.check_game_over_on_token_gain,
            'game_over_callback': self.handle_game_over_from_round,
            'animate_effect_callback': self.ui_animate_effect,
        }

        self.current_round_manager = GameRound(
            self.players_session_list, game_deck, self.human_player_id,
            self.log_message, ui_callbacks
        )
        self.current_round_manager.start_round()

    def on_player_card_selected(self, instance):
        if not self.current_round_manager or not self.current_round_manager.round_active or \
                self.players_session_list[self.human_player_id].is_cpu or \
                self.current_round_manager.current_player_idx != self.human_player_id or \
                self.waiting_for_input:
            return
        card_name_to_play = instance.card_name
        self.current_round_manager.human_plays_card(card_name_to_play)

    def set_waiting_for_input_flag(self, is_waiting):
        self.waiting_for_input = is_waiting
        self.update_ui_full()

    def dismiss_active_popup(self):
        if self.active_popup:
            self.active_popup.dismiss()
            self.active_popup = None

    def _create_popup_layout_with_scroll(self, title_text):
        popup_layout = BoxLayout(orientation='vertical', spacing="10dp", padding="10dp")
        popup_layout.add_widget(Label(text=title_text))
        scroll_content = GridLayout(cols=1, spacing="5dp", size_hint_y=None)
        scroll_content.bind(minimum_height=scroll_content.setter('height'))
        scroll_view = ScrollView(size_hint=(1, 1));
        scroll_view.add_widget(scroll_content)
        popup_layout.add_widget(scroll_view)
        return popup_layout, scroll_content

    def ui_display_target_selection_popup(self, acting_player_obj, card_played_obj, valid_targets_list,
                                          continuation_callback_in_gameround):
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        popup_layout, scroll_content = self._create_popup_layout_with_scroll(
            f"{card_played_obj.name}: Choose target for {acting_player_obj.name}:"
        )
        for target in valid_targets_list:
            btn_text = f"{target.name}"
            if target == acting_player_obj: btn_text += " (Yourself)"
            btn = Button(text=btn_text, size_hint_y=None, height="40dp")
            btn.target_player_id = target.id
            btn.bind(on_press=lambda instance, ap=acting_player_obj, tid=target.id:
            (self.dismiss_active_popup(), continuation_callback_in_gameround(ap, tid)))
            scroll_content.add_widget(btn)
        self.active_popup = Popup(title=f"{card_played_obj.name} Target", content=popup_layout,
                                  size_hint=(0.8, 0.7), auto_dismiss=False)
        self.active_popup.open()

    def ui_display_guard_value_popup(self, acting_player_obj, target_player_obj, possible_values_list,
                                     continuation_callback_in_gameround):
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        popup_layout, options_layout = self._create_popup_layout_with_scroll(
            f"Guard: Guess {target_player_obj.name}'s card value (not 1):"
        )
        options_layout.cols = 4
        for val in possible_values_list:
            btn = Button(text=str(val), size_hint_y=None, height="40dp")
            btn.bind(on_press=lambda inst_val, ap=acting_player_obj, tp=target_player_obj, v=val:
            (self.dismiss_active_popup(), continuation_callback_in_gameround(ap, tp, v)))
            options_layout.add_widget(btn)
        self.active_popup = Popup(title="Guard Guess Value", content=popup_layout,
                                  size_hint=(0.8, 0.6), auto_dismiss=False)
        self.active_popup.open()

    def ui_display_bishop_value_popup(self, acting_player_obj, target_player_obj, possible_values_list,
                                      continuation_callback_in_gameround):
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        popup_layout, options_layout = self._create_popup_layout_with_scroll(
            f"Bishop: Guess {target_player_obj.name}'s card value (not Guard):"
        )
        options_layout.cols = 4
        for val in possible_values_list:
            btn = Button(text=str(val), size_hint_y=None, height="40dp")
            btn.bind(on_press=lambda inst_val, ap=acting_player_obj, tp=target_player_obj, v=val:
            (self.dismiss_active_popup(), continuation_callback_in_gameround(ap, tp, v)))
            options_layout.add_widget(btn)
        self.active_popup = Popup(title="Bishop Guess Value", content=popup_layout,
                                  size_hint=(0.8, 0.6), auto_dismiss=False)
        self.active_popup.open()

    def ui_display_bishop_redraw_choice_popup(self, acting_player_obj, target_player_obj, was_correct_guess,
                                              continuation_callback_in_gameround):
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        guess_text = "correctly" if was_correct_guess else "incorrectly"
        popup_layout.add_widget(Label(
            text=f"{acting_player_obj.name} played Bishop. Your card ({target_player_obj.hand[0].name}) was guessed {guess_text}.\n"
                 f"Discard and draw new card?"
        ))
        btn_yes = Button(text="Yes, Discard & Draw", size_hint_y=None, height="40dp")
        btn_yes.bind(on_press=lambda x, tp=target_player_obj, choice=True:
        (self.dismiss_active_popup(), continuation_callback_in_gameround(tp, choice)))
        popup_layout.add_widget(btn_yes)
        btn_no = Button(text="No, Keep Card", size_hint_y=None, height="40dp")
        btn_no.bind(on_press=lambda x, tp=target_player_obj, choice=False:
        (self.dismiss_active_popup(), continuation_callback_in_gameround(tp, choice)))
        popup_layout.add_widget(btn_no)
        self.active_popup = Popup(title=f"Bishop: {target_player_obj.name}'s Choice", content=popup_layout,
                                  size_hint=(0.7, 0.5), auto_dismiss=False)
        self.active_popup.open()

    def ui_display_cardinal_first_target_popup(self, acting_player_obj, card_played_obj, valid_targets_list,
                                               continuation_callback):
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        popup_layout, scroll_content = self._create_popup_layout_with_scroll(
            f"{card_played_obj.name}: Choose 1st player for swap:"
        )
        for target in valid_targets_list:
            btn = Button(text=target.name, size_hint_y=None, height="40dp")
            btn.bind(on_press=lambda inst, ap=acting_player_obj, t_id=target.id:
            (self.dismiss_active_popup(), continuation_callback(ap, t_id)))
            scroll_content.add_widget(btn)
        self.active_popup = Popup(title="Cardinal Swap (1/2)", content=popup_layout, size_hint=(0.8, 0.7),
                                  auto_dismiss=False)
        self.active_popup.open()

    def ui_display_cardinal_second_target_popup(self, acting_player_obj, p1_swap_obj, valid_targets_for_p2_list,
                                                continuation_callback):
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        popup_layout, scroll_content = self._create_popup_layout_with_scroll(
            f"Cardinal: Choose 2nd player to swap with {p1_swap_obj.name}:"
        )
        for target in valid_targets_for_p2_list:
            btn = Button(text=target.name, size_hint_y=None, height="40dp")
            btn.bind(on_press=lambda inst, ap=acting_player_obj, p1s=p1_swap_obj, t2_id=target.id:
            (self.dismiss_active_popup(), continuation_callback(ap, p1s, t2_id)))
            scroll_content.add_widget(btn)
        self.active_popup = Popup(title="Cardinal Swap (2/2)", content=popup_layout, size_hint=(0.8, 0.7),
                                  auto_dismiss=False)
        self.active_popup.open()

    def ui_display_cardinal_look_choice_popup(self, acting_player_obj, p1_swapped_obj, p2_swapped_obj,
                                              continuation_callback):
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup_layout.add_widget(Label(text="Cardinal: Look at whose new hand?"))

        btn1 = Button(text=f"Look at {p1_swapped_obj.name}'s card", size_hint_y=None, height="40dp")
        btn1.bind(on_press=lambda inst, ap=acting_player_obj, look_id=p1_swapped_obj.id:
        (self.dismiss_active_popup(), continuation_callback(ap, look_id)))
        popup_layout.add_widget(btn1)
        btn2 = Button(text=f"Look at {p2_swapped_obj.name}'s card", size_hint_y=None, height="40dp")
        btn2.bind(on_press=lambda inst, ap=acting_player_obj, look_id=p2_swapped_obj.id:
        (self.dismiss_active_popup(), continuation_callback(ap, look_id)))
        popup_layout.add_widget(btn2)
        self.active_popup = Popup(title="Cardinal Look Choice", content=popup_layout, size_hint=(0.7, 0.5),
                                  auto_dismiss=False)
        self.active_popup.open()

    def award_round_tokens_and_check_game_over(self, list_of_winner_players):
        game_ended_this_round = False
        final_winner_of_game = None

        for winner_of_round in list_of_winner_players:
            if winner_of_round is None: continue

            self.log_message(f"{winner_of_round.name} gains a token of affection for winning the round!")
            winner_of_round.tokens += 1
            if self.check_game_over_on_token_gain(winner_of_round):
                game_ended_this_round = True
                final_winner_of_game = winner_of_round

            if self.current_round_manager._is_card_in_current_deck('Jester'):
                for p_observer in self.players_session_list:
                    if p_observer.id != winner_of_round.id and p_observer.jester_on_player_id == winner_of_round.id:
                        self.log_message(f"{p_observer.name} also gains token (Jester on {winner_of_round.name})!")
                        p_observer.tokens += 1
                        if not game_ended_this_round and self.check_game_over_on_token_gain(p_observer):
                            game_ended_this_round = True
                            final_winner_of_game = p_observer

        if game_ended_this_round and final_winner_of_game:
            self.handle_game_over_from_round(final_winner_of_game)

        self.update_ui_full()

    def check_game_over_on_token_gain(self, player_who_gained_token):
        if self.game_over_session_flag: return True
        if player_who_gained_token.tokens >= self.tokens_to_win_session:
            return True
        return False

    def handle_game_over_from_round(self, winner_of_game):
        if self.game_over_session_flag: return
        self.log_message(f"--- GAME OVER! {winner_of_game.name} wins the game with {winner_of_game.tokens} tokens! ---")
        self.game_over_session_flag = True
        if self.current_round_manager: self.current_round_manager.round_active = False
        self.update_ui_full()

class LoveLetterApp(App):
    def build(self):
        os.makedirs(CARD_FOLDER, exist_ok=True)
        self.title = 'Love Letter Board Game'
        
        # Tạo ScreenManager để quản lý các màn hình
        sm = ScreenManager(transition=FadeTransition(duration=0.5))
        
        # Thêm màn hình intro
        sm.add_widget(IntroScreen(name='intro'))
        
        # Thêm màn hình luật chơi
        sm.add_widget(RulesScreen(name='rules'))
        
        # Thêm màn hình game chính
        game_screen = Screen(name='game')
        self.game = LoveLetterGame()
        game_screen.add_widget(self.game)
        sm.add_widget(game_screen)
        
        # Bắt đầu với màn hình intro
        return sm

if __name__ == '__main__':
    os.makedirs(CARD_FOLDER, exist_ok=True)
    if not os.path.exists(CARD_BACK_IMAGE):
        try:
            from PIL import Image as PILImage, ImageDraw
            img = PILImage.new('RGB', (200, 300), color=(25, 40, 100))
            d = ImageDraw.Draw(img)
            d.text((10, 10), "CARD BACK", fill=(255, 255, 0))
            img.save(CARD_BACK_IMAGE)
            print(f"INFO: Created dummy {CARD_BACK_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create dummy card back: {e}")

    if not os.path.exists(ELIMINATED_IMAGE):
        try:
            from PIL import Image as PILImage, ImageDraw
            img = PILImage.new('RGB', (100, 150), color=(100, 20, 20))
            d = ImageDraw.Draw(img)
            d.text((10, 10), "ELIMINATED", fill=(255, 255, 255))
            img.save(ELIMINATED_IMAGE)
            print(f"INFO: Created dummy {ELIMINATED_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create dummy ELIMINATED_IMAGE: {e}")

    for card_name_key, card_detail_raw in CARDS_DATA_RAW.items():
        v_name = card_detail_raw['vietnamese_name']
        expected_path_png = os.path.join(CARD_FOLDER, f"{v_name}.png")
        expected_path_jpg = os.path.join(CARD_FOLDER, f"{v_name}.jpg")
        if not os.path.exists(expected_path_png) and not os.path.exists(expected_path_jpg):
            try:
                from PIL import Image as PILImage, ImageDraw
                img = PILImage.new('RGB', (200, 300),
                                color=(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
                d = ImageDraw.Draw(img)
                d.text((10, 10), card_name_key, fill=(255, 255, 255))
                d.text((10, 50), f"V:{card_detail_raw['value']}", fill=(255, 255, 255))
                d.text((10, 90), f"({v_name})", fill=(255, 255, 255))
                img.save(expected_path_png)
                print(f"INFO: Created dummy {expected_path_png} for {card_name_key}")
            except Exception as e:
                print(f"WARNING: Could not create dummy image for {card_name_key}: {e}")

    LoveLetterApp().run()