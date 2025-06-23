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
from kivy.graphics import Color, Rectangle # For animations later

Window.size = (900, 750)

CARD_FOLDER = "assets/cards"
CARD_BACK_IMAGE = "assets/cards/back.jpg"
ELIMINATED_IMAGE = "assets/cards/eliminated.jpg"

# Renamed to avoid conflict, this is the raw data
CARDS_DATA_RAW = {
    'Guard': {'value': 1, 'vietnamese_name': 'canve',
              'description': "Guess a player's card (not Guard). If correct, they are out.",
              'count_classic': 5, 'count_large': 8},
    'Priest': {'value': 2, 'vietnamese_name': 'mucsu',
               'description': "Look at another player's hand.",
               'count_classic': 2, 'count_large': 0},
    'Baron': {'value': 3, 'vietnamese_name': 'namtuoc',
              'description': "Compare hands; lower value is out.",
              'count_classic': 2, 'count_large': 0},
    'Handmaid': {'value': 4, 'vietnamese_name': 'cohau',
                 'description': "Immune to effects until your next turn.",
                 'count_classic': 2, 'count_large': 0},
    'Prince': {'value': 5, 'vietnamese_name': 'hoangtu',
               'description': "Choose player to discard hand and draw.",
               'count_classic': 2, 'count_large': 0},
    'King': {'value': 6, 'vietnamese_name': 'nhavua',
             'description': "Trade hands with another player.",
             'count_classic': 1, 'count_large': 0},
    'Countess': {'value': 7, 'vietnamese_name': 'nubatuoc',
                 'description': "Must discard if you have King or Prince.",
                 'count_classic': 1, 'count_large': 0},
    'Princess': {'value': 8, 'vietnamese_name': 'congchua',
                 'description': "Lose if you discard this card.",
                 'count_classic': 1, 'count_large': 0},
    'Assassin': {'value': 0, 'vietnamese_name': 'satthu',
                 'description': "If targeted by Guard, Guard player is out. Discard & draw.",
                 'count_classic': 0, 'count_large': 1},
    'Jester': {'value': 0, 'vietnamese_name': 'tenhe',
               'description': "Target player. If they win round, you get token.",
               'count_classic': 0, 'count_large': 1},
    'Cardinal': {'value': 2, 'vietnamese_name': 'hongy',
                 'description': "Two players swap hands. Look at one.",
                 'count_classic': 0, 'count_large': 2},
    'Baroness': {'value': 3, 'vietnamese_name': 'nunamtuoc',
                 'description': "Look at 1 or 2 players' hands.",
                 'count_classic': 0, 'count_large': 2},
    'Sycophant': {'value': 4, 'vietnamese_name': 'keninhbo',
                  'description': "Target player must target self with next effect card.",
                  'count_classic': 0, 'count_large': 2},
    'Count': {'value': 5, 'vietnamese_name': 'batuoc',
              'description': "+1 to hand value if this is in your discard pile.",
              'count_classic': 0, 'count_large': 2},
    'Sheriff': {'value': 6, 'vietnamese_name': 'nguyensoai',
                'description': "If eliminated with this in discard, gain token.",
                'count_classic': 0, 'count_large': 1},
    'Queen Mother': {'value': 7, 'vietnamese_name': 'nuhoang',
                     'description': "Compare hands; higher value is out.",
                     'count_classic': 0, 'count_large': 1},
    'Bishop': {'value': 9, 'vietnamese_name': 'giammuc',
               'description': "Guess card value (not Guard). Gain token if correct. Target may redraw.",
               'count_classic': 0, 'count_large': 1},
}

CARD_PROTOTYPES = {}  # Will be populated by Card objects


# --- Core Game Logic Classes ---

class Card:
    def __init__(self, name, value, description, image_path, vietnamese_name, count_classic, count_large):
        self.name = name
        self.value = value
        self.description = description
        self.image_path = image_path
        self.vietnamese_name = vietnamese_name
        self.count_classic = count_classic
        self.count_large = count_large
        self.is_targeting_effect = name not in ['Handmaid', 'Countess', 'Princess', 'Assassin', 'Count',
                                                'Sheriff']  # General heuristic

    def __repr__(self):
        return f"Card({self.name}, V:{self.value})"

    def to_dict(self):  # For compatibility with old discard pile logic if needed, or logging
        return {
            'name': self.name, 'value': self.value, 'image_path': self.image_path,
            'description': self.description, 'vietnamese_name': self.vietnamese_name
        }


class Deck:
    def __init__(self, num_players, log_callback):
        self.cards = []
        self.burned_card = None
        self.log_callback = log_callback
        self._create_deck(num_players)
        self.shuffle()

    def _create_deck(self, num_players):
        self.cards = []
        composition_key = 'count_classic' if num_players <= 4 else 'count_large'
        self.log_callback(
            f"Deck: Using composition for {'2-4 players (classic)' if composition_key == 'count_classic' else '5-8 players (large)'}.")

        for card_name, prototype in CARD_PROTOTYPES.items():
            count = getattr(prototype, composition_key, 0)
            for _ in range(count):
                # Add a new instance or reference. For this game, references are fine.
                self.cards.append(prototype)

        if not self.cards:
            self.log_callback("ERROR: No cards defined for this player count! Check CARD_PROTOTYPES counts.")
            if composition_key == 'count_large' and any(
                    proto.count_classic > 0 for proto in CARD_PROTOTYPES.values()):
                self.log_callback("Deck: Falling back to classic deck due to empty large deck definition.")
                composition_key = 'count_classic'
                for card_name, prototype in CARD_PROTOTYPES.items():
                    count = getattr(prototype, composition_key, 0)
                    for _ in range(count): self.cards.append(prototype)

        self.log_callback(f"Deck: Created with {len(self.cards)} cards.")

    def shuffle(self):
        random.shuffle(self.cards)
        self.log_callback("Deck: Shuffled.")

    def draw(self):
        return self.cards.pop(0) if self.cards else None

    def burn_one_card(self, num_players):
        if num_players > 1 and self.cards:  # Standard Love Letter rule
            self.burned_card = self.draw()
            if self.burned_card:
                self.log_callback(
                    f"Deck: Burned one card ({self.burned_card.name}). {len(self.cards)} cards remaining.")
            else:
                self.log_callback("Deck: Tried to burn card, but deck was empty after draw attempt.")
        elif num_players == 2:  # Special rule for 2 players, burn 3 face up
            # This implementation doesn't burn 3 face up, but the original didn't either for simplicity.
            # Sticking to one burned card for now as per original simpler implementation.
            # If complex 2-player rules are needed, this needs more specific handling.
            if self.cards:
                self.burned_card = self.draw()
                if self.burned_card:
                    self.log_callback(
                        f"Deck (2P): Burned one card ({self.burned_card.name}). {len(self.cards)} cards remaining.")

    def is_empty(self):
        return not self.cards

    def count(self):
        return len(self.cards)


class Player:
    def __init__(self, id_num, name, is_cpu=False):
        self.id = id_num
        self.name = name
        self.hand = []  # List of Card objects
        self.discard_pile = []  # List of Card objects
        self.tokens = 0
        self.is_eliminated = False
        self.is_protected = False
        self.is_cpu = is_cpu
        self.sycophant_target_self = False
        self.jester_on_player_id = None  # ID of player they Jestered
        # self.has_jester_token_from_id = None # Not strictly needed on target
        self.effective_value_end_round = 0  # For Count card and end of round comparison
        self.discard_sum_end_round = 0  # For tie-breaking

    def reset_for_round(self):
        self.hand = []
        self.discard_pile = []
        self.is_eliminated = False
        self.is_protected = False
        self.sycophant_target_self = False
        self.jester_on_player_id = None
        self.effective_value_end_round = 0
        self.discard_sum_end_round = 0

    def add_card_to_hand(self, card):
        if card:
            self.hand.append(card)

    def play_card(self, card_name_to_play):
        """Removes card from hand, adds to discard, returns the Card object played."""
        card_to_play = next((c for c in self.hand if c.name == card_name_to_play), None)
        if card_to_play:
            self.hand.remove(card_to_play)
            self.discard_pile.append(card_to_play)
            return card_to_play
        return None

    def force_discard(self, game_deck, burned_card_ref):  # For Prince effect
        """Discards hand, draws new. Returns discarded card. Modifies burned_card_ref if used."""
        if not self.hand: return None

        discarded_card = self.hand.pop(0)
        self.discard_pile.append(discarded_card)

        new_card = None
        if not game_deck.is_empty():
            new_card = game_deck.draw()
        elif burned_card_ref['card']:  # Use shared mutable reference for burned card
            new_card = burned_card_ref['card']
            burned_card_ref['card'] = None  # Burned card is used

        if new_card:
            self.add_card_to_hand(new_card)
        return discarded_card

    def get_hand_card_names(self):
        return [card.name for card in self.hand]

    def get_hand_card_values(self):
        return [card.value for card in self.hand]

    def has_card(self, card_name):
        return any(c.name == card_name for c in self.hand)

    def has_discarded(self, card_name):
        return any(c.name == card_name for c in self.discard_pile)

    def __repr__(self):
        return f"Player({self.name}, Tokens:{self.tokens}, Hand:{[c.name for c in self.hand]})"


