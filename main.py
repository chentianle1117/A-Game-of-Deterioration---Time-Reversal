from cmu_graphics import *
from game import Game
from menu import MenuState
from map_editor import MapEditor

def onAppStart(app):
    app.width = 800
    app.height = 600
    app.stepsPerSecond = 60
    app.setMaxShapeCount(99999)
    app.state = 'menu'
    app.menu = MenuState(app.width, app.height)
    app.game = None
    app.mapEditor = None

def initializeGame(app, customMap=None):
    app.game = Game(customMap)

def gameKeyEvents(app, key):
    if key == 'escape':
        app.state = 'menu'
    elif key == '=':
        app.game.setZoom(app.game.zoomLevel * 1.2)
    elif key == '-':
        app.game.setZoom(app.game.zoomLevel / 1.2)

def onKeyPress(app, key):
    if app.state == 'game':
        gameKeyEvents(app, key)
    elif app.state == 'editor' and key == 'escape':
        app.state = 'menu'
    elif app.state == 'editor':
        app.mapEditor.handleKey(key.lower())

def onKeyHold(app, keys):
    if app.state == 'game':
        dx = dy = 0
        if 'left' in keys:
            dx = -1
        if 'right' in keys:
            dx = 1
        if 'up' in keys:
            dy = -1
        if 'down' in keys:
            dy = 1
        if dx or dy:
            if dx:
                app.game.character.direction = 'left' if dx < 0 else 'right'
            if dy:
                app.game.character.direction = 'up' if dy < 0 else 'down'
            app.game.character.move(dx, dy)
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
        else:
            app.mapEditor.updateMousePos(mouseX, mouseY)

def onMouseMove(app, mouseX, mouseY):
    if app.state == 'editor':
        app.mapEditor.updateMousePos(mouseX, mouseY)

def onMouseDrag(app, mouseX, mouseY):
    if app.state == 'editor':
        app.mapEditor.updateMousePos(mouseX, mouseY)
        app.mapEditor.paint(mouseX, mouseY)

def redrawGame(app):
    drawRect(0, 0, app.width, app.height, fill='white')
    startRow, startCol, endRow, endCol = app.game.getVisibleCells()
    for row in range(startRow, endRow):
        for col in range(startCol, endCol):
            if 0 <= row < app.game.worldHeight and 0 <= col < app.game.worldWidth:
                app.game.drawCell(row, col)
    charX, charY = app.game.character.getPosition()
    screenX, screenY = app.game.worldToScreen(charX, charY)
    app.game.character.draw(screenX, screenY, app.game.zoomLevel)
    app.game.drawUI()
    app.game.drawMiniMap()

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
        drawLabel("Error in rendering", app.width // 2, app.height // 2, fill='red', bold=True, size=20)

def main():
    runApp(width=800, height=600)

if __name__ == '__main__':
    main()
