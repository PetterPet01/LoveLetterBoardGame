# file: ui/ui_components.py

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import NumericProperty, ListProperty

class StyledLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = kwargs.get('color', (0.9, 0.9, 1, 1))
        self.bold = kwargs.get('bold', False)
        self.outline_width = kwargs.get('outline_width', 0)
        self.outline_color = kwargs.get('outline_color', (0, 0, 0, 1))
        # Ensure text_size is bound for proper wrapping/alignment if halign/valign are used
        if 'halign' in kwargs or 'valign' in kwargs:
            self.bind(size=self.setter('text_size'))

class ImageButton(ButtonBehavior, Image):
    scale = NumericProperty(1.0)

    def __init__(self, **kwargs):
        self.card_info_callback = kwargs.pop('card_info_callback', None)
        self.card_data = kwargs.pop('card_data', None)
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True

    def on_press(self):
        if not self.disabled:
            self.opacity = 0.8
            self.scale = 0.98

    def on_release(self):
        if not self.disabled:
            self.opacity = 1.0
            self.scale = 1.0

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == 'right' and self.card_info_callback and self.card_data:
            self.card_info_callback(self.card_data)
            return True
        return super(ImageButton, self).on_touch_down(touch)

def create_selection_button(text, on_press_callback, color_scheme='default'):
    schemes = {
        'default': {'normal': (0.25, 0.28, 0.42, 0.95), 'press': (0.35, 0.38, 0.52, 1.0)},
        'cancel': {'normal': (0.7, 0.2, 0.2, 0.92), 'press': (0.85, 0.3, 0.3, 1.0)},
        'confirm': {'normal': (0.2, 0.5, 0.3, 0.92), 'press': (0.3, 0.65, 0.4, 1.0)}
    }
    colors = schemes.get(color_scheme, schemes['default'])

    btn = Button(
        text=text,
        size_hint_y=None,
        height=dp(50),
        background_normal='',
        background_color=(0,0,0,0), # Transparent
        color=(1, 0.95, 0.8, 1),
        font_size=dp(16),
        bold=True
    )
    
    with btn.canvas.before:
        btn.bg_color_instruction = Color(*colors['normal'])
        btn.bg_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
        
    def update_graphics(inst, _):
        inst.bg_rect.pos = inst.pos
        inst.bg_rect.size = inst.size
        
    btn.bind(pos=update_graphics, size=update_graphics)
    
    # Bind press/release for color change feedback
    btn.bind(
        on_press=lambda inst: setattr(inst.bg_color_instruction, 'rgba', colors['press']),
        on_release=lambda inst: setattr(inst.bg_color_instruction, 'rgba', colors['normal'])
    )
    
    # Bind the actual action callback
    btn.bind(on_press=on_press_callback)
    return btn


class TurnNotificationPopup(BoxLayout):
    scale = NumericProperty(1.0)

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
            text=detail_text, font_size='15sp', color=(0.95, 0.95, 1, 1), halign='center',
            size_hint_y=None
        )
        # Bindings for dynamic height based on text wrapping
        detail_label.bind(width=lambda *x: detail_label.setter('text_size')(detail_label, (detail_label.width, None)))
        detail_label.bind(texture_size=detail_label.setter('size'))
        self.add_widget(detail_label)
        
        # Ensure the BoxLayout height adjusts to content
        self.bind(minimum_height=self.setter('height'))

    def _update_rect(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size

