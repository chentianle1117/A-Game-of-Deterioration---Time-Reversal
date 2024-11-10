from cmu_graphics import CMUImage
import os

class TextureManager:
    def __init__(self):
        """Initialize the texture manager"""
        print("\n=== Initializing TextureManager ===")
        self._textures = {}  # Private texture storage
        self._texture_paths = {}  # Store paths for reloading if needed
        self.texture_mappings = {
            'water': 'WATER.png',
            'dirt': 'DIRT.png',
            'tall_grass': 'TALLGRASS.png',
            'path_rocks': 'PATHROCKS.png'
        }
        self._initialized = False
        self.load_textures()

    def _find_texture_directory(self):
        """Find the directory containing texture files"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(current_dir, 'assets', 'textures'),
            os.path.join(current_dir, '..', 'assets', 'textures'),
            os.path.join(current_dir, 'textures'),
            os.path.join(current_dir, '..', 'textures'),
            'assets/textures',
            '../assets/textures',
            'textures'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        return None

    def load_textures(self):
        """Load all textures from the assets directory"""
        if self._initialized:
            return

        print("\n=== Loading Textures ===")
        texture_dir = self._find_texture_directory()
        
        if texture_dir is None:
            print("ERROR: Could not find texture directory!")
            self._initialized = True
            return
            
        print(f"\nUsing texture directory: {texture_dir}")
        
        for terrain_type, filename in self.texture_mappings.items():
            try:
                image_path = os.path.join(texture_dir, filename)
                self._texture_paths[terrain_type] = image_path
                
                if os.path.exists(image_path):
                    try:
                        # Load image as CMUImage and store both path and image
                        self._textures[terrain_type] = CMUImage(image_path)
                        print(f"✓ Successfully loaded {filename}")
                    except Exception as e:
                        print(f"✗ Error creating CMUImage for {filename}: {e}")
                        self._textures[terrain_type] = None
                else:
                    print(f"✗ File not found: {image_path}")
                    self._textures[terrain_type] = None
            except Exception as e:
                print(f"✗ Error loading {filename}: {e}")
                self._textures[terrain_type] = None
        
        self._initialized = True
        self.verify_textures()

    def get_texture(self, terrain_type):
        """Get a texture by terrain type, reloading if necessary"""
        # If texture is missing but we have its path, try to reload it
        if (terrain_type in self._textures and 
            self._textures[terrain_type] is None and 
            terrain_type in self._texture_paths):
            try:
                self._textures[terrain_type] = CMUImage(self._texture_paths[terrain_type])
            except Exception:
                return None
                
        return self._textures.get(terrain_type)

    def verify_textures(self):
        """Verify all textures are loaded correctly and print status"""
        print("\n=== Texture Verification ===")
        total_loaded = 0
        for terrain_type in self.texture_mappings:
            is_loaded = self._textures.get(terrain_type) is not None
            status = "✓ Loaded" if is_loaded else "✗ Missing"
            if is_loaded:
                total_loaded += 1
            print(f"{terrain_type}: {status}")
        print(f"\nTotal textures loaded: {total_loaded}/{len(self.texture_mappings)}")