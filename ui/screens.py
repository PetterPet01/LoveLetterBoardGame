# file: screens.py

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

from ui.constants import INTRO_BACKGROUND, RULES_BACKGROUND

class IntroScreen(Screen):
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
        button_container = RelativeLayout(
            size_hint=(0.4, 0.12),
            pos_hint={'center_x': 0.5, 'center_y': 0.2}
        )
        start_button = Button(
            text="BẮT ĐẦU CHƠI",
            font_size=32,
            bold=True,
            background_color=(0.8, 0.1, 0.1, 0.85),
            color=(1, 0.9, 0.5, 1),
            size_hint=(0.95, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        def on_press(instance):
            instance.background_color = (0.9, 0.2, 0.2, 0.9)
            instance.font_size = 34

        def on_release(instance):
            instance.background_color = (0.8, 0.1, 0.1, 0.85)
            instance.font_size = 32
            self.go_to_rules()

        start_button.bind(on_press=on_press)
        start_button.bind(on_release=on_release)
        button_container.add_widget(start_button)
        layout.add_widget(button_container)
        self.add_widget(layout)

    def go_to_rules(self):
        self.manager.current = 'rules'


class RulesScreen(Screen):
    game_instance = None  # Sẽ được thiết lập từ file main.py

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
        hint_label = Label(
            text="Nhấn vào màn hình để bắt đầu chơi",
            font_size=24,
            bold=True,
            color=(1, 0.9, 0.5, 1),
            size_hint=(0.8, 0.1),
            pos_hint={'center_x': 0.5, 'bottom': 0.05}
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
        self.manager.current = 'game'
        if self.game_instance:
            Clock.schedule_once(lambda dt: self.game_instance.initialize_game_setup(), 0.1)