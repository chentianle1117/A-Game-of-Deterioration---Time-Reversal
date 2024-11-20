from PIL import Image, ImageEnhance, ImageFilter
import os
from cmu_graphics import CMUImage
import time

class TextureManagerOptimized:
    def __init__(self):
        self.textures = {}
        self.deterioratedTextures = {}
        self.cache = {}
        self.lastUpdate = time.time()
        self.updateCount = 0
        self.deteriorationLevel = 0
        self.textureMappings = {
            'water': 'WATER.png',
            'dirt': 'DIRT.png',
            'tall_grass': 'TALLGRASS.png',
            'path_rocks': 'PATHROCKS.png'
        }
        self.loadTextures()

    def loadTextures(self):
        textureDir = self.findTextureDirectory()
        if not textureDir:
            return
        for terrain, filename in self.textureMappings.items():
            path = os.path.join(textureDir, filename)
            try:
                self.textures[terrain] = Image.open(path).convert('RGB')
                self.deterioratedTextures[terrain] = self.textures[terrain].copy()
            except Exception as e:
                print(f"Failed to load texture {filename}: {e}")

    def findTextureDirectory(self):
        currentDir = os.path.dirname(os.path.abspath(__file__))
        possiblePaths = [
            os.path.join(currentDir, 'assets', 'textures'),
            os.path.join(currentDir, '..', 'assets', 'textures'),
            'assets/textures'
        ]
        for path in possiblePaths:
            if os.path.exists(path):
                return os.path.abspath(path)
        return None

    def updateDeterioration(self):
        currentTime = time.time()
        if currentTime - self.lastUpdate < 1.0:
            return
        self.lastUpdate = currentTime
        self.updateCount += 1
        if self.updateCount % 1 == 0:
            self.deteriorationLevel = min(1.0, self.deteriorationLevel + 0.1)
            for terrain, original in self.textures.items():
                try:
                    if terrain == "dirt":
                        self.deterioratedTextures[terrain] = self.deteriorateDirt(original, self.deteriorationLevel)
                    elif terrain == "water":
                        self.deterioratedTextures[terrain] = self.deteriorateWater(original, self.deteriorationLevel)
                    elif terrain == "tall_grass":
                        self.deterioratedTextures[terrain] = self.deteriorateTallGrass(original, self.deteriorationLevel)
                    elif terrain == "path_rocks":
                        self.deterioratedTextures[terrain] = self.deterioratePathRocks(original, self.deteriorationLevel)
                except Exception as e:
                    print(f"Failed to update {terrain}: {e}")
            self.cache.clear()

    def deteriorateDirt(self, image, level):
        modified = image.copy()
        contrastFactor = 1 + (0.2 * level)
        enhancer = ImageEnhance.Contrast(modified)
        modified = enhancer.enhance(contrastFactor)
        brightnessFactor = 1 - (0.3 * level)
        enhancer = ImageEnhance.Brightness(modified)
        return enhancer.enhance(brightnessFactor)

    def deteriorateWater(self, image, level):
        blurRadius = level * 2
        return image.filter(ImageFilter.GaussianBlur(radius=blurRadius))

    def deteriorateTallGrass(self, image, level):
        modified = image.copy()
        colorFactor = 1 - (0.4 * level)
        enhancer = ImageEnhance.Color(modified)
        faded = enhancer.enhance(colorFactor)
        brightnessFactor = 1 - (0.2 * level)
        enhancer = ImageEnhance.Brightness(faded)
        return enhancer.enhance(brightnessFactor)

    def deterioratePathRocks(self, image, level):
        modified = image.copy()
        brightnessFactor = 1 - (0.4 * level)
        enhancer = ImageEnhance.Brightness(modified)
        darkened = enhancer.enhance(brightnessFactor)
        if level > 0.5:
            return darkened.filter(ImageFilter.SMOOTH_MORE)
        return darkened

    def drawTexture(self, terrainType, width, height):
        if terrainType not in self.deterioratedTextures:
            print(f"Error: Unknown terrain type '{terrainType}'")
            return None
        cacheKey = (terrainType, width, height, self.deteriorationLevel)
        if cacheKey not in self.cache:
            try:
                currentImage = self.deterioratedTextures[terrainType]
                resized = currentImage.resize((width, height), Image.LANCZOS)
                self.cache[cacheKey] = CMUImage(resized)
            except Exception as e:
                print(f"Failed to create texture for terrain '{terrainType}': {e}")
                return None
        return self.cache[cacheKey]

    def clearCache(self):
        self.cache.clear()
