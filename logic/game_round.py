# file: logic/game_round.py
from .player import Player
from .deck import Deck
from .constants import CARD_PROTOTYPES
import random
from kivy.clock import Clock

class GameRound:
    """
    Manages the state and logic for a single round of the game.
    It acts as a service provider for card effects, offering a stable API
    for them to interact with the game state (e.g., getting targets, eliminating players).
    """
    def __init__(self, players_list, deck_obj, human_player_id, log_callback, ui_callbacks):
        self.players = players_list
        self.deck = deck_obj
        self.human_player_id = human_player_id
        self.log_message = log_callback
        self.ui = ui_callbacks

        self.current_player_idx = 0
        self.round_active = False
        self.game_over_pending_from_round = False
        self.game_over_winner = None
        self.shared_burned_card_ref = {'card': self.deck.burned_card}

    # --- Round Lifecycle ---

    def start_round(self):
        self.log_message("--- Bắt đầu vòng mới (Logic) ---")
        for p in self.players:
            p.reset_for_round()
            drawn_card = self.deck.draw()
            if drawn_card:
                p.add_card_to_hand(drawn_card)
            else:
                self.log_message(f"Lỗi: Không đủ bài để chia cho {p.name}. Chồng bài đã hết.")
                p.is_eliminated = True

        self.current_player_idx = random.randrange(len(self.players))
        self.round_active = True
        self.log_message(f"Vòng đấu bắt đầu. {self.players[self.current_player_idx].name} đi trước.")

        self.ui['animate_deal_callback'](self._process_current_player_turn_start)


    def _end_round_by_elimination(self, active_players_list=None):
        if not self.round_active: return
        self.log_message("Vòng đấu kết thúc: chỉ còn một hoặc không người chơi.")
        self.round_active = False
        if active_players_list is None:
            active_players_list = [p for p in self.players if not p.is_eliminated]

        winner = active_players_list[0] if len(active_players_list) == 1 else None
        reason = f"{winner.name} là người cuối cùng còn lại." if winner else "Tất cả người chơi đã bị loại cùng lúc."
        self.log_message(f"{reason} {'Người chiến thắng là ' + winner.name + '!' if winner else 'Không có ai thắng vòng này.'}")
        self.ui['award_round_tokens_callback']([winner] if winner else [], reason)

    def _end_round_deck_empty(self):
        if not self.round_active: return
        self.log_message("Vòng đấu kết thúc: chồng bài đã hết. So bài của những người chơi còn lại.")
        self.round_active = False
        active_players_with_hands = [p for p in self.players if not p.is_eliminated and p.hand]
        if not active_players_with_hands:
            reason = "Không có người chơi nào còn bài để so."
            self.log_message(f"{reason} Không có người thắng vòng này.")
            self.ui['award_round_tokens_callback']([], reason)
            return

        # Calculate effective value (considering Count card)
        is_count_in_deck = self.is_card_in_current_deck('Count')
        for p in active_players_with_hands:
            p.effective_value_end_round = p.hand[0].value
            if is_count_in_deck and p.has_discarded('Count'):
                p.effective_value_end_round += 1
                self.log_message(f"{p.name} có Bá tước trong bài bỏ. Bài: {p.hand[0].name}, Giá trị hiệu dụng: {p.effective_value_end_round}")

        # Sort by card value
        active_players_with_hands.sort(key=lambda p: p.effective_value_end_round, reverse=True)
        highest_val = active_players_with_hands[0].effective_value_end_round
        winners_by_val = [p for p in active_players_with_hands if p.effective_value_end_round == highest_val]

        if len(winners_by_val) == 1:
            winner = winners_by_val[0]
            reason = f"{winner.name} có lá bài cao nhất ({winner.hand[0].name}, giá trị {winner.effective_value_end_round})!"
            self.log_message(f"{reason} Người chiến thắng là {winner.name}.")
            self.ui['award_round_tokens_callback'](winners_by_val, reason)
        else:
            # Tie-breaker: sum of discarded cards
            self.log_message(f"Hòa điểm ở giá trị {highest_val}. So tổng điểm các lá bài đã bỏ.")
            for p in winners_by_val:
                p.discard_sum_end_round = sum(c.value for c in p.discard_pile)
                self.log_message(f"{p.name} (Bài: {p.hand[0].name}) tổng điểm bài bỏ: {p.discard_sum_end_round}")
            winners_by_val.sort(key=lambda p: p.discard_sum_end_round, reverse=True)
            highest_discard_sum = winners_by_val[0].discard_sum_end_round
            final_winners = [p for p in winners_by_val if p.discard_sum_end_round == highest_discard_sum]

            if len(final_winners) == 1:
                winner = final_winners[0]
                reason = f"{winner.name} thắng nhờ tổng điểm bài bỏ cao hơn ({highest_discard_sum})!"
                self.log_message(f"{reason} Người chiến thắng là {winner.name}.")
            else:
                winner_names = ", ".join([p.name for p in final_winners])
                reason = f"Vẫn hòa! {winner_names} cùng thắng vòng này."
                self.log_message(reason)
            self.ui['award_round_tokens_callback'](final_winners, reason)

    # --- Turn Management ---

    def _process_current_player_turn_start(self):
        if not self.round_active: return

        current_player = self.players[self.current_player_idx]
        if current_player.is_eliminated:
            self._advance_to_next_turn()
            return

        current_player.is_protected = False
        self.ui['update_ui_full_callback']()

        if self.deck.is_empty():
            self.log_message("Chồng bài đã hết. Vòng đấu kết thúc.")
            self._end_round_deck_empty()
            return

        drawn_card = self.deck.draw()

        def after_draw_animation():
            current_player.add_card_to_hand(drawn_card)
            log_msg = f"Bạn ({current_player.name}) đã rút được {drawn_card.name}. Bài trên tay: {current_player.get_hand_card_names()}." if not current_player.is_cpu else f"{current_player.name} đã rút một lá bài. Số bài trên tay: {len(current_player.hand)}."
            self.log_message(log_msg)
            self.ui['update_ui_full_callback']()

            if current_player.is_cpu:
                self.log_message(f"Máy ({current_player.name}) đang suy nghĩ...")
                Clock.schedule_once(lambda dt: self._execute_cpu_turn_after_delay(current_player), 2.5)
            else:
                self.log_message(f"Đến lượt bạn, {current_player.name}. Hãy chọn một lá bài để chơi.")
                self.ui['set_waiting_flag_callback'](False)
                if self._check_countess_rule(current_player):
                    self.log_message("LƯU Ý: Bạn có Nữ Bá tước và Vua/Hoàng tử. Bạn PHẢI chơi Nữ Bá tước.")

        self.ui['animate_draw_callback'](current_player, after_draw_animation)

    def _advance_to_next_turn(self):
        if not self.round_active: return

        active_players_count = sum(1 for p in self.players if not p.is_eliminated)
        if active_players_count <= 1:
            self._end_round_by_elimination()
            return

        # Find next non-eliminated player
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        while self.players[self.current_player_idx].is_eliminated:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

        next_player = self.players[self.current_player_idx]
        log_msg = f"--- Đến lượt bạn ({next_player.name}) ---" if not next_player.is_cpu else f"--- Lượt của {next_player.name} ---"
        self.log_message(log_msg)
        self._process_current_player_turn_start()

    def finish_effect_and_proceed(self):
        """Callback for card effects to call when they are fully resolved."""
        self.ui['set_waiting_flag_callback'](False)
        if self.ui['get_active_popup_callback']():
            self.ui['dismiss_active_popup_callback']()

        if self.game_over_pending_from_round:
            self.round_active = False
            self.ui['game_over_callback'](self.game_over_winner)
            return

        active_players = [p for p in self.players if not p.is_eliminated]
        if len(active_players) <= 1:
            self._end_round_by_elimination(active_players)
        elif self.round_active:
            self._advance_to_next_turn()

        self.ui['update_ui_full_callback']()


    # --- Player Actions & Card Logic ---

    def human_plays_card(self, card_name_played):
        player = self.players[self.current_player_idx]
        if player.is_cpu or not self.round_active: return

        # Enforce Countess rule
        actual_card_to_play_name = card_name_played
        if self._check_countess_rule(player) and card_name_played != 'Countess':
            self.log_message("Luật Nữ Bá tước: Tự động chơi Nữ Bá tước vì có Vua/Hoàng tử trên tay.")
            actual_card_to_play_name = 'Countess'

        card_object_played = player.play_card(actual_card_to_play_name)
        if card_object_played:
            self._handle_card_played_logic(player, card_object_played)
        else:
            self.log_message(f"LỖI: {player.name} đã thử chơi {actual_card_to_play_name} nhưng thất bại.")
            self.ui['set_waiting_flag_callback'](False)
            if self.round_active: self._advance_to_next_turn()

    def _execute_cpu_turn_after_delay(self, cpu_player):
        if not self.round_active or self.players[self.current_player_idx] != cpu_player:
            return # Stale turn, do nothing
        self.log_message(f"Máy ({cpu_player.name}) quyết định chơi.")
        self._cpu_play_turn(cpu_player)

    def _cpu_play_turn(self, cpu_player):
        # Countess rule
        if self._check_countess_rule(cpu_player):
            self.log_message(f"Máy ({cpu_player.name}) có Nữ Bá tước và Vua/Hoàng tử, phải chơi Nữ Bá tước.")
            card_object_played = cpu_player.play_card('Countess')
            self._handle_card_played_logic(cpu_player, card_object_played)
            return

        # Simple AI: avoid playing Princess if possible
        playable_cards = list(cpu_player.hand)
        if self.is_card_in_current_deck('Princess') and len(playable_cards) > 1:
            non_princess_cards = [c for c in playable_cards if c.name != 'Princess']
            if non_princess_cards:
                playable_cards = non_princess_cards

        chosen_card_object = random.choice(playable_cards)
        card_object_played = cpu_player.play_card(chosen_card_object.name)
        self._handle_card_played_logic(cpu_player, card_object_played)

    def _handle_card_played_logic(self, player, card_object_played):
        self.log_message(f"{player.name} chơi lá {card_object_played.name}.")
        if self.ui.get('add_to_global_discard_callback'):
            self.ui['add_to_global_discard_callback'](player, card_object_played)

        def after_play_animation():
            self.ui['update_ui_full_callback']()
            # Handle Princess elimination before calling the effect
            if self.is_card_in_current_deck('Princess') and card_object_played.name == 'Princess':
                self.log_message(f"{player.name} đã bỏ Công chúa và bị loại!")
                self.eliminate_player(player, self.finish_effect_and_proceed)
                return

            needs_input = self._execute_card_effect(player, card_object_played)
            if not needs_input:
                self.finish_effect_and_proceed()

        self.ui['animate_play_card_callback'](player, card_object_played, after_play_animation)

    def _execute_card_effect(self, player, card):
        """Dispatches to the appropriate card effect function."""
        player.sycophant_target_self = False # Reset flag
        if card.effect:
            return card.effect(self, player, card)
        else:
            self.log_message(f"Hiệu ứng cho {card.name} chưa được cài đặt hoặc là bị động/tự động.")
            return False # No input needed

    def cancel_played_card_action(self, acting_player):
        self.log_message(f"{acting_player.name} quyết định lấy lại lá bài của mình.")
        if not acting_player.discard_pile:
            self.log_message(f"LỖI: Không thể hủy hành động, không có bài trong chồng bài bỏ của {acting_player.name}.")
        else:
            card_to_return = acting_player.discard_pile.pop()
            acting_player.add_card_to_hand(card_to_return)

        if self.ui.get('dismiss_active_popup_callback'): self.ui['dismiss_active_popup_callback']()
        if self.ui.get('set_waiting_flag_callback'): self.ui['set_waiting_flag_callback'](False)
        if self.ui.get('update_ui_full_callback'): self.ui['update_ui_full_callback']()

    # --- Game State API for Card Effects ---

    def get_valid_targets(self, acting_player, include_self=False, targeted_effect_requires_unprotected=True, allow_no_hand=False):
        """Provides a list of valid player targets for an effect."""
        targets = []
        for p in self.players:
            if p.is_eliminated: continue
            if p == acting_player and not include_self: continue
            if targeted_effect_requires_unprotected and p.is_protected and p != acting_player: continue
            if not p.hand and not allow_no_hand and p != acting_player: continue
            targets.append(p)
        return targets

    def eliminate_player(self, player_to_eliminate, continuation=None):
        """Handles player elimination and checks for Sheriff bonus."""
        if player_to_eliminate.is_eliminated:
            if continuation: continuation()
            return

        player_to_eliminate.is_eliminated = True
        self.log_message(f"{player_to_eliminate.name} đã bị loại!")

        def after_elimination_animation():
            if self.is_card_in_current_deck('Sheriff') and player_to_eliminate.has_discarded('Sheriff'):
                self.log_message(f"{player_to_eliminate.name} có Nguyên soái trong bài bỏ và nhận được một tín vật!")
                player_to_eliminate.tokens += 1
                if self.ui['check_game_over_token_callback'](player_to_eliminate):
                    self.game_over_pending_from_round = True
                    self.game_over_winner = player_to_eliminate
            if continuation:
                continuation()

        self.ui['animate_elimination_callback'](player_to_eliminate, after_elimination_animation)

    def draw_from_deck_or_burned(self):
        """Draws a card from the deck, or the burned card if the deck is empty."""
        if not self.deck.is_empty():
            return self.deck.draw()
        if self.shared_burned_card_ref['card']:
            card = self.shared_burned_card_ref['card']
            self.shared_burned_card_ref['card'] = None
            return card
        return None

    def is_card_in_current_deck(self, card_name):
        """Checks if a card type is part of the current game's deck composition."""
        prototype = CARD_PROTOTYPES.get(card_name)
        if not prototype: return False
        composition_key = 'count_classic' if len(self.players) <= 4 else 'count_large'
        return getattr(prototype, composition_key, 0) > 0

    def _check_countess_rule(self, player):
        """Checks if the Countess rule is active for a given player."""
        hand_names = player.get_hand_card_names()
        has_countess = self.is_card_in_current_deck('Countess') and 'Countess' in hand_names
        has_royalty = (self.is_card_in_current_deck('King') and 'King' in hand_names) or \
                      (self.is_card_in_current_deck('Prince') and 'Prince' in hand_names)
        return has_countess and has_royalty