class GameRound:
    def __init__(self, players_list, deck_obj, human_player_id, log_callback, ui_callbacks):
        self.players = players_list  # List of Player objects
        self.deck = deck_obj
        self.human_player_id = human_player_id
        self.log_message = log_callback
        self.ui = ui_callbacks  # Dictionary of callbacks to the UI

        self.current_player_idx = 0
        self.round_active = False
        self.game_over_pending_from_round = False  # If an effect causes game to end mid-round (e.g. Bishop token)

        # Shared mutable reference for the burned card if Prince needs it
        # self.deck.burned_card is the actual Card object
        self.shared_burned_card_ref = {'card': self.deck.burned_card}

    def start_round(self):
        self.log_message("--- Starting New Round (GameRound) ---")
        for p in self.players:
            p.reset_for_round()
            drawn_card = self.deck.draw()
            if drawn_card:
                p.add_card_to_hand(drawn_card)
            else:
                self.log_message(f"Error: Not enough cards to deal to {p.name}. Deck empty.")
                p.is_eliminated = True  # Should not happen with proper deck sizes

        self.current_player_idx = random.randrange(len(self.players))
        self.round_active = True
        self.log_message(f"Round started. {self.players[self.current_player_idx].name} goes first.")
        self.ui['update_ui_full_callback']()
        self._process_current_player_turn_start()

    # In class GameRound
    def _execute_cpu_turn_after_delay(self, cpu_player):
        if not self.round_active or cpu_player.is_eliminated:
            if self.round_active and not self.players[
                self.current_player_idx].is_eliminated:  # If current player is still this CPU and round active
                self._advance_to_next_turn()
            return

        # Ensure it's still this CPU's turn. If another CPU was faster due to random delays, or player eliminated, skip.
        if self.players[self.current_player_idx] != cpu_player:
            # This case should be rare if delays are handled per CPU turn.
            # If it happens, and current player is CPU, their own delay timer should be running.
            # If current player is human, game is waiting for human.
            return

        self.log_message(f"CPU ({cpu_player.name}) decides to play.")
        self._cpu_play_turn(cpu_player)  # Call the original CPU play logic

    # In class GameRound
    def _process_current_player_turn_start(self):
        if not self.round_active: return

        current_player = self.players[self.current_player_idx]
        if current_player.is_eliminated:
            self._advance_to_next_turn()
            return

        current_player.is_protected = False  # Protection wears off

        if not self.deck.is_empty():
            drawn_card = self.deck.draw()
            current_player.add_card_to_hand(drawn_card)
            if not current_player.is_cpu:
                self.log_message(
                    f"You ({current_player.name}) drew {drawn_card.name}. Hand: {current_player.get_hand_card_names()}.")
            else:
                self.log_message(f"{current_player.name} drew a card. Hand size: {len(current_player.hand)}.")
            self.ui['update_ui_full_callback']()
        else:
            self.log_message("Deck is empty. Round ends by deck out.")
            self._end_round_deck_empty()
            return

        # Now player makes a choice
        if current_player.is_cpu:
            self.log_message(f"CPU ({current_player.name}) is thinking...")
            delay_duration = random.uniform(1.0, 2.0)  # Random delay between 1 and 2 seconds
            Clock.schedule_once(lambda dt: self._execute_cpu_turn_after_delay(current_player), delay_duration)
        else:  # Human player
            self.log_message(f"Your turn, {current_player.name}. Choose a card to play.")
            self.ui['set_waiting_flag_callback'](False)
            hand_names = current_player.get_hand_card_names()
            if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and \
                    ((self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                     (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)):
                self.log_message("INFO: You have Countess and King/Prince. You MUST play Countess.")

    def human_plays_card(self, card_name_played):
        player = self.players[self.current_player_idx]
        if player.is_cpu or not self.round_active: return

        actual_card_to_play_name = card_name_played
        hand_names = player.get_hand_card_names()

        has_king_or_prince = (self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                             (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)

        if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and has_king_or_prince:
            if card_name_played != 'Countess':
                self.log_message("Countess Rule: Auto-playing Countess as King/Prince also in hand.")
                actual_card_to_play_name = 'Countess'

        card_object_played = player.play_card(actual_card_to_play_name)
        if card_object_played:
            self._handle_card_played_logic(player, card_object_played)
        else:
            self.log_message(
                f"ERROR: {player.name} tried to play {actual_card_to_play_name} but failed (not in hand or other issue).")
            # This indicates a bug or desync. For safety, try to proceed if possible.
            self.ui['set_waiting_flag_callback'](False)  # Release wait
            if self.round_active: self._advance_to_next_turn()

    def _cpu_play_turn(self, cpu_player):
        self.log_message(f"CPU ({cpu_player.name})'s turn.")
        hand_names = cpu_player.get_hand_card_names()

        has_king_or_prince = (self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                             (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)

        if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and has_king_or_prince:
            self.log_message(f"CPU ({cpu_player.name}) has Countess and King/Prince, must play Countess.")
            card_object_played = cpu_player.play_card('Countess')
            self._handle_card_played_logic(cpu_player, card_object_played)
            return

        playable_cards = list(cpu_player.hand)
        if self._is_card_in_current_deck('Princess') and len(playable_cards) > 1:
            playable_cards = [c for c in playable_cards if c.name != 'Princess']
            if not playable_cards: playable_cards = list(cpu_player.hand)  # Should not happen

        chosen_card_object = random.choice(playable_cards) if playable_cards else random.choice(cpu_player.hand)
        card_object_played = cpu_player.play_card(chosen_card_object.name)
        self._handle_card_played_logic(cpu_player, card_object_played)

    def _handle_card_played_logic(self, player, card_object_played):
        self.log_message(f"{player.name} plays {card_object_played.name}.")
        self.ui['update_ui_full_callback']()  # Show card moved to discard

        if self._is_card_in_current_deck('Princess') and card_object_played.name == 'Princess':
            self.log_message(f"{player.name} discarded the Princess and is eliminated!")
            self._eliminate_player(player)
            self._finish_effect_and_proceed()
            return

        needs_input = self._execute_card_effect(player, card_object_played)
        if not needs_input:
            self._finish_effect_and_proceed()

    def _is_card_in_current_deck(self, card_name):
        prototype = CARD_PROTOTYPES.get(card_name)
        if not prototype: return False
        composition_key = 'count_classic' if len(self.players) <= 4 else 'count_large'
        return getattr(prototype, composition_key, 0) > 0

    def _get_valid_targets(self, acting_player, include_self=False, targeted_effect_requires_unprotected=True,
                           allow_no_hand=False):
        targets = []
        for p in self.players:
            if p == acting_player and not include_self:
                continue
            if p.is_eliminated:
                continue
            if targeted_effect_requires_unprotected and p.is_protected and p != acting_player:
                continue
            if not p.hand and not allow_no_hand and p != acting_player:  # Player can target self with Prince even if no hand (to draw burned)
                # Baroness/Priest etc. can target players with no hand, but effect might fizzle.
                # Let's assume most effects require a hand unless specified.
                # Guard, Baron, QM definitely need hands. Prince can target empty hand (to force draw burned).
                if card_object_played.name in ["Guard", "Baron", "Queen Mother", "King",
                                               "Cardinal"]:  # Check card being played
                    continue
            targets.append(p)
        return targets

    # --- Card Effect Execution ---
    def _execute_card_effect(self, player, card):  # card is Card object
        card_name = card.name
        if not self._is_card_in_current_deck(card_name):
            self.log_message(f"{card_name} is not part of the current deck composition. Effect fizzles.")
            return False

        must_target_self = player.sycophant_target_self
        player.sycophant_target_self = False  # Reset flag

        # Note: 'self' here refers to GameRound instance
        effect_method_name = f"_effect_{card_name.lower().replace(' ', '_')}"
        effect_method = getattr(self, effect_method_name, None)

        if effect_method:
            if card_name in ['Handmaid', 'Countess', 'Assassin', 'Count', 'Sheriff']:  # No target / passive
                return effect_method(player, card)  # must_target_self not relevant
            else:  # Targeting effects
                return effect_method(player, card, must_target_self)
        else:
            self.log_message(f"Effect for {card_name} not implemented or is passive/automatic.");
            return False  # Default to no further input needed

    def _finish_effect_and_proceed(self):
        self.ui['set_waiting_flag_callback'](False)
        if self.ui['get_active_popup_callback']():  # If a popup was active, ensure it's dismissed
            self.ui['dismiss_active_popup_callback']()

        if self.game_over_pending_from_round:  # Game ended due to token gain (e.g. Bishop)
            self.round_active = False  # Ensure round is marked as not active
            self.ui['game_over_callback'](self.game_over_winner)  # Trigger game over in UI
            return

        round_ended_by_elimination = self._check_round_end_by_elimination()
        if not round_ended_by_elimination and self.round_active:
            self._advance_to_next_turn()

        self.ui['update_ui_full_callback']()

    def _eliminate_player(self, player_to_eliminate):
        if player_to_eliminate.is_eliminated: return
        player_to_eliminate.is_eliminated = True
        self.log_message(f"{player_to_eliminate.name} has been eliminated!")

        if self._is_card_in_current_deck('Sheriff') and player_to_eliminate.has_discarded('Sheriff'):
            self.log_message(f"{player_to_eliminate.name} had Sheriff in discard and gains a token!")
            player_to_eliminate.tokens += 1
            if self.ui['check_game_over_token_callback'](player_to_eliminate):
                self.game_over_pending_from_round = True
                self.game_over_winner = player_to_eliminate

        # self.ui['update_ui_full_callback']() # Called by finisher

    def _advance_to_next_turn(self):
        if not self.round_active: return

        original_idx = self.current_player_idx
        attempts = 0
        while attempts < len(self.players) * 2:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            if not self.players[self.current_player_idx].is_eliminated:
                break
            attempts += 1

        # This check is secondary; primary check is in _check_round_end_by_elimination
        active_players_count = sum(1 for p in self.players if not p.is_eliminated)
        if active_players_count <= 1 and self.round_active:
            self._end_round_by_elimination()  # Should have been caught by _check_round_end_by_elimination
            return

        next_player = self.players[self.current_player_idx]
        if not next_player.is_cpu:
            self.log_message(f"--- Your turn ({next_player.name}) ---")
        else:
            self.log_message(f"--- {next_player.name}'s turn ---")

        self._process_current_player_turn_start()

    def _check_round_end_by_elimination(self):  # Returns True if round ended this way
        if not self.round_active: return True

        active_players = [p for p in self.players if not p.is_eliminated]
        if len(active_players) <= 1:
            self._end_round_by_elimination(active_players)
            return True
        return False

    def _end_round_by_elimination(self, active_players_list=None):
        if not self.round_active: return
        self.log_message("Round ends: one or zero players remain active.")
        self.round_active = False

        if active_players_list is None:  # Recalculate if not passed
            active_players_list = [p for p in self.players if not p.is_eliminated]

        winner = active_players_list[0] if len(active_players_list) == 1 else None

        if winner:
            self.log_message(f"{winner.name} is the last player remaining and wins the round!")
        else:
            self.log_message("All players were eliminated simultaneously! No winner this round from eliminations.")

        self.ui['award_round_tokens_callback']([winner] if winner else [])

    def _end_round_deck_empty(self):
        if not self.round_active: return
        self.log_message("Round ends: deck is empty. Comparing hands of remaining active players.")
        self.round_active = False

        active_players_with_hands = [p for p in self.players if not p.is_eliminated and p.hand]
        if not active_players_with_hands:
            self.log_message("No active players with cards remaining. No winner this round.");
            self.ui['award_round_tokens_callback']([])
            return

        is_count_in_deck = self._is_card_in_current_deck('Count')
        for p_obj in active_players_with_hands:
            p_obj.effective_value_end_round = p_obj.hand[0].value
            if is_count_in_deck and p_obj.has_discarded('Count'):
                p_obj.effective_value_end_round += 1
                self.log_message(
                    f"{p_obj.name} has Count in discard. Hand: {p_obj.hand[0].name}, Effective Value: {p_obj.effective_value_end_round}")

        active_players_with_hands.sort(key=lambda p: p.effective_value_end_round, reverse=True)
        highest_val = active_players_with_hands[0].effective_value_end_round
        winners_by_val = [p for p in active_players_with_hands if p.effective_value_end_round == highest_val]

        final_winners = []
        if len(winners_by_val) == 1:
            final_winners = winners_by_val
            self.log_message(
                f"{final_winners[0].name} has the highest card ({final_winners[0].hand[0].name}, effective value {final_winners[0].effective_value_end_round}) and wins!")
        else:  # Tie in card values
            self.log_message(f"Tie in card values at {highest_val}. Comparing sum of discarded card values.")
            for p_obj in winners_by_val:
                p_obj.discard_sum_end_round = sum(c.value for c in p_obj.discard_pile)
                self.log_message(
                    f"{p_obj.name} (Card: {p_obj.hand[0].name}, Eff: {p_obj.effective_value_end_round}) discard sum: {p_obj.discard_sum_end_round}")

            winners_by_val.sort(key=lambda p: p.discard_sum_end_round, reverse=True)
            highest_discard_sum = winners_by_val[0].discard_sum_end_round
            final_winners = [p for p in winners_by_val if p.discard_sum_end_round == highest_discard_sum]

            if len(final_winners) == 1:
                self.log_message(
                    f"{final_winners[0].name} wins the tie-breaker with highest discard sum ({highest_discard_sum})!")
            else:
                self.log_message(
                    f"Still a tie! {[p.name for p in final_winners]} win this round.")

        self.ui['award_round_tokens_callback'](final_winners)

    # --- Specific Card Effect Implementations ---
    # These methods now belong to GameRound. They will use self.ui['request_xxx_popup_callback']
    # and provide a method of GameRound (e.g., self._resolve_guard_target_selected) as the continuation.

    def _effect_guard(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:  # Guard cannot target self
            self.log_message(f"Sycophant: {player.name} must target self, but Guard cannot. Effect fizzles.")
            return False
        if not valid_targets: self.log_message("Guard: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            possible_values = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                              if proto.value != 1 and self._is_card_in_current_deck(name))))
            if not possible_values: self.log_message("Guard (CPU): No valid card values to guess!"); return False
            guess_val = random.choice(possible_values)
            self.log_message(f"CPU ({player.name}) plays Guard on {target_player.name}, guessing value {guess_val}.")
            self._resolve_guard_guess(player, target_player, guess_val)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_guard_target_selected  # GameRound method as callback
            )
            return True  # Input awaited

    def _resolve_guard_target_selected(self, acting_player, target_player_id):  # Called by UI
        target_player = next(p for p in self.players if p.id == target_player_id)

        possible_values_to_guess = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                                   if proto.value != 1 and self._is_card_in_current_deck(name))))
        if not possible_values_to_guess:
            self.log_message(f"Guard: No valid card values to guess against {target_player.name}! Effect fizzles.");
            self._finish_effect_and_proceed()
            return

        self.ui['request_guard_value_popup_callback'](
            acting_player, target_player, possible_values_to_guess,
            self._resolve_guard_value_guessed  # GameRound method as callback
        )
        # Still waiting for input

    def _resolve_guard_value_guessed(self, acting_player, target_player, guessed_value):  # Called by UI
        self.log_message(f"{acting_player.name} (Guard) guesses value {guessed_value} for {target_player.name}.")
        self._resolve_guard_guess(acting_player, target_player, guessed_value)
        self._finish_effect_and_proceed()

    def _resolve_guard_guess(self, acting_player, target_player, guessed_value):  # Core logic
        if not target_player.hand: return

        target_card = target_player.hand[0]

        if self._is_card_in_current_deck('Assassin') and target_card.name == 'Assassin':
            self.log_message(f"{target_player.name} reveals Assassin! {acting_player.name} is eliminated!")
            self._eliminate_player(acting_player)

            target_player.play_card('Assassin')  # Discard Assassin
            if not self.deck.is_empty():
                new_card = self.deck.draw()
                if new_card: target_player.add_card_to_hand(new_card)
            elif self.shared_burned_card_ref['card']:
                new_card = self.shared_burned_card_ref['card']
                target_player.add_card_to_hand(new_card)
                self.shared_burned_card_ref['card'] = None

            self.log_message(f"{target_player.name} discards Assassin and draws a new card.")
            return

        if target_card.value == guessed_value:
            self.log_message(f"Correct! {target_player.name} had {target_card.name}. Eliminated.")
            self._eliminate_player(target_player)
        else:
            self.log_message(f"Incorrect guess. {target_player.name} did not have value {guessed_value}.")

    def _effect_priest(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but Priest cannot. Fizzles.")
            return False
        if not valid_targets: self.log_message("Priest: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_priest_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_priest_target_selected
            )
            return True

    def _resolve_priest_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_priest_effect(acting_player, target_player)
        # UI does not show card for human player directly, log message is enough.
        self._finish_effect_and_proceed()

    def _resolve_priest_effect(self, acting_player, target_player):
        if not target_player.hand:
            self.log_message(f"{target_player.name} has no hand to see (Priest).")
            return

        target_card_name = target_player.hand[0].name
        if not acting_player.is_cpu:  # Human player
            self.log_message(
                f"You ({acting_player.name}) use Priest on {target_player.name} and see their {target_card_name}.")
        elif not target_player.is_cpu:  # CPU on Human
            self.log_message(f"{acting_player.name} (Priest) looks at your hand and sees your {target_card_name}.")
        else:  # CPU on CPU
            self.log_message(f"{acting_player.name} (Priest) looks at {target_player.name}'s hand.")
            # AI would store this info: acting_player.remember_card(target_player.id, target_card_name)

    def _effect_baron(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but Baron cannot. Fizzles.")
            return False
        if not valid_targets: self.log_message("Baron: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_baron_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_baron_target_selected
            )
            return True

    def _resolve_baron_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_baron_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_baron_effect(self, player, target_player):
        if not player.hand or not target_player.hand:
            self.log_message("Baron comparison requires both players to have cards. Fizzles.")
            return

        player_card = player.hand[0]
        opponent_card = target_player.hand[0]

        log_msg = f"{player.name}({player_card.name} V:{player_card.value}) vs {target_player.name}({opponent_card.name} V:{opponent_card.value}). "
        if player_card.value > opponent_card.value:
            log_msg += f"{target_player.name} is eliminated."
            self._eliminate_player(target_player)
        elif opponent_card.value > player_card.value:
            log_msg += f"{player.name} is eliminated."
            self._eliminate_player(player)
        else:
            log_msg += "Tie. No one eliminated."
        self.log_message(log_msg)

    def _effect_handmaid(self, player, card_played):
        player.is_protected = True
        self.log_message(f"{player.name} plays Handmaid and is protected.")
        return False  # No input needed

    def _effect_prince(self, player, card_played, must_target_self):
        valid_targets = []
        if must_target_self:
            if not player.is_eliminated: valid_targets = [player]
            if not valid_targets: self.log_message(
                f"Prince (Sycophant): {player.name} must target self but invalid. Fizzles."); return False
        else:
            # Prince can target self, even if no hand (to draw burned card)
            valid_targets = self._get_valid_targets(player, include_self=True,
                                                    targeted_effect_requires_unprotected=True, allow_no_hand=True)

        if not valid_targets: self.log_message("Prince: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self.log_message(f"CPU ({player.name}) plays Prince, targeting {target_player.name}.")
            self._resolve_prince_effect(target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_prince_target_selected
            )
            return True

    def _resolve_prince_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self.log_message(f"{acting_player.name} (Prince) targets {target_player.name} to discard and draw.")
        self._resolve_prince_effect(target_player)
        self._finish_effect_and_proceed()

    def _resolve_prince_effect(self, target_player):  # Reusable by Bishop too
        if not target_player.hand and not self.shared_burned_card_ref[
            'card'] and self.deck.is_empty():  # Nothing to discard, nothing to draw
            self.log_message(f"{target_player.name} has no hand and no cards to draw (Prince).")
            return

        discarded_card = None
        if target_player.hand:
            # Player.force_discard handles removing from hand and adding to discard_pile
            # It also handles drawing the new card.
            # We need to pass self.deck and self.shared_burned_card_ref to it.
            original_hand_card = target_player.hand[0]  # For logging, if it's Princess
            discarded_card = target_player.force_discard(self.deck, self.shared_burned_card_ref)
            self.log_message(f"{target_player.name} discards {discarded_card.name}.")

            if self._is_card_in_current_deck('Princess') and discarded_card.name == 'Princess':
                self.log_message(f"{target_player.name} discarded Princess (forced by Prince) and is eliminated!")
                self._eliminate_player(target_player)
                return  # No new card if eliminated this way
        else:  # No hand to discard, but might draw burned card
            if not self.deck.is_empty():
                new_card = self.deck.draw()
                target_player.add_card_to_hand(new_card)
            elif self.shared_burned_card_ref['card']:
                new_card = self.shared_burned_card_ref['card']
                target_player.add_card_to_hand(new_card)
                self.shared_burned_card_ref['card'] = None
            else:  # No card to draw
                self.log_message(f"{target_player.name} has no card to draw (deck and burned card empty).")

        if target_player.hand:  # If they drew a card
            if not target_player.is_cpu:
                self.log_message(f"You ({target_player.name}) draw {target_player.hand[0].name}.")
            else:
                self.log_message(f"{target_player.name} draws a new card.")
        elif not target_player.is_eliminated:  # No hand and not eliminated (e.g. deck/burned empty)
            self.log_message(f"{target_player.name} has no card after Prince effect (deck and burned card empty).")

    def _effect_king(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but King cannot. Fizzles.")
            return False
        if not valid_targets: self.log_message("King: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_king_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_king_target_selected
            )
            return True

    def _resolve_king_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_king_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_king_effect(self, player, target_player):
        if not player.hand or not target_player.hand:
            self.log_message("King swap requires both players to have cards. Fizzles.");
            return

        player_card_obj = player.hand.pop(0)
        opponent_card_obj = target_player.hand.pop(0)

        player.add_card_to_hand(opponent_card_obj)
        target_player.add_card_to_hand(player_card_obj)

        self.log_message(f"{player.name} (King) swaps hand with {target_player.name}. "
                         f"{player.name} gets {opponent_card_obj.name}, {target_player.name} gets {player_card_obj.name}.")

    def _effect_countess(self, player, card_played):
        self.log_message("Countess played. No special effect.");
        return False

    def _effect_princess(self, player, card_played):  # Should be caught before this by _handle_card_played_logic
        self.log_message(f"ERROR: Princess effect executed, should have been caught earlier.");
        return False

    # Expansion Card Effects
    def _effect_assassin(self, player, card_played):
        self.log_message("Assassin played. (Passive effect on being targeted by Guard)");
        return False

    def _effect_jester(self, player, card_played, must_target_self):
        valid_targets = []
        if must_target_self:
            if not player.is_eliminated: valid_targets = [player]
            if not valid_targets: self.log_message(
                f"Jester (Sycophant): {player.name} must target self but invalid. Fizzles."); return False
        else:  # Jester not affected by Handmaid
            valid_targets = self._get_valid_targets(player, include_self=True,
                                                    targeted_effect_requires_unprotected=False)

        if not valid_targets: self.log_message("Jester: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_jester_effect(player, target_player);
            return False
        else:
            self.ui['request_target_selection_callback'](player, card_played, valid_targets,
                                                         self._resolve_jester_target_selected);
            return True

    def _resolve_jester_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_jester_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_jester_effect(self, player, target_player):
        player.jester_on_player_id = target_player.id
        self.log_message(f"{player.name} (Jester) targets {target_player.name}. If they win, {player.name} gets token.")

    def _effect_cardinal(self, player, card_played,
                         must_target_self):  # must_target_self not really applicable due to 2 targets
        other_active_players_with_hands = [p for p in self.players if p != player and not p.is_eliminated and p.hand]

        if len(other_active_players_with_hands) < 2:
            self.log_message("Cardinal: Not enough other players with hands for swap.");
            return False

        if player.is_cpu:
            p1_swap, p2_swap = random.sample(other_active_players_with_hands, 2)
            self._resolve_cardinal_swap_and_look_cpu(player, p1_swap, p2_swap)
            return False
        else:
            self.ui['request_cardinal_first_target_popup_callback'](player, card_played,
                                                                    other_active_players_with_hands,
                                                                    self._resolve_cardinal_first_target_selected)
            return True

    def _resolve_cardinal_first_target_selected(self, acting_player, p1_swap_id):
        p1_swap = next(p for p in self.players if p.id == p1_swap_id)
        other_valid_for_p2 = [p for p in self.players if
                              p != acting_player and p != p1_swap and not p.is_eliminated and p.hand]
        if not other_valid_for_p2:
            self.log_message(f"Cardinal: No valid second player to swap with {p1_swap.name}. Fizzles.");
            self._finish_effect_and_proceed();
            return

        self.ui['request_cardinal_second_target_popup_callback'](acting_player, p1_swap, other_valid_for_p2,
                                                                 self._resolve_cardinal_second_target_selected)

    def _resolve_cardinal_second_target_selected(self, acting_player, p1_swap, p2_swap_id):
        p2_swap = next(p for p in self.players if p.id == p2_swap_id)

        swapped_any = self._perform_cardinal_swap(p1_swap, p2_swap)
        if not swapped_any: self._finish_effect_and_proceed(); return

        # Human now chooses who to look at
        self.ui['request_cardinal_look_choice_popup_callback'](acting_player, p1_swap, p2_swap,
                                                               self._resolve_cardinal_look_choice_selected)

    def _perform_cardinal_swap(self, p1_swap, p2_swap):
        if not p1_swap.hand or not p2_swap.hand:
            self.log_message(f"Cardinal: One of {p1_swap.name}, {p2_swap.name} has no hand. Swap fizzles.");
            return False

        p1_card = p1_swap.hand.pop(0)
        p2_card = p2_swap.hand.pop(0)
        p1_swap.add_card_to_hand(p2_card)
        p2_swap.add_card_to_hand(p1_card)
        self.log_message(
            f"Cardinal: {p1_swap.name} (now has {p2_card.name}) and {p2_swap.name} (now has {p1_card.name}) swapped hands.")
        return True

    def _resolve_cardinal_swap_and_look_cpu(self, acting_player, p1_swap, p2_swap):
        swapped_any = self._perform_cardinal_swap(p1_swap, p2_swap)
        if not swapped_any: return  # Already logged

        look_target = random.choice([p1_swap, p2_swap])
        if look_target.hand:
            card_seen = look_target.hand[0].name
            if not look_target.is_cpu:  # CPU looks at human
                self.log_message(
                    f"CPU ({acting_player.name}) (Cardinal) looks at your ({look_target.name}) new card: {card_seen}.")
            else:  # CPU looks at CPU
                self.log_message(
                    f"CPU ({acting_player.name}) (Cardinal) looks at {look_target.name}'s new card ({card_seen}).")  # Log for debug/AI
        else:
            self.log_message(
                f"CPU ({acting_player.name}) (Cardinal) tries to look at {look_target.name}'s hand, but it's empty.")

    def _resolve_cardinal_look_choice_selected(self, acting_player, look_target_id):
        look_target = next(p for p in self.players if p.id == look_target_id)
        if look_target.hand:
            card_seen = look_target.hand[0].name
            self.log_message(
                f"You ({acting_player.name}) (Cardinal) look at {look_target.name}'s new card: {card_seen}.")
        else:
            self.log_message(f"You ({acting_player.name}) (Cardinal) look at {look_target.name}'s hand, it's empty.")
        self._finish_effect_and_proceed()

    def _effect_baroness(self, player, card_played, must_target_self):
        valid_targets_all = self._get_valid_targets(player, include_self=False,
                                                    targeted_effect_requires_unprotected=False)  # Not affected by Handmaid for looking
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but Baroness cannot. Fizzles.")
            return False
        if not valid_targets_all: self.log_message("Baroness: No other players to look at."); return False

        if player.is_cpu:
            num_to_look = random.randint(1, min(2, len(valid_targets_all)))
            targets_to_look = random.sample(valid_targets_all, num_to_look)
            for i, target_p in enumerate(targets_to_look):
                log_prefix = f"CPU ({player.name}) (Baroness, target {i + 1}/{num_to_look})"
                if target_p.hand:
                    seen_card = target_p.hand[0].name
                    if not target_p.is_cpu:
                        self.log_message(f"{log_prefix} sees your ({target_p.name}) card: {seen_card}.")
                    else:
                        self.log_message(
                            f"{log_prefix} looks at {target_p.name}'s hand ({seen_card}).")  # Log for debug/AI
                else:
                    self.log_message(f"{log_prefix}: {target_p.name} has no card.")
            return False
        else:
            # Simplified: human chooses one target. Can be extended to choose 1 or 2.
            self.log_message("Baroness: Choose one player to look at their hand (currently simplified).")
            self.ui['request_target_selection_callback'](player, card_played, valid_targets_all,
                                                         self._resolve_baroness_look_selected);
            return True

    def _resolve_baroness_look_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        if target_player.hand:
            self.log_message(
                f"You ({acting_player.name}) (Baroness) look at {target_player.name}'s hand and see {target_player.hand[0].name}.")
        else:
            self.log_message(f"You ({acting_player.name}) (Baroness) look at {target_player.name}'s hand. It is empty.")
        self._finish_effect_and_proceed()

    def _effect_sycophant(self, player, card_played, must_target_self):
        valid_targets = []
        if must_target_self:
            if not player.is_eliminated: valid_targets = [player]
            if not valid_targets: self.log_message(
                f"Sycophant (Sycophant): {player.name} must target self but invalid. Fizzles."); return False
        else:
            valid_targets = self._get_valid_targets(player, include_self=True,
                                                    targeted_effect_requires_unprotected=True)

        if not valid_targets: self.log_message("Sycophant: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_sycophant_effect(player, target_player);
            return False
        else:
            self.ui['request_target_selection_callback'](player, card_played, valid_targets,
                                                         self._resolve_sycophant_target_selected);
            return True

    def _resolve_sycophant_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_sycophant_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_sycophant_effect(self, player, target_player):
        target_player.sycophant_target_self = True
        self.log_message(
            f"{player.name} (Sycophant) targets {target_player.name}. Their next effect card must self-target.")

    def _effect_count(self, player, card_played):
        self.log_message("Count played. Effect at round end if in discard pile.");
        return False

    def _effect_sheriff(self, player, card_played):
        self.log_message("Sheriff played. Effect if eliminated while in discard pile.");
        return False

    def _effect_queen_mother(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but Queen Mother cannot. Fizzles.")
            return False
        if not valid_targets: self.log_message("Queen Mother: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_queen_mother_effect(player, target_player);
            return False
        else:
            self.ui['request_target_selection_callback'](player, card_played, valid_targets,
                                                         self._resolve_queen_mother_target_selected);
            return True

    def _resolve_queen_mother_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_queen_mother_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_queen_mother_effect(self, player, target_player):
        if not player.hand or not target_player.hand:
            self.log_message("Queen Mother comparison requires both players to have cards. Fizzles.");
            return

        player_card = player.hand[0]
        opponent_card = target_player.hand[0]
        log_msg = f"{player.name}({player_card.name} V:{player_card.value}) vs {target_player.name}({opponent_card.name} V:{opponent_card.value}). "

        if player_card.value > opponent_card.value:
            log_msg += f"{player.name} has higher card and is eliminated."
            self._eliminate_player(player)
        elif opponent_card.value > player_card.value:
            log_msg += f"{target_player.name} has higher card and is eliminated."
            self._eliminate_player(target_player)
        else:
            log_msg += "Tie. No one eliminated."
        self.log_message(log_msg)

    def _effect_bishop(self, player, card_played, must_target_self):
        # Bishop target not affected by Handmaid for guess part.
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=False)
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but Bishop cannot. Fizzles.")
            return False
        if not valid_targets: self.log_message("Bishop: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            possible_values = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                              if
                                              proto.value != 1 and self._is_card_in_current_deck(name))))  # Not Guard
            if not possible_values: self.log_message("Bishop (CPU): No valid card values to guess!"); return False
            guess_val = random.choice(possible_values)
            self.log_message(f"CPU ({player.name}) plays Bishop on {target_player.name}, guessing {guess_val}.")
            self._resolve_bishop_guess_and_maybe_redraw_cpu(player, target_player, guess_val)
            return False
        else:
            self.ui['request_target_selection_callback'](player, card_played, valid_targets,
                                                         self._resolve_bishop_target_selected);
            return True

    def _resolve_bishop_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        possible_values_to_guess = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                                   if proto.value != 1 and self._is_card_in_current_deck(name))))
        if not possible_values_to_guess:
            self.log_message(f"Bishop: No valid card values to guess against {target_player.name}! Effect fizzles.");
            self._finish_effect_and_proceed();
            return

        self.ui['request_bishop_value_popup_callback'](acting_player, target_player, possible_values_to_guess,
                                                       self._resolve_bishop_value_guessed)

    def _resolve_bishop_value_guessed(self, acting_player, target_player, guessed_value):  # Human acting
        correct_guess = False
        if target_player.hand and target_player.hand[0].value == guessed_value:
            correct_guess = True
            self.log_message(
                f"Correct Bishop guess! {target_player.name} had {target_player.hand[0].name}. {acting_player.name} gets token.")
            acting_player.tokens += 1
            if self.ui['check_game_over_token_callback'](acting_player):
                self.game_over_pending_from_round = True
                self.game_over_winner = acting_player
                # If game over, target doesn't get to redraw option.
                self._finish_effect_and_proceed();
                return
        else:
            card_info = f"had {target_player.hand[0].name}" if target_player.hand else "has no hand"
            self.log_message(
                f"Incorrect Bishop guess for {target_player.name} (Value {guessed_value}). Target {card_info}.")

        if target_player.is_eliminated or not target_player.hand:
            self.log_message(f"{target_player.name} cannot discard (eliminated or no hand). Bishop effect concludes.");
            self._finish_effect_and_proceed();
            return

        # Offer redraw to target (if human)
        if not target_player.is_cpu:
            self.ui['request_bishop_redraw_choice_popup_callback'](acting_player, target_player, correct_guess,
                                                                   self._resolve_bishop_human_redraw_choice)
        else:  # CPU target makes choice (handled in _resolve_bishop_guess_and_maybe_redraw_cpu)
            # This path is for human acting player, cpu target player
            self._resolve_bishop_cpu_redraw_choice(target_player, correct_guess)
            self._finish_effect_and_proceed()

    def _resolve_bishop_guess_and_maybe_redraw_cpu(self, acting_player, target_player, guessed_value):  # CPU acting
        correct_guess = False
        if target_player.hand and target_player.hand[0].value == guessed_value:
            correct_guess = True
            log_reveal = f"({target_player.hand[0].name})" if not target_player.is_cpu else ""
            self.log_message(
                f"CPU ({acting_player.name}) Bishop guess correct! {target_player.name} had {guessed_value} {log_reveal}. CPU gets token.")
            acting_player.tokens += 1
            if self.ui['check_game_over_token_callback'](acting_player):
                self.game_over_pending_from_round = True
                self.game_over_winner = acting_player;
                return  # Game over, no redraw
        else:
            self.log_message(
                f"CPU ({acting_player.name}) Bishop guess incorrect for {target_player.name} (Value {guessed_value}).")

        if target_player.is_eliminated or not target_player.hand:
            self.log_message(f"{target_player.name} cannot discard. Bishop effect concludes.");
            return

        if not target_player.is_cpu:  # CPU acting, Human target: offer redraw choice
            self.ui['request_bishop_redraw_choice_popup_callback'](acting_player, target_player, correct_guess,
                                                                   self._resolve_bishop_human_redraw_choice)
            # Returns true implicitly because it's waiting for human target
        else:  # CPU acting, CPU target: CPU makes choice
            self._resolve_bishop_cpu_redraw_choice(target_player, correct_guess)
            # Returns false implicitly

    def _resolve_bishop_human_redraw_choice(self, target_player, choice_yes):  # Human target's choice
        if choice_yes:
            self.log_message(f"{target_player.name} (Human) chooses to discard and draw (Bishop).")
            self._resolve_prince_effect(target_player)  # Re-use Prince logic
        else:
            self.log_message(f"{target_player.name} (Human) chooses NOT to discard (Bishop).")
        self._finish_effect_and_proceed()

    def _resolve_bishop_cpu_redraw_choice(self, target_cpu_player, was_correct_guess):  # CPU target's choice
        redraw_chance = 0.5
        if was_correct_guess and target_cpu_player.hand[0].name != 'Princess':
            redraw_chance = 0.8
        elif target_cpu_player.hand[0].value <= 3:
            redraw_chance = 0.7

        if random.random() < redraw_chance:
            self.log_message(f"CPU ({target_cpu_player.name}) chooses to discard and draw (Bishop).")
            self._resolve_prince_effect(target_cpu_player)
        else:
            self.log_message(f"CPU ({target_cpu_player.name}) chooses NOT to discard (Bishop).")
        # If this was called from _resolve_bishop_value_guessed (human acting), then finish_effect_and_proceed is called there.
        # If this was called from _resolve_bishop_guess_and_maybe_redraw_cpu (cpu acting), then finish_effect_and_proceed is called by the caller of that.


# --- Kivy UI and Game Session Management ---

class ImageButton(ButtonBehavior, Image):
    pass


class LoveLetterGame(BoxLayout):  # Kivy Main Widget
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        self.num_players_session = 0
        self.players_session_list = []  # List of Player objects for the whole game session
        self.human_player_id = 0

        self.current_round_manager = None  # GameRound instance

        self.game_log = ["Welcome to Love Letter Kivy!"]
        self.tokens_to_win_session = 0
        self.game_over_session_flag = True
        self.active_popup = None
        self.waiting_for_input = False  # UI waiting for human action

        self._load_card_prototypes_and_images()  # Renamed and combined
        self.setup_ui_placeholders()
        self.prompt_player_count()
        self.opponent_widgets_map = {}  # player_id -> opponent_widget_boxlayout
        self.animated_widget_details = {}  # widget_ref -> {details for clearing}

    def _load_card_prototypes_and_images(self):
        global CARD_PROTOTYPES, CARDS_DATA_RAW  # Ensure using global
        CARD_PROTOTYPES = {}  # Clear previous if any (e.g. restart)

        missing_card_back = False
        if not os.path.exists(CARD_BACK_IMAGE):
            self.log_message(f"CRITICAL ERROR: Card back image not found at {CARD_BACK_IMAGE}", permanent=True)
            missing_card_back = True
        # (ELIMINATED_IMAGE creation logic remains same as original)

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
                image_path=actual_path,  # Store resolved path
                vietnamese_name=viet_name,
                count_classic=data['count_classic'],
                count_large=data['count_large']
            )
        self.log_message(f"Card prototypes and images loaded. {len(CARD_PROTOTYPES)} card types found.", permanent=True)

    def setup_ui_placeholders(self):  # As original
        self.clear_widgets()
        self.add_widget(Label(text="Setting up game... Choose player count."))

    def prompt_player_count(self):  # As original
        self.game_log = ["Welcome to Love Letter Kivy!", "Please select number of players (2-8)."]
        if hasattr(self, 'message_label'): self.log_message("", permanent=False)

        popup_layout = BoxLayout(orientation='vertical', spacing="10dp", padding="10dp")
        popup_layout.add_widget(Label(text="Select Number of Players (2-8):"))
        options_layout = GridLayout(cols=4, spacing="5dp", size_hint_y=None)
        options_layout.bind(minimum_height=options_layout.setter('height'))
        for i in range(2, 9):
            btn = Button(text=str(i), size_hint_y=None, height="40dp")
            btn.player_count = i  # Store on button directly
            btn.bind(on_press=self.initialize_game_with_player_count)
            options_layout.add_widget(btn)
        popup_layout.add_widget(options_layout)
        self.active_popup = Popup(title="Player Count", content=popup_layout,
                                  size_hint=(0.7, 0.5), auto_dismiss=False)
        self.active_popup.open()

    def initialize_game_with_player_count(self, instance):  # Modified for session
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
            self.tokens_to_win_session = 3  # 5-8 players
        self.log_message(f"Tokens needed to win: {self.tokens_to_win_session}")

        self.players_session_list = [Player(id_num=0, name="Player 1 (You)")]
        self.human_player_id = self.players_session_list[0].id
        for i in range(1, self.num_players_session):
            self.players_session_list.append(Player(id_num=i, name=f"CPU {i}", is_cpu=True))

        self.setup_main_ui()  # Rebuilds UI based on player count
        self.start_new_game_session()

    def setup_main_ui(self):  # Mostly as original, uses self.num_players_session
        self.clear_widgets()
        # ... (Top section: score_label, turn_label, message_label - as original)
        top_section = BoxLayout(size_hint_y=0.25, orientation='vertical')
        info_bar = BoxLayout(size_hint_y=None, height=30)
        self.score_label = Label(text="Scores:", size_hint_x=0.7, halign='left', valign='middle')
        self.score_label.bind(size=self.score_label.setter('text_size'))
        self.turn_label = Label(text="Game Over", size_hint_x=0.3, halign='right', valign='middle')
        self.turn_label.bind(size=self.turn_label.setter('text_size'))
        info_bar.add_widget(self.score_label)
        info_bar.add_widget(self.turn_label)
        top_section.add_widget(info_bar)
        log_scroll_view = ScrollView(size_hint_y=1)
        self.message_label = Label(text="\n".join(self.game_log), size_hint_y=None, halign='left', valign='top')
        self.message_label.bind(texture_size=self.message_label.setter('size'))
        log_scroll_view.add_widget(self.message_label)
        top_section.add_widget(log_scroll_view)
        self.add_widget(top_section)

        game_area = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.6)
        self.opponents_area_scrollview = ScrollView(size_hint=(1, 0.4))
        # Ensure opponents_grid cols is based on num_players_session
        self.opponents_grid = GridLayout(
            cols=max(1, self.num_players_session - 1 if self.num_players_session > 1 else 1),
            size_hint_x=None if self.num_players_session - 1 > 3 else 1, size_hint_y=None,
            spacing=5)
        self.opponents_grid.bind(minimum_width=self.opponents_grid.setter('width'))
        self.opponents_grid.bind(minimum_height=self.opponents_grid.setter('height'))
        self.opponents_area_scrollview.add_widget(self.opponents_grid)
        game_area.add_widget(Label(text="Opponents", size_hint_y=None, height=20))
        game_area.add_widget(self.opponents_area_scrollview)
        # ... (Deck area, Player hand area - as original)
        deck_area = BoxLayout(size_hint_y=0.2, spacing=10)
        self.deck_image = Image(source=CARD_BACK_IMAGE, size_hint_x=0.3)
        self.deck_count_label = Label(text="Deck: 0", size_hint_x=0.7)
        deck_area.add_widget(self.deck_image)
        deck_area.add_widget(self.deck_count_label)
        game_area.add_widget(deck_area)
        player_main_area = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=5)
        player_main_area.add_widget(Label(text="Your Hand (Click to Play)", size_hint_y=None, height=20))
        self.player_hand_area = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.7)
        player_main_area.add_widget(self.player_hand_area)
        self.player_discard_display = Image(source="", size_hint_y=0.3)  # Will show top of human player's discard
        player_main_area.add_widget(self.player_discard_display)
        game_area.add_widget(player_main_area)
        self.add_widget(game_area)
        self.human_player_display_wrapper = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=5)
        human_player_display_wrapper_label = Label(text="Your Hand (Click to Play)", size_hint_y=None, height=20)
        self.human_player_display_wrapper.add_widget(human_player_display_wrapper_label)
        self.player_hand_area = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.7)
        self.human_player_display_wrapper.add_widget(self.player_hand_area)
        self.player_discard_display = Image(source="", size_hint_y=0.3)
        self.human_player_display_wrapper.add_widget(self.player_discard_display)
        game_area.add_widget(self.human_player_display_wrapper)  # Add the new wrapper
        self.add_widget(game_area)

        self.action_button = Button(text="Start New Game Session", size_hint_y=None, height=50)
        self.action_button.bind(on_press=self.on_press_action_button)
        self.add_widget(self.action_button)
        self.update_ui_full()  # Initial UI update

    def log_message(self, msg, permanent=True):  # As original
        print(msg)  # For console debugging
        if permanent:
            self.game_log.append(msg)
            if len(self.game_log) > 100: self.game_log = self.game_log[-100:]
        if hasattr(self, 'message_label'):
            self.message_label.text = "\n".join(self.game_log)
            if self.message_label.parent and isinstance(self.message_label.parent, ScrollView):
                self.message_label.parent.scroll_y = 0  # Auto-scroll to bottom

    def update_ui_full(self):
        if not hasattr(self, 'score_label'): return  # UI not fully setup

        score_texts = [f"{p.name}: {p.tokens}" for p in self.players_session_list]
        self.score_label.text = "Scores: " + " | ".join(score_texts)

        current_player_name_round = "N/A"
        is_round_active_for_ui = False
        if self.current_round_manager and self.current_round_manager.round_active:
            is_round_active_for_ui = True
            current_player_name_round = self.players_session_list[self.current_round_manager.current_player_idx].name

        if self.game_over_session_flag:
            self.turn_label.text = "Game Over!"
            self.action_button.text = "Start New Game Session"
        elif not is_round_active_for_ui:  # Round ended, waiting for next or game setup
            self.turn_label.text = "Round Over"
            self.action_button.text = "Start Next Round"
        else:  # Round is active
            self.turn_label.text = f"Turn: {current_player_name_round}"
            self.action_button.text = "Forfeit Round (DEBUG)"  # Or other active round action

        # Deck UI
        if self.current_round_manager and self.current_round_manager.deck:
            self.deck_count_label.text = f"Deck: {self.current_round_manager.deck.count()}"
            self.deck_image.source = CARD_BACK_IMAGE if not self.current_round_manager.deck.is_empty() else ""
        else:
            self.deck_count_label.text = "Deck: N/A"
            self.deck_image.source = ""

        # Opponents UI
        self.opponents_grid.clear_widgets()
        self.opponent_widgets_map.clear()  # Clear map before repopulating
        if self.num_players_session > 1:  # Make sure there are opponents to display
            self.opponents_grid.cols = max(1, self.num_players_session - 1)
            if self.num_players_session - 1 > 4:
                self.opponents_grid.size_hint_x = None
            else:
                self.opponents_grid.size_hint_x = 1

            for p_opponent in self.players_session_list:
                if p_opponent.id == self.human_player_id: continue  # Skip human player

                opponent_widget = BoxLayout(orientation='vertical', size_hint_y=None, height=120, width=80,
                                            padding=2)  # Added padding
                opponent_widget.add_widget(Label(text=p_opponent.name, size_hint_y=0.15, font_size='10sp'))

                card_img_src = CARD_BACK_IMAGE  # Default to card back
                if p_opponent.is_eliminated:
                    card_img_src = ELIMINATED_IMAGE
                elif not p_opponent.hand:
                    card_img_src = ""  # No card (e.g. eliminated and hand cleared)
                opponent_widget.add_widget(Image(source=card_img_src, size_hint_y=0.55))

                discard_img_src = ""
                if p_opponent.discard_pile:
                    discard_img_src = p_opponent.discard_pile[-1].image_path
                opponent_widget.add_widget(Image(source=discard_img_src, size_hint_y=0.3))
                self.opponents_grid.add_widget(opponent_widget)
                self.opponent_widgets_map[p_opponent.id] = opponent_widget  # Store reference

        # Human Player Hand UI
        human_player = self.players_session_list[self.human_player_id]
        self.player_hand_area.clear_widgets()
        if human_player.is_eliminated:
            self.player_hand_area.add_widget(Image(source=ELIMINATED_IMAGE, allow_stretch=True))
            self.player_hand_area.add_widget(Label(text="Eliminated!"))
        elif human_player.hand:
            is_player_turn_active_ui = (self.current_round_manager and
                                        self.current_round_manager.round_active and
                                        self.current_round_manager.current_player_idx == self.human_player_id and
                                        not self.waiting_for_input)  # Not waiting for popup response

            for card_obj in human_player.hand:
                card_button = ImageButton(source=card_obj.image_path,
                                          size_hint=(1 / len(human_player.hand) if len(human_player.hand) > 0 else 1,
                                                     1),
                                          allow_stretch=True, keep_ratio=True)
                card_button.card_name = card_obj.name  # Store name for on_press
                card_button.bind(on_press=self.on_player_card_selected)
                card_button.disabled = not is_player_turn_active_ui
                self.player_hand_area.add_widget(card_button)

        # Human Player Discard UI
        self.player_discard_display.source = human_player.discard_pile[
            -1].image_path if human_player.discard_pile else ""

        self.log_message("", permanent=False)  # Refresh log scroll

    def _get_player_widget_by_id(self, player_id):
        if player_id == self.human_player_id:
            return self.human_player_display_wrapper  # Use the new wrapper
        return self.opponent_widgets_map.get(player_id)

    def _update_anim_rect_pos_size(self, instance, value):
        # Callback to update rectangle size/pos if widget moves/resizes during animation (unlikely for simple highlights)
        if hasattr(instance, 'canvas_anim_bg_rect'):
            instance.canvas_anim_bg_rect.pos = instance.pos
            instance.canvas_anim_bg_rect.size = instance.size

    def ui_animate_effect(self, effect_details, duration=1.0, on_complete_callback=None):
        self.dismiss_active_popup()  # Close any choice popups before animation

        processed_animation = False
        anim_type = effect_details.get('type')

        if anim_type == 'highlight_player':
            player_ids = effect_details.get('player_ids', [])
            color_type = effect_details.get('color_type', 'target')
            actor_id = effect_details.get('actor_id')  # Player performing the action

            if color_type == 'target':
                highlight_color_rgba = (0.5, 0.8, 1, 0.6)  # Light blue
            elif color_type == 'elimination':
                highlight_color_rgba = (1, 0.2, 0.2, 0.7)  # Reddish
            elif color_type == 'protection':
                highlight_color_rgba = (0.2, 1, 0.2, 0.7)  # Greenish
            elif color_type == 'actor_action':
                highlight_color_rgba = (1, 0.8, 0.2, 0.6)  # Yellowish for actor
            else:
                highlight_color_rgba = (0.7, 0.7, 0.7, 0.5)  # Default grey

            widgets_to_animate_this_call = []

            # Animate actor first, if specified and different duration or distinct
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

                if widget_to_animate not in self.animated_widget_details:  # Only add canvas instructions once
                    with widget_to_animate.canvas.before:
                        # Store on the widget itself for easy access/modification
                        widget_to_animate.canvas_anim_bg_color = Color(*color_rgba)
                        widget_to_animate.canvas_anim_bg_rect = Rectangle(size=widget_to_animate.size,
                                                                          pos=widget_to_animate.pos)
                    widget_to_animate.bind(pos=self._update_anim_rect_pos_size, size=self._update_anim_rect_pos_size)
                    self.animated_widget_details[widget_to_animate] = {
                        'widget': widget_to_animate,
                        'instruction_color': widget_to_animate.canvas_anim_bg_color,
                        'instruction_rect': widget_to_animate.canvas_anim_bg_rect,
                        'original_bound_pos_size': True  # Flag that we bound it
                    }
                else:  # Instructions exist, just update color and ensure rect is visible/correct
                    widget_to_animate.canvas_anim_bg_color.rgba = color_rgba
                    widget_to_animate.canvas_anim_bg_rect.size = widget_to_animate.size
                    widget_to_animate.canvas_anim_bg_rect.pos = widget_to_animate.pos

        # Add other animation types here (e.g., 'card_reveal', 'card_swap_visual')
        # elif anim_type == 'show_message':
        #     msg = effect_details.get('message', "Effect!")
        #     # Create a temporary label, add to root, then remove. Simpler might be log message.
        #     self.log_message(f"ANIMATION HINT: {msg}") # Placeholder for more visual message
        #     processed_animation = True

        if processed_animation:
            # Important: Ensure this is scheduled only ONCE for a set of related animations if they share a common end
            Clock.schedule_once(lambda dt: self._clear_animations_and_proceed(on_complete_callback), duration)
        elif on_complete_callback:  # No animation to show, but need to continue
            on_complete_callback()

    def _clear_animations_and_proceed(self, on_complete_callback):
        widgets_to_unbind = []
        for widget, details in list(
                self.animated_widget_details.items()):  # Use list for safe iteration if modifying dict
            w = details['widget']
            if hasattr(w, 'canvas_anim_bg_color'):
                w.canvas_anim_bg_color.rgba = (0, 0, 0, 0)  # Make transparent (safer than removing)
                # If you want to fully remove and unbind:
                # w.canvas.before.remove(details['instruction_color'])
                # w.canvas.before.remove(details['instruction_rect'])
                # if details.get('original_bound_pos_size'):
                #     widgets_to_unbind.append(w) # Collect to unbind outside loop
                # delattr(w, 'canvas_anim_bg_color')
                # delattr(w, 'canvas_anim_bg_rect')

        # for w_unbind in widgets_to_unbind:
        #    w_unbind.unbind(pos=self._update_anim_rect_pos_size, size=self._update_anim_rect_pos_size)

        self.animated_widget_details.clear()  # Clear after processing all

        if on_complete_callback:
            on_complete_callback()

    def on_press_action_button(self, instance):
        if self.game_over_session_flag:
            self.prompt_player_count()  # This will re-init and start new session
        elif self.current_round_manager and not self.current_round_manager.round_active:  # Round ended
            self.start_new_round()  # Start next round of current session
        else:  # Forfeit (Debug)
            if self.current_round_manager and self.current_round_manager.round_active and \
                    self.current_round_manager.players[
                        self.current_round_manager.current_player_idx].id == self.human_player_id:
                self.log_message(f"{self.players_session_list[self.human_player_id].name} forfeits the round.")
                # This needs to interact with GameRound to eliminate and advance.
                # For simplicity, this debug feature might be tricky to re-implement perfectly now.
                # self.current_round_manager._eliminate_player(self.players_session_list[self.human_player_id])
                # self.current_round_manager._finish_effect_and_proceed() # This should handle it
                self.log_message("DEBUG: Forfeit currently complex to reimplement cleanly. Ignored.")
            else:
                self.log_message("Cannot forfeit now.")

    def start_new_game_session(self):
        self.log_message(f"--- Starting New Game Session with {self.num_players_session} players ---")
        for p in self.players_session_list: p.tokens = 0  # Reset tokens for new session
        self.game_over_session_flag = False
        self.start_new_round()

    def start_new_round(self):
        self.log_message("--- UI: Preparing New Round ---")
        if self.game_over_session_flag:  # Don't start new round if game is over
            self.log_message("Game is over. Cannot start new round until new game session.")
            self.update_ui_full()
            return

        game_deck = Deck(self.num_players_session, self.log_message)
        game_deck.burn_one_card(self.num_players_session)  # Burn card after shuffle

        min_cards_needed = self.num_players_session  # Each player gets one card initially
        if game_deck.count() < min_cards_needed:
            self.log_message(
                f"Error: Not enough cards in deck ({game_deck.count()}) for {self.num_players_session} players. Needs {min_cards_needed}.")
            self.game_over_session_flag = True  # Cannot proceed
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
            'check_game_over_token_callback': self.check_game_over_on_token_gain,  # For mid-round token gains
            'game_over_callback': self.handle_game_over_from_round,  # if round itself declares game over
            'animate_effect_callback': self.ui_animate_effect,  # Add this
            'award_round_tokens_callback': self.award_round_tokens_and_check_game_over,

        }

        self.current_round_manager = GameRound(
            self.players_session_list, game_deck, self.human_player_id,
            self.log_message, ui_callbacks
        )
        self.current_round_manager.start_round()  # This will call update_ui via callbacks

    def on_player_card_selected(self, instance):  # Instance is the ImageButton
        if not self.current_round_manager or not self.current_round_manager.round_active or \
                self.players_session_list[self.human_player_id].is_cpu or \
                self.current_round_manager.current_player_idx != self.human_player_id or \
                self.waiting_for_input:  # If already waiting for a popup response
            return

        # self.set_waiting_for_input_flag(False)  # No longer waiting for card click, will wait for effect popup if any
        card_name_to_play = instance.card_name
        self.current_round_manager.human_plays_card(card_name_to_play)
        # GameRound will handle Countess logic and then call _finish_effect_and_proceed which updates UI.

    def set_waiting_for_input_flag(self, is_waiting):
        self.waiting_for_input = is_waiting
        self.update_ui_full()  # Refresh UI to enable/disable card buttons

    def dismiss_active_popup(self):
        if self.active_popup:
            self.active_popup.dismiss()
            self.active_popup = None

    # --- UI Popup Display Methods (called by GameRound via callbacks) ---
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
        self.dismiss_active_popup()  # Close any existing
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
        options_layout.cols = 4  # Override for grid-like values

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

        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)  # No scroll needed for 2 buttons
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

    # --- Game Session Logic Callbacks (Called by GameRound) ---
    def award_round_tokens_and_check_game_over(self, list_of_winner_players):
        game_ended_this_round = False
        final_winner_of_game = None

        for winner_of_round in list_of_winner_players:
            if winner_of_round is None: continue  # Should not happen if list_of_winner_players is filtered

            self.log_message(f"{winner_of_round.name} gains a token of affection for winning the round!")
            winner_of_round.tokens += 1
            if self.check_game_over_on_token_gain(winner_of_round):  # Checks if this player won game
                game_ended_this_round = True
                final_winner_of_game = winner_of_round  # Prioritize first to reach token count

            # Jester check
            if self.current_round_manager._is_card_in_current_deck('Jester'):  # Check if Jester is in play
                for p_observer in self.players_session_list:
                    if p_observer.id != winner_of_round.id and p_observer.jester_on_player_id == winner_of_round.id:
                        self.log_message(f"{p_observer.name} also gains token (Jester on {winner_of_round.name})!")
                        p_observer.tokens += 1
                        if not game_ended_this_round and self.check_game_over_on_token_gain(p_observer):
                            game_ended_this_round = True  # Jester player might win game
                            final_winner_of_game = p_observer

        if game_ended_this_round and final_winner_of_game:
            self.handle_game_over_from_round(final_winner_of_game)

        self.update_ui_full()  # Update scores etc.

    def check_game_over_on_token_gain(self, player_who_gained_token):  # Returns True if game ended
        if self.game_over_session_flag: return True
        if player_who_gained_token.tokens >= self.tokens_to_win_session:
            # Game over is handled by the caller (award_round_tokens or GameRound directly for Bishop)
            return True
        return False

    def handle_game_over_from_round(self, winner_of_game):
        if self.game_over_session_flag: return  # Already handled
        self.log_message(f"--- GAME OVER! {winner_of_game.name} wins the game with {winner_of_game.tokens} tokens! ---")
        self.game_over_session_flag = True
        if self.current_round_manager: self.current_round_manager.round_active = False  # Ensure round is inactive
        self.update_ui_full()


