import os
import random
from kivy.clock import Clock  # Clock is needed for CPU turn delays, a minor dependency.

# --- Constants and Raw Data ---

CARD_FOLDER = "assets/cards"
CARD_BACK_IMAGE = "assets/cards/back.png"
ELIMINATED_IMAGE = "assets/cards/back.png"

CARDS_DATA_RAW = {
    'Guard': {'value': 1, 'vietnamese_name': 'canve',
              'description': "Đoán lá bài của người chơi khác (không phải Cận vệ). Nếu đúng, người đó bị loại.",
              'count_classic': 5, 'count_large': 8},
    'Priest': {'value': 2, 'vietnamese_name': 'mucsu',
               'description': "Nhìn bài trên tay một người chơi khác.",
               'count_classic': 2, 'count_large': 0},
    'Baron': {'value': 3, 'vietnamese_name': 'namtuoc',
              'description': "So bài; người có bài giá trị thấp hơn sẽ bị loại.",
              'count_classic': 2, 'count_large': 0},
    'Handmaid': {'value': 4, 'vietnamese_name': 'cohau',
                 'description': "Miễn nhiễm với hiệu ứng của các lá bài khác cho đến lượt tiếp theo của bạn.",
                 'count_classic': 2, 'count_large': 0},
    'Prince': {'value': 5, 'vietnamese_name': 'hoangtu',
               'description': "Chọn một người chơi (có thể là bạn) để bỏ bài trên tay và rút một lá mới.",
               'count_classic': 2, 'count_large': 0},
    'King': {'value': 6, 'vietnamese_name': 'nhavua',
             'description': "Tráo đổi bài trên tay với một người chơi khác.",
             'count_classic': 1, 'count_large': 0},
    'Countess': {'value': 7, 'vietnamese_name': 'nubatuoc',
                 'description': "Phải bỏ lá này nếu trên tay bạn có Vua hoặc Hoàng tử.",
                 'count_classic': 1, 'count_large': 0},
    'Princess': {'value': 8, 'vietnamese_name': 'congchua',
                 'description': "Bạn sẽ bị loại nếu bỏ lá bài này.",
                 'count_classic': 1, 'count_large': 0},
    'Assassin': {'value': 0, 'vietnamese_name': 'satthu',
                 'description': "Nếu bị Cận vệ nhắm đến, người chơi Cận vệ sẽ bị loại. Bỏ lá này và rút lá mới.",
                 'count_classic': 0, 'count_large': 1},
    'Jester': {'value': 0, 'vietnamese_name': 'tenhe',
               'description': "Chọn một người chơi. Nếu họ thắng vòng này, bạn cũng nhận được một tín vật.",
               'count_classic': 0, 'count_large': 1},
    'Cardinal': {'value': 2, 'vietnamese_name': 'hongy',
                 'description': "Hai người chơi đổi bài cho nhau. Bạn được nhìn một trong hai lá bài đó.",
                 'count_classic': 0, 'count_large': 2},
    'Baroness': {'value': 3, 'vietnamese_name': 'nunamtuoc',
                 'description': "Nhìn bài trên tay của 1 hoặc 2 người chơi khác.",
                 'count_classic': 0, 'count_large': 2},
    'Sycophant': {'value': 4, 'vietnamese_name': 'keninhbo',
                  'description': "Người bị chọn phải tự chọn mình làm mục tiêu cho lá bài hiệu ứng tiếp theo.",
                  'count_classic': 0, 'count_large': 2},
    'Count': {'value': 5, 'vietnamese_name': 'batuoc',
              'description': "+1 vào giá trị bài trên tay nếu lá này nằm trong chồng bài bỏ của bạn.",
              'count_classic': 0, 'count_large': 2},
    'Sheriff': {'value': 6, 'vietnamese_name': 'nguyensoai',
                'description': "Nếu bạn bị loại khi có lá này trong chồng bài bỏ, bạn nhận được một tín vật.",
                'count_classic': 0, 'count_large': 1},
    'Queen Mother': {'value': 7, 'vietnamese_name': 'nuhoang',
                     'description': "So bài; người có bài giá trị cao hơn sẽ bị loại.",
                     'count_classic': 0, 'count_large': 1},
    'Bishop': {'value': 9, 'vietnamese_name': 'giammuc',
               'description': "Đoán giá trị lá bài (không phải Cận vệ). Nhận một tín vật nếu đúng. Người bị đoán có thể rút lại bài.",
               'count_classic': 0, 'count_large': 1},
}

