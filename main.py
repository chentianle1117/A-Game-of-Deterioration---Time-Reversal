from cmu_graphics import *
from game import Game
from menu import MenuState
from map_editor import MapEditor
import time 

def onAppStart(app):
    app.width = 800
    app.height = 600
    app.stepsPerSecond = 60
    app.setMaxShapeCount(99999)
    app.state = 'menu'
    app.menu = MenuState(app.width, app.height)
    app.game = None
    app.mapEditor = None

def initializeGame(app, customMap=None, isInfiniteMode=False):
    app.game = Game(customMap, isInfiniteMode=isInfiniteMode)

def gameKeyEvents(app, key):
    if key == 'escape':
        app.state = 'menu'
    elif key == '=':
        app.game.setZoom(app.game.zoomLevel * 1.2)
    elif key == '-':
        app.game.setZoom(app.game.zoomLevel / 1.2)
    elif key == 'd':  # Toggle debug info
        app.game.toggleDebugInfo()
    elif key == 'm':  # Toggle minimap mode
        app.game.toggleMinimapMode()
    elif key == ']':  # Increase character strength
        app.game.character.setStrength(app.game.character.strength + 0.5)
    elif key == '[':  # Decrease character strength
        app.game.character.setStrength(app.game.character.strength - 0.5)
    elif key == 't':  # Adjust tree density up
        app.game.treeDensity = min(1.0, app.game.treeDensity + 0.05)
        app.game.placeTrees()
    elif key == 'g':  # Adjust tree density down
        app.game.treeDensity = max(0.0, app.game.treeDensity - 0.05)
        app.game.placeTrees()

def onKeyPress(app, key):
    if app.state == 'game':
        if app.game.gameOver:
            if key == 'escape':
                app.state = 'menu'
        else:
            if key == 'e' and app.game.isInfiniteMode:
                app.game.endGame()
            elif key == 'space':
                app.game.emitHealingWave()
            elif key == 'escape':
                app.state = 'menu'
            elif key == '=':
                app.game.setZoom(app.game.zoomLevel * 1.2)
            elif key == '-':
                app.game.setZoom(app.game.zoomLevel / 1.2)
            elif key == 'd':
                app.game.toggleDebugInfo()
            elif key == 'm':
                app.game.toggleMinimapMode()
            elif key == 't':
                app.game.treeDensity = min(1.0, app.game.treeDensity + 0.05)
                app.game.placeTrees()
            elif key == 'g':
                app.game.treeDensity = max(0.0, app.game.treeDensity - 0.05)
                app.game.placeTrees()
    elif app.state == 'editor':
        if key == 'escape':
            app.state = 'menu'
        else:
            app.mapEditor.handleKey(key.lower())

def onKeyHold(app, keys):
    if app.state == 'game' and not app.game.gameOver:
        dx = dy = 0
        if 'left' in keys or 'a' in keys:
            dx = -1
        if 'right' in keys or 'd' in keys:
            dx = 1
        if 'up' in keys or 'w' in keys:
            dy = -1
        if 'down' in keys or 's' in keys:
            dy = 1
        if 'shift' in keys:
            dx *= 2
            dy *= 2
        if dx or dy:
            if dx:
                app.game.character.direction = 'left' if dx < 0 else 'right'
            if dy:
                app.game.character.direction = 'up' if dy < 0 else 'down'
            app.game.character.move(app.game, dx, dy)
            app.game.updateCamera()

def onMousePress(app, mouseX, mouseY):
    if app.state == 'menu':
        action = app.menu.handleClick(mouseX, mouseY)
        if action == 'construct_map':
            app.mapEditor = MapEditor(app.width, app.height, 200, 150)
            app.state = 'editor'
    elif app.state == 'editor':
        if app.mapEditor.isOverSaveButton(mouseX, mouseY):
            terrainMap = app.mapEditor.generateTerrainMap()
            if terrainMap:
                initializeGame(app, customMap=terrainMap)
                app.state = 'game'
                app.game.startTime = time.time()
        elif app.mapEditor.isOverInfiniteButton(mouseX, mouseY):
            terrainMap = app.mapEditor.generateTerrainMap()
            if terrainMap:
                initializeGame(app, customMap=terrainMap, isInfiniteMode=True)
                app.state = 'game'
    elif app.state == 'game' and app.game.isInfiniteMode:
        # Check if the end game button is clicked
        if app.game.isEndGameButtonClicked(mouseX, mouseY):
            app.game.endGame()

def onStep(app):
    if app.state == 'game' and not app.game.gameOver:
        app.game.updateGame(1/app.stepsPerSecond)
        app.game.update()
        app.game.character.updateAnimation()

def onMouseMove(app, mouseX, mouseY):
    if app.state == 'editor':
        app.mapEditor.updateMousePos(mouseX, mouseY)

def onMouseDrag(app, mouseX, mouseY):
    if app.state == 'editor':
        app.mapEditor.updateMousePos(mouseX, mouseY)
        app.mapEditor.paint(mouseX, mouseY)

def redrawGame(app):
    app.game.redrawGame()  # Use Game class's redrawGame method directly

def redrawAll(app):
    try:
        if app.state == 'menu':
            app.menu.draw()
        elif app.state == 'game':
            redrawGame(app)
        elif app.state == 'editor':
            app.mapEditor.draw()
    except Exception as e:
        print(f"Rendering error: {e}")
        drawLabel("Error in rendering", app.width // 2, app.height // 2, 
                 fill='red', bold=True, size=20)

def main():
    runApp(width=800, height=600)

if __name__ == '__main__':
    main()