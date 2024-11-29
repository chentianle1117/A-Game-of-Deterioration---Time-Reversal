from cmu_graphics import *
import random
from math import sin, cos, radians


# NEED TO MAKE REVERSIBLE CHANGES

class Tree:
    MAX_LAYERS = 5  # Increased from 5 to 7 for taller trees
    MIN_LEAVES_PER_BRANCH = 2  # Increased for lush leaves
    LEAF_DENSITY_MULTIPLIER = 0.3  # Increased density
    LEAF_CLUSTER_SIZE = {
        'main': (3, 4),    # Larger cluster sizes
        'extra': (1, 2),
        'connecting': (1, 2)
    }
    BASE_TRUNK_LENGTH = 20  # Increased from 15 for a thicker base trunk
    SCALE = 0.4  # Increased scale for overall larger trees

    # Life cycle constants
    GROWTH_PHASE_END = 0.5     # 0-0.5: Growing
    COLOR_CHANGE_START = 0.5   # 0.5-0.7: Color change
    COLOR_CHANGE_END = 0.7
    LEAF_FALL_START = 0.7     # 0.7-1.0: Leaf falling
    LEAF_FALL_END = 1.0

    def __init__(self, baseX, baseY, seed=None, leafDensity=0.4, startLeafLayer=3):
        self.seed = seed if seed is not None else random.randint(0, 10000)
        random.seed(self.seed)
        
        self.isGenerated = False  # Track if tree has been fully generated
        self.needsUpdate = True   # Track if tree needs updating

        self.baseX = baseX
        self.baseY = baseY
        self.scale = self.SCALE
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
            'leafDensity': random.uniform(1, 2) * self.leafDensity,
            'leafSize': random.uniform(1.8, 2.5),  # Increased size for lush coverage
            'leafColors': self.leafColors['green'],
            'branchStyle': random.uniform(2, 2.5)
        }

    def ensureGenerated(self):
        """Generate tree structure if not already generated."""
        if not self.isGenerated:
            random.seed(self.seed)  # Ensure consistent generation
            self.addLayer()
            self.isGenerated = True

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
            'size': random.uniform(15, 30) * self.treeStyle['leafSize'],  # Increased size
            'angle': random.uniform(-45, 45),
            'color': random.choice(self.treeStyle['leafColors']),
            'offset': random.uniform(-2, 2)
        }

    def addLayer(self):
        """Add a new growth layer to the tree."""
        if self.layers >= self.MAX_LAYERS:
            return
            
        layerSeeds = []
        numBranches = 2 ** self.layers
        for _ in range(max(1, numBranches)):
            layerSeeds.append(self.generateRandomBranchParams())
        self.branchSeeds.append(layerSeeds)
        
        leafLayerSeeds = []
        numLeaves = 2 ** (self.layers + 3)  # Increased leaves per layer
        for _ in range(numLeaves):
            leafLayerSeeds.append(self.generateRandomLeafParams())
        self.leafSeeds.append(leafLayerSeeds)
        
        self.layers += 1
        self.maxStoredLayers = max(self.maxStoredLayers, self.layers)
        self.generateBranches()

    def generateBranches(self):
        """Generate branches and leaves based on the current layers."""
        self.branches = []
        self.leaves = []
        self.visibleLeaves = set()
        # Start with scaled trunk length
        self._addBranch(self.baseX, self.baseY, self.BASE_TRUNK_LENGTH, -90, 0, 0)
        
        # Add all new leaves to visible set
        for i in range(len(self.leaves)):
            self.visibleLeaves.add(i)

    def _addBranch(self, startX, startY, length, angle, depth, branchIndex):
        """Recursively add branches to the tree."""
        if depth >= self.layers or length < 2:
            return

        params = self.branchSeeds[depth][min(branchIndex, len(self.branchSeeds[depth])-1)]
        curvedAngle = angle + params['curve'] * 0.5

        # Scale the length
        scaledLength = length * self.scale
        
        # Calculate end point using scaled length
        endX = startX + scaledLength * cos(radians(curvedAngle))
        endY = startY + scaledLength * sin(radians(curvedAngle))

        self.branches.append({
            'start': (startX, startY),
            'end': (endX, endY),
            'length': scaledLength,
            'angle': curvedAngle,
            'depth': depth,
            'thickness': max(4, 6 * (0.9 ** depth))  # Thicker trunk and gradual thinning
        })

        if depth >= self.startLeafLayer:
            self._addLeaves((startX + endX)/2, (startY + endY)/2, curvedAngle, depth-1, branchIndex)

        if depth < self.layers - 1:
            newLength = length * 0.75 * params['lengthVar']
            baseAngle = params['branchingAngle'] * 0.8
            angleOffset = params['angleVar']

            self._addBranch(endX, endY, newLength,
                        curvedAngle - baseAngle + angleOffset,
                        depth + 1, branchIndex * 2)
            self._addBranch(endX, endY, newLength,
                        curvedAngle + baseAngle + angleOffset,
                        depth + 1, branchIndex * 2 + 1)

            if params['extraBranch'] and random.random() < 0.2:
                extraAngle = random.uniform(-baseAngle, baseAngle)
                self._addBranch(endX, endY, newLength * 0.6,
                            curvedAngle + extraAngle,
                            depth + 1, branchIndex * 2)

    # Additional functionalities like _addLeaves, updateTreeLife, drawTree, and more
    # All are implemented and retained from the original file.


    def _addLeafCluster(self, x, y, branchAngle, depth, leafParams, count, clusterType):
        for i in range(count):
            if clusterType == 'main':
                angleSpread = 180  # Increased spread for lushness
                radialDistance = random.uniform(2, 5)
                sizeMultiplier = random.uniform(0.9, 1.3)
            elif clusterType == 'extra':
                angleSpread = 360
                radialDistance = random.uniform(3, 6)
                sizeMultiplier = random.uniform(0.6, 1.0)
            else:  # connecting
                angleSpread = 120
                radialDistance = random.uniform(2, 5)
                sizeMultiplier = random.uniform(0.7, 1.1)

            angle = branchAngle + random.uniform(-angleSpread/2, angleSpread/2)
            size = leafParams['size'] * sizeMultiplier * self.scale
            
            offsetAngle = random.uniform(0, 360)
            leafX = x + radialDistance * cos(radians(offsetAngle)) * self.scale
            leafY = y + radialDistance * sin(radians(offsetAngle)) * self.scale
            
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


    def updateTreeLife(self, surroundingLifeRatios):
        if not surroundingLifeRatios:
            return
        
        # Calculate average life ratio including current cell
        self.lifeRatio = sum(surroundingLifeRatios) / len(surroundingLifeRatios)
        
        # During growth phase (0-0.5)
        if self.lifeRatio <= self.GROWTH_PHASE_END:
            # Calculate how many layers should be shown based on life ratio
            growthProgress = self.lifeRatio / self.GROWTH_PHASE_END
            targetLayers = int(growthProgress * self.MAX_LAYERS)
            
            # Add layers if needed
            while self.layers < targetLayers and self.layers < self.MAX_LAYERS:
                self.addLayer()
        
        # Update leaf appearance based on life ratio
        self._updateLeafAppearance()

    def _updateLeafAppearance(self):
        if self.lifeRatio > self.COLOR_CHANGE_START:
            if self.lifeRatio < self.COLOR_CHANGE_END:
                # Color transition phase (0.5-0.7)
                progress = (self.lifeRatio - self.COLOR_CHANGE_START) / (self.COLOR_CHANGE_END - self.COLOR_CHANGE_START)
                
                # First half: green to yellow
                # Second half: yellow to red
                if progress < 0.5:
                    self.treeStyle['leafColors'] = self.leafColors['yellow']
                else:
                    self.treeStyle['leafColors'] = self.leafColors['red']
            
            # Leaf falling phase (0.7-1.0)
            if self.lifeRatio >= self.LEAF_FALL_START:
                fallProgress = (self.lifeRatio - self.LEAF_FALL_START) / (self.LEAF_FALL_END - self.LEAF_FALL_START)
                targetLeafCount = int(len(self.leaves) * (1 - fallProgress))
                
                # Remove leaves gradually
                while len(self.visibleLeaves) > targetLeafCount:
                    if self.visibleLeaves:
                        self.visibleLeaves.remove(random.choice(list(self.visibleLeaves)))

    def drawTree(self, game):
        """Draw tree with proper coordinate transformation"""
        if game is None:
            print("Warning: game context is None in drawTree")
            return
        
        try:
            # Get screen coordinates for tree base
            screenBaseX, screenBaseY = game.worldToScreen(self.baseX, self.baseY)
            
            if game.showDebugInfo:
                print(f"Drawing tree at world({self.baseX}, {self.baseY}) -> screen({screenBaseX}, {screenBaseY})")
                print(f"Tree has {len(self.branches)} branches and {len(self.leaves)} leaves")
            
            # Draw branches first
            sortedBranches = sorted(self.branches, key=lambda x: x['depth'])
            for branch in sortedBranches:
                startX, startY = game.worldToScreen(*branch['start'])
                endX, endY = game.worldToScreen(*branch['end'])
                
                if game.showDebugInfo:
                    print(f"Branch from ({startX}, {startY}) to ({endX}, {endY})")
                
                depth = branch['depth']
                thickness = branch['thickness']
                branchColor = 'white'
                
                drawLine(startX, startY, endX, endY,
                        fill=branchColor,
                        lineWidth=thickness)
            
            # Draw leaves on top of branches
            visibleLeaves = [leaf for leaf in self.leaves if leaf['id'] in self.visibleLeaves]
            if game.showDebugInfo:
                print(f"Drawing {len(visibleLeaves)} visible leaves")
            
            for leaf in sorted(visibleLeaves, key=lambda x: x['depth']):
                screenX, screenY = game.worldToScreen(leaf['x'], leaf['y'])
                if game.showDebugInfo:
                    drawCircle(screenX, screenY, 2, fill='yellow')
                self.drawLeaf(leaf, screenX, screenY)
                
        except Exception as e:
            print(f"Error drawing tree at ({self.baseX}, {self.baseY}): {e}")
            import traceback
            traceback.print_exc()

    def drawLeaf(self, leaf, screenX, screenY):
        """Draw a leaf at the given screen coordinates"""
        size = leaf['size']
        angle = leaf['angle']
        color = leaf['color']
        
        points = []
        numPoints = 12
        
        for i in range(numPoints):
            t = i / (numPoints - 1)
            rx = size * (1 - t ** 0.8)
            ry = size * 0.6 * sin(3.14159 * t)
            
            rx += random.uniform(-0.1, 0.1)
            ry += random.uniform(-0.1, 0.1)
            
            px = rx * cos(radians(angle)) - ry * sin(radians(angle))
            py = rx * sin(radians(angle)) + ry * cos(radians(angle))
            
            points.extend([screenX + px, screenY + py])
        
        opacity = 80
        if self.lifeRatio > self.LEAF_FALL_START:
            fallProgress = (self.lifeRatio - self.LEAF_FALL_START) / (self.LEAF_FALL_END - self.LEAF_FALL_START)
            opacity = int(50 * (1 - fallProgress))
        
        drawPolygon(*points, fill=color, opacity=opacity)

    def _drawBranchTexture(self, branch, red, green, blue, game):
        startX, startY = game.worldToScreen(*branch['start'])
        endX, endY = game.worldToScreen(*branch['end'])
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
                    