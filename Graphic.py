# main.py with enhanced UI

import os
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
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
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

INTRO_BACKGROUND = "assets/intro.jpg"  # Tạo file này hoặc dùng ảnh có sẵn
RULES_BACKGROUND = "assets/rule.jpg"  # Tạo file này hoặc dùng ảnh có sẵn
EMPTY_CARD_IMAGE = "assets/cards/empty_card.png"

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
        self.card_info_callback = kwargs.pop('card_info_callback', None)
        self.card_data = kwargs.pop('card_data', None)
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True
        
    def on_press(self):
        # Add slight scale effect on press
        self.opacity = 0.8
        
    def on_release(self):
        self.opacity = 1.0
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Check for right click (button = 'right')
            if touch.button == 'right' and self.card_info_callback and self.card_data:
                self.card_info_callback(self.card_data)
                return True
        # Call parent method for regular click handling
        return super(ImageButton, self).on_touch_down(touch)

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
        
    def display_card_info_popup(self, card_data):
        """Display detailed information about a card in a popup"""
        self.dismiss_active_popup()  # Close any existing popup
        
        # Card type colors based on value
        card_colors = {
            0: (0.5, 0.5, 0.5),  # Assassin, Jester - Gray
            1: (0.2, 0.4, 1.0),  # Guard - Blue
            2: (0.7, 0.7, 1.0),  # Priest/Cardinal - Light blue
            3: (0.6, 0.3, 0.7),  # Baron/Baroness - Purple
            4: (0.3, 0.7, 0.3),  # Handmaid/Sycophant - Green
            5: (0.9, 0.7, 0.2),  # Prince/Count - Gold
            6: (0.9, 0.5, 0.3),  # King/Sheriff - Orange
            7: (0.7, 0.3, 0.7),  # Countess/Queen Mother - Violet
            8: (1.0, 0.3, 0.3),  # Princess - Red
            9: (0.9, 0.9, 1.0),  # Bishop - White
        }
        
        # Get card color based on value
        card_value = card_data.value if hasattr(card_data, 'value') else 0
        card_color = card_colors.get(card_value, (0.5, 0.5, 0.5))
        
        # Create main popup layout
        popup_layout = BoxLayout(orientation='vertical', spacing=0, padding=0)
        
        # Create header with integrated info
        header = BoxLayout(orientation='vertical', 
                        size_hint_y=0.15, 
                        padding=[15, 5])
        with header.canvas.before:
            Color(*card_color, 0.9)  # More opacity for better visibility
            self.header_bg = RoundedRectangle(pos=header.pos, 
                                            size=header.size, 
                                            radius=[5, 5, 0, 0])
        header.bind(pos=self._update_card_popup_header, size=self._update_card_popup_header)
        
        # Card name with Vietnamese name underneath
        name_row = BoxLayout(orientation='horizontal')
        
        name_box = BoxLayout(orientation='vertical', size_hint_x=0.7)
        card_name_label = StyledLabel(
            text=f"{card_data.name}",
            font_size=24,
            bold=True,
            color=(1, 1, 1, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 0.5),
            halign='left'
        )
        name_box.add_widget(card_name_label)
        
        # Vietnamese name directly below English name
        if hasattr(card_data, 'vietnamese_name'):
            viet_name_label = StyledLabel(
                text=f"({card_data.vietnamese_name})",
                font_size=16,
                italic=True,
                color=(1, 1, 1, 0.9),
                halign='left'
            )
            name_box.add_widget(viet_name_label)
        
        # Value with more emphasis
        value_box = BoxLayout(orientation='vertical', size_hint_x=0.3)
        value_label = StyledLabel(
            text=f"Value: {card_data.value}",
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1),
            outline_width=1,
            outline_color=(0, 0, 0, 0.5)
        )
        value_box.add_widget(value_label)
        
        name_row.add_widget(name_box)
        name_row.add_widget(value_box)
        header.add_widget(name_row)
        
        popup_layout.add_widget(header)
        
        # Main content in horizontal layout
        content = BoxLayout(orientation='horizontal', padding=15, spacing=10)
        
        # Left: Card image with better framing
        image_frame = BoxLayout(orientation='vertical', size_hint_x=0.4, padding=5)
        with image_frame.canvas.before:
            Color(0.15, 0.15, 0.2, 0.8)  # Darker background for contrast
            self.image_bg = RoundedRectangle(pos=image_frame.pos, 
                                        size=image_frame.size, 
                                        radius=[5])
        image_frame.bind(pos=self._update_card_popup_image_bg, 
                    size=self._update_card_popup_image_bg)
        
        card_image = Image(
            source=card_data.image_path,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}  # Center the image
        )
        image_frame.add_widget(card_image)
        content.add_widget(image_frame)
        
        # Right: Card effect with centered text
        effect_panel = BoxLayout(orientation='vertical', 
                            size_hint_x=0.6,
                            spacing=10)
        
        # Effect title
        effect_title = StyledLabel(
            text="Effect:",
            font_size=22,
            bold=True,
            color=(0.9, 0.8, 0.3, 1),
            size_hint_y=None,
            height=40,
            halign='center'
        )
        effect_title.bind(size=effect_title.setter('text_size'))
        effect_panel.add_widget(effect_title)
        
        # Effect content box with dark background
        effect_box = BoxLayout(size_hint_y=1, padding=10)
        with effect_box.canvas.before:
            Color(0.15, 0.15, 0.2, 0.6)
            RoundedRectangle(pos=effect_box.pos, size=effect_box.size, radius=[5])
        effect_box.bind(pos=lambda *x: self._update_card_effect_bg(effect_box), 
                    size=lambda *x: self._update_card_effect_bg(effect_box))
        
        # Scrollable effect description (centered)
        effect_scroll = ScrollView(do_scroll_x=False)
        
        # Larger, centered effect text
        effect_text = StyledLabel(
            text=card_data.description,
            font_size=20,
            size_hint_y=None,
            halign='center',
            valign='middle',
            color=(0.95, 0.95, 1, 1),
            padding=(15, 15),
            markup=True
        )
        
        effect_text.bind(width=lambda *x: effect_text.setter('text_size')(effect_text, (effect_text.width, None)))
        effect_text.bind(texture_size=effect_text.setter('size'))
        effect_scroll.add_widget(effect_text)
        effect_box.add_widget(effect_scroll)
        effect_panel.add_widget(effect_box)
        
        content.add_widget(effect_panel)
        popup_layout.add_widget(content)
        
        # Footer with close button
        footer = BoxLayout(
            orientation='horizontal', 
            size_hint_y=0.1, 
            padding=[15, 10]
        )
        
        # Center the close button
        footer.add_widget(Widget(size_hint_x=0.35))
        
        close_btn = Button(
            text="Close",
            size_hint=(0.3, 0.8),
            background_color=(*card_color, 1.0),
            font_size=18,
            bold=True
        )
        close_btn.bind(on_press=lambda x: self.dismiss_active_popup())
        footer.add_widget(close_btn)
        
        footer.add_widget(Widget(size_hint_x=0.35))
        popup_layout.add_widget(footer)
        
        # Create popup with nice styling
        self.active_popup = Popup(
            title="Card Information",
            content=popup_layout,
            size_hint=(0.85, 0.8),
            title_color=(0.9, 0.9, 0.7, 1),
            title_size='20sp',
            title_align='center',
            separator_color=card_color,
            auto_dismiss=True
        )
        
        self.active_popup.open()

    # Add helper method for updating effect background
    def _update_card_effect_bg(self, instance):
        for child in instance.canvas.before.children:
            if isinstance(child, RoundedRectangle):
                child.pos = instance.pos
                child.size = instance.size

    # Add helper methods to update backgrounds
    def _update_card_popup_header(self, instance, value):
        if hasattr(self, 'header_bg'):
            self.header_bg.pos = instance.pos
            self.header_bg.size = instance.size

    def _update_card_popup_image_bg(self, instance, value):
        if hasattr(self, 'image_bg'):
            self.image_bg.pos = instance.pos
            self.image_bg.size = instance.size
    
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
        top_section = BoxLayout(size_hint_y=0.17, orientation='vertical', spacing=5)
        
        # Info bar with improved styling
        info_bar = BoxLayout(size_hint_y=None, height=40, padding=[10, 5])
        with info_bar.canvas.before:
            # Gradient màu đẹp hơn
            Color(0.25, 0.35, 0.55, 0.85)
            RoundedRectangle(pos=info_bar.pos, size=info_bar.size, radius=[10,])
        info_bar.bind(pos=self._update_info_bar_bg, size=self._update_info_bar_bg)
            
        self.score_label = StyledLabel(
            text="Scores:", 
            size_hint_x=0.7, 
            halign='left', 
            valign='middle', 
            font_size=16,
            bold=True,
            color=(0.95, 0.9, 0.7, 1)  # Màu vàng gold cho điểm số
        )
        self.score_label.bind(size=self.score_label.setter('text_size'))
        
        self.turn_label = StyledLabel(
            text="Game Over", 
            size_hint_x=0.3, 
            halign='right', 
            valign='middle', 
            color=(1, 0.85, 0.3, 1),  # Màu vàng sáng hơn
            font_size=17,
            bold=True
        )
        
        self.turn_label.bind(size=self.turn_label.setter('text_size'))
        
        info_bar.add_widget(self.score_label)
        info_bar.add_widget(self.turn_label)
        top_section.add_widget(info_bar)
        
        # Game log with improved styling
        log_container = BoxLayout(size_hint_y=1, padding=[10, 5])
        with log_container.canvas.before:
            # Màu tối hơn và đẹp hơn
            Color(0.08, 0.08, 0.15, 0.8)
            RoundedRectangle(pos=log_container.pos, size=log_container.size, radius=[10,])
        log_container.bind(pos=self._update_log_container_bg, size=self._update_log_container_bg)
        
        log_scroll_view = ScrollView(size_hint_y=1)
        self.message_label = Label(
            text="\n".join(self.game_log), 
            size_hint_y=None, 
            halign='left', 
            valign='top',
            color=(0.95, 0.95, 0.98, 1),  # Màu sáng hơn
            font_size=14,
            padding=(15, 10),  # Padding lớn hơn
            font_name='Roboto'  # Sử dụng font Roboto nếu có
        )
        self.message_label.bind(texture_size=self.message_label.setter('size'))
        log_scroll_view.add_widget(self.message_label)
        log_container.add_widget(log_scroll_view)
        top_section.add_widget(log_container)
        self.add_widget(top_section)

        # Game area with better layout
        game_area = BoxLayout(orientation='vertical', spacing=15, size_hint_y=0.7)
        
        # Opponents area with title
        opponents_header = BoxLayout(size_hint_y=None, height=35, padding=[10, 0])
        with opponents_header.canvas.before:
            Color(0.2, 0.2, 0.35, 0.8)  # Màu nền tối
            RoundedRectangle(pos=opponents_header.pos, size=opponents_header.size, radius=[10, 10, 0, 0])
        opponents_header.bind(pos=self._update_opponents_header_bg, size=self._update_opponents_header_bg)

        title_icon = BoxLayout(size_hint_x=0.08)  # Thêm không gian cho icon (nếu muốn)
        opponents_header.add_widget(title_icon)

        opponents_header.add_widget(StyledLabel(
            text="Opponents", 
            size_hint_x=0.92,
            size_hint_y=None, 
            height=35, 
            font_size=18,
            bold=True,
            color=(0.95, 0.8, 0.4, 1)  # Màu vàng sáng hơn
        ))
        game_area.add_widget(opponents_header)
        
        # Improved opponents display
        opponents_container = BoxLayout(size_hint_y=0.4, padding=[5, 0, 5, 10])
        with opponents_container.canvas.before:
            Color(0.12, 0.12, 0.22, 0.8)  # Màu nền tối hơn
            self.opponents_bg = RoundedRectangle(pos=opponents_container.pos, size=opponents_container.size, radius=[0, 0, 10, 10])
        opponents_container.bind(pos=self._update_opponents_container_bg, size=self._update_opponents_container_bg)

        self.opponents_area_scrollview = ScrollView(size_hint=(1, 1))
        self.opponents_grid = GridLayout(
            cols=max(1, min(4, self.num_players_session - 1) if self.num_players_session > 1 else 1),
            size_hint_x=None if self.num_players_session - 1 > 3 else 1, 
            size_hint_y=None,
            spacing=15,  # Tăng khoảng cách giữa các đối thủ
            padding=[10, 10]  # Thêm padding
        )
        self.opponents_grid.bind(minimum_width=self.opponents_grid.setter('width'))
        self.opponents_grid.bind(minimum_height=self.opponents_grid.setter('height'))
        self.opponents_area_scrollview.add_widget(self.opponents_grid)
        opponents_container.add_widget(self.opponents_area_scrollview)
        game_area.add_widget(opponents_container)
        
        # Player hand area with improved styling
        self.human_player_display_wrapper = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)
        
        player_header = BoxLayout(size_hint_y=None, height=35, padding=[10, 0])
        with player_header.canvas.before:
            Color(0.15, 0.3, 0.25, 0.8)  # Màu xanh lục đậm
            RoundedRectangle(pos=player_header.pos, size=player_header.size, radius=[10, 10, 0, 0])
        player_header.bind(pos=self._update_player_header_bg, size=self._update_player_header_bg)

        player_icon = BoxLayout(size_hint_x=0.08)  # Không gian cho icon (tương lai)
        player_header.add_widget(player_icon)

        player_header.add_widget(StyledLabel(
            text="Your Hand (Click to Play)", 
            size_hint_x=0.92,
            size_hint_y=None, 
            height=35, 
            font_size=18,
            bold=True,
            color=(0.4, 0.9, 0.7, 1)  # Màu xanh sáng hơn
        ))
        self.human_player_display_wrapper.add_widget(player_header)
        
        player_hand_container = BoxLayout(size_hint_y=0.7)
        with player_hand_container.canvas.before:
            Color(0.08, 0.2, 0.15, 0.8)  # Màu tối hơn để lá bài nổi bật
            RoundedRectangle(pos=player_hand_container.pos, size=player_hand_container.size, radius=[0, 0, 10, 10])
        player_hand_container.bind(pos=self._update_player_hand_bg, size=self._update_player_hand_bg)

        self.player_hand_area = BoxLayout(orientation='horizontal', spacing=20, padding=[20, 15])  # Padding lớn hơn
        player_hand_container.add_widget(self.player_hand_area)
        self.human_player_display_wrapper.add_widget(player_hand_container)
        
        game_area.add_widget(self.human_player_display_wrapper)
        center_game_area = BoxLayout(size_hint_y=0.2, spacing=10, padding=[10, 5])

        # Khu vực bên trái: Deck (nhỏ gọn)
        left_area = BoxLayout(orientation='vertical', size_hint_x=0.25)
        deck_title = StyledLabel(
            text="Deck", 
            size_hint_y=0.2,
            font_size=16,
            color=(0.9, 0.9, 0.7, 1)
        )
        left_area.add_widget(deck_title)

        # Deck nhỏ gọn với hiệu ứng 3D
        deck_display = RelativeLayout(size_hint_y=0.6)
        for i in range(2):  # Giảm số lớp để không tốn quá nhiều không gian
            offset = 1.0 * (i + 1)
            shadow_card = Image(
                source=CARD_BACK_IMAGE,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(0.8, 0.8),  # Nhỏ hơn
                pos_hint={'center_x': 0.5 - 0.02 * offset, 'center_y': 0.5 - 0.02 * offset},
                opacity=0.5 - 0.15*i
            )
            deck_display.add_widget(shadow_card)

        self.deck_image = Image(
            source=CARD_BACK_IMAGE, 
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.8, 0.8),  # Nhỏ hơn
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        deck_display.add_widget(self.deck_image)
        left_area.add_widget(deck_display)

        # Số lượng lá bài còn lại
        self.deck_count_label = StyledLabel(
            text="0 cards", 
            size_hint_y=0.2,
            font_size=14,
            color=(0.9, 0.9, 0.7, 1)
        )
        left_area.add_widget(self.deck_count_label)

        # Khu vực chính giữa: Lá bài được đánh ra gần đây (lớn)
        center_area = BoxLayout(orientation='vertical', size_hint_x=0.5)
        self.last_played_title = StyledLabel(
            text="Lá bài vừa đánh", 
            size_hint_y=0.2,
            font_size=16,
            bold=True,
            color=(0.9, 0.8, 0.3, 1)
        )
        center_area.add_widget(self.last_played_title)

        # Chứa lá bài đánh ra với hiệu ứng bóng đổ
        played_card_frame = BoxLayout(size_hint_y=0.8, padding=[10, 5])
        with played_card_frame.canvas.before:
            Color(0.1, 0.15, 0.2, 0.5)  # Nền tối hơn để lá bài nổi bật
            RoundedRectangle(pos=played_card_frame.pos, size=played_card_frame.size, radius=[10,])
        played_card_frame.bind(pos=self._update_played_card_frame_bg, size=self._update_played_card_frame_bg)

        self.last_played_card_container = RelativeLayout(size_hint=(1, 1))
        self.last_played_card_image = Image(
            source=EMPTY_CARD_IMAGE,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.9, 0.9),  # Lớn hơn
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0.3
        )
        self.last_played_card_container.add_widget(self.last_played_card_image)
        played_card_frame.add_widget(self.last_played_card_container)
        center_area.add_widget(played_card_frame)

        # Khu vực bên phải: Thông tin trò chơi
        right_area = BoxLayout(orientation='vertical', size_hint_x=0.25)
        game_info_title = StyledLabel(
            text="Thông tin", 
            size_hint_y=0.2,
            font_size=16,
            color=(0.9, 0.9, 0.7, 1)
        )
        right_area.add_widget(game_info_title)

        # Thông tin trò chơi với nền tối
        game_info_frame = BoxLayout(orientation='vertical', size_hint_y=0.8)
        with game_info_frame.canvas.before:
            Color(0.1, 0.15, 0.2, 0.5)
            RoundedRectangle(pos=game_info_frame.pos, size=game_info_frame.size, radius=[10,])
        game_info_frame.bind(pos=self._update_game_info_frame_bg, size=self._update_game_info_frame_bg)

        # Thông tin về vòng đấu và số người chơi còn lại
        self.round_info_label = StyledLabel(
            text="Vòng đấu đang diễn ra", 
            font_size=12,
            color=(0.9, 0.9, 1, 1),
            halign='center'
        )
        self.round_info_label.bind(size=self.round_info_label.setter('text_size'))
        game_info_frame.add_widget(self.round_info_label)

        self.players_remaining_label = StyledLabel(
            text="Người chơi: 0/0", 
            font_size=12,
            color=(0.9, 0.9, 1, 1),
            halign='center'
        )
        self.players_remaining_label.bind(size=self.players_remaining_label.setter('text_size'))
        game_info_frame.add_widget(self.players_remaining_label)
        right_area.add_widget(game_info_frame)

        # Thêm các phần vào khu vực trung tâm
        center_game_area.add_widget(left_area)
        center_game_area.add_widget(center_area)
        center_game_area.add_widget(right_area)

        # Thêm khu vực trung tâm vào game_area
        game_area.add_widget(center_game_area)
        self.add_widget(game_area)

        # Bottom action button with improved styling
        button_container = BoxLayout(size_hint_y=None, height=60, padding=[100, 0])

        # Nút đẹp hơn với viền 3D
        self.action_button = Button(
            text="Start New Game Session", 
            size_hint=(1, 0.9),
            pos_hint={'center_y': 0.5},
            background_color=(0.4, 0.6, 0.9, 1),
            font_size=19,
            bold=True,
            border=(0, 0, 0, 5)  # Border bottom để tạo hiệu ứng 3D
        )
        self.action_button.bind(on_press=self.on_press_action_button)
        button_container.add_widget(self.action_button)
        self.add_widget(button_container)
                
        self.update_ui_full()
        
    def _update_player_header_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.15, 0.3, 0.25, 0.8)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10, 10, 0, 0])
            
    def _update_opponents_container_bg(self, instance, value):
        if hasattr(self, 'opponents_bg'):
            self.opponents_bg.pos = instance.pos
            self.opponents_bg.size = instance.size
            
    def _update_opponents_header_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.2, 0.2, 0.35, 0.8)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10, 10, 0, 0])
            
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
            # Cập nhật thông tin deck
            self.deck_count_label.text = f"{self.current_round_manager.deck.count()}"
            self.deck_image.source = CARD_BACK_IMAGE if not self.current_round_manager.deck.is_empty() else EMPTY_CARD_IMAGE
            self.deck_image.opacity = 1.0 if not self.current_round_manager.deck.is_empty() else 0.3
            
            # Cập nhật thông tin trò chơi
            active_players = sum(1 for p in self.players_session_list if not p.is_eliminated)
            total_players = len(self.players_session_list)
            self.players_remaining_label.text = f"Người chơi: {active_players}/{total_players}"
            
            # Cập nhật thông tin vòng đấu
            if self.current_round_manager.round_active:
                current_player = self.players_session_list[self.current_round_manager.current_player_idx].name
                self.round_info_label.text = f"Lượt của: {current_player}"
            else:
                self.round_info_label.text = "Vòng đấu kết thúc"
        else:
            self.deck_count_label.text = "0"
            self.deck_image.source = EMPTY_CARD_IMAGE
            self.deck_image.opacity = 0.3
            self.round_info_label.text = "Không có vòng đấu"
            self.players_remaining_label.text = "Người chơi: 0/0"
            
        last_played_card = None
        last_played_by = None

        # Ưu tiên hiển thị lá bài của người chơi chính
        human_player = self.players_session_list[self.human_player_id]
        if human_player.discard_pile and len(human_player.discard_pile) > 0:
            last_played_card = human_player.discard_pile[-1]
            last_played_by = human_player
        else:
            # Nếu người chơi chính chưa đánh lá nào, tìm lá bài gần nhất từ đối thủ
            for player in self.players_session_list:
                if player.id != self.human_player_id and player.discard_pile and len(player.discard_pile) > 0:
                    last_played_card = player.discard_pile[-1]
                    last_played_by = player
                    break

        # Cập nhật hiển thị lá bài đánh ra
        if last_played_card:
            # Xóa widget cũ và tạo widget mới
            self.last_played_card_container.clear_widgets()
            
            # Sử dụng ImageButton để người chơi có thể click xem thông tin lá bài
            card_button = ImageButton(
                source=last_played_card.image_path,
                card_info_callback=self.display_card_info_popup,
                card_data=last_played_card,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(0.95, 0.95),
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            self.last_played_card_container.add_widget(card_button)
            
            # Hiển thị tên người chơi đã đánh ra lá bài
            player_name = last_played_by.name if last_played_by else "Unknown"
            self.last_played_title.text = f"Bài của: {player_name}"
        else:
            # Nếu chưa có lá bài nào được đánh ra
            self.last_played_card_container.clear_widgets()
            self.last_played_card_image = Image(
                source=EMPTY_CARD_IMAGE,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(0.95, 0.95),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                opacity=0.3
            )
            self.last_played_card_container.add_widget(self.last_played_card_image)
            self.last_played_title.text = "Chưa có bài đánh ra"

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
                opponent_container = BoxLayout(
                    orientation='vertical', 
                    size_hint_y=None, 
                    height=210, 
                    width=160, 
                    padding=[8, 8, 8, 8]  # Padding đều hơn
                )
                
                # Add background with border and status color
                with opponent_container.canvas.before:
                    # Thêm viền sáng
                    Color(0.3, 0.3, 0.4, 0.9)
                    RoundedRectangle(
                        pos=(opponent_container.pos[0]-2, opponent_container.pos[1]-2), 
                        size=(opponent_container.size[0]+4, opponent_container.size[1]+4), 
                        radius=[15,]
                    )
                    # Nền chính - màu phụ thuộc vào trạng thái
                    if p_opponent.is_eliminated:
                        Color(0.5, 0.1, 0.1, 0.7)  # Red for eliminated
                    elif p_opponent.is_protected:
                        Color(0.2, 0.5, 0.2, 0.7)  # Green for protected
                    else:
                        Color(0.15, 0.15, 0.25, 0.7)  # Màu nền tối hơn cho mặc định
                    RoundedRectangle(pos=opponent_container.pos, size=opponent_container.size, radius=[15,])
                
                opponent_container.bind(pos=self._update_opponent_bg, size=self._update_opponent_bg)
                
                # Name with token count
                name_box = BoxLayout(size_hint_y=0.15)
                # Thêm nền cho name_box
                with name_box.canvas.before:
                    if p_opponent.is_eliminated:
                        Color(0.4, 0.08, 0.08, 0.9)  # Đỏ tối hơn
                    elif p_opponent.is_protected:
                        Color(0.15, 0.4, 0.15, 0.9)  # Xanh tối hơn
                    else:
                        Color(0.1, 0.1, 0.2, 0.9)  # Xanh tối mặc định
                    RoundedRectangle(pos=name_box.pos, size=name_box.size, radius=[10, 10, 0, 0])
                name_box.bind(pos=self._update_name_box_bg, size=self._update_name_box_bg)

                # Cải thiện hiển thị tên và token
                token_text = f"{p_opponent.name}"
                token_stars = " " + ("★" * p_opponent.tokens)
                status_text = " [E]" if p_opponent.is_eliminated else " [P]" if p_opponent.is_protected else ""

                name_label = StyledLabel(
                    text=token_text + status_text, 
                    font_size='13sp',
                    bold=True,
                    color=(1, 1, 0.85, 1) if not p_opponent.is_eliminated else (1, 0.7, 0.7, 1)
                )
                name_box.add_widget(name_label)
                
                opponent_container.add_widget(name_box)
                
                # Card display
                card_img_src = CARD_BACK_IMAGE
                if p_opponent.is_eliminated:
                    card_img_src = ELIMINATED_IMAGE
                elif not p_opponent.hand:
                    card_img_src = "transparent"  # Tạo một giá trị đặc biệt để xử lý
                
                card_box = BoxLayout(size_hint_y=0.55)
                if card_img_src == "transparent":
                    # Tạo một widget trống thay vì image khi không có bài
                    card_image = Widget()
                elif card_img_src == CARD_BACK_IMAGE or card_img_src == ELIMINATED_IMAGE:
                    # Sử dụng Image thông thường cho card back và eliminated
                    card_image = Image(source=card_img_src, allow_stretch=True, keep_ratio=True)
                else:
                    # Sử dụng card_obj từ tay người chơi đối thủ nếu có thể nhìn thấy
                    if p_opponent.hand:
                        card_obj = p_opponent.hand[0]
                        card_image = ImageButton(
                            source=card_img_src,
                            card_info_callback=self.display_card_info_popup,
                            card_data=card_obj
                        )
                    else:
                        card_image = Widget()
                        
                card_box.add_widget(card_image)
                
                # Discard pile display
                discard_box = BoxLayout(orientation='vertical', size_hint_y=0.3)
                discard_label = StyledLabel(text="Discard", font_size='10sp', size_hint_y=0.3)
                discard_box.add_widget(discard_label)
                
                discard_img_src = ""
                if p_opponent.discard_pile:
                    discard_card = p_opponent.discard_pile[-1]
                    discard_image = ImageButton(
                        source=discard_card.image_path, 
                        allow_stretch=True, 
                        keep_ratio=True, 
                        size_hint_y=0.7,
                        card_info_callback=self.display_card_info_popup,
                        card_data=discard_card
                    )
                else:
                    # Sử dụng lá bài rỗng thay vì chuỗi rỗng
                    discard_image = Image(
                        source=EMPTY_CARD_IMAGE, 
                        allow_stretch=True, 
                        keep_ratio=True, 
                        size_hint_y=0.7,
                        opacity=0.3  # Làm mờ để chỉ ra rằng không có lá bài
                    )
                discard_box.add_widget(discard_image)
                opponent_container.add_widget(discard_box)
                
                self.opponents_grid.add_widget(opponent_container)
                self.opponent_widgets_map[p_opponent.id] = opponent_container

        # Update human player hand display with enhanced styling
        human_player = self.players_session_list[self.human_player_id]
        self.player_hand_area.clear_widgets()
        
        print(f"DEBUG: Human player hand: {[card.name for card in human_player.hand] if human_player.hand else 'empty'}")
        
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
                print(f"DEBUG: Displaying card: {card_obj.name} with image path: {card_obj.image_path}")
                card_container = BoxLayout(
                    orientation='vertical',
                    size_hint=(1 / len(human_player.hand) if len(human_player.hand) > 0 else 1, 1),
                    padding=[10, 10, 10, 5]  # Padding tốt hơn
                )

                if is_player_turn_active_ui:
                    with card_container.canvas.before:
                        # Bóng đổ nhẹ cho lá bài
                        Color(0.2, 0.4, 0.3, 0.4)
                        RoundedRectangle(
                            pos=(card_container.pos[0]+4, card_container.pos[1]-4), 
                            size=card_container.size,
                            radius=[8,]
                        )
                        
                card_frame = BoxLayout(padding=[2, 2, 2, 2])
                with card_frame.canvas.before:
                    # Viền cho lá bài
                    if is_player_turn_active_ui:
                        Color(0.9, 0.8, 0.3, 0.8)  # Viền vàng cho bài có thể chơi
                    else:
                        Color(0.4, 0.4, 0.5, 0.4)  # Viền xám khi không thể chơi
                    RoundedRectangle(pos=card_frame.pos, size=card_frame.size, radius=[5,])
                card_frame.bind(pos=lambda inst, val: self._update_card_frame(inst, val), 
                            size=lambda inst, val: self._update_card_frame(inst, val))
                                
                # Card button with shadow effect when active
                card_button = ImageButton(
                    source=card_obj.image_path,
                    card_info_callback=self.display_card_info_popup,
                    card_data=card_obj,
                    size_hint=(0.95, 0.95),
                    pos_hint={'center_x': 0.5, 'center_y': 0.5}  # Căn giữa lá bài
                )
                
                card_button.card_name = card_obj.name
                card_button.bind(on_press=self.on_player_card_selected)
                card_button.disabled = not is_player_turn_active_ui
                card_button.opacity = 1.0 if is_player_turn_active_ui else 0.7
                
                card_frame.add_widget(card_button)
                card_container.add_widget(card_frame)
                                
                # Add card value indicator
                card_info_box = BoxLayout(size_hint_y=None, height=25, padding=[0, 5, 0, 0])
                # Thêm background cho thông tin lá bài
                with card_info_box.canvas.before:
                    Color(0.15, 0.15, 0.2, 0.8)
                    RoundedRectangle(pos=card_info_box.pos, size=card_info_box.size, radius=[0, 0, 5, 5])
                card_info_box.bind(pos=self._update_card_info_box, size=self._update_card_info_box)

                # Hiển thị tên và giá trị lá bài đẹp hơn
                card_value_label = StyledLabel(
                    text=f"{card_obj.name} ({card_obj.value})", 
                    font_size='13sp',
                    color=(1, 0.92, 0.7, 1),
                    bold=True
                )
                card_info_box.add_widget(card_value_label)

                card_container.add_widget(card_info_box)
                self.player_hand_area.add_widget(card_container)

        self.log_message("", permanent=False)
        
    def _update_card_info_box(self, instance, value):
        for child in instance.canvas.before.children:
            if isinstance(child, RoundedRectangle):
                child.pos = instance.pos
                child.size = instance.size
                
    def _update_card_frame(self, instance, value):
        for child in instance.canvas.before.children:
            if isinstance(child, RoundedRectangle):
                child.pos = instance.pos
                child.size = instance.size
            
    def _update_name_box_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            # Lấy màu từ parent (opponent_container)
            if instance.parent:
                for child in instance.parent.canvas.before.children:
                    if isinstance(child, Color):
                        r, g, b, a = child.rgba
                        # Làm tối hơn một chút
                        Color(max(0, r*0.8), max(0, g*0.8), max(0, b*0.8), a)
                        break
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10, 10, 0, 0])
            
    def _update_opponent_bg(self, instance, value):
        if hasattr(instance, 'canvas') and hasattr(instance, 'canvas.before'):
            for child in instance.canvas.before.children:
                if isinstance(child, RoundedRectangle):
                    child.pos = instance.pos
                    child.size = instance.size
                    
                    
    def _update_center_game_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.13, 0.17, 0.25, 0.7)  # Màu nền tối
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[15,])
            
    def _update_played_card_frame_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.1, 0.15, 0.2, 0.5)  # Nền tối hơn để lá bài nổi bật
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10,])
            
    def _update_game_info_frame_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.1, 0.15, 0.2, 0.5)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[10,])

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
            
    if not os.path.exists(EMPTY_CARD_IMAGE):
        try:
            from PIL import Image as PILImage
            # Tạo ảnh trong suốt cho lá bài rỗng
            img = PILImage.new('RGBA', (200, 300), color=(0, 0, 0, 0))
            img.save(EMPTY_CARD_IMAGE)
            print(f"INFO: Created empty card image at {EMPTY_CARD_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create empty card image: {e}")

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