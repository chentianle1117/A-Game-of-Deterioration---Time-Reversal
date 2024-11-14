# texture_manager.py
from cmu_graphics import *
import os
from PIL import Image
import numpy as np

class TextureManager:
    def __init__(self):
        self.original_textures = {}  # Original high-res textures
        self.cache = {}  # Cache for processed textures
        self.max_cache_entries = 1000
        
        self.texture_mappings = {
            'water': 'WATER.png',
            'dirt': 'DIRT.png',
            'tall_grass': 'TALLGRASS.png',
            'path_rocks': 'PATHROCKS.png'
        }
        self.load_textures()

    def load_textures(self):
        texture_dir = self._find_texture_directory()
        if not texture_dir:
            print("Texture directory not found.")
            return

        for terrain_type, filename in self.texture_mappings.items():
            try:
                image_path = os.path.join(texture_dir, filename)
                image = Image.open(image_path).convert('RGB')
                # Convert to numpy array for faster processing
                self.original_textures[terrain_type] = np.array(image)
                print(f"Loaded texture for {terrain_type}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")

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

    def get_cache_key(self, terrain_type, width, height, zoom_level):
        # Round dimensions and zoom to reduce cache variations
        rwidth = rounded(width / 4) * 4
        rheight = rounded(height / 4) * 4
        rzoom = rounded(zoom_level * 2) / 2
        return (terrain_type, rwidth, rheight, rzoom)

    def process_texture(self, texture, target_width, target_height, zoom_level):
        """Process texture into drawable blocks with detail preservation"""
        h, w = texture.shape[:2]
        
        # Calculate number of blocks based on zoom level
        if zoom_level >= 3.0:
            blocks = 8  # Maximum detail
        elif zoom_level >= 2.0:
            blocks = 6
        elif zoom_level >= 1.0:
            blocks = 4
        else:
            blocks = 2

        block_h = h // blocks
        block_w = w // blocks
        
        # Calculate colors for each block
        colors = []
        for i in range(blocks):
            row = []
            for j in range(blocks):
                y_start = i * block_h
                y_end = (i + 1) * block_h
                x_start = j * block_w
                x_end = (j + 1) * block_w
                
                # Get block from texture and calculate average color
                block = texture[y_start:y_end, x_start:x_end]
                avg_color = np.mean(block, axis=(0, 1)).astype(int)
                row.append((int(avg_color[0]), int(avg_color[1]), int(avg_color[2])))
            colors.append(row)
        
        return colors, blocks

    # texture_manager.py
    def draw_texture(self, terrain_type, x, y, width, height, zoom_level):
        """Draw texture with preserved detail and no borders"""
        if terrain_type not in self.original_textures:
            return False

        # Get cached result if available
        cache_key = self.get_cache_key(terrain_type, width, height, zoom_level)
        cache_result = self.cache.get(cache_key)

        if cache_result is None:
            # Process texture
            texture = self.original_textures[terrain_type]
            colors, blocks = self.process_texture(texture, width, height, zoom_level)
            
            # Cache the result
            cache_result = (colors, blocks)
            if len(self.cache) > self.max_cache_entries:
                self.cache.clear()
            self.cache[cache_key] = cache_result
        else:
            colors, blocks = cache_result

        # Draw the blocks with adjusted positions to eliminate gaps
        block_width = width / blocks
        block_height = height / blocks

        for i in range(blocks):
            for j in range(blocks):
                color = colors[i][j]
                # Adjust positions to overlap slightly
                block_x = x + (j * block_width)
                block_y = y + (i * block_height)
                
                # Add 1 pixel to width and height to ensure no gaps
                drawRect(block_x, block_y, 
                        block_width + 1, block_height + 1,  # Add 1 to overlap
                        fill=rgb(color[0], color[1], color[2]),
                        border=None)  # Remove border

        return True

    def process_texture(self, texture, target_width, target_height, zoom_level):
        """Process texture into drawable blocks with detail preservation"""
        h, w = texture.shape[:2]
        
        # Determine blocks based on zoom level - adjusted for higher detail
        if zoom_level >= 4.0:
            blocks = 12  # Increased maximum detail
        elif zoom_level >= 3.0:
            blocks = 10
        elif zoom_level >= 2.0:
            blocks = 8
        elif zoom_level >= 1.0:
            blocks = 6
        else:
            blocks = 4
        
        block_h = max(1, h // blocks)
        block_w = max(1, w // blocks)
        
        colors = []
        for i in range(blocks):
            row = []
            for j in range(blocks):
                y_start = min(i * block_h, h-1)
                y_end = min((i + 1) * block_h, h)
                x_start = min(j * block_w, w-1)
                x_end = min((j + 1) * block_w, w)
                
                block = texture[y_start:y_end, x_start:x_end]
                avg_color = np.mean(block, axis=(0, 1)).astype(int)
                row.append((int(avg_color[0]), int(avg_color[1]), int(avg_color[2])))
            colors.append(row)
        
        return colors, blocks