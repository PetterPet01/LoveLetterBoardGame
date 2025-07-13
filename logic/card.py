# file: logic/card.py
class Card:
    def __init__(self, name, value, description, image_path, vietnamese_name, count_classic, count_large, effect_handler, needs_target):
        self.name = name
        self.value = value
        self.description = description
        self.image_path = image_path
        self.vietnamese_name = vietnamese_name
        self.count_classic = count_classic
        self.count_large = count_large
        self.effect = effect_handler
        self.needs_target = needs_target

    def __repr__(self):
        return f"Card({self.name}, V:{self.value})"

    def to_dict(self):
        return {
            'name': self.name, 'value': self.value, 'image_path': self.image_path,
            'description': self.description, 'vietnamese_name': self.vietnamese_name
        }


