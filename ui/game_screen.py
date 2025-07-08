# file: game_screen.py

import os
import time
from functools import partial
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter

# Imports from local files
from logic.player import Player
from logic.deck import Deck
from logic.game_round import GameRound
from logic.card import Card
from logic.constants import CARD_PROTOTYPES, CARDS_DATA_RAW

from .constants import (
    CARD_RULES_IMAGE, EMPTY_CARD_IMAGE, CARD_BACK_IMAGE, ELIMINATED_IMAGE,
    CARD_VALUE_COLORS, VICTORY_IMAGE, DEFEAT_IMAGE
)
from ui.ui_components import StyledLabel, ImageButton, TurnNotificationPopup, create_selection_button

TUTORIAL_SCRIPT = [
    {
        'title': "Chào mừng đến với Hướng dẫn!",
        'text': ("Hướng dẫn này sẽ chỉ cho bạn cách chơi Thư Tình (Love Letter).\n"
                 "Bạn sẽ xem một ván đấu giữa hai người chơi máy: An và Bình.\n\n"
                 "Nhấn 'Tiếp tục' để bắt đầu."),
        'action': 'do_nothing'
    },
    {
        'title': "Bắt đầu Vòng đấu",
        'text': ("Mỗi vòng đấu bắt đầu bằng việc mỗi người chơi rút một lá bài. "
                 "Một lá bài cũng sẽ được 'đốt' (loại bỏ khỏi vòng chơi) mà không ai biết."),
        'action': 'setup_round_1'
    },
    {
        'title': "Lượt của An: Chơi Nam tước",
        'text': ("An đi trước. An rút lá Nam tước (3).\n"
                 "An có trên tay: Vệ binh (1) và Nam tước (3).\n"
                 "An sẽ chơi Nam tước để so bài với Bình."),
        'action': 'turn_1_an'
    },
    {
        'title': "Hiệu ứng Nam tước",
        'text': ("Nam tước so sánh bài trên tay. Người có lá bài giá trị thấp hơn sẽ bị loại.\n"
                 "An có Vệ binh (1), Bình có Thầy tu (2).\n"
                 "An có bài thấp hơn nên An bị loại!"),
        'action': 'resolve_baron_1'
    },
    {
        'title': "Kết thúc Vòng 1",
        'text': ("Vì An đã bị loại, Bình là người cuối cùng còn lại và thắng vòng này.\n"
                 "Bình nhận được một Tín vật Tình yêu. Cần 7 tín vật để thắng trò chơi (trong ván 2 người)."),
        'action': 'end_round_1'
    },
    {
        'title': "Vòng 2: Luật Nữ bá tước",
        'text': ("Bắt đầu vòng mới. Lần này, An có Cô hầu (4) và Bình có Vua (6).\n"
                 "Đến lượt Bình, và Bình rút trúng Nữ bá tước (7)."),
        'action': 'setup_round_2'
    },
    {
        'title': "Lượt của Bình: Chơi Nữ bá tước",
        'text': ("LUẬT QUAN TRỌNG: Nếu bạn có Nữ bá tước cùng với Vua hoặc Hoàng tử, bạn BẮT BUỘC phải chơi Nữ bá tước.\n"
                 "Bình chơi Nữ bá tước. Lá này không có hiệu ứng gì cả."),
        'action': 'turn_2_binh'
    },
    {
        'title': "Lượt của An: Chơi Cô hầu",
        'text': ("An rút được Vệ binh (1). An có trên tay Cô hầu (4) và Vệ binh (1).\n"
                 "An chơi Cô hầu để tự bảo vệ mình."),
        'action': 'turn_2_an'
    },
    {
        'title': "Hiệu ứng Cô hầu",
        'text': ("Khi một người chơi được 'bảo vệ' bởi Cô hầu, họ không thể bị nhắm đến bởi hiệu ứng của người chơi khác cho đến lượt tiếp theo của họ.\n"
                 "Hãy xem điều gì xảy ra khi Bình cố gắng sử dụng Vệ binh."),
        'action': 'do_nothing'
    },
    {
        'title': "Lượt của Bình: Vệ binh vô dụng",
        'text': ("Bình rút được Hoàng tử (5).\n"
                 "Bình muốn chơi Vệ binh để đoán bài của An, nhưng An đang được bảo vệ. Vệ binh không có mục tiêu hợp lệ, vì vậy hiệu ứng của nó bị lãng phí."),
        'action': 'turn_3_binh'
    },
    {
        'title': "Lượt của An: Chơi Vệ binh",
        'text': ("An không còn được bảo vệ nữa. An rút được Công chúa (8).\n"
                 "An sẽ chơi Vệ binh và đoán rằng Bình đang cầm Vua (6)."),
        'action': 'turn_3_an'
    },
    {
        'title': "Hiệu ứng Vệ binh",
        'text': ("An đoán Vua (6) và Bình đang cầm Vua (6). Đoán đúng!\n"
                 "Bình bị loại, và An thắng vòng này."),
        'action': 'resolve_guard_3'
    },
    {
        'title': "Kết thúc Hướng dẫn",
        'text': ("Bây giờ bạn đã biết những điều cơ bản!\n"
                 "Các lá bài khác như Hoàng tử (bắt người khác bỏ bài), Vua (tráo đổi bài) và Công chúa (bỏ là thua) cũng tạo nên những tình huống thú vị.\n"
                 "Chúc bạn chơi vui vẻ!"),
        'action': 'end_tutorial'
    },
]

