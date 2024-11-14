# main.py
from cmu_graphics import *
from game import Game
from menu import MenuState
from map_editor import MapEditor

def onAppStart(app):
    """Initialize the application"""
    # Basic app settings
    app.width = 800
    app.height = 600
    app.stepsPerSecond = 60
    app.setMaxShapeCount(99999)
    
    # Initialize game states
    app.state = 'menu'  # States: 'menu', 'game', 'editor'
    app.menu = MenuState(app.width, app.height)
    app.game = None
    app.map_editor = None

def initializeGame(app, custom_map=None):
    """Initialize or reset the game state"""
    app.game = Game()
    if custom_map:
        app.game.setCustomGrid(custom_map)

def gameKeyEvents(app, key):
    """Handle game-specific key events"""
    if key == 'escape':
        app.state = 'menu'
    elif key == '=':
        app.game.setZoom(app.game.zoomLevel * 1.2)
    elif key == '-':
        app.game.setZoom(app.game.zoomLevel / 1.2)

def onKeyPress(app, key):
    """Handle all key press events"""
    if app.state == 'game':
        gameKeyEvents(app, key)
    elif app.state == 'editor' and key == 'escape':
        app.state = 'menu'
    elif app.state == 'editor':
        app.map_editor.handle_key(key.lower())

def onKeyHold(app, keys):
    """Handle continuous key press events"""
    if app.state == 'game':
        dx = dy = 0
        if 'left' in keys:  dx = -1
        if 'right' in keys: dx = 1
        if 'up' in keys:    dy = -1
        if 'down' in keys:  dy = 1
        
        if dx or dy:
            if dx: app.game.character.direction = 'left' if dx < 0 else 'right'
            if dy: app.game.character.direction = 'up' if dy < 0 else 'down'
            app.game.character.move(dx, dy)
            app.game.updateCamera()

def onMousePress(app, mouseX, mouseY):
    if app.state == 'menu':
        action = app.menu.handleClick(mouseX, mouseY)
        if action == 'construct_map':
            app.map_editor = MapEditor(app.width, app.height, 200, 150)
            app.state = 'editor'
    
    elif app.state == 'editor':
        if app.map_editor.isOverSaveButton(mouseX, mouseY):
            terrain_map = app.map_editor._generateTerrainMap()
            if terrain_map:
                app.game = Game(custom_map=terrain_map)
                app.state = 'game'
        else:
            app.map_editor.updateMousePos(mouseX, mouseY)

def onMouseMove(app, mouseX, mouseY):
    """Handle mouse movement"""
    if app.state == 'editor':
        app.map_editor.updateMousePos(mouseX, mouseY)

def onMouseDrag(app, mouseX, mouseY):
    """Handle mouse drag events"""
    if app.state == 'editor':
        app.map_editor.updateMousePos(mouseX, mouseY)
        app.map_editor.paint(mouseX, mouseY)

def redrawGame(app):
    drawRect(0, 0, app.width, app.height, fill='white')
    startRow, startCol, endRow, endCol = app.game.getVisibleCells()

    for row in range(startRow, endRow):
        for col in range(startCol, endCol):
            if (0 <= row < app.game.WORLD_HEIGHT and 
                0 <= col < app.game.WORLD_WIDTH):
                app.game.drawCell(row, col)

    charX, charY = app.game.character.get_position()
    screenX, screenY = app.game.worldToScreen(charX, charY)
    app.game.character.draw(screenX, screenY, app.game.zoomLevel)

    app.game.drawUI()
    app.game.drawMiniMap()


def redrawAll(app):
    """Main render function"""
    try:
        if app.state == 'menu':
            app.menu.draw()
        elif app.state == 'game':
            redrawGame(app)
        elif app.state == 'editor':
            app.map_editor.draw()
    except Exception as e:
        print(f"Rendering error: {e}")
        drawLabel("Error in rendering", app.width//2, app.height//2,
                 fill='red', bold=True, size=20)

def main():
    runApp(width=800, height=600)

if __name__ == '__main__':
    main()