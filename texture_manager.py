from PIL import Image, ImageEnhance, ImageFilter
import os
from cmu_graphics import CMUImage
import time

class TextureManagerOptimized:
    def __init__(self):
        self.textures = {}  # Original PIL images
        self.deteriorated_textures = {}  # Store deteriorated versions
        self.cache = {}     # Resized CMUImage cache
        self.last_update = time.time()
        self.update_count = 0
        self.deterioration_level = 0  # Track overall deterioration progress
        
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
            print("[DEBUG] Texture directory not found.")
            return

        for terrain, filename in self.texture_mappings.items():
            path = os.path.join(texture_dir, filename)
            try:
                # Load and store as PIL Image
                self.textures[terrain] = Image.open(path).convert('RGB')
                # Initialize deteriorated textures with original images
                self.deteriorated_textures[terrain] = self.textures[terrain].copy()
                print(f"[DEBUG] Loaded texture for {terrain}")
            except Exception as e:
                print(f"[ERROR] Failed to load texture {filename}: {e}")

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

    def update_deterioration(self):
        """Apply progressive deterioration effects"""
        current_time = time.time()
        if current_time - self.last_update < 1.0:  # Check every second
            return
            
        self.last_update = current_time
        self.update_count += 1
        
        # Update every 5 counts
        if self.update_count % 1 == 0:
            print(f"[DEBUG] Deterioration update #{self.update_count}")
            
            # Increase deterioration level
            self.deterioration_level = min(1.0, self.deterioration_level + 0.1)
            print(f"[DEBUG] New deterioration level: {self.deterioration_level}")
            
            # Apply specific deterioration effects
            for terrain, original in self.textures.items():
                try:
                    if terrain == "dirt":
                        self.deteriorated_textures[terrain] = self._deteriorate_dirt(
                            original, self.deterioration_level
                        )
                    elif terrain == "water":
                        self.deteriorated_textures[terrain] = self._deteriorate_water(
                            original, self.deterioration_level
                        )
                    elif terrain == "tall_grass":
                        self.deteriorated_textures[terrain] = self._deteriorate_tall_grass(
                            original, self.deterioration_level
                        )
                    elif terrain == "path_rocks":
                        self.deteriorated_textures[terrain] = self._deteriorate_path_rocks(
                            original, self.deterioration_level
                        )
                    print(f"[DEBUG] Updated {terrain} texture effects")
                except Exception as e:
                    print(f"[ERROR] Failed to update {terrain}: {e}")
            
            # Clear cache to force texture updates
            self.cache.clear()

    def _deteriorate_dirt(self, image, level):
        """Increase contrast and darken dirt progressively"""
        # Start with a fresh copy
        modified = image.copy()
        
        # Progressive contrast increase
        contrast_factor = 1 + (0.2 * level)  # Up to 20% increase
        enhancer = ImageEnhance.Contrast(modified)
        modified = enhancer.enhance(contrast_factor)
        
        # Progressive darkening
        brightness_factor = 1 - (0.3 * level)  # Up to 30% darker
        enhancer = ImageEnhance.Brightness(modified)
        return enhancer.enhance(brightness_factor)

    def _deteriorate_water(self, image, level):
        """Add increasing ripple effect for water"""
        # Blur radius increases with deterioration
        blur_radius = level * 2  # Up to 2 pixels blur
        return image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    def _deteriorate_tall_grass(self, image, level):
        """Progressive color fading for grass"""
        modified = image.copy()
        
        # Progressive color saturation reduction
        color_factor = 1 - (0.4 * level)  # Up to 40% color reduction
        enhancer = ImageEnhance.Color(modified)
        faded = enhancer.enhance(color_factor)
        
        # Progressive brightness reduction
        brightness_factor = 1 - (0.2 * level)  # Up to 20% brightness reduction
        enhancer = ImageEnhance.Brightness(faded)
        return enhancer.enhance(brightness_factor)

    def _deteriorate_path_rocks(self, image, level):
        """Progressive darkening and smoothing for rocks"""
        modified = image.copy()
        
        # Progressive darkening
        brightness_factor = 1 - (0.4 * level)  # Up to 40% darker
        enhancer = ImageEnhance.Brightness(modified)
        darkened = enhancer.enhance(brightness_factor)
        
        # Progressive smoothing
        if level > 0.5:  # Only apply smoothing after 50% deterioration
            return darkened.filter(ImageFilter.SMOOTH_MORE)
        return darkened

    def draw_texture(self, terrain_type, width, height):
        """Draw deteriorated texture with caching"""
        if terrain_type not in self.deteriorated_textures:
            return None
            
        # Cache key includes deterioration level for proper updates
        cache_key = (terrain_type, width, height, self.deterioration_level)
        
        if cache_key not in self.cache:
            try:
                # Get current deteriorated texture
                current_image = self.deteriorated_textures[terrain_type]
                # Resize for display
                resized = current_image.resize((width, height), Image.LANCZOS)
                # Convert to CMUImage
                self.cache[cache_key] = CMUImage(resized)
                print(f"[DEBUG] Created new CMUImage for {terrain_type} at level {self.deterioration_level:.2f}")
            except Exception as e:
                print(f"[ERROR] Failed to create texture: {e}")
                return None
            
        return self.cache[cache_key]

    def clear_cache(self):
        """Clear the cache to force texture updates"""
        cache_size = len(self.cache)
        self.cache.clear()
        print(f"[DEBUG] Cleared {cache_size} cached images")