CARD_PROTOTYPES = {}  # Will be populated by Card objects from the UI side


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
                                                'Sheriff']

    def __repr__(self):
        return f"Card({self.name}, V:{self.value})"

    def to_dict(self):
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
            f"Chồng bài: Sử dụng bộ bài cho {'2-4 người chơi (cơ bản)' if composition_key == 'count_classic' else '5-8 người chơi (lớn)'}.")

        for card_name, prototype in CARD_PROTOTYPES.items():
            count = getattr(prototype, composition_key, 0)
            for _ in range(count):
                self.cards.append(prototype)

        if not self.cards:
            self.log_callback(
                "LỖI: Không có lá bài nào được định nghĩa cho số người chơi này! Kiểm tra số lượng trong CARD_PROTOTYPES.")
            if composition_key == 'count_large' and any(
                    proto.count_classic > 0 for proto in CARD_PROTOTYPES.values()):
                self.log_callback("Chồng bài: Quay lại dùng bộ cơ bản vì bộ lớn chưa được định nghĩa.")
                composition_key = 'count_classic'
                for card_name, prototype in CARD_PROTOTYPES.items():
                    count = getattr(prototype, composition_key, 0)
                    for _ in range(count): self.cards.append(prototype)

        self.log_callback(f"Chồng bài: Đã tạo với {len(self.cards)} lá.")

    def shuffle(self):
        random.shuffle(self.cards)
        self.log_callback("Chồng bài: Đã xáo bài.")

    def draw(self):
        return self.cards.pop(0) if self.cards else None

    def burn_one_card(self, num_players):
        if num_players > 1 and self.cards:
            self.burned_card = self.draw()
            if self.burned_card:
                self.log_callback(
                    f"Chồng bài: Đã đốt một lá ({self.burned_card.name}). Còn lại {len(self.cards)} lá.")
            else:
                self.log_callback("Chồng bài: Thử đốt bài nhưng chồng bài đã hết.")
        elif num_players == 2:
            if self.cards:
                self.burned_card = self.draw()
                if self.burned_card:
                    self.log_callback(
                        f"Chồng bài (2P): Đã đốt một lá ({self.burned_card.name}). Còn lại {len(self.cards)} lá.")

    def is_empty(self):
        return not self.cards

    def count(self):
        return len(self.cards)


