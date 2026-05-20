import os
from PIL import Image


class ClothingCatalogManager:

    SIZE_THRESHOLDS = [
        (0.14, 'XS'),
        (0.18, 'S'),
        (0.22, 'M'),
        (0.27, 'L'),
        (0.32, 'XL'),
    ]
    DEFAULT_FRAME_W = 720

    def __init__(self, clothing_dir='clothing'):
        self.clothing_dir = clothing_dir
        self._cache = {}
        self.catalog = []
        self._load_catalog()

    def _load_catalog(self):
        if not os.path.isdir(self.clothing_dir):
            os.makedirs(self.clothing_dir)
        self.catalog = sorted(
            f for f in os.listdir(self.clothing_dir)
            if f.lower().endswith('.png')
        )

    def get_image(self, filename):
        if filename not in self._cache:
            path = os.path.join(self.clothing_dir, filename)
            self._cache[filename] = Image.open(path).convert('RGBA')
        return self._cache[filename]

    def get_display_name(self, filename):
        name = os.path.splitext(filename)[0]
        return name.replace('_', ' ').title()

    def estimate_size(self, shoulder_px, frame_w=None):
        fw = frame_w or self.DEFAULT_FRAME_W
        ratio = shoulder_px / fw
        for threshold, size in self.SIZE_THRESHOLDS:
            if ratio < threshold:
                return size
        return 'XXL'
