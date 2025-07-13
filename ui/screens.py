# file: screens.py

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from ui.constants import INTRO_BACKGROUND, RULES_BACKGROUND
from ui.ui_components import StyledLabel

class IntroScreen(Screen):
    game_instance = None  # Class-level variable to hold the game instance

    @staticmethod
    def _get_and_cache_game_instance(screen_manager):
        """
        Finds the game instance from the screen manager and caches it.
        This is a robust way to ensure we have the instance when needed.
        """
        if not IntroScreen.game_instance:
            if screen_manager and screen_manager.has_screen('game'):
                game_screen = screen_manager.get_screen('game')
                # The game instance is expected to be the first child of the GameScreen
                if game_screen.children:
                    instance = game_screen.children[0]
                    # Cache it for both screens to avoid repeated lookups
                    IntroScreen.game_instance = instance
                    RulesScreen.game_instance = instance
        return IntroScreen.game_instance

    def __init__(self, **kwargs):
        super(IntroScreen, self).__init__(**kwargs)
        layout = FloatLayout()
        bg_image = Image(
            source=INTRO_BACKGROUND,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        layout.add_widget(bg_image)

        # Add a title
        title_label = StyledLabel(
            text="[b]Thư Tình[/b]\n[i](Love Letter)[/i]",
            font_size=dp(80),
            markup=True,
            color=(1, 0.9, 0.8, 1),
            pos_hint={'center_x': 0.5, 'top': 0.9},
            outline_width=2,
            outline_color=(0,0,0,1),
            halign='center'
        )
        layout.add_widget(title_label)

        button_container = BoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint=(0.4, 0.25),
            pos_hint={'center_x': 0.5, 'center_y': 0.3}
        )

        start_button = self.create_menu_button(
            text="BẮT ĐẦU CHƠI",
            font_size=dp(28),
            on_release_action=self.go_to_rules,
            base_color=(0.8, 0.1, 0.1, 0.9),
            press_color=(0.9, 0.2, 0.2, 0.95)
        )
        button_container.add_widget(start_button)

        tutorial_button = self.create_menu_button(
            text="HƯỚNG DẪN",
            font_size=dp(24),
            on_release_action=self.go_to_tutorial,
            base_color=(0.1, 0.5, 0.8, 0.9),
            press_color=(0.2, 0.6, 0.9, 0.95)
        )
        button_container.add_widget(tutorial_button)

        layout.add_widget(button_container)
        self.add_widget(layout)

    def create_menu_button(self, text, font_size, on_release_action, base_color, press_color):
        btn = Button(
            text=text,
            font_size=font_size,
            bold=True,
            color=(1, 0.9, 0.5, 1),
            size_hint=(1, 1),
            background_color=(0,0,0,0) # Transparent background
        )
        with btn.canvas.before:
            btn.bg_color_instruction = Color(*base_color)
            btn.bg_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(18)])

        def update_graphics(instance, value):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
        btn.bind(pos=update_graphics, size=update_graphics)

        def on_press(instance):
            instance.bg_color_instruction.rgba = press_color
        def on_release(instance):
            instance.bg_color_instruction.rgba = base_color
            on_release_action()

        btn.bind(on_press=on_press, on_release=on_release)
        return btn

    def go_to_rules(self):
        self.manager.current = 'rules'

    def go_to_tutorial(self):
        # Find the game instance just before switching screens
        game_inst = IntroScreen._get_and_cache_game_instance(self.manager)
        self.manager.current = 'game'
        if game_inst:
            # Schedule the tutorial to start after the screen transition begins
            Clock.schedule_once(lambda dt: game_inst.start_tutorial(), 0.1)

class RulesScreen(Screen):
    game_instance = None  # Class-level variable to hold the game instance

    def __init__(self, **kwargs):
        super(RulesScreen, self).__init__(**kwargs)
        layout = FloatLayout()
        bg_image = Image(
            source=RULES_BACKGROUND,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        hint_label = StyledLabel(
            text="[b]Nhấn vào màn hình để bắt đầu chơi[/b]",
            font_size=dp(30),
            markup=True,
            bold=True,
            color=(1, 0.9, 0.5, 1),
            outline_width=2,
            outline_color=(0,0,0,1),
            size_hint=(0.8, 0.1),
            pos_hint={'center_x': 0.5, 'y': 0.05}
        )
        layout.add_widget(bg_image)
        layout.add_widget(hint_label)
        layout.bind(on_touch_down=self.on_layout_click)
        self.add_widget(layout)

    def on_layout_click(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.start_game()
            return True
        return super(RulesScreen, self).on_touch_down(touch)

    def start_game(self):
        # Use the same robust method to get the game instance
        game_inst = IntroScreen._get_and_cache_game_instance(self.manager)
        self.manager.current = 'game'
        if game_inst:
            # Schedule the game setup to start after the screen transition begins
            Clock.schedule_once(lambda dt: game_inst.initialize_game_setup(), 0.1)

