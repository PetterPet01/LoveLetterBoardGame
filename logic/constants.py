# file: logic/constants.py
import os
import sys
from .card import Card

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# This import is now safe because we are not cross-importing game_round
# from . import card_effects  <- This line is removed from here

CARD_FOLDER = resource_path("assets/cards")
CARD_BACK_IMAGE = resource_path("assets/cards/back.png")
ELIMINATED_IMAGE = resource_path("assets/cards/back.png")

CARDS_DATA_RAW = {
    # Card Name: { data }
    'Guard': {'value': 1, 'vietnamese_name': 'canve', 'effect_name': 'effect_guard', 'needs_target': True,
              'description': "Đoán lá bài của người chơi khác (không phải Cận vệ). Nếu đúng, người đó bị loại.",
              'count_classic': 5, 'count_large': 8},
    'Priest': {'value': 2, 'vietnamese_name': 'mucsu', 'effect_name': 'effect_priest', 'needs_target': True,
               'description': "Nhìn bài trên tay một người chơi khác.",
               'count_classic': 2, 'count_large': 0},
    'Baron': {'value': 3, 'vietnamese_name': 'namtuoc', 'effect_name': 'effect_baron', 'needs_target': True,
              'description': "So bài; người có bài giá trị thấp hơn sẽ bị loại.",
              'count_classic': 2, 'count_large': 0},
    'Handmaid': {'value': 4, 'vietnamese_name': 'cohau', 'effect_name': 'effect_handmaid', 'needs_target': False,
                 'description': "Miễn nhiễm với hiệu ứng của các lá bài khác cho đến lượt tiếp theo của bạn.",
                 'count_classic': 2, 'count_large': 0},
    'Prince': {'value': 5, 'vietnamese_name': 'hoangtu', 'effect_name': 'effect_prince', 'needs_target': True,
               'description': "Chọn một người chơi (có thể là bạn) để bỏ bài trên tay và rút một lá mới.",
               'count_classic': 2, 'count_large': 0},
    'King': {'value': 6, 'vietnamese_name': 'nhavua', 'effect_name': 'effect_king', 'needs_target': True,
             'description': "Tráo đổi bài trên tay với một người chơi khác.",
             'count_classic': 1, 'count_large': 0},
    'Countess': {'value': 7, 'vietnamese_name': 'nubatuoc', 'effect_name': 'effect_countess', 'needs_target': False,
                 'description': "Phải bỏ lá này nếu trên tay bạn có Vua hoặc Hoàng tử.",
                 'count_classic': 1, 'count_large': 0},
    'Princess': {'value': 8, 'vietnamese_name': 'congchua', 'effect_name': 'effect_princess', 'needs_target': False,
                 'description': "Bạn sẽ bị loại nếu bỏ lá bài này.",
                 'count_classic': 1, 'count_large': 0},
    'Assassin': {'value': 0, 'vietnamese_name': 'satthu', 'effect_name': 'effect_assassin', 'needs_target': False,
                 'description': "Nếu bị Cận vệ nhắm đến, người chơi Cận vệ sẽ bị loại. Bỏ lá này và rút lá mới.",
                 'count_classic': 0, 'count_large': 1},
    'Jester': {'value': 0, 'vietnamese_name': 'tenhe', 'effect_name': 'effect_jester', 'needs_target': True,
               'description': "Chọn một người chơi. Nếu họ thắng vòng này, bạn cũng nhận được một tín vật.",
               'count_classic': 0, 'count_large': 1},
    'Cardinal': {'value': 2, 'vietnamese_name': 'hongy', 'effect_name': 'effect_cardinal', 'needs_target': True,
                 'description': "Hai người chơi đổi bài cho nhau. Bạn được nhìn một trong hai lá bài đó.",
                 'count_classic': 0, 'count_large': 2},
    'Baroness': {'value': 3, 'vietnamese_name': 'nunamtuoc', 'effect_name': 'effect_baroness', 'needs_target': True,
                 'description': "Nhìn bài trên tay của 1 hoặc 2 người chơi khác.",
                 'count_classic': 0, 'count_large': 2},
    'Sycophant': {'value': 4, 'vietnamese_name': 'keninhbo', 'effect_name': 'effect_sycophant', 'needs_target': True,
                  'description': "Người bị chọn phải tự chọn mình làm mục tiêu cho lá bài hiệu ứng tiếp theo.",
                  'count_classic': 0, 'count_large': 2},
    'Count': {'value': 5, 'vietnamese_name': 'batuoc', 'effect_name': 'effect_count', 'needs_target': False,
              'description': "+1 vào giá trị bài trên tay nếu lá này nằm trong chồng bài bỏ của bạn.",
              'count_classic': 0, 'count_large': 2},
    'Sheriff': {'value': 6, 'vietnamese_name': 'nguyensoai', 'effect_name': 'effect_sheriff', 'needs_target': False,
                'description': "Nếu bạn bị loại khi có lá này trong chồng bài bỏ, bạn nhận được một tín vật.",
                'count_classic': 0, 'count_large': 1},
    'Queen Mother': {'value': 7, 'vietnamese_name': 'nuhoang', 'effect_name': 'effect_queen_mother', 'needs_target': True,
                     'description': "So bài; người có bài giá trị cao hơn sẽ bị loại.",
                     'count_classic': 0, 'count_large': 1},
    'Bishop': {'value': 9, 'vietnamese_name': 'giammuc', 'effect_name': 'effect_bishop', 'needs_target': True,
               'description': "Đoán giá trị lá bài (không phải Cận vệ). Nhận một tín vật nếu đúng. Người bị đoán có thể rút lại bài.",
               'count_classic': 0, 'count_large': 1},
}

CARD_PROTOTYPES = {}

def initialize_card_prototypes():
    """
    Populates the CARD_PROTOTYPES dictionary with Card objects.
    This should be called once at application startup.
    """
    if CARD_PROTOTYPES: # Avoid re-initialization
        return

    from . import card_effects # <- Import is moved here, inside the function

    for eng_name, data in CARDS_DATA_RAW.items():
        # Construct image path
        viet_name = data['vietnamese_name']
        path_jpg = os.path.join(CARD_FOLDER, f"{viet_name}.jpg")
        path_png = os.path.join(CARD_FOLDER, f"{viet_name}.png")
        # Use PNG if it exists, otherwise JPG, otherwise fall back to back image
        actual_path = next((p for p in [path_png, path_jpg] if os.path.exists(p)), CARD_BACK_IMAGE)

        # Get the effect handler function from the card_effects module
        effect_handler = getattr(card_effects, data['effect_name'], None)
        if not effect_handler:
            print(f"Warning: No effect implementation found for '{eng_name}' (expected function '{data['effect_name']}').")

        # Create the Card object
        CARD_PROTOTYPES[eng_name] = Card(
            name=eng_name,
            value=data['value'],
            description=data['description'],
            image_path=actual_path,
            vietnamese_name=viet_name,
            count_classic=data.get('count_classic', 0),
            count_large=data.get('count_large', 0),
            effect_handler=effect_handler,
            needs_target=data.get('needs_target', False)
        )

# Automatically initialize prototypes when this module is imported
initialize_card_prototypes()
