# file: main.py

import os
import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

# Imports từ các file cục bộ
from ui.constants import (
    CARD_FOLDER, CARD_BACK_IMAGE, ELIMINATED_IMAGE, EMPTY_CARD_IMAGE,
    CARD_RULES_IMAGE, ASSETS_DIR
)
from logic.constants import CARDS_DATA_RAW
from ui.game_screen import LoveLetterGame
from ui.screens import IntroScreen, RulesScreen

class LoveLetterApp(App):
    def build(self):
        # Tạo thư mục assets nếu chưa tồn tại
        os.makedirs(CARD_FOLDER, exist_ok=True)
        
        self.title = 'Thư Tình Board Game'
        
        # Thiết lập ScreenManager
        sm = ScreenManager(transition=FadeTransition(duration=0.5))
        
        # Tạo instance của màn hình game chính
        game_widget = LoveLetterGame()
        
        # Tạo các màn hình
        intro_screen = IntroScreen(name='intro')
        rules_screen = RulesScreen(name='rules')
        game_screen = Screen(name='game')
        
        # Liên kết màn hình luật chơi với instance của game
        # để nó có thể gọi hàm bắt đầu game
        rules_screen.game_instance = game_widget
        
        # Thêm widget game vào màn hình game
        game_screen.add_widget(game_widget)
        
        # Thêm các màn hình vào ScreenManager
        sm.add_widget(intro_screen)
        sm.add_widget(rules_screen)
        sm.add_widget(game_screen)
        
        return sm

# ---- Hàm tạo ảnh giả để chạy thử nghiệm ----
def create_dummy_images():
    """Tạo các ảnh placeholder nếu chúng không tồn tại."""
    try:
        from PIL import Image as PILImage, ImageDraw
    except ImportError:
        print("WARNING: PIL/Pillow is not installed. Cannot create dummy images.")
        print("Install it with: pip install Pillow")
        return

    def create_image(path, size, color, text):
        if not os.path.exists(path):
            try:
                img = PILImage.new('RGB', size, color=color)
                d = ImageDraw.Draw(img)
                d.text((10, 10), text, fill=(255, 255, 255))
                img.save(path)
                print(f"INFO: Created dummy image at {path}")
            except Exception as e:
                print(f"WARNING: Could not create dummy image {path}: {e}")

    create_image(CARD_BACK_IMAGE, (200, 300), (25, 40, 100), "CARD BACK")
    create_image(ELIMINATED_IMAGE, (100, 150), (100, 20, 20), "ELIMINATED")
    create_image(CARD_RULES_IMAGE, (1200, 800), (20, 20, 30), "CARD RULES")

    if not os.path.exists(EMPTY_CARD_IMAGE):
        try:
            img = PILImage.new('RGBA', (200, 300), color=(0, 0, 0, 0))
            img.save(EMPTY_CARD_IMAGE)
            print(f"INFO: Created empty card image at {EMPTY_CARD_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create empty card image: {e}")

    for card_key, card_data in CARDS_DATA_RAW.items():
        v_name = card_data['vietnamese_name']
        path_png = os.path.join(CARD_FOLDER, f"{v_name}.png")
        if not os.path.exists(path_png):
            create_image(path_png, (200, 300), 
                         (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)),
                         f"{card_key}\n(V:{card_data['value']})\n{v_name}")

if __name__ == '__main__':
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(CARD_FOLDER, exist_ok=True)
    create_dummy_images()
    LoveLetterApp().run()