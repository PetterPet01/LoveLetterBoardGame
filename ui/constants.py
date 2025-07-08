# file: ui/constants.py

import os
from kivy.config import Config
from kivy.core.window import Window

# Cấu hình Kivy
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# Đường dẫn tài nguyên
ASSETS_DIR = "assets"
CARD_FOLDER = os.path.join(ASSETS_DIR, "cards")

# Hình ảnh giao diện
INTRO_BACKGROUND = os.path.join(ASSETS_DIR, "chill.webp")
RULES_BACKGROUND = os.path.join(ASSETS_DIR, "Rules.png")
VICTORY_IMAGE = os.path.join(ASSETS_DIR, "victory.webp")
DEFEAT_IMAGE = os.path.join(ASSETS_DIR, "defeat.webp")

# Hình ảnh lá bài
CARD_BACK_IMAGE = os.path.join(CARD_FOLDER, "back.png")
EMPTY_CARD_IMAGE = os.path.join(CARD_FOLDER, "empty_card.png")
ELIMINATED_IMAGE = os.path.join(CARD_FOLDER, "back.png")
CARD_RULES_IMAGE = os.path.join(CARD_FOLDER, "card_list_2_4.png")

# Cấu hình cửa sổ
WINDOW_SIZE = (1000, 800)
WINDOW_CLEAR_COLOR = (0.12, 0.07, 0.07, 1)

# Màu sắc
CARD_VALUE_COLORS = {
    0: (0.5, 0.5, 0.5), 1: (0.2, 0.4, 1.0), 2: (0.7, 0.7, 1.0),
    3: (0.6, 0.3, 0.7), 4: (0.3, 0.7, 0.3), 5: (0.9, 0.7, 0.2),
    6: (0.9, 0.5, 0.3), 7: (0.7, 0.3, 0.7), 8: (1.0, 0.3, 0.3),
    9: (0.9, 0.9, 1.0),
}

# Áp dụng cấu hình cửa sổ
Window.size = WINDOW_SIZE
Window.clearcolor = WINDOW_CLEAR_COLOR

