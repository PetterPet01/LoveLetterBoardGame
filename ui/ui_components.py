
# file: ui_components.py

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

class StyledLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = kwargs.get('color', (0.9, 0.9, 1, 1))
        self.bold = kwargs.get('bold', True)
        self.outline_width = kwargs.get('outline_width', 1)
        self.outline_color = kwargs.get('outline_color', (0, 0, 0, 1))

class ImageButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        self.card_info_callback = kwargs.pop('card_info_callback', None)
        self.card_data = kwargs.pop('card_data', None)
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True

    def on_press(self):
        self.opacity = 0.8

    def on_release(self):
        self.opacity = 1.0

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == 'right' and self.card_info_callback and self.card_data:
            self.card_info_callback(self.card_data)
            return True
        return super(ImageButton, self).on_touch_down(touch)

class CardDisplay(BoxLayout):
    def __init__(self, card_source="", name="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 5
        self.size_hint_y = None
        self.height = 180
        with self.canvas.before:
            Color(0.2, 0.2, 0.3, 0.7)
            self.bg = RoundedRectangle(radius=[10, ])
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.card_image = Image(source=card_source, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.card_image)
        self.name_label = StyledLabel(text=name, size_hint_y=0.2, font_size='12sp')
        self.add_widget(self.name_label)

    def _update_rect(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size

class TurnNotificationPopup(BoxLayout):
    def __init__(self, title_text, detail_text, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(15)
        self.spacing = dp(8)
        self.size_hint = (None, None)
        self.width = dp(450)
        self.opacity = 0

        with self.canvas.before:
            Color(0.1, 0.1, 0.15, 0.9)
            self.bg = RoundedRectangle(radius=[dp(12)])

        self.bind(pos=self._update_rect, size=self._update_rect)

        title_label = StyledLabel(
            text=f"[b]{title_text}[/b]", font_size='18sp', color=(1, 0.85, 0.4, 1),
            markup=True, halign='center', size_hint_y=None, height=dp(30)
        )
        self.add_widget(title_label)

        detail_label = StyledLabel(
            text=detail_text, font_size='15sp', color=(0.95, 0.95, 1, 1), halign='center'
        )
        detail_label.bind(width=lambda *x: detail_label.setter('text_size')(detail_label, (detail_label.width, None)))
        detail_label.bind(texture_size=detail_label.setter('size'))
        self.add_widget(detail_label)
        self.bind(minimum_height=self.setter('height'))

    def _update_rect(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size