import time
from PIL import Image, ImageEnhance, ImageFilter
from texture_manager import TextureManagerOptimized

def test_deterioration():
    # Load a single texture
    texture_manager = TextureManagerOptimized()
    terrain_type = "dirt"  # Choose one texture to test
    texture = texture_manager.textures.get(terrain_type)

    if not texture:
        print(f"Failed to load texture for {terrain_type}.")
        return

    print(f"Loaded {terrain_type} texture. Starting deterioration test...")

    # Simulate time-based deterioration
    deterioration_steps = 10
    for step in range(deterioration_steps):
        print(f"\n[STEP {step + 1}] Applying deterioration...")
        
        # Apply deterioration logic for dirt
        enhancer = ImageEnhance.Contrast(texture)
        texture = enhancer.enhance(1.1)  # Increase contrast by 10%
        enhancer = ImageEnhance.Brightness(texture)
        texture = enhancer.enhance(0.9)  # Reduce brightness by 10%

        # Save the deteriorated texture for inspection
        debug_filename = f"debug_dirt_step_{step + 1}.png"
        texture.save(debug_filename)
        print(f"[STEP {step + 1}] Saved deteriorated texture as {debug_filename}.")

        # Wait 1 second to simulate time passage
        time.sleep(1)

    print("Deterioration test complete.")

if __name__ == "__main__":
    test_deterioration()