class LoveLetterApp(App):
    def build(self):
        # Asset check from original main
        os.makedirs(CARD_FOLDER, exist_ok=True)
        # Dummy asset creation can be kept here if desired for standalone running
        # ... (dummy asset creation as in original __main__) ...
        return LoveLetterGame()


if __name__ == '__main__':
    # Create dummy assets if they don't exist, for testing purposes
    # This part is identical to your original __main__
    os.makedirs(CARD_FOLDER, exist_ok=True)
    if not os.path.exists(CARD_BACK_IMAGE):
        try:
            from PIL import Image as PILImage, ImageDraw  # Renamed to avoid class name conflict

            img = PILImage.new('RGB', (200, 300), color='blue')
            d = ImageDraw.Draw(img);
            d.text((10, 10), "CARD BACK", fill=(255, 255, 0))
            img.save(CARD_BACK_IMAGE);
            print(f"INFO: Created dummy {CARD_BACK_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create dummy card back: {e}")

    if not os.path.exists(ELIMINATED_IMAGE):
        try:
            from PIL import Image as PILImage, ImageDraw

            img = PILImage.new('RGB', (100, 150), color='darkred')
            d = ImageDraw.Draw(img);
            d.text((10, 10), "ELIM", fill=(255, 255, 255))
            img.save(ELIMINATED_IMAGE);
            print(f"INFO: Created dummy {ELIMINATED_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create dummy ELIMINATED_IMAGE: {e}")

    # Create dummy card images if not present
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
                img.save(expected_path_png)  # Prefer PNG for dummy
                print(f"INFO: Created dummy {expected_path_png} for {card_name_key}")
            except Exception as e:
                print(f"WARNING: Could not create dummy image for {card_name_key}: {e}")

    LoveLetterApp().run()