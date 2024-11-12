# texture_manager.py
from cmu_graphics import *
import os
from PIL import Image
import numpy as np

class TextureManager:
    def __init__(self):
        self._textures = {}
        self._initialized = False
        self.BLOCK_SIZE = 8  # Increased block size for better performance
        
        self.texture_mappings = {
            'water': 'WATER.png',
            'dirt': 'DIRT.png',
            'tall_grass': 'TALLGRASS.png',
            'path_rocks': 'PATHROCKS.png'
        }
        
        # Pre-calculate RGB colors for performance
        self._color_cache = {}
        self.load_textures()
        self.verify_textures()

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

    def _cache_color(self, r, g, b):
        """Cache RGB colors for reuse"""
        key = (r, g, b)
        if key not in self._color_cache:
            self._color_cache[key] = rgb(r, g, b)
        return self._color_cache[key]

    def load_textures(self):
        texture_dir = self._find_texture_directory()
        if not texture_dir:
            return

        for terrain_type, filename in self.texture_mappings.items():
            try:
                image_path = os.path.join(texture_dir, filename)
                if os.path.exists(image_path):
                    # Load and process image
                    pil_image = Image.open(image_path).convert('RGB')
                    # Resize image to smaller size for better performance
                    pil_image = pil_image.resize((32, 32), Image.Resampling.LANCZOS)
                    pixel_array = np.array(pil_image)
                    
                    # Calculate blocks
                    height, width, _ = pixel_array.shape
                    blocks_height = height // self.BLOCK_SIZE
                    blocks_width = width // self.BLOCK_SIZE
                    
                    # Process blocks more efficiently
                    blocks = np.zeros((blocks_height, blocks_width, 3), dtype=np.int32)
                    for y in range(blocks_height):
                        for x in range(blocks_width):
                            block = pixel_array[
                                y*self.BLOCK_SIZE:(y+1)*self.BLOCK_SIZE,
                                x*self.BLOCK_SIZE:(x+1)*self.BLOCK_SIZE
                            ]
                            blocks[y, x] = np.mean(block, axis=(0, 1)).astype(np.int32)
                    
                    # Pre-cache all colors
                    for y in range(blocks_height):
                        for x in range(blocks_width):
                            r, g, b = blocks[y, x]
                            self._cache_color(int(r), int(g), int(b))
                    
                    self._textures[terrain_type] = {
                        'blocks': blocks,
                        'size': (blocks_width, blocks_height)
                    }
                    
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    def draw_texture(self, terrain_type, x, y, width, height):
        """Draw a texture at the specified location and size using cached colors"""
        texture_data = self._textures.get(terrain_type)
        if not texture_data:
            return False
        
        try:
            blocks = texture_data['blocks']
            blocks_width, blocks_height = texture_data['size']
            
            # Calculate block dimensions and round to integers
            block_width = int(width / blocks_width)
            block_height = int(height / blocks_height)
            
            # Draw blocks in larger chunks
            for by in range(blocks_height):
                block_y = int(y + by * block_height)
                for bx in range(blocks_width):
                    r, g, b = blocks[by, bx]
                    color = self._cache_color(int(r), int(g), int(b))
                    block_x = int(x + bx * block_width)
                    
                    drawRect(block_x, block_y, 
                            block_width + 1, block_height + 1,
                            fill=color)
            return True
            
        except Exception as e:
            print(f"Error drawing texture {terrain_type}: {e}")
            return False

    def verify_textures(self):
        """Verify loaded textures"""
        print("\n=== Texture Verification ===")
        total_loaded = 0
        for terrain_type in self.texture_mappings:
            if terrain_type in self._textures:
                print(f"✓ {terrain_type}: Loaded")
                total_loaded += 1
            else:
                print(f"✗ {terrain_type}: Not loaded")
        print(f"\nTextures loaded: {total_loaded}/{len(self.texture_mappings)}")
        return total_loaded > 0

    def get_texture(self, terrain_type):
        """Legacy method for compatibility"""
        return None