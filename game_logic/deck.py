import random
from card import CARD_PROTOTYPES

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
