# file: ui/animation_manager.py

from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from .constants import CARD_BACK_IMAGE

class AnimationManager:
    def __init__(self, game_screen):
        self.game_screen = game_screen

    def get_widget_center(self, widget):
        if widget.parent:
            return widget.parent.to_window(*widget.center)
        return widget.center

    def deal_card(self, player_id, on_complete=None):
        deck_pos = self.get_widget_center(self.game_screen.deck_image)

        player_widget = self.game_screen._get_player_widget_by_id(player_id)
        if not player_widget:
            if on_complete:
                on_complete()
            return

        target_pos = self.get_widget_center(player_widget)

        card_image = Image(
            source=CARD_BACK_IMAGE,
            size_hint=(None, None),
            size=(100, 140),
            pos=deck_pos
        )
        self.game_screen.add_widget(card_image)

        anim = Animation(
            pos=target_pos,
            duration=0.5,
            transition='out_quad'
        )
        anim.bind(on_complete=lambda *args: (
            self.game_screen.remove_widget(card_image),
            on_complete() if on_complete else None
        ))
        anim.start(card_image)

    def animate_card_to_discard(self, card, player_id, on_complete=None):
        player_widget = self.game_screen._get_player_widget_by_id(player_id)
        if not player_widget:
            if on_complete:
                on_complete()
            return

        start_pos = self.get_widget_center(player_widget)
        discard_pos = self.get_widget_center(self.game_screen.last_played_card_container)

        card_image = Image(
            source=card.image_path,
            size_hint=(None, None),
            size=(100, 140),
            pos=start_pos
        )
        self.game_screen.add_widget(card_image)

        anim = Animation(
            pos=discard_pos,
            duration=0.7,
            transition='out_quint'
        )
        anim.bind(on_complete=lambda *args: (
            self.game_screen.remove_widget(card_image),
            on_complete() if on_complete else None
        ))
        anim.start(card_image)

    def draw_card(self, player_id, on_complete=None):
        deck_pos = self.get_widget_center(self.game_screen.deck_image)

        player_widget = self.game_screen._get_player_widget_by_id(player_id)
        if not player_widget:
            if on_complete:
                on_complete()
            return

        target_pos = self.get_widget_center(player_widget)

        card_image = Image(
            source=CARD_BACK_IMAGE,
            size_hint=(None, None),
            size=(100, 140),
            pos=deck_pos
        )
        self.game_screen.add_widget(card_image)

        anim = Animation(
            pos=target_pos,
            duration=0.5,
            transition='out_quad'
        )
        anim.bind(on_complete=lambda *args: (
            self.game_screen.remove_widget(card_image),
            on_complete() if on_complete else None
        ))
        anim.start(card_image)