class Player:
    def __init__(self, id_num, name, is_cpu=False):
        self.id = id_num
        self.name = name
        self.hand = []
        self.discard_pile = []
        self.tokens = 0
        self.is_eliminated = False
        self.is_protected = False
        self.is_cpu = is_cpu
        self.sycophant_target_self = False
        self.jester_on_player_id = None
        self.effective_value_end_round = 0
        self.discard_sum_end_round = 0

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
        card_to_play = next((c for c in self.hand if c.name == card_name_to_play), None)
        if card_to_play:
            self.hand.remove(card_to_play)
            self.discard_pile.append(card_to_play)
            return card_to_play
        return None

    def force_discard(self, game_deck, burned_card_ref):
        if not self.hand: return None
        discarded_card = self.hand.pop(0)
        self.discard_pile.append(discarded_card)
        new_card = None
        if not game_deck.is_empty():
            new_card = game_deck.draw()
        elif burned_card_ref['card']:
            new_card = burned_card_ref['card']
            burned_card_ref['card'] = None
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
        self.ui['update_ui_full_callback']()
        self._process_current_player_turn_start()

    def cancel_played_card_action(self, acting_player):
        self.log_message(f"{acting_player.name} quyết định lấy lại lá bài của mình.")

        if not acting_player.discard_pile:
            self.log_message(f"LỖI: Không thể hủy hành động, không có bài trong chồng bài bỏ của {acting_player.name}.")
            if self.ui.get('dismiss_active_popup_callback'): self.ui['dismiss_active_popup_callback']()
            if self.ui.get('set_waiting_flag_callback'): self.ui['set_waiting_flag_callback'](False)
            if self.ui.get('update_ui_full_callback'): self.ui['update_ui_full_callback']()
            return

        card_to_return = acting_player.discard_pile.pop()
        acting_player.add_card_to_hand(card_to_return)

        if self.ui.get('dismiss_active_popup_callback'): self.ui['dismiss_active_popup_callback']()
        if self.ui.get('set_waiting_flag_callback'): self.ui['set_waiting_flag_callback'](False)
        if self.ui.get('update_ui_full_callback'): self.ui['update_ui_full_callback']()

    def _execute_cpu_turn_after_delay(self, cpu_player):
        if not self.round_active:
            return
        if self.players[self.current_player_idx] != cpu_player:
            return
        self.log_message(f"Máy ({cpu_player.name}) quyết định chơi.")
        self._cpu_play_turn(cpu_player)

    def _process_current_player_turn_start(self):
        if not self.round_active: return

        current_player = self.players[self.current_player_idx]
        if current_player.is_eliminated:
            self._advance_to_next_turn()
            return

        current_player.is_protected = False

        if not self.deck.is_empty():
            drawn_card = self.deck.draw()
            current_player.add_card_to_hand(drawn_card)
            if not current_player.is_cpu:
                self.log_message(
                    f"Bạn ({current_player.name}) đã rút được {drawn_card.name}. Bài trên tay: {current_player.get_hand_card_names()}.")
            else:
                self.log_message(
                    f"{current_player.name} đã rút một lá bài. Số bài trên tay: {len(current_player.hand)}.")
            self.ui['update_ui_full_callback']()
        else:
            self.log_message("Chồng bài đã hết. Vòng đấu kết thúc.")
            self._end_round_deck_empty()
            return

        if current_player.is_cpu:
            self.log_message(f"Máy ({current_player.name}) đang suy nghĩ...")
            delay_duration = 4
            Clock.schedule_once(lambda dt: self._execute_cpu_turn_after_delay(current_player), delay_duration)
        else:
            self.log_message(f"Đến lượt bạn, {current_player.name}. Hãy chọn một lá bài để chơi.")
            self.ui['set_waiting_flag_callback'](False)
            hand_names = current_player.get_hand_card_names()
            if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and \
                    ((self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                     (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)):
                self.log_message("LƯU Ý: Bạn có Nữ Bá tước và Vua/Hoàng tử. Bạn PHẢI chơi Nữ Bá tước.")

    def human_plays_card(self, card_name_played):
        player = self.players[self.current_player_idx]
        if player.is_cpu or not self.round_active: return

        actual_card_to_play_name = card_name_played
        hand_names = player.get_hand_card_names()
        has_king_or_prince = (self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                             (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)
        if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and has_king_or_prince:
            if card_name_played != 'Countess':
                self.log_message("Luật Nữ Bá tước: Tự động chơi Nữ Bá tước vì có Vua/Hoàng tử trên tay.")
                actual_card_to_play_name = 'Countess'
        card_object_played = player.play_card(actual_card_to_play_name)
        if card_object_played:
            self._handle_card_played_logic(player, card_object_played)
        else:
            self.log_message(
                f"LỖI: {player.name} đã thử chơi {actual_card_to_play_name} nhưng thất bại (không có trên tay hoặc lỗi khác).")
            self.ui['set_waiting_flag_callback'](False)
            if self.round_active: self._advance_to_next_turn()

    def _cpu_play_turn(self, cpu_player):
        self.log_message(f"Lượt của Máy ({cpu_player.name}).")
        hand_names = cpu_player.get_hand_card_names()

        has_king_or_prince = (self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                             (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)
        if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and has_king_or_prince:
            self.log_message(f"Máy ({cpu_player.name}) có Nữ Bá tước và Vua/Hoàng tử, phải chơi Nữ Bá tước.")
            card_object_played = cpu_player.play_card('Countess')
            self._handle_card_played_logic(cpu_player, card_object_played)
            return

        playable_cards = list(cpu_player.hand)
        if self._is_card_in_current_deck('Princess') and len(playable_cards) > 1:
            playable_cards = [c for c in playable_cards if c.name != 'Princess']
            if not playable_cards:
                playable_cards = list(cpu_player.hand)

        chosen_card_object = random.choice(playable_cards) if playable_cards else random.choice(cpu_player.hand)
        card_object_played = cpu_player.play_card(chosen_card_object.name)
        self._handle_card_played_logic(cpu_player, card_object_played)

    def _handle_card_played_logic(self, player, card_object_played):
        self.log_message(f"{player.name} chơi lá {card_object_played.name}.")
        self.ui['update_ui_full_callback']()
        if self._is_card_in_current_deck('Princess') and card_object_played.name == 'Princess':
            self.log_message(f"{player.name} đã bỏ Công chúa và bị loại!")
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
            if not p.hand and not allow_no_hand and p != acting_player:
                continue
            targets.append(p)
        return targets

    def _execute_card_effect(self, player, card):
        card_name = card.name
        if not self._is_card_in_current_deck(card_name):
            self.log_message(f"{card_name} không có trong bộ bài hiện tại. Hiệu ứng không xảy ra.")
            return False
        must_target_self = player.sycophant_target_self
        player.sycophant_target_self = False
        effect_method_name = f"_effect_{card_name.lower().replace(' ', '_')}"
        effect_method = getattr(self, effect_method_name, None)
        if effect_method:
            if card_name in ['Handmaid', 'Countess', 'Assassin', 'Count', 'Sheriff']:
                return effect_method(player, card)
            else:
                return effect_method(player, card, must_target_self)
        else:
            self.log_message(f"Hiệu ứng cho {card_name} chưa được cài đặt hoặc là bị động/tự động.");
            return False

    def _finish_effect_and_proceed(self):
        self.ui['set_waiting_flag_callback'](False)
        if self.ui['get_active_popup_callback']():
            self.ui['dismiss_active_popup_callback']()
        if self.game_over_pending_from_round:
            self.round_active = False
            self.ui['game_over_callback'](self.game_over_winner)
            return
        round_ended_by_elimination = self._check_round_end_by_elimination()
        if not round_ended_by_elimination and self.round_active:
            self._advance_to_next_turn()
        self.ui['update_ui_full_callback']()

    def _eliminate_player(self, player_to_eliminate):
        if player_to_eliminate.is_eliminated: return
        player_to_eliminate.is_eliminated = True
        self.log_message(f"{player_to_eliminate.name} đã bị loại!")
        if self._is_card_in_current_deck('Sheriff') and player_to_eliminate.has_discarded('Sheriff'):
            self.log_message(f"{player_to_eliminate.name} có Nguyên soái trong bài bỏ và nhận được một tín vật!")
            player_to_eliminate.tokens += 1
            if self.ui['check_game_over_token_callback'](player_to_eliminate):
                self.game_over_pending_from_round = True
                self.game_over_winner = player_to_eliminate

    def _advance_to_next_turn(self):
        if not self.round_active: return
        attempts = 0
        while attempts < len(self.players) * 2:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            if not self.players[self.current_player_idx].is_eliminated:
                break
            attempts += 1
        active_players_count = sum(1 for p in self.players if not p.is_eliminated)
        if active_players_count <= 1 and self.round_active:
            self._end_round_by_elimination()
            return
        next_player = self.players[self.current_player_idx]
        if not next_player.is_cpu:
            self.log_message(f"--- Đến lượt bạn ({next_player.name}) ---")
        else:
            self.log_message(f"--- Lượt của {next_player.name} ---")
        self._process_current_player_turn_start()

    def _check_round_end_by_elimination(self):
        if not self.round_active: return True
        active_players = [p for p in self.players if not p.is_eliminated]
        if len(active_players) <= 1:
            self._end_round_by_elimination(active_players)
            return True
        return False

    def _end_round_by_elimination(self, active_players_list=None):
        if not self.round_active: return
        self.log_message("Vòng đấu kết thúc: chỉ còn một hoặc không người chơi.")
        self.round_active = False
        if active_players_list is None:
            active_players_list = [p for p in self.players if not p.is_eliminated]
        winner = active_players_list[0] if len(active_players_list) == 1 else None
        if winner:
            self.log_message(f"{winner.name} là người cuối cùng còn lại và chiến thắng vòng này!")
        else:
            self.log_message("Tất cả người chơi đã bị loại cùng lúc! Không có ai thắng vòng này.")
        self.ui['award_round_tokens_callback']([winner] if winner else [])

    def _end_round_deck_empty(self):
        if not self.round_active: return
        self.log_message("Vòng đấu kết thúc: chồng bài đã hết. So bài của những người chơi còn lại.")
        self.round_active = False
        active_players_with_hands = [p for p in self.players if not p.is_eliminated and p.hand]
        if not active_players_with_hands:
            self.log_message("Không có người chơi nào còn bài. Không có người thắng vòng này.");
            self.ui['award_round_tokens_callback']([])
            return
        is_count_in_deck = self._is_card_in_current_deck('Count')
        for p_obj in active_players_with_hands:
            p_obj.effective_value_end_round = p_obj.hand[0].value
            if is_count_in_deck and p_obj.has_discarded('Count'):
                p_obj.effective_value_end_round += 1
                self.log_message(
                    f"{p_obj.name} có Bá tước trong bài bỏ. Bài: {p_obj.hand[0].name}, Giá trị hiệu dụng: {p_obj.effective_value_end_round}")
        active_players_with_hands.sort(key=lambda p: p.effective_value_end_round, reverse=True)
        highest_val = active_players_with_hands[0].effective_value_end_round
        winners_by_val = [p for p in active_players_with_hands if p.effective_value_end_round == highest_val]
        final_winners = []
        if len(winners_by_val) == 1:
            final_winners = winners_by_val
            self.log_message(
                f"{final_winners[0].name} có lá bài cao nhất ({final_winners[0].hand[0].name}, giá trị hiệu dụng {final_winners[0].effective_value_end_round}) và chiến thắng!")
        else:
            self.log_message(f"Hòa điểm ở giá trị {highest_val}. So tổng điểm các lá bài đã bỏ.")
            for p_obj in winners_by_val:
                p_obj.discard_sum_end_round = sum(c.value for c in p_obj.discard_pile)
                self.log_message(
                    f"{p_obj.name} (Bài: {p_obj.hand[0].name}, Điểm: {p_obj.effective_value_end_round}) tổng điểm bài bỏ: {p_obj.discard_sum_end_round}")
            winners_by_val.sort(key=lambda p: p.discard_sum_end_round, reverse=True)
            highest_discard_sum = winners_by_val[0].discard_sum_end_round
            final_winners = [p for p in winners_by_val if p.discard_sum_end_round == highest_discard_sum]
            if len(final_winners) == 1:
                self.log_message(
                    f"{final_winners[0].name} thắng nhờ tổng điểm bài bỏ cao hơn ({highest_discard_sum})!")
            else:
                self.log_message(
                    f"Vẫn hòa! {[p.name for p in final_winners]} cùng thắng vòng này.")
        self.ui['award_round_tokens_callback'](final_winners)

    def _effect_guard(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Kẻ nịnh bợ: {player.name} phải tự chọn mình, nhưng Cận vệ không thể. Hiệu ứng mất.")
            return False
        if not valid_targets: self.log_message("Cận vệ: Không có mục tiêu hợp lệ."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            possible_values = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                              if proto.value != 1 and self._is_card_in_current_deck(name))))
            if not possible_values: self.log_message("Cận vệ (Máy): Không có giá trị hợp lệ để đoán!"); return False
            guess_val = random.choice(possible_values)
            self.log_message(f"Máy ({player.name}) chơi Cận vệ lên {target_player.name}, đoán giá trị {guess_val}.")
            self._resolve_guard_guess(player, target_player, guess_val)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_guard_target_selected,
                self.cancel_played_card_action
            )
            return True

    def _resolve_guard_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        possible_values_to_guess = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                                   if proto.value != 1 and self._is_card_in_current_deck(name))))
        if not possible_values_to_guess:
            self.log_message(f"Cận vệ: Không có giá trị hợp lệ để đoán {target_player.name}! Hiệu ứng mất.");
            self._finish_effect_and_proceed()
            return

        self.ui['request_guard_value_popup_callback'](
            acting_player, target_player, possible_values_to_guess,
            self._resolve_guard_value_guessed,
            self.cancel_played_card_action
        )

    def _resolve_guard_value_guessed(self, acting_player, target_player, guessed_value):
        self.log_message(f"{acting_player.name} (Cận vệ) đoán giá trị {guessed_value} cho {target_player.name}.")
        self._resolve_guard_guess(acting_player, target_player, guessed_value)
        self._finish_effect_and_proceed()

    def _resolve_guard_guess(self, acting_player, target_player, guessed_value):
        if not target_player.hand: return

        target_card = target_player.hand[0]
        title = f"{acting_player.name} chơi Cận vệ lên {target_player.name}"

        if self._is_card_in_current_deck('Assassin') and target_card.name == 'Assassin':
            self.log_message(f"{target_player.name} lộ ra Sát thủ! {acting_player.name} bị loại!")
            self._eliminate_player(acting_player)

            target_player.play_card('Assassin')
            if not self.deck.is_empty():
                new_card = self.deck.draw()
                if new_card: target_player.add_card_to_hand(new_card)
            elif self.shared_burned_card_ref['card']:
                new_card = self.shared_burned_card_ref['card']
                target_player.add_card_to_hand(new_card)
                self.shared_burned_card_ref['card'] = None
            self.log_message(f"{target_player.name} bỏ Sát thủ và rút một lá bài mới.")
            return

        if target_card.value == guessed_value:
            details = f"Đoán đúng! {target_player.name} có {target_card.name}. Đã bị loại."
            self.log_message(details)
            if 'show_turn_notification_callback' in self.ui:
                self.ui['show_turn_notification_callback'](title, details)
            self._eliminate_player(target_player)
        else:
            details = f"Đoán sai. {target_player.name} không có lá bài giá trị {guessed_value}."
            self.log_message(details)
            if 'show_turn_notification_callback' in self.ui:
                self.ui['show_turn_notification_callback'](title, details)

    def _effect_priest(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Kẻ nịnh bợ: {player.name} phải tự chọn mình, nhưng Mục sư không thể. Hiệu ứng mất.")
            return False
        if not valid_targets: self.log_message("Mục sư: Không có mục tiêu hợp lệ."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_priest_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_priest_target_selected,
                self.cancel_played_card_action
            )
            return True

    def _resolve_priest_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_priest_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_priest_effect(self, acting_player, target_player):
        if not target_player.hand:
            self.log_message(f"{target_player.name} không có bài để xem (Mục sư).")
            return

        target_card_name = target_player.hand[0].name
        title = f"{acting_player.name} chơi Mục sư"
        details = ""
        if not acting_player.is_cpu:
            details = f"Bạn nhìn vào tay của {target_player.name} và thấy lá {target_card_name}."
        else:
            details = f"{acting_player.name} nhìn vào tay của {target_player.name}."
        self.log_message(details)
        if 'show_turn_notification_callback' in self.ui:
            self.ui['show_turn_notification_callback'](title, details)

    def _effect_baron(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Kẻ nịnh bợ: {player.name} phải tự chọn mình, nhưng Nam tước không thể. Hiệu ứng mất.")
            return False
        if not valid_targets: self.log_message("Nam tước: Không có mục tiêu hợp lệ."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_baron_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_baron_target_selected,
                self.cancel_played_card_action
            )
            return True

    def _resolve_baron_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_baron_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_baron_effect(self, player, target_player):
        if not player.hand or not target_player.hand:
            self.log_message("So bài Nam tước cần cả hai người chơi đều có bài. Hiệu ứng mất.")
            return

        player_card = player.hand[0]
        opponent_card = target_player.hand[0]
        title = f"{player.name} chơi Nam tước với {target_player.name}"
        details = f"Họ so bài: {player.name} có {player_card.name} ({player_card.value}) vs {target_player.name} có {opponent_card.name} ({opponent_card.value}). "

        if player_card.value > opponent_card.value:
            details += f"{target_player.name} bị loại."
            self._eliminate_player(target_player)
        elif opponent_card.value > player_card.value:
            details += f"{player.name} bị loại."
            self._eliminate_player(player)
        else:
            details += "Hòa! Không ai bị loại."

        self.log_message(details)
        if 'show_turn_notification_callback' in self.ui:
            self.ui['show_turn_notification_callback'](title, details)

    # Add these two new methods to your GameRound class

    def _resolve_handmaid_and_proceed(self, player):
        """Helper to resolve the effect AND then proceed for a human player."""
        self._resolve_handmaid_effect(player)
        self._finish_effect_and_proceed()

    def _resolve_countess_and_proceed(self, player):
        """Helper to resolve the effect AND then proceed for a human player."""
        self._resolve_countess_effect(player)
        self._finish_effect_and_proceed()

    def _effect_handmaid(self, player, card_played):
        # For a human, we need input. For a CPU, we don't.
        if player.is_cpu:
            self._resolve_handmaid_effect(player)
            return False  # Correctly signals to the main loop that no more input is needed.
        else:
            # For a human, we need to wait for a popup confirmation.
            self.ui['request_confirmation_popup_callback'](player,
                                                           card_played,
                                                           self._resolve_handmaid_and_proceed,
                                                           self.cancel_played_card_action
            )
            return True  # Correctly signals to the main loop to WAIT.

    def _resolve_handmaid_effect(self, player):
        player.is_protected = True
        title = f"{player.name} chơi Cô hầu"
        details = "Họ được an toàn khỏi các hiệu ứng cho đến lượt tiếp theo."
        self.log_message(f"{player.name} chơi Cô hầu và được bảo vệ.")
        if 'show_turn_notification_callback' in self.ui:
            self.ui['show_turn_notification_callback'](title, details)
        # self._finish_effect_and_proceed()

    def _effect_prince(self, player, card_played, must_target_self):
        valid_targets = []
        if must_target_self:
            if not player.is_eliminated: valid_targets = [player]
            if not valid_targets: self.log_message(
                f"Hoàng tử (Kẻ nịnh bợ): {player.name} phải tự chọn mình nhưng không hợp lệ. Hiệu ứng mất."); return False
        else:
            valid_targets = self._get_valid_targets(player, include_self=True,
                                                    targeted_effect_requires_unprotected=True, allow_no_hand=True)
        if not valid_targets: self.log_message("Hoàng tử: Không có mục tiêu hợp lệ."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self.log_message(f"Máy ({player.name}) chơi Hoàng tử, chọn {target_player.name}.")
            self._resolve_prince_effect(target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_prince_target_selected,
                self.cancel_played_card_action
            )
            return True

    def _resolve_prince_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self.log_message(f"{acting_player.name} (Hoàng tử) chọn {target_player.name} để bỏ bài và rút.")
        self._resolve_prince_effect(target_player)
        self._finish_effect_and_proceed()

    def _resolve_prince_effect(self, target_player):
        if not target_player.hand and not self.shared_burned_card_ref[
            'card'] and self.deck.is_empty():
            self.log_message(f"{target_player.name} không có bài và không có lá nào để rút (Hoàng tử).")
            return

        discarded_card = None
        if target_player.hand:
            original_hand_card = target_player.hand[0]
            discarded_card = target_player.force_discard(self.deck, self.shared_burned_card_ref)
            details = f"{target_player.name} bị buộc phải bỏ lá {discarded_card.name} và rút một lá mới."
            self.log_message(details)
            if 'show_turn_notification_callback' in self.ui:
                self.ui['show_turn_notification_callback']("Hiệu ứng Hoàng tử", details)

            if self._is_card_in_current_deck('Princess') and discarded_card.name == 'Princess':
                self.log_message(f"{target_player.name} đã bỏ Công chúa (bị ép bởi Hoàng tử) và bị loại!")
                self._eliminate_player(target_player)
                return
        else:
            if not self.deck.is_empty():
                new_card = self.deck.draw()
                target_player.add_card_to_hand(new_card)
            elif self.shared_burned_card_ref['card']:
                new_card = self.shared_burned_card_ref['card']
                target_player.add_card_to_hand(new_card)
                self.shared_burned_card_ref['card'] = None
            else:
                self.log_message(f"{target_player.name} không có bài để rút (chồng bài và bài đốt đã hết).")

        if target_player.hand:
            if not target_player.is_cpu:
                self.log_message(f"Bạn ({target_player.name}) rút được {target_player.hand[0].name}.")
            else:
                self.log_message(f"{target_player.name} rút một lá mới.")
        elif not target_player.is_eliminated:
            self.log_message(f"{target_player.name} không có bài sau hiệu ứng Hoàng tử (chồng bài và bài đốt đã hết).")

    def _effect_king(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Kẻ nịnh bợ: {player.name} phải tự chọn mình, nhưng Vua không thể. Hiệu ứng mất.")
            return False
        if not valid_targets: self.log_message("Vua: Không có mục tiêu hợp lệ."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_king_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_king_target_selected,
                self.cancel_played_card_action
            )
            return True

    def _resolve_king_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_king_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_king_effect(self, player, target_player):
        if not player.hand or not target_player.hand:
            self.log_message("Tráo bài Vua cần cả hai người chơi đều có bài. Hiệu ứng mất.");
            return

        player_card_obj = player.hand.pop(0)
        opponent_card_obj = target_player.hand.pop(0)

        player.add_card_to_hand(opponent_card_obj)
        target_player.add_card_to_hand(player_card_obj)

        title = f"{player.name} chơi Vua"
        details = f"Họ tráo đổi bài với {target_player.name}. \n{player.name} nhận được lá {opponent_card_obj.name}."
        self.log_message(f"{player.name} (Vua) tráo bài với {target_player.name}. "
                         f"{player.name} nhận {opponent_card_obj.name}, {target_player.name} nhận {player_card_obj.name}.")
        if 'show_turn_notification_callback' in self.ui:
            self.ui['show_turn_notification_callback'](title, details)

    def _effect_countess(self, player, card_played):
        if player.is_cpu:
            self._resolve_countess_effect(player)
            return False
        else:
            self.ui['request_confirmation_popup_callback'](
                player, card_played, self._resolve_countess_and_proceed, self.cancel_played_card_action
            )
            return True

    def _resolve_countess_effect(self, player):
        title = f"{player.name} chơi Nữ Bá tước"
        details = "Một cử chỉ quý phái, nhưng không có hiệu ứng trực tiếp lên người khác."
        self.log_message("Nữ Bá tước được chơi. Không có hiệu ứng đặc biệt.")
        if 'show_turn_notification_callback' in self.ui:
            self.ui['show_turn_notification_callback'](title, details)
        # self._finish_effect_and_proceed()

    def _effect_princess(self, player, card_played):
        self.log_message(f"LỖI: Hiệu ứng Công chúa đã được thực thi, đáng lẽ phải bị chặn sớm hơn.");
        return False