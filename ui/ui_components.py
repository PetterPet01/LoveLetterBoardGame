# file: ui_components.py

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
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
        background_color=(0, 0, 0, 0),  # Transparent
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


class EffectAnimationPanel(BoxLayout):
    scale = NumericProperty(1.0)

    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(5)

        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 0.95)
            self.bg = RoundedRectangle(radius=[dp(15)])
        self.bind(pos=self._update_rect, size=self._update_rect)

        # Top section: "Player uses Card on Player"
        header_text = f"{data['acting_player'].name} dùng [b]{data['card'].name}[/b]"
        if data['acting_player'] != data['target_player']:
            header_text += f" lên {data['target_player'].name}"
        self.header = StyledLabel(text=header_text, markup=True, font_size=dp(18), size_hint_y=0.25)
        self.add_widget(self.header)

        # Mid section: The visual display
        self.mid_section = FloatLayout(size_hint_y=0.5)
        self.add_widget(self.mid_section)

        # Bottom section: Result text
        self.footer = StyledLabel(text="...", font_size=dp(16), size_hint_y=0.25, bold=True, markup=True)
        self.add_widget(self.footer)

        self.update_state('initial')

    def _get_outcome_text_and_color(self):
        """Generates footer text and color based on the card's outcome. Generic and data-driven."""
        acting_player = self.data['acting_player']
        target_player = self.data['target_player']
        outcome = self.data['outcome']
        details = self.data['details']
        card_name = self.data['card'].name

        text, color = "...", (1, 1, 1, 1)

        if card_name == 'Guard':
            if outcome == 'success': text, color = f"[b]{target_player.name}[/b] đã bị loại!", (0.4, 1, 0.4, 1)
            elif outcome == 'fail': text, color = f"[b]{acting_player.name}[/b] đã đoán sai!", (1, 0.4, 0.4, 1)
            elif outcome == 'reversed': text, color = f"[b]{acting_player.name}[/b] đã bị Sát thủ loại!", (1, 0.2, 0.8, 1)
        elif card_name == 'Priest':
            card_name_seen = details['target_card'].name
            text = f"Bạn thấy lá [b]{card_name_seen}[/b] của [b]{target_player.name}[/b]." if not acting_player.is_cpu else f"[b]{acting_player.name}[/b] đã xem bài của [b]{target_player.name}[/b]."
        elif card_name == 'Baron':
            if outcome == 'win': text, color = f"[b]{acting_player.name}[/b] thắng! [b]{target_player.name}[/b] bị loại.", (0.4, 1, 0.4, 1)
            elif outcome == 'loss': text, color = f"[b]{acting_player.name}[/b] thua và bị loại!", (1, 0.4, 0.4, 1)
            else: text = f"[b]{acting_player.name}[/b] và [b]{target_player.name}[/b] hòa nhau!"
        elif card_name == 'King':
            text, color = f"[b]{acting_player.name}[/b] tráo bài với [b]{target_player.name}[/b]!", (0.9, 0.7, 0.2, 1)
        elif card_name == 'Prince':
            if outcome == 'eliminated': text, color = f"[b]{target_player.name}[/b] phải bỏ Công chúa và bị loại!", (1, 0.2, 0.2, 1)
            else:
                discarded_name = details['discarded_card'].name if details.get('discarded_card') else "bài"
                text = f"[b]{target_player.name}[/b] bỏ lá [b]{discarded_name}[/b] và rút bài mới."
        elif card_name == 'Handmaid':
            text, color = f"[b]{acting_player.name}[/b] đã được bảo vệ!", (0.5, 0.8, 1, 1)

        return text, color


    def update_state(self, state):
        self.mid_section.clear_widgets()
        card_name = self.data['card'].name
        details = self.data.get('details', {})

        if state == 'initial':
            self.footer.text = "Đang chơi..."
            self.mid_section.add_widget(Image(source=self.data['card'].image_path, size_hint=(0.25, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5}))

        elif state == 'intermediate':
            if card_name == 'Guard': self.footer.text = f"Đoán giá trị là [b]{details.get('guessed_value', '?')}[/b]"
            elif card_name == 'Baron': self.footer.text = "So bài..."
            elif card_name == 'King': self.footer.text = "Tráo đổi bài..."
            elif card_name == 'Priest': self.footer.text = "Nhìn trộm bài..."
            elif card_name == 'Prince': self.footer.text = "Bắt bỏ bài..."
            elif card_name == 'Handmaid': self.footer.text = "Tự bảo vệ!"
            else: self.footer.text = "..."

        elif state == 'final':
            if card_name == 'Baron':
                p_card, o_card = details.get('player_card'), details.get('opponent_card')
                if p_card: self.mid_section.add_widget(Image(source=p_card.image_path, size_hint=(0.25, 1), pos_hint={'center_x': 0.25, 'center_y': 0.5}))
                if o_card: self.mid_section.add_widget(Image(source=o_card.image_path, size_hint=(0.25, 1), pos_hint={'center_x': 0.75, 'center_y': 0.5}))

            outcome_text, outcome_color = self._get_outcome_text_and_color()
            self.footer.text = outcome_text
            self.footer.color = outcome_color

    def _update_rect(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size
