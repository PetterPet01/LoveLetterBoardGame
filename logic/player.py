# file: logic/player.py
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

    def force_discard(self, game_deck, burned_card_ref, draw_new=True):
        if not self.hand: return None
        discarded_card = self.hand.pop(0)
        self.discard_pile.append(discarded_card)
        if not draw_new:
            return discarded_card

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

