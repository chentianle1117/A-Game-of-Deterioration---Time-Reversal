![game demo](https://file.notion.so/f/f/ef69813d-5b0d-4465-ae10-f770f962d7d9/6f5ceee5-6628-42b6-9ddd-0bef7ece2662/Untitled-video-_11_.gif?table=block&id=16a33d12-d95a-8077-9ab7-f488cbc13f1f&spaceId=ef69813d-5b0d-4465-ae10-f770f962d7d9&expirationTimestamp=1736488800000&signature=dV0Vat0udr6wJ6X3RaD5LVqoBRyrDujtB2yBH082Yso)


Deterioration & Restoration
A game about healing a deteriorating environment against time

About:
You control a character who can heal deteriorating terrain. Move around the world, collect power-ups, and use your healing abilities to prevent the environment from decaying too much. The game features both timed and infinite modes.

How to Run:
1. Make sure you have Python 3.6+ installed
2. Install required libraries:
   - cmu_graphics (pip install cmu_graphics)
   - Pillow (pip install Pillow)

3. Run main.py to start the game

Game Controls:
- WASD/Arrow Keys: Move character
- Space: Release healing wave
- Shift: Sprint
- M: Toggle map view
- ESC: Return to menu/pause

Debug Commands:
- +/-: Zoom in/out
- [/]: Adjust healing power
- T/G: Change tree density
- D: Toggle debug info

File Structure:
- main.py: Entry point
- game.py: Main game logic
- menu.py: Menu system
- assets/: Contains textures and sprites
  - textures/: Terrain textures
  - objects/: Character sprites

Notes:
- Make sure the assets folder is in the same directory as the game files
- First time loading might take a few seconds to cache textures

Known Issues:
- Might lag a bit with lots of trees on screen
- Some textures might flicker when deteriorating rapidly
