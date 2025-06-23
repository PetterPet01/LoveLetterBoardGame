# game_logic/card.py
import os
from constants import CARDS_DATA_RAW, CARD_FOLDER, CARD_BACK_IMAGE

CARD_PROTOTYPES = {}

class Card:
    def __init__(self, name, value, description, image_path, vietnamese_name, count_classic, count_large):
        self.name = name
        self.value = value
        self.description = description
        self.image_path = image_path
        self.vietnamese_name = vietnamese_name
        self.count_classic = count_classic
        self.count_large = count_large
        self.is_targeting_effect = name not in ['Handmaid', 'Countess', 'Princess']

    def __repr__(self):
        return f"Card({self.name}, V:{self.value})"


def load_card_prototypes():
    """Populates the CARD_PROTOTYPES dictionary. Should be called once at startup."""
    if CARD_PROTOTYPES:
        return  # Already loaded

    print("Loading card prototypes...")
    for eng_name, data in CARDS_DATA_RAW.items():
        viet_name = data['vietnamese_name']
        path_jpg = os.path.join(CARD_FOLDER, f"{viet_name}.jpg")
        path_png = os.path.join(CARD_FOLDER, f"{viet_name}.png")
        actual_path = next((p for p in [path_jpg, path_png] if os.path.exists(p)), None)

        if not actual_path:
            print(f"Warning: Image for '{eng_name}' ({viet_name}) not found. Using card back.")
            actual_path = CARD_BACK_IMAGE if os.path.exists(CARD_BACK_IMAGE) else ""

        CARD_PROTOTYPES[eng_name] = Card(
            name=eng_name,
            value=data['value'],
            description=data['description'],
            image_path=actual_path,
            vietnamese_name=viet_name,
            count_classic=data['count_classic'],
            count_large=data['count_large']
        )
    print(f"Card prototypes loaded: {len(CARD_PROTOTYPES)} card types")