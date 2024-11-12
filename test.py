# test.py
from cmu_graphics import *
import os
from PIL import Image
import numpy as np

def onAppStart(app):
    app.messages = []
    app.blockSize = 4  # Size of each block in pixels
    
    try:
        # Load with PIL
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, 'assets', 'textures', 'WATER.png')
        
        # Open and convert image
        pil_image = Image.open(image_path)
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to numpy array for faster processing
        pixel_array = np.array(pil_image)
        width, height = pil_image.size
        
        # Calculate number of blocks
        blocks_width = width // app.blockSize
        blocks_height = height // app.blockSize
        
        # Store averaged blocks
        app.blocks = []
        for y in range(blocks_height):
            row = []
            for x in range(blocks_width):
                # Get block of pixels
                block = pixel_array[
                    y*app.blockSize:(y+1)*app.blockSize,
                    x*app.blockSize:(x+1)*app.blockSize
                ]
                # Average the colors in the block and convert to regular integers
                avg_color = [int(x) for x in np.mean(block, axis=(0, 1))]
                row.append(avg_color)
            app.blocks.append(row)
            
        app.blocks_size = (blocks_width, blocks_height)
        app.messages.append("Processed image into blocks")
        
    except Exception as e:
        app.messages.append(f"Error: {str(e)}")

def redrawAll(app):
    drawRect(0, 0, 400, 400, fill='white')
    
    # Draw messages
    y = 30
    for msg in app.messages:
        drawLabel(msg, 200, y)
        y += 30
    
    # Draw the blocks if we have them
    if hasattr(app, 'blocks') and hasattr(app, 'blocks_size'):
        blocks_width, blocks_height = app.blocks_size
        scale = 4  # Scale up the final image
        
        # Draw each averaged block
        for y in range(blocks_height):
            for x in range(blocks_width):
                r, g, b = app.blocks[y][x]  # These are now regular Python ints
                color = rgb(r, g, b)
                drawRect(100 + x*scale, 200 + y*scale, 
                        scale, scale, fill=color)

def main():
    runApp(width=400, height=400)

main()