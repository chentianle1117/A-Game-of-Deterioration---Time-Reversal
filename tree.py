from cmu_graphics import *
import random
from math import sin, cos, radians

class Tree:
    MAX_LAYERS = 7
    MIN_LEAVES_PER_BRANCH = 1
    LEAF_DENSITY_MULTIPLIER = 0.5
    LEAF_CLUSTER_SIZE = {
        'main': (2, 3),
        'extra': (1, 2),
        'connecting': (1, 2)
    }
    GROWTH_PHASE_END = 0.5
    COLOR_CHANGE_START = 0.5
    COLOR_CHANGE_END = 0.7
    LEAF_FALL_START = 0.7
    LEAF_FALL_END = 1.0

    def __init__(self, baseX, baseY, seed=None, leafDensity=1.0, startLeafLayer=2):
        self.seed = seed if seed is not None else random.randint(0, 10000)
        random.seed(self.seed)
        
        self.baseX = baseX
        self.baseY = baseY
        self.layers = 0
        self.branches = []
        self.leaves = []
        self.branchSeeds = []
        self.leafSeeds = []
        self.maxStoredLayers = 0
        
        self.leafDensity = leafDensity * self.LEAF_DENSITY_MULTIPLIER
        self.startLeafLayer = startLeafLayer
        
        self.lifeRatio = 0.0
        self.targetLayers = 0
        self.visibleLeaves = set()
        
        self.leafColors = {
            'green': ['forestGreen', 'green', 'darkGreen'],
            'yellow': ['gold', 'yellow', 'darkGoldenrod'],
            'red': ['crimson', 'red', 'darkRed']
        }
        
        self.treeStyle = {
            'leafDensity': random.uniform(0.8, 1.2) * self.leafDensity,
            'leafSize': random.uniform(0.8, 1.2),
            'leafColors': self.leafColors['green'],
            'branchStyle': random.uniform(0.9, 1.1)
        }
        
        self.addLayer()  # Add initial layer

    def updateTreeLife(self, surroundingLifeRatios):
        if not surroundingLifeRatios:
            return
        
        # Calculate average life ratio of surrounding cells
        avgLifeRatio = sum(surroundingLifeRatios) / len(surroundingLifeRatios)
        # Smooth the transition
        self.lifeRatio = self.lifeRatio * 0.95 + avgLifeRatio * 0.05
        
        # Calculate target layers based on growth phase
        if self.lifeRatio <= self.GROWTH_PHASE_END:
            growthProgress = self.lifeRatio / self.GROWTH_PHASE_END
            self.targetLayers = max(1, min(self.MAX_LAYERS, 
                                        int(growthProgress * self.MAX_LAYERS)))
            
            # Update actual layers if needed
            if self.layers < self.targetLayers:
                self.addLayer()
        
        # Update leaf colors and visibility
        self._updateLeafAppearance()

    def _updateLeafAppearance(self):
        """Update leaf colors and visibility based on life ratio"""
        if self.lifeRatio > self.COLOR_CHANGE_START:
            # Calculate color transition
            if self.lifeRatio < self.COLOR_CHANGE_END:
                progress = (self.lifeRatio - self.COLOR_CHANGE_START) / (self.COLOR_CHANGE_END - self.COLOR_CHANGE_START)
                if progress < 0.5:
                    self.treeStyle['leafColors'] = self.leafColors['yellow']
                else:
                    self.treeStyle['leafColors'] = self.leafColors['red']
            
            # Handle leaf falling
            if self.lifeRatio >= self.LEAF_FALL_START:
                fallProgress = (self.lifeRatio - self.LEAF_FALL_START) / (self.LEAF_FALL_END - self.LEAF_FALL_START)
                targetLeafCount = int(len(self.leaves) * (1 - fallProgress))
                
                while len(self.visibleLeaves) > targetLeafCount:
                    if self.visibleLeaves:
                        self.visibleLeaves.remove(random.choice(list(self.visibleLeaves)))

    def generateRandomBranchParams(self):
        return {
            'angleVar': random.uniform(-15, 15) * self.treeStyle['branchStyle'],
            'lengthVar': random.uniform(0.85, 1.15),
            'branchingAngle': random.uniform(20, 35) * self.treeStyle['branchStyle'],
            'curve': random.uniform(-15, 15),
            'extraBranch': random.random() < 0.3
        }

    def generateRandomLeafParams(self):
        return {
            'size': random.uniform(20, 40) * self.treeStyle['leafSize'],
            'angle': random.uniform(-45, 45),
            'color': random.choice(self.treeStyle['leafColors']),
            'offset': random.uniform(-8, 8)
        }

    def addLayer(self):
        if self.layers >= self.MAX_LAYERS:
            return
            
        layerSeeds = []
        numBranches = 2 ** self.layers
        for _ in range(max(1, numBranches)):
            layerSeeds.append(self.generateRandomBranchParams())
        self.branchSeeds.append(layerSeeds)
        
        leafLayerSeeds = []
        numLeaves = 2 ** (self.layers + 2)
        for _ in range(numLeaves):
            leafLayerSeeds.append(self.generateRandomLeafParams())
        self.leafSeeds.append(leafLayerSeeds)
        
        self.layers += 1
        self.maxStoredLayers = max(self.maxStoredLayers, self.layers)
        self.generateBranches()

    def generateBranches(self):
        self.branches = []
        self.leaves = []
        self.visibleLeaves = set()
        self._addBranch(self.baseX, self.baseY, 100, -90, 0, 0)
        
        # Add all new leaves to visible set
        for i in range(len(self.leaves)):
            self.visibleLeaves.add(i)

    def _addBranch(self, startX, startY, length, angle, depth, branchIndex):
        if depth >= self.layers or length < 5:
            return

        params = self.branchSeeds[depth][min(branchIndex, len(self.branchSeeds[depth])-1)]
        curvedAngle = angle + params['curve']

        endX = startX + length * cos(radians(curvedAngle))
        endY = startY + length * sin(radians(curvedAngle))

        self.branches.append({
            'start': (startX, startY),
            'end': (endX, endY),
            'length': length,
            'angle': curvedAngle,
            'depth': depth,
            'thickness': max(1, min(12, 10 - depth))
        })

        if depth >= self.startLeafLayer:
            self._addLeaves((startX + endX)/2, (startY + endY)/2, curvedAngle, depth-1, branchIndex)

        if depth < self.layers - 1:
            newLength = length * 0.75 * params['lengthVar']
            baseAngle = params['branchingAngle']
            angleOffset = params['angleVar']

            if depth >= self.startLeafLayer:
                self._addLeaves(endX, endY, curvedAngle, depth, branchIndex)

            self._addBranch(endX, endY, newLength,
                          curvedAngle - baseAngle + angleOffset,
                          depth + 1, branchIndex * 2)
            self._addBranch(endX, endY, newLength,
                          curvedAngle + baseAngle + angleOffset,
                          depth + 1, branchIndex * 2 + 1)

            if params['extraBranch']:
                extraAngle = random.uniform(-baseAngle, baseAngle)
                self._addBranch(endX, endY, newLength * 0.7,
                              curvedAngle + extraAngle,
                              depth + 1, branchIndex * 2)

    def _addLeaves(self, x, y, branchAngle, depth, branchIndex):
        if depth >= len(self.leafSeeds):
            return
            
        leafParams = self.leafSeeds[depth][min(branchIndex, len(self.leafSeeds[depth])-1)]
        
        min_main = max(self.MIN_LEAVES_PER_BRANCH,
                      int(random.randint(*self.LEAF_CLUSTER_SIZE['main']) * 
                          self.treeStyle['leafDensity']))
        min_extra = max(self.MIN_LEAVES_PER_BRANCH // 2,
                       int(random.randint(*self.LEAF_CLUSTER_SIZE['extra']) * 
                           self.treeStyle['leafDensity']))

        self._addLeafCluster(x, y, branchAngle, depth, leafParams, min_main, 'main')
        self._addLeafCluster(x, y, branchAngle, depth, leafParams, min_extra, 'extra')
        self._addLeafCluster(x, y, branchAngle, depth, leafParams, 
                            int(min_extra * 0.5), 'connecting')

    def _addLeafCluster(self, x, y, branchAngle, depth, leafParams, count, clusterType):
        for i in range(count):
            if clusterType == 'main':
                angleSpread = 120
                radialDistance = random.uniform(1, 6) if i < count//2 else random.uniform(4, 10)
                sizeMultiplier = random.uniform(0.8, 1.2)
            elif clusterType == 'extra':
                angleSpread = 360
                radialDistance = random.uniform(8, 15)
                sizeMultiplier = random.uniform(0.4, 0.8)
            else:  # connecting
                angleSpread = 90
                radialDistance = random.uniform(5, 15)
                sizeMultiplier = random.uniform(0.6, 0.9)

            angle = branchAngle + random.uniform(-angleSpread/2, angleSpread/2)
            size = leafParams['size'] * sizeMultiplier
            
            offsetAngle = random.uniform(0, 360)
            leafX = x + radialDistance * cos(radians(offsetAngle))
            leafY = y + radialDistance * sin(radians(offsetAngle))
            
            leafX += random.uniform(-2, 2)
            leafY += random.uniform(-2, 2)
            
            leaf = {
                'x': leafX,
                'y': leafY,
                'size': size,
                'angle': angle,
                'color': random.choice(self.treeStyle['leafColors']),
                'depth': depth,
                'id': len(self.leaves)
            }
            self.leaves.append(leaf)

    def drawTree(self, context):
        sortedBranches = sorted(self.branches, key=lambda x: x['depth'])
        
        for branch in sortedBranches:
            startX, startY = branch['start']
            endX, endY = branch['end']
            depth = branch['depth']
            thickness = branch['thickness']
            
            baseColor = 139 - (depth * 8)
            red = baseColor
            green = baseColor//2
            blue = baseColor//4
            branchColor = rgb(red, green, blue)
            
            drawLine(startX, startY, endX, endY,
                    fill=branchColor,
                    lineWidth=thickness)
            
            if thickness > 3:
                self._drawBranchTexture(branch, red, green, blue)
        
        sortedLeaves = sorted([leaf for leaf in self.leaves if leaf['id'] in self.visibleLeaves],
                            key=lambda x: x['depth'])
        for leaf in sortedLeaves:
            self.drawLeaf(leaf)

    def drawLeaf(self, leaf):
        x, y = leaf['x'], leaf['y']
        size = leaf['size']
        angle = leaf['angle']
        color = leaf['color']
        
        points = []
        numPoints = 12
        
        for i in range(numPoints):
            t = i / (numPoints - 1)
            rx = size * (1 - t ** 0.8)
            ry = size * 0.4 * sin(3.14159 * t)
            
            rx += random.uniform(-0.3, 0.3)
            ry += random.uniform(-0.3, 0.3)
            
            px = rx * cos(radians(angle)) - ry * sin(radians(angle))
            py = rx * sin(radians(angle)) + ry * cos(radians(angle))
            
            points.extend([x + px, y + py])
        
        opacity = 50
        if self.lifeRatio > self.LEAF_FALL_START:
            fallProgress = (self.lifeRatio - self.LEAF_FALL_START) / (self.LEAF_FALL_END - self.LEAF_FALL_START)
            opacity = int(50 * (1 - fallProgress))
        
        drawPolygon(*points, fill=color, opacity=opacity)

    def _drawBranchTexture(self, branch, red, green, blue):
        startX, startY = branch['start']
        endX, endY = branch['end']
        thickness = branch['thickness']
        
        midX = (startX + endX) / 2
        midY = (startY + endY) / 2
        perpAngle = branch['angle'] + 90
        textureLength = thickness / 2
        
        textureColor = rgb(max(0, red-20), max(0, green-20), max(0, blue-20))
        
        for _ in range(2):
            offsetX = random.uniform(-thickness, thickness)
            offsetY = random.uniform(-thickness, thickness)
            texX = midX + offsetX
            texY = midY + offsetY
            
            endTexX = texX + textureLength * cos(radians(perpAngle))
            endTexY = texY + textureLength * sin(radians(perpAngle))
            
            drawLine(texX, texY, endTexX, endTexY,
                    fill=textureColor,
                    lineWidth=1)