class TutorialManager:
    def __init__(self, game_screen):
        self.game = game_screen
        self.current_step_index = -1
        self.script = TUTORIAL_SCRIPT
        self.popup = None
        self.temp_deck = None
        self.temp_round_manager = lambda: None # Mock object
        self.temp_round_manager.round_active = False

    def start(self):
        self.current_step_index = -1
        self.next_step()

    def next_step(self, *args):
        if self.popup:
            self.popup.dismiss()
            self.popup = None

        self.current_step_index += 1
        if self.current_step_index < len(self.script):
            self.run_current_step()
        else:
            self.game.end_tutorial_and_go_to_menu()

    def run_current_step(self):
        step = self.script[self.current_step_index]
        on_next = partial(self.execute_step_action, step)
        self.show_instructions(step['title'], step['text'], on_next)

    def show_instructions(self, title, text, on_next):
        if self.popup: self.popup.dismiss()

        popup_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        popup_layout.add_widget(StyledLabel(text=title, font_size=dp(24), bold=True, size_hint_y=None, height=dp(40), halign='center'))
        
        scroll = ScrollView(size_hint_y=1)
        info_label = StyledLabel(text=text, font_size=dp(18), halign='center', valign='top', size_hint_y=None)
        info_label.bind(width=lambda *x: info_label.setter('text_size')(info_label, (info_label.width, None)))
        info_label.bind(texture_size=info_label.setter('size'))
        scroll.add_widget(info_label)
        popup_layout.add_widget(scroll)

        next_button = create_selection_button("Tiếp tục", lambda *a: on_next())
        popup_layout.add_widget(next_button)

        self.popup = Popup(
            title="Hướng dẫn", content=popup_layout, size_hint=(0.7, 0.6), auto_dismiss=False,
            title_align='center', background_color=(0.1, 0.1, 0.15, 0.98)
        )
        self.popup.open()

    def execute_step_action(self, step):
        if self.popup:
            self.popup.dismiss()
            self.popup = None

        action_name = step.get('action')
        method = getattr(self, f"action_{action_name}", None)
        if method:
            method(step)
        else:
            self.next_step()
    
    def find_player(self, name): return next((p for p in self.game.players_session_list if p.name == name), None)
    def get_card(self, name): return CARD_PROTOTYPES[name]

    def action_do_nothing(self, step): self.next_step()
    def action_end_tutorial(self, step): self.game.end_tutorial_and_go_to_menu()

    def action_setup_round_1(self, step):
        self.game.log_message("--- Bắt đầu Vòng Hướng dẫn 1 ---")
        for p in self.game.players_session_list: p.reset_for_round()
        self.temp_deck = Deck(2, self.game.log_message)
        self.temp_deck.cards = [self.get_card(c) for c in ['Guard', 'Priest', 'Baron', 'Princess']]
        an, binh = self.find_player("An"), self.find_player("Bình")
        an.add_card_to_hand(self.get_card('Guard')); binh.add_card_to_hand(self.get_card('Priest'))
        self.game.current_round_manager = self.temp_round_manager
        self.game.current_round_manager.deck = self.temp_deck
        self.game.current_round_manager.round_active = True
        # Set initial player for the round before any UI update
        an_player = self.find_player("An")
        an_idx = self.game.players_session_list.index(an_player)
        self.game.current_round_manager.current_player_idx = an_idx
        self.game.ui_animate_deal(self.next_step)

    def _perform_turn(self, player_name, draw_card_name, play_card_name, on_complete):
        player = self.find_player(player_name)
        player_idx = self.game.players_session_list.index(player)
        self.game.current_round_manager.current_player_idx = player_idx
        self.game.turn_label.text = f"Lượt của: {player_name}"
        player.is_protected = False
        
        card_to_draw = self.get_card(draw_card_name)
        def after_draw():
            player.add_card_to_hand(card_to_draw)
            self.game.update_ui_full()
            card_to_play = self.get_card(play_card_name)
            def after_play():
                player.play_card(card_to_play.name)
                self.game.update_ui_full()
                on_complete()
            self.game.log_message(f"{player.name} chơi lá {card_to_play.name}")
            self.game.ui_animate_play_card(player, card_to_play, after_play)
        
        self.game.log_message(f"{player.name} rút lá {card_to_draw.name}")
        self.game.ui_animate_draw(player, after_draw)

    def action_turn_1_an(self, step): self._perform_turn("An", "Baron", "Baron", self.next_step)
    
    def action_resolve_baron_1(self, step):
        an, binh = self.find_player("An"), self.find_player("Bình")
        self.game.log_message(f"So bài Nam tước: An ({an.hand[0].value}) vs. Bình ({binh.hand[0].value})")
        an.is_eliminated = True
        self.game.ui_animate_elimination(an, self.next_step)

    def action_end_round_1(self, step):
        binh = self.find_player("Bình")
        binh.tokens += 1
        self.game.animate_token_fly(Label(text="*", font_size=dp(40), color=(1, 0.6, 0.6, 1), bold=True), self.game._get_player_widget_by_id(binh.id), self.next_step)

    def action_setup_round_2(self, step):
        self.game.log_message("--- Bắt đầu Vòng Hướng dẫn 2 ---")
        for p in self.game.players_session_list: p.reset_for_round()
        self.temp_deck.cards = [self.get_card(c) for c in ['Countess', 'Guard', 'Prince', 'Princess', 'King']]
        an, binh = self.find_player("An"), self.find_player("Bình")
        an.add_card_to_hand(self.get_card('Handmaid')); binh.add_card_to_hand(self.get_card('King'))
        # Set initial player for the round
        binh_player = self.find_player("Bình")
        binh_idx = self.game.players_session_list.index(binh_player)
        self.game.current_round_manager.current_player_idx = binh_idx
        self.game.ui_animate_deal(self.next_step)

    def action_turn_2_binh(self, step): self._perform_turn("Bình", "Countess", "Countess", self.next_step)
    def action_turn_2_an(self, step): self._perform_turn("An", "Guard", "Handmaid", self.next_step)
    def action_turn_3_binh(self, step): self._perform_turn("Bình", "Prince", "Guard", self.next_step)
    def action_turn_3_an(self, step): self._perform_turn("An", "Princess", "Guard", self.next_step)
    
    def action_resolve_guard_3(self, step):
        an, binh = self.find_player("An"), self.find_player("Bình")
        self.game.log_message(f"An dùng Vệ binh lên Bình, đoán Vua (6).")
        self.game.log_message(f"Bình có {binh.hand[0].name} ({binh.hand[0].value}). Đoán đúng!")
        binh.is_eliminated = True
        self.game.ui_animate_elimination(binh, self.next_step)


class LoveLetterGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_log = ["Chào mừng đến với Thư Tình (Kivy)!"]
        self.num_players_session = 0
        self.players_session_list = []
        self.human_player_id = 0
        self.current_round_manager = None
        self.tokens_to_win_session = 0
        self.game_over_session_flag = True
        self.active_popup = None
        self.waiting_for_input = False
        self.opponent_widgets_map = {}
        self.active_notification = None
        self.tutorial_manager = None
        self.log_container = None
        
        with self.canvas.before:
            Color(0.18, 0.07, 0.07, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        Clock.schedule_once(self._delayed_setup, 1)

    def _update_rect(self, instance, value):
        # This helper ensures background rectangles resize with the widget.
        bg_attr = getattr(instance, 'bg', None)
        if bg_attr:
            bg_attr.pos = instance.pos
            bg_attr.size = instance.size

    def _delayed_setup(self, dt):
        self._load_card_prototypes_and_images()
        self.setup_ui_placeholders()

    def _load_card_prototypes_and_images(self):
        # Populates the global CARD_PROTOTYPES dictionary with Card objects.
        global CARD_PROTOTYPES
        CARD_PROTOTYPES.clear()
        missing_card_back = not os.path.exists(CARD_BACK_IMAGE)
        if missing_card_back:
            self.log_message(f"LỖI NGHIÊM TRỌNG: Không tìm thấy ảnh mặt sau lá bài tại {CARD_BACK_IMAGE}", permanent=True)
        for eng_name, data in CARDS_DATA_RAW.items():
            viet_name = data['vietnamese_name']
            path_jpg = os.path.join("assets/cards", f"{viet_name}.jpg")
            path_png = os.path.join("assets/cards", f"{viet_name}.png")
            actual_path = next((p for p in [path_jpg, path_png] if os.path.exists(p)), None)
            if not actual_path:
                self.log_message(f"Cảnh báo: Không tìm thấy ảnh cho '{eng_name}' ({viet_name}). Sử dụng ảnh mặt sau.", permanent=True)
                actual_path = CARD_BACK_IMAGE if not missing_card_back else ""
            CARD_PROTOTYPES[eng_name] = Card(
                name=eng_name, value=data['value'], description=data['description'],
                image_path=actual_path, vietnamese_name=viet_name,
                count_classic=data['count_classic'], count_large=data['count_large']
            )
        self.log_message(f"Đã tải {len(CARD_PROTOTYPES)} loại lá bài.", permanent=True)

    def toggle_log_panel(self, instance):
        if not self.log_container:
            return
        if self.log_container.opacity == 0:
            # Show
            self.log_container.opacity = 1
            self.log_container.disabled = False
            # Re-add to bring to front
            self.remove_widget(self.log_container)
            self.add_widget(self.log_container)
        else:
            # Hide
            self.log_container.opacity = 0
            self.log_container.disabled = True

    # --- Game Lifecycle & UI Setup ---

    def initialize_game_setup(self):
        self._clear_animations_and_proceed(None)
        self.prompt_player_count()

    def setup_ui_placeholders(self):
        # Initial screen shown before a game starts.
        self.clear_widgets()
        welcome_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        welcome_layout.add_widget(StyledLabel(text="Board Game Thư Tình", font_size=32, color=(0.9, 0.7, 0.8, 1), size_hint_y=0.3))
        image_box = BoxLayout(size_hint_y=0.4)
        if os.path.exists(CARD_BACK_IMAGE):
            image_box.add_widget(Image(source=CARD_BACK_IMAGE, size_hint_max_x=0.7, pos_hint={'center_x': 0.5}))
        welcome_layout.add_widget(image_box)
        welcome_layout.add_widget(StyledLabel(text="Đang chờ bắt đầu trò chơi...", font_size=24, size_hint_y=0.3))
        self.add_widget(welcome_layout)

    def prompt_player_count(self):
        # Displays a popup to ask for the number of players.
        self.game_log = ["Chào mừng đến với Thư Tình (Kivy)!", "Vui lòng chọn số người chơi (2-4)."]
        if hasattr(self, 'message_label'): self.log_message("", permanent=False)
        self.dismiss_active_popup()

        popup_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
        popup_layout.add_widget(StyledLabel(text="Chọn số người chơi", font_size=28, bold=True, color=(1, 0.92, 0.7, 1), size_hint_y=None, height=50, halign='center'))
        popup_layout.add_widget(StyledLabel(text="(2 - 4 người, chỉ bản cơ bản)", font_size=18, color=(0.9, 0.9, 1, 0.8), size_hint_y=None, height=30, halign='center'))
        
        options_layout = GridLayout(cols=3, spacing=20, size_hint_y=None, height=70)
        for i in range(2, 5):
            btn = create_selection_button(str(i), self.initialize_game_with_player_count)
            btn.player_count = i
            options_layout.add_widget(btn)
        popup_layout.add_widget(options_layout)

        self.active_popup = Popup(
            title="Thư Tình - Bắt đầu", content=popup_layout, size_hint=(0.55, 0.38),
            auto_dismiss=False, title_color=(1, 0.9, 0.8, 1), title_size='22sp',
            title_align='center', separator_color=(0.8, 0.7, 0.3, 0.7), background_color=(0.09, 0.09, 0.13, 0.98)
        )
        self.active_popup.open()

    def initialize_game_with_player_count(self, instance):
        self.dismiss_active_popup()
        self.num_players_session = instance.player_count
        self.log_message(f"Số người chơi được đặt là: {self.num_players_session}")
        
        if self.num_players_session == 2: self.tokens_to_win_session = 7
        elif self.num_players_session == 3: self.tokens_to_win_session = 5
        else: self.tokens_to_win_session = 4
        
        self.log_message(f"Số tín vật cần để chiến thắng: {self.tokens_to_win_session}")
        self.players_session_list = [Player(id_num=0, name="Người chơi 1 (Bạn)")]
        self.human_player_id = 0
        for i in range(1, self.num_players_session):
            self.players_session_list.append(Player(id_num=i, name=f"Máy {i}", is_cpu=True))
        
        self.setup_main_ui()
        self.start_new_game_session()

    def setup_main_ui(self):
        self.clear_widgets()

        # --- Top Info Panel (Top-Left) ---
        info_bar = BoxLayout(orientation='vertical', size_hint=(0.28, None), pos_hint={'x': 0.01, 'top': 0.98}, spacing=dp(8), padding=dp(8))
        info_bar.bind(minimum_height=info_bar.setter('height'))
        with info_bar.canvas.before: Color(0, 0, 0, 0.3); info_bar.bg = RoundedRectangle(radius=[10]);
        info_bar.bind(pos=self._update_rect, size=self._update_rect)

        self.score_label = StyledLabel(text="Điểm số:", size_hint_y=None, height=dp(50), halign='left', valign='top', font_size=dp(16), bold=True, color=(0.95, 0.9, 0.7, 1))
        self.score_label.bind(width=lambda *x: self.score_label.setter('text_size')(self.score_label, (self.score_label.width, None)))
        self.turn_label = StyledLabel(text="Bắt đầu", size_hint_y=None, height=dp(30), halign='left', color=(1, 0.85, 0.3, 1), font_size=dp(18), bold=True)
        
        buttons_layout = BoxLayout(size_hint=(None, None), width=dp(220), height=dp(40), spacing=dp(10))
        rules_btn = create_selection_button("Luật", self.show_card_rules_popup)
        log_toggle_btn = create_selection_button("Nhật ký", self.toggle_log_panel)
        buttons_layout.add_widget(rules_btn)
        buttons_layout.add_widget(log_toggle_btn)
        
        info_bar.add_widget(self.score_label); info_bar.add_widget(self.turn_label); info_bar.add_widget(buttons_layout)
        self.add_widget(info_bar)

        # --- Log Panel (Right) ---
        self.log_container = BoxLayout(orientation='vertical', size_hint=(0.28, 0.8), pos_hint={'right': 0.99, 'y': 0.1}, padding=dp(8), spacing=dp(5))
        with self.log_container.canvas.before: Color(0, 0, 0, 0.4); self.log_container.bg = RoundedRectangle(radius=[10]);
        self.log_container.bind(pos=self._update_rect, size=self._update_rect)
        self.log_container.add_widget(StyledLabel(text="Nhật ký ván đấu", font_size=dp(18), bold=True, size_hint_y=None, height=dp(30)))
        log_scroll_view = ScrollView()
        self.message_label = Label(text="\n".join(self.game_log), size_hint_y=None, halign='left', valign='top', color=(0.95, 0.95, 0.98, 1), font_size=dp(14), padding=(10, 10))
        self.message_label.bind(texture_size=self.message_label.setter('size'))
        log_scroll_view.add_widget(self.message_label)
        self.log_container.add_widget(log_scroll_view)
        
        self.log_container.opacity = 0
        self.log_container.disabled = True
        self.add_widget(self.log_container)

        # --- Opponents Grid (Top-Center) ---
        self.opponents_grid = GridLayout(cols=min(3, self.num_players_session - 1 if self.num_players_session > 1 else 1),
                                         size_hint=(0.6, 0.22), pos_hint={'center_x': 0.5, 'top': 0.98}, spacing=dp(15), padding=dp(10))
        self.add_widget(self.opponents_grid)
        
        # --- Center Table Area ---
        center_table = RelativeLayout(size_hint=(0.4, 0.3), pos_hint={'center_x': 0.5, 'center_y': 0.55})
        
        # Deck
        deck_area = BoxLayout(orientation='vertical', size_hint=(0.4, 1), pos_hint={'x': 0, 'center_y': 0.5})
        deck_area.add_widget(StyledLabel(text="Chồng bài", size_hint_y=0.15, font_size=dp(16)))
        self.deck_image = Image(source=CARD_BACK_IMAGE, size_hint_y=0.7)
        self.deck_count_label = StyledLabel(text="0 lá", size_hint_y=0.15, font_size=dp(14))
        deck_area.add_widget(self.deck_image); deck_area.add_widget(self.deck_count_label)
        center_table.add_widget(deck_area)

        # Discard Pile
        played_card_area = BoxLayout(orientation='vertical', size_hint=(0.4, 1), pos_hint={'right': 1, 'center_y': 0.5})
        self.last_played_title = StyledLabel(text="Bài đã đánh", size_hint_y=0.15, font_size=dp(16))
        self.last_played_card_container = RelativeLayout(size_hint_y=0.85)
        played_card_area.add_widget(self.last_played_title); played_card_area.add_widget(self.last_played_card_container)
        center_table.add_widget(played_card_area)

        self.add_widget(center_table)
        
        # --- Player Hand Area (Bottom) ---
        self.human_player_display_wrapper = BoxLayout(orientation='vertical', size_hint=(0.85, 0.35), pos_hint={'center_x': 0.5, 'y': 0.1}, spacing=dp(5))
        player_header = StyledLabel(text="Bài của bạn (Nhấn để chơi, Chuột phải để xem chi tiết)", size_hint_y=None, height=dp(25), font_size=dp(14), bold=True, color=(0.7, 0.9, 0.8, 1))
        
        player_hand_container = BoxLayout(padding=dp(10))
        with player_hand_container.canvas.before: Color(0, 0, 0, 0.3); player_hand_container.bg = RoundedRectangle(radius=[15])
        player_hand_container.bind(pos=self._update_rect, size=self._update_rect)
        self.player_hand_area = BoxLayout(orientation='horizontal', spacing=dp(15), padding=dp(5))
        player_hand_container.add_widget(self.player_hand_area)
        
        self.human_player_display_wrapper.add_widget(player_hand_container)
        # self.human_player_display_wrapper.add_widget(player_header)
        self.add_widget(self.human_player_display_wrapper)

        # --- Action Button ---
        self.action_button = create_selection_button("Bắt đầu ván mới", self.on_press_action_button)
        self.action_button.size_hint = (0.35, 0.08)
        self.action_button.pos_hint = {'center_x': 0.5, 'y': 0.01}
        self.add_widget(self.action_button)
        
        # Store references for info not in the main bar
        self.round_info_label = Label() # Dummy labels to prevent crashes, info integrated elsewhere
        self.players_remaining_label = Label()

        self.update_ui_full()

    # --- UI Update & Rendering ---

    def log_message(self, msg, permanent=True):
        if permanent:
            self.game_log.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            if len(self.game_log) > 100: self.game_log = self.game_log[-100:]
        if hasattr(self, 'message_label') and self.message_label and self.message_label.parent:
            self.message_label.text = "\n".join(self.game_log)
            if isinstance(self.message_label.parent, ScrollView):
                self.message_label.parent.scroll_y = 0

    def update_ui_full(self):
        # Master function to refresh the entire UI based on game state.
        if not hasattr(self, 'score_label'): return

        score_texts = [f"{p.name}: {'★' * p.tokens}" for p in self.players_session_list]
        self.score_label.text = "\n".join(score_texts)

        is_round_active = self.current_round_manager and self.current_round_manager.round_active
        if self.game_over_session_flag:
            self.turn_label.text = "Trò chơi kết thúc!"
            if self.tutorial_manager is None:
                self.action_button.text = "Bắt đầu ván mới"
                self.action_button.disabled = False
                self.action_button.opacity = 1
        elif not is_round_active:
            self.turn_label.text = "Vòng đấu kết thúc"
            self.action_button.text = "Bắt đầu vòng tiếp theo"
            self.action_button.disabled = False
            self.action_button.opacity = 1
        else:
            current_player = self.players_session_list[self.current_round_manager.current_player_idx]
            self.turn_label.text = f"Lượt của: {current_player.name}"
            if self.tutorial_manager is None:
                self.action_button.text = ""
                self.action_button.disabled = True
                self.action_button.opacity = 0

        if self.current_round_manager and self.current_round_manager.deck:
            deck = self.current_round_manager.deck
            self.deck_count_label.text = f"{deck.count()} lá"
            self.deck_image.source = CARD_BACK_IMAGE if not deck.is_empty() else EMPTY_CARD_IMAGE
            self.deck_image.opacity = 1.0 if not deck.is_empty() else 0.3
        else:
            self.deck_count_label.text = "0 lá"; self.deck_image.source = EMPTY_CARD_IMAGE; self.deck_image.opacity = 0.3
        
        last_played_card, last_player = None, None
        all_discards = [(p, card, i) for p in self.players_session_list for i, card in enumerate(p.discard_pile)]
        if all_discards:
            last_player, last_played_card, _ = max(all_discards, key=lambda item: len(item[0].discard_pile) * 100 + item[2])
        
        self.last_played_card_container.clear_widgets()
        if last_played_card and last_player:
            self.last_played_card_container.add_widget(ImageButton(source=last_played_card.image_path, card_info_callback=self.display_card_info_popup, card_data=last_played_card, size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5}))
            self.last_played_title.text = f"Bài của: {last_player.name}"
        else:
            self.last_played_card_container.add_widget(Image(source=EMPTY_CARD_IMAGE, size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5}, opacity=0.3))
            self.last_played_title.text = "Chưa có bài"
        
        self.update_opponents_display()
        self.update_player_hand()
        self.log_message("", permanent=False)

    def update_opponents_display(self):
        self.opponents_grid.clear_widgets()
        self.opponent_widgets_map.clear()
        if not self.players_session_list: return
        
        opponents = []
        if self.human_player_id == -1: # Tutorial mode
             opponents = self.players_session_list
        else:
             opponents = [p for p in self.players_session_list if p.id != self.human_player_id]

        for p_opponent in opponents:
            opponent_container = BoxLayout(orientation='vertical', padding=dp(5), spacing=dp(3))
            with opponent_container.canvas.before:
                bg_color = (0.5, 0.1, 0.1, 0.9) if p_opponent.is_eliminated else (0.1, 0.1, 0.2, 0.9)
                Color(*bg_color)
                opponent_container.bg = RoundedRectangle(radius=[dp(10)])
            opponent_container.bind(pos=self._update_rect, size=self._update_rect)
            
            opponent_container.canvas.after.clear()
            if p_opponent.is_protected:
                with opponent_container.canvas.after:
                    Color(0.3, 0.8, 1, 0.9) # Bright blue
                    Line(rounded_rectangle=(opponent_container.x, opponent_container.y, opponent_container.width, opponent_container.height, dp(10)), width=dp(2))

            name_label = StyledLabel(text=f"{p_opponent.name[:10]} ({'★' * p_opponent.tokens})", font_size='13sp', bold=True, size_hint_y=0.2)
            opponent_container.add_widget(name_label)
            
            card_img_src = ELIMINATED_IMAGE if p_opponent.is_eliminated else CARD_BACK_IMAGE if p_opponent.hand else EMPTY_CARD_IMAGE
            # In tutorial, we want to see CPU hands for clarity
            if self.human_player_id == -1 and len(p_opponent.hand) > 0:
                card_img_src = p_opponent.hand[0].image_path
            
            card_image = Image(source=card_img_src, size_hint_y=0.6)
            if p_opponent.is_eliminated: card_image.color = (0.5, 0.5, 0.5, 1) # Gray out
            if not p_opponent.hand and not p_opponent.is_eliminated: card_image.opacity = 0.4
            opponent_container.add_widget(card_image)

            if p_opponent.discard_pile:
                discard_card = p_opponent.discard_pile[-1]
                discard_info = StyledLabel(text=f"Bỏ: {discard_card.name} ({discard_card.value})", font_size='10sp', size_hint_y=0.2)
            else:
                discard_info = StyledLabel(text="Chưa bỏ bài", font_size='10sp', size_hint_y=0.2)
            opponent_container.add_widget(discard_info)
            
            self.opponents_grid.add_widget(opponent_container)
            self.opponent_widgets_map[p_opponent.id] = {
                'container': opponent_container,
                'card_image': card_image
            }

    def update_player_hand(self):
        if self.human_player_id == -1: # Tutorial mode, no human player view
            if self.human_player_display_wrapper:
                self.human_player_display_wrapper.clear_widgets()
            return
            
        human_player = self.players_session_list[self.human_player_id]
        self.player_hand_area.clear_widgets()

        if human_player.is_eliminated:
            self.player_hand_area.add_widget(Image(source=ELIMINATED_IMAGE, color=(0.5,0.5,0.5,1)))
            self.player_hand_area.add_widget(StyledLabel(text="Đã bị loại!", color=(1, 0.5, 0.5, 1), font_size=24))
            return
        
        is_player_turn = self.current_round_manager and self.current_round_manager.round_active and self.current_round_manager.current_player_idx == self.human_player_id and not self.waiting_for_input
        
        self.player_hand_area.add_widget(StyledLabel(text=f"Tín vật:\n{'★' * human_player.tokens}", font_size='15sp', color=(1, 0.95, 0.5, 1), bold=True, halign='center', valign='middle'))

        for card_obj in human_player.hand:
            card_container = BoxLayout(orientation='vertical', size_hint_x=0.45, spacing=dp(5))
            
            card_button = ImageButton(source=card_obj.image_path, card_info_callback=self.display_card_info_popup, card_data=card_obj, disabled=not is_player_turn, opacity=1.0 if is_player_turn else 0.7)
            card_button.card_name = card_obj.name
            card_button.bind(on_press=self.on_player_card_selected)
            card_container.add_widget(card_button)
            
            card_info = StyledLabel(text=f"{card_obj.name} ({card_obj.value})", font_size='13sp', color=(1, 0.92, 0.7, 1), bold=True, size_hint_y=None, height=dp(25))
            card_container.add_widget(card_info)
            
            self.player_hand_area.add_widget(card_container)

    # --- Animation & Visual Effects ---

    def get_widget_center(self, widget):
        if not widget or not widget.parent: return self.center
        return widget.parent.to_window(*widget.center)

    def _animate_card_flight(self, source_widget, target_widget, card_image_path, on_complete, duration=0.6):
        if not self.parent: # Ensure the game screen is attached to a parent
            if on_complete: on_complete()
            return
            
        start_pos = self.get_widget_center(source_widget)
        end_pos = self.get_widget_center(target_widget)
        
        card_widget = Image(source=card_image_path, size_hint=(None, None), size=(dp(100), dp(140)), opacity=0.8)
        card_widget.center = start_pos
        card_widget.is_temp_anim = True
        
        self.add_widget(card_widget) # Add to game screen (FloatLayout)
        
        anim = Animation(center=end_pos, opacity=1, duration=duration, t='out_quad')
        def on_anim_end(*args):
            if card_widget.parent: self.remove_widget(card_widget)
            if on_complete: on_complete()
        anim.bind(on_complete=on_anim_end)
        anim.start(card_widget)

    def animate_token_fly(self, token_widget, target_widget, on_complete=None, duration=1.2):
        if not self.parent:
            if on_complete: on_complete()
            return
            
        start_pos = self.center
        end_pos = self.get_widget_center(target_widget)
        token_widget.size_hint = (None, None); token_widget.size = (dp(50), dp(50))
        token_widget.center = start_pos; token_widget.opacity = 0; token_widget.scale = 1.0
        self.add_widget(token_widget)
        anim = (Animation(opacity=1, scale=1.5, duration=duration * 0.2, t='out_quad') +
                Animation(center=end_pos, scale=0.5, duration=duration * 0.6, t='in_cubic') +
                Animation(opacity=0, duration=duration * 0.2))
        def final_callback(*args):
            if token_widget.parent: self.remove_widget(token_widget)
            self.update_ui_full()
            if on_complete: on_complete()
        anim.bind(on_complete=final_callback)
        anim.start(token_widget)

    def create_animated_rect(self, target_widget, color):
        if not self.parent: return None
        
        rect_container = Widget(size=(self.width, target_widget.height), pos=(0, target_widget.y), opacity=0)
        with rect_container.canvas:
            Color(*color)
            # The Rectangle's pos is relative to its parent Widget.
            rect_container.bg_rect = Rectangle(pos=(0, 0), size=rect_container.size)

        def update_rect_pos_size(instance, value):
            if not rect_container.parent: return
            # Update container widget's position (y) and size (height) based on target
            rect_container.y = instance.y
            rect_container.height = instance.height
            rect_container.size = (self.width, instance.height)
            # Update canvas instruction's size to match
            rect_container.bg_rect.size = rect_container.size

        # Bind to target widget's vertical position and size changes
        target_widget.bind(y=update_rect_pos_size, height=update_rect_pos_size)
        self.add_widget(rect_container)
        return rect_container

    def ui_animate_effect(self, effect_details, on_complete_callback=None):
        anim_type = effect_details.get('type')
        if anim_type == 'highlight_player':
            colors = {'target': (0.5, 0.8, 1, 0.6), 'elimination': (1, 0.2, 0.2, 0.7), 'protection': (0.2, 1, 0.2, 0.7)}
            highlight_color = colors.get(effect_details.get('color_type', 'target'), (0.7, 0.7, 0.7, 0.5))
            for p_id in effect_details.get('player_ids', []):
                widget = self._get_player_widget_by_id(p_id)
                if widget:
                    anim_rect = self.create_animated_rect(widget, highlight_color)
                    if not anim_rect: continue
                    anim = Animation(opacity=1, duration=0.2) + Animation(duration=0.6) + Animation(opacity=0, duration=0.3)
                    anim.bind(on_complete=lambda *args, r=anim_rect: self.remove_widget(r) if r.parent else None)
                    anim.start(anim_rect)
        if on_complete_callback: Clock.schedule_once(lambda dt: on_complete_callback(), 1.1)

    def show_turn_notification(self, title, details, stay_duration=2.5):
        if not self.parent: return
        if self.active_notification and self.active_notification.parent:
            Animation.cancel_all(self.active_notification)
            self.remove_widget(self.active_notification)
        notification = TurnNotificationPopup(title_text=title, detail_text=details)
        notification.pos_hint = {'center_x': 0.5, 'center_y': 0.65}; notification.opacity = 0; notification.scale = 0.8
        self.add_widget(notification)
        self.active_notification = notification
        anim = (Animation(opacity=1, scale=1, duration=0.4, t='out_back') + Animation(duration=stay_duration) + Animation(opacity=0, scale=0.8, duration=0.5, t='in_back'))
        def on_complete(*args):
            if notification.parent: notification.parent.remove_widget(notification)
            if self.active_notification == notification: self.active_notification = None
        anim.bind(on_complete=on_complete)
        anim.start(notification)

    def show_victory_defeat_effect(self, is_victory=True, on_complete=None):
        if not self.parent:
            if on_complete: on_complete()
            return

        img_path = VICTORY_IMAGE if is_victory else DEFEAT_IMAGE
        if not os.path.exists(img_path):
            if on_complete: on_complete()
            return
        
        effect_img = Image(
            source=img_path,
            size=(dp(600), dp(300)),
            allow_stretch=True,
            keep_ratio=False
        )
        scatter = Scatter(
            size_hint=(None, None),
            size=effect_img.size,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            do_rotation=False,
            do_translation=False,
            do_scale=True,
            scale=0.5,
            opacity=0,
            auto_bring_to_front=False,
        )
        scatter.add_widget(effect_img)
        scatter.is_temp_anim = True

        self.add_widget(scatter)
        anim = Animation(opacity=1, scale=1, duration=0.5, t='out_elastic') + Animation(duration=1.6) + Animation(opacity=0, scale=1.5, duration=0.5, t='in_quad')
        def remove_img(*_):
            if scatter.parent: self.remove_widget(scatter)
            if on_complete: on_complete()
        anim.bind(on_complete=remove_img)
        anim.start(scatter)
    
    # --- Event Handlers & Callbacks ---

    def _get_player_widget_by_id(self, player_id):
        if player_id == self.human_player_id:
            return self.human_player_display_wrapper
        widget_info = self.opponent_widgets_map.get(player_id)
        return widget_info['container'] if widget_info else None

    def _get_player_card_area_widget(self, player_id):
        if player_id == self.human_player_id:
            return self.player_hand_area
        widget_info = self.opponent_widgets_map.get(player_id)
        return widget_info['card_image'] if widget_info else None
        
    def on_press_action_button(self, instance):
        if instance.disabled: return
        if self.game_over_session_flag: self.prompt_player_count()
        elif self.current_round_manager and not self.current_round_manager.round_active: self.start_new_round()

    def on_player_card_selected(self, instance):
        if not self.current_round_manager or self.waiting_for_input: return
        self.set_waiting_for_input_flag(True)
        self.current_round_manager.human_plays_card(instance.card_name)

    def set_waiting_for_input_flag(self, is_waiting):
        self.waiting_for_input = is_waiting
        self.update_ui_full()

    def dismiss_active_popup(self):
        if self.active_popup:
            self.active_popup.dismiss(); self.active_popup = None

    def _clear_animations_and_proceed(self, on_complete_callback):
        if self.parent:
            for w in self.children[:]:
                if hasattr(w, 'is_temp_anim'): self.remove_widget(w)
        if on_complete_callback: on_complete_callback()

    # --- Game Logic Flow Control ---

    def start_new_game_session(self):
        self._clear_animations_and_proceed(None)
        self.log_message(f"--- Bắt đầu ván chơi mới với {self.num_players_session} người chơi ---")
        for p in self.players_session_list: p.tokens = 0
        self.game_over_session_flag = False
        self.start_new_round()

    def start_tutorial(self):
        self._clear_animations_and_proceed(None)
        self.game_log = ["Chào mừng đến với Hướng dẫn Thư Tình!"]
        self.num_players_session = 2
        self.players_session_list = [
            Player(id_num=0, name="An", is_cpu=True),
            Player(id_num=1, name="Bình", is_cpu=True)
        ]
        self.human_player_id = -1 # No human player
        self.tokens_to_win_session = 7
        self.game_over_session_flag = True # Prevent normal button presses
        self.active_popup = None
        self.waiting_for_input = False
        self.opponent_widgets_map = {}
        self.active_notification = None

        self.setup_main_ui()
        if hasattr(self, 'human_player_display_wrapper') and self.human_player_display_wrapper.parent:
            self.human_player_display_wrapper.parent.remove_widget(self.human_player_display_wrapper)
        
        self.action_button.text = "Thoát Hướng dẫn"
        self.action_button.unbind(on_press=self.on_press_action_button)
        self.action_button.bind(on_press=self.end_tutorial_and_go_to_menu)
        self.action_button.disabled = False
        self.action_button.opacity = 1

        self.tutorial_manager = TutorialManager(self)
        self.tutorial_manager.start()

    def end_tutorial_and_go_to_menu(self, *args):
        if self.tutorial_manager and self.tutorial_manager.popup:
            self.tutorial_manager.popup.dismiss()
            self.tutorial_manager = None
        if self.parent and hasattr(self.parent, 'manager'):
            self.parent.manager.current = 'intro'
        # Reset the game screen to its initial placeholder state
        Clock.schedule_once(lambda dt: self.setup_ui_placeholders(), 0.1)

    def start_new_round(self):
        self.log_message("--- Giao diện: Chuẩn bị vòng mới ---")
        self._clear_animations_and_proceed(None)
        if self.game_over_session_flag:
            self.log_message("Trò chơi đã kết thúc."); self.update_ui_full(); return

        game_deck = Deck(self.num_players_session, self.log_message)
        game_deck.burn_one_card(self.num_players_session)
        
        if game_deck.count() < self.num_players_session:
            self.log_message("Lỗi: Không đủ bài trong chồng bài."); self.game_over_session_flag = True; self.update_ui_full(); return

        ui_callbacks = {
            'update_ui_full_callback': self.update_ui_full,
            'set_waiting_flag_callback': self.set_waiting_for_input_flag,
            'get_active_popup_callback': lambda: self.active_popup,
            'dismiss_active_popup_callback': self.dismiss_active_popup,
            'request_target_selection_callback': self.ui_display_target_selection_popup,
            'request_confirmation_popup_callback': self.ui_display_confirmation_popup,
            'request_guard_value_popup_callback': self.ui_display_guard_value_popup,
            'award_round_tokens_callback': self.award_round_tokens_and_check_game_over,
            'check_game_over_token_callback': self.check_game_over_on_token_gain,
            'game_over_callback': self.handle_game_over_from_round,
            'animate_effect_callback': self.ui_animate_effect,
            'show_turn_notification_callback': self.show_turn_notification,
            'animate_deal_callback': self.ui_animate_deal,
            'animate_draw_callback': self.ui_animate_draw,
            'animate_play_card_callback': self.ui_animate_play_card,
            'animate_elimination_callback': self.ui_animate_elimination,
            'animate_king_swap_callback': self.ui_animate_king_swap,
            'animate_prince_discard_callback': self.ui_animate_prince_discard
        }
        self.current_round_manager = GameRound(self.players_session_list, game_deck, self.human_player_id, self.log_message, ui_callbacks)
        self.current_round_manager.start_round()

    def award_round_tokens_and_check_game_over(self, list_of_winner_players):
        self.update_ui_full()
        if not list_of_winner_players or not list_of_winner_players[0]:
            Clock.schedule_once(lambda dt: self.update_ui_full(), 1.0); return
            
        final_winner_of_game = None
        for winner_of_round in list_of_winner_players:
            if not winner_of_round: continue
            self.log_message(f"{winner_of_round.name} nhận được một tín vật tình yêu!")
            winner_of_round.tokens += 1
            if self.check_game_over_on_token_gain(winner_of_round):
                final_winner_of_game = winner_of_round
            
            player_widget = self._get_player_widget_by_id(winner_of_round.id)
            if player_widget:
                self.animate_token_fly(Label(text="★", font_size=dp(40), color=(1, 0.9, 0.4, 1), bold=True), player_widget)

        if final_winner_of_game:
            Clock.schedule_once(lambda dt: self.handle_game_over_from_round(final_winner_of_game), 1.5)
        else:
            Clock.schedule_once(lambda dt: self.update_ui_full(), 1.5)

    def check_game_over_on_token_gain(self, player):
        return not self.game_over_session_flag and player.tokens >= self.tokens_to_win_session

    def handle_game_over_from_round(self, winner_of_game):
        if self.game_over_session_flag: return
        self.log_message(f"--- TRÒ CHƠI KẾT THÚC! {winner_of_game.name} chiến thắng! ---")
        self.game_over_session_flag = True
        if self.current_round_manager: self.current_round_manager.round_active = False
        self.update_ui_full()
        self.display_victory_screen(winner_of_game)

    def display_victory_screen(self, winner):
        self.dismiss_active_popup()
        def show_popup(*_):
            layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
            with layout.canvas.before: Color(0.2, 0.2, 0.3, 0.9); layout.bg = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[15])
            layout.bind(pos=self._update_rect, size=self._update_rect)
            layout.add_widget(StyledLabel(text=f"{winner.name} CHIẾN THẮNG!", font_size=40, bold=True, color=(1, 0.9, 0.3, 1), size_hint_y=0.3))
            layout.add_widget(Image(source=VICTORY_IMAGE, size_hint_y=0.3))
            layout.add_widget(StyledLabel(text=f"Đã chinh phục trái tim của Công chúa!", font_size=22, color=(0.9, 0.9, 1, 1), size_hint_y=0.2, halign='center'))
            layout.add_widget(create_selection_button("Chơi Lại", lambda _: (self.dismiss_active_popup(), self.prompt_player_count())))
            self.active_popup = Popup(title="Kết Thúc Trò Chơi", content=layout, size_hint=(0.8, 0.7), auto_dismiss=False, background_color=(0.1, 0.1, 0.1, 0.8))
            self.active_popup.open()
        self.show_victory_defeat_effect(is_victory=(winner.id == self.human_player_id), on_complete=show_popup)

    # --- UI Popups ---

    def show_card_rules_popup(self, instance):
        self.dismiss_active_popup()
        if not os.path.exists(CARD_RULES_IMAGE):
            self.log_message(f"LỖI: Không tìm thấy ảnh luật chơi tại {CARD_RULES_IMAGE}"); return
        popup_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        popup_layout.add_widget(StyledLabel(text="Luật & Hiệu ứng các lá bài", font_size='22sp', color=(1, 0.9, 0.4, 1), size_hint_y=None, height=dp(40)))
        scroll_view = ScrollView(do_scroll_x=True, do_scroll_y=False)
        rules_image = Image(source=CARD_RULES_IMAGE, size_hint=(None, 1), allow_stretch=True)
        rules_image.bind(height=lambda i, h: setattr(i, 'width', h * i.image_ratio) if i.image_ratio > 0 else None)
        scroll_view.add_widget(rules_image)
        popup_layout.add_widget(create_selection_button("Đóng", lambda x: self.dismiss_active_popup(), color_scheme='cancel'))
        self.active_popup = Popup(title="", separator_height=0, content=popup_layout, size_hint=(0.95, 0.95), auto_dismiss=True, background_color=(0.18, 0.07, 0.07, 0.98))
        self.active_popup.bind(on_open=lambda popup: setattr(scroll_view, 'scroll_x', 0.5))
        self.active_popup.open()
        
    def display_card_info_popup(self, card_data):
        self.dismiss_active_popup()
        card_color = CARD_VALUE_COLORS.get(card_data.value, (0.5, 0.5, 0.5))
        popup_layout = BoxLayout(orientation='vertical', spacing=0, padding=0)
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(70), padding=[15, 5])
        with header.canvas.before: Color(*card_color, 0.9); header.bg = RoundedRectangle(radius=[5, 5, 0, 0])
        header.bind(pos=self._update_rect, size=self._update_rect)
        name_box = BoxLayout(orientation='vertical', size_hint_x=0.7)
        name_box.add_widget(StyledLabel(text=f"{card_data.name}", font_size=dp(24), bold=True, halign='left'))
        name_box.add_widget(StyledLabel(text=f"({card_data.vietnamese_name})", font_size=dp(16), italic=True, halign='left'))
        value_box = StyledLabel(text=f"Giá trị: {card_data.value}", font_size=dp(20), bold=True, size_hint_x=0.3)
        header.add_widget(name_box); header.add_widget(value_box)
        popup_layout.add_widget(header)
        # Content
        content = BoxLayout(padding=15, spacing=10)
        content.add_widget(Image(source=card_data.image_path, size_hint_x=0.4))
        effect_panel = BoxLayout(orientation='vertical', size_hint_x=0.6, spacing=10)
        effect_panel.add_widget(StyledLabel(text="Hiệu ứng:", font_size=dp(22), bold=True, color=(0.9, 0.8, 0.3, 1), size_hint_y=None, height=dp(40)))
        effect_box = ScrollView(); 
        effect_text = StyledLabel(text=card_data.description, font_size=dp(20), size_hint_y=None, halign='center', valign='middle', padding=(15,15), markup=True)
        effect_text.bind(width=lambda *x: effect_text.setter('text_size')(effect_text, (effect_text.width, None)), texture_size=effect_text.setter('size'))
        effect_box.add_widget(effect_text)
        effect_panel.add_widget(effect_box)
        content.add_widget(effect_panel)
        popup_layout.add_widget(content)
        # Footer
        footer = BoxLayout(size_hint_y=None, height=dp(60), padding=[dp(100), dp(5), dp(100), 0])
        footer.add_widget(create_selection_button("Đóng", lambda x: self.dismiss_active_popup(), color_scheme='cancel'))
        popup_layout.add_widget(footer)
        self.active_popup = Popup(title="", content=popup_layout, size_hint=(0.85, 0.8), separator_height=0, auto_dismiss=True, background_color=(0.1, 0.1, 0.1, 0.95))
        self.active_popup.open()
        
    def ui_display_target_selection_popup(self, acting_player, card_played, valid_targets, on_select, on_cancel):
        self.dismiss_active_popup(); self.set_waiting_for_input_flag(True)
        popup_layout = BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(30))
        header_box = BoxLayout(size_hint_y=None, height=dp(80), spacing=18)
        header_box.add_widget(Image(source=card_played.image_path, size_hint_x=0.25))
        info_box = BoxLayout(orientation='vertical', size_hint_x=0.75)
        info_box.add_widget(StyledLabel(text=f"{card_played.name}", font_size=20, color=(1, 0.92, 0.7, 1), bold=True))
        info_box.add_widget(StyledLabel(text=card_played.description, font_size=15, color=(1, 1, 1, 0.85)))
        popup_layout.add_widget(header_box)
        popup_layout.add_widget(StyledLabel(text=f"Chọn mục tiêu:", font_size=18, color=(1, 0.92, 0.7, 1), size_hint_y=None, height=dp(36)))
        
        target_grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        target_grid.bind(minimum_height=target_grid.setter('height'))
        for target in valid_targets:
            target_grid.add_widget(create_selection_button(f"{target.name}{' (Chính mình)' if target == acting_player else ''}", lambda _, t=target.id: (self.dismiss_active_popup(), on_select(acting_player, t))))
        scroll_view = ScrollView(); scroll_view.add_widget(target_grid)
        popup_layout.add_widget(scroll_view)
        
        popup_layout.add_widget(create_selection_button("Quay lại (Chọn lá khác)", lambda _: on_cancel(acting_player), color_scheme='cancel'))
        self.active_popup = Popup(title=f"Chơi {card_played.name}", content=popup_layout, size_hint=(0.8, 0.85), auto_dismiss=False, title_size='20sp', background_color=(0.18, 0.07, 0.07, 0.98))
        self.active_popup.open()

    def ui_display_confirmation_popup(self, acting_player, card_played, on_confirm, on_cancel):
        self.dismiss_active_popup(); self.set_waiting_for_input_flag(True)
        popup_layout = BoxLayout(orientation='vertical', spacing=dp(24), padding=dp(36))
        header_box = BoxLayout(size_hint_y=0.6, spacing=18)
        header_box.add_widget(Image(source=card_played.image_path, size_hint_x=0.35))
        info_box = BoxLayout(orientation='vertical', size_hint_x=0.65)
        info_box.add_widget(StyledLabel(text=f"{card_played.name} (Giá trị: {card_played.value})", font_size=20, color=(1, 0.92, 0.7, 1), bold=True))
        info_box.add_widget(StyledLabel(text=f"[b]Hiệu ứng:[/b] {card_played.description}", font_size=15, markup=True, color=(1, 1, 1, 0.85)))
        popup_layout.add_widget(header_box)
        
        button_box = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=15)
        button_box.add_widget(create_selection_button(f"Xác nhận chơi {card_played.name}", lambda _: (self.dismiss_active_popup(), on_confirm(acting_player)), color_scheme='confirm'))
        button_box.add_widget(create_selection_button("Quay lại (Chọn lá khác)", lambda _: on_cancel(acting_player), color_scheme='cancel'))
        popup_layout.add_widget(button_box)
        self.active_popup = Popup(title="Xác nhận chơi bài", content=popup_layout, size_hint=(0.7, 0.6), auto_dismiss=False, title_size='20sp', background_color=(0.18, 0.07, 0.07, 0.98))
        self.active_popup.open()

    def ui_display_guard_value_popup(self, acting_player, target_player, possible_values, on_select, on_cancel):
        self.dismiss_active_popup(); self.set_waiting_for_input_flag(True)
        popup_layout = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        popup_layout.add_widget(StyledLabel(text=f"Đoán bài của {target_player.name} (không phải 1):", font_size=18, color=(1, 0.9, 0.7, 1), size_hint_y=None, height=dp(50)))
        options_grid = GridLayout(cols=4, spacing=dp(10))
        for val in possible_values:
            options_grid.add_widget(create_selection_button(str(val), lambda _, v=val: (self.dismiss_active_popup(), on_select(acting_player, target_player, v))))
        popup_layout.add_widget(options_grid)
        popup_layout.add_widget(create_selection_button("Quay lại (Chọn lá khác)", lambda _: on_cancel(acting_player), color_scheme='cancel'))
        self.active_popup = Popup(title="Chọn giá trị cho Cận vệ", content=popup_layout, size_hint=(0.7, 0.6), auto_dismiss=False, title_size='20sp')
        self.active_popup.open()

    # --- Animation Callbacks for GameRound ---
    def ui_animate_deal(self, on_complete):
        self.update_ui_full()

        def _start_deal_animation(dt):
            delay = 0.0
            players_to_animate = []
            if self.human_player_id == -1: # Tutorial mode
                players_to_animate = self.players_session_list
            else:
                players_to_animate = self.players_session_list
            
            for player in players_to_animate:
                target_widget = self._get_player_card_area_widget(player.id)
                if target_widget:
                    Clock.schedule_once(lambda _, p=player, t=target_widget: self._animate_card_flight(self.deck_image, t, CARD_BACK_IMAGE, None), delay)
                    delay += 0.2
            Clock.schedule_once(lambda _, oc=on_complete: oc(), delay + 0.5)

        Clock.schedule_once(_start_deal_animation)


    def ui_animate_draw(self, player, on_complete):
        target_widget = self._get_player_card_area_widget(player.id)
        if target_widget:
            self._animate_card_flight(self.deck_image, target_widget, CARD_BACK_IMAGE, on_complete)
        else:
            if on_complete: on_complete()

    def ui_animate_play_card(self, player, card, on_complete):
        source_widget = self._get_player_card_area_widget(player.id)
        if source_widget:
            self._animate_card_flight(source_widget, self.last_played_card_container, card.image_path, on_complete)
        else:
            if on_complete: on_complete()
        
    def ui_animate_elimination(self, player, on_complete):
        self.ui_animate_effect({'type': 'highlight_player', 'player_ids': [player.id], 'color_type': 'elimination'}, on_complete)
        self.update_ui_full()

    def ui_animate_king_swap(self, player1, player2, on_complete):
        if not self.parent:
            if on_complete: on_complete()
            return
            
        p1_widget = self._get_player_card_area_widget(player1.id)
        p2_widget = self._get_player_card_area_widget(player2.id)
        
        if not p1_widget or not p2_widget:
            if on_complete: on_complete()
            return

        p1_pos, p2_pos = self.get_widget_center(p1_widget), self.get_widget_center(p2_widget)
        
        card1 = Image(source=CARD_BACK_IMAGE, size_hint=(None, None), size=(dp(80), dp(112)), center=p1_pos)
        card2 = Image(source=CARD_BACK_IMAGE, size_hint=(None, None), size=(dp(80), dp(112)), center=p2_pos)
        
        self.add_widget(card1); self.add_widget(card2)
        
        anim1 = Animation(center=p2_pos, duration=0.8, t='in_out_sine')
        anim2 = Animation(center=p1_pos, duration=0.8, t='in_out_sine')
        
        def on_anim_end(*args):
            if card1.parent: self.remove_widget(card1)
            if card2.parent: self.remove_widget(card2)
            self.update_ui_full()
            if on_complete: on_complete()
            
        anim1.bind(on_complete=on_anim_end)
        anim1.start(card1); anim2.start(card2)

    def ui_animate_prince_discard(self, target_player, discarded_card, on_complete, draw_new=False):
        source_widget = self._get_player_card_area_widget(target_player.id)
        discard_pile_widget = self.last_played_card_container
        
        def after_discard():
            self.update_ui_full()
            if draw_new:
                self.ui_animate_draw(target_player, on_complete)
            elif on_complete:
                on_complete()

        if source_widget:
            self._animate_card_flight(source_widget, discard_pile_widget, discarded_card.image_path, after_discard)
        else:
            after_discard()

