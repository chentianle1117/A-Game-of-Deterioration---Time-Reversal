from PIL import Image
import os
from cmu_graphics import CMUImage

class TextureManagerOptimized:
    def __init__(self):
        self.textures = {}  # Original PIL images
        self.cache = {}     # Resized CMUImage cache
        self.texture_mappings = {
            'water': 'WATER.png',
            'dirt': 'DIRT.png',
            'tall_grass': 'TALLGRASS.png',
            'path_rocks': 'PATHROCKS.png'
        }
        self.load_textures()

    def load_textures(self):
        """Load textures as PIL Images"""
        texture_dir = self._find_texture_directory()
        if not texture_dir:
            print("Texture directory not found.")
            return

        for terrain, filename in self.texture_mappings.items():
            path = os.path.join(texture_dir, filename)
            try:
                # Load and store as PIL Image
                self.textures[terrain] = Image.open(path).convert('RGB')
                print(f"Loaded texture for {terrain}")
            except Exception as e:
                print(f"Failed to load texture {filename}: {e}")

    def _find_texture_directory(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(current_dir, 'assets', 'textures'),
            os.path.join(current_dir, '..', 'assets', 'textures'),
            'assets/textures'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        return None

    def draw_texture(self, terrain_type, width, height):
        """Retrieve a cached CMUImage of the resized texture."""
        if terrain_type not in self.textures:
            return None

        # Use (terrain_type, width, height) as cache key
        cache_key = (terrain_type, width, height)
        if cache_key not in self.cache:
            # Resize the PIL image to the specified width and height
            # Using Image.LANCZOS instead of ImageResampling.LANCZOS
            resized_image = self.textures[terrain_type].resize(
                (width, height), 
                Image.LANCZOS  # This is the compatible way to specify LANCZOS resampling
            )
            # Convert the resized image to a CMUImage
            self.cache[cache_key] = CMUImage(resized_image)
        return self.cache[cache_key]

    def clear_cache(self):
        """Clear the texture cache to save memory."""
        self.cache.clear()