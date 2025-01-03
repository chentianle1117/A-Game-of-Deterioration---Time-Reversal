from cmu_graphics import *
import random
from math import sin, cos, radians

'''
====AI Assistance Summary====
The following features were implemented with Claude 3.5's help:

1. _addBranch():
   - Recursive branch generation algorithm
   - Branch angle and length calculations
   - Extra branch probability handling

2. _addLeafCluster():
   - Leaf clustering methods
   - Radial distribution implementation
   - Size and angle variation
'''

class Tree:
    maxLayers = 4
    minLeavesPerBranch = 2
    leafDensityMultiplier = 0.3
    leafClusterSize = {
        'main': (3, 4),
        'extra': (1, 2),
        'connecting': (1, 2)
    }
    baseTrunkLength = 20
    scale = 0.4

    growthPhaseEnd = 0.5
    colorChangeStart = 0.5
    colorChangeEnd = 0.7
    leafFallStart = 0.7
    leafFallEnd = 1.0

    def __init__(self, baseX, baseY, seed=None, leafDensity=0.4, startLeafLayer=3):
        self.seed = seed if seed else random.randint(0, 10000)
        random.seed(self.seed)
        
        self.isGenerated = False
        self.needsUpdate = True
        self.baseX = baseX
        self.baseY = baseY
        self.scale = self.scale
        self.layers = 0
        self.branches = []
        self.leaves = []
        self.branchSeeds = []
        self.leafSeeds = []
        self.maxStoredLayers = 0
        
        self.leafDensity = leafDensity * self.leafDensityMultiplier
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
            'leafSize': random.uniform(1.8, 2.5),
            'leafColors': self.leafColors['green'],
            'branchStyle': random.uniform(2, 2.5)
        }

    def ensureGenerated(self):
        if not self.isGenerated:
            random.seed(self.seed)
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
            'size': random.uniform(15, 30) * self.treeStyle['leafSize'],
            'angle': random.uniform(-45, 45),
            'color': random.choice(self.treeStyle['leafColors']),
            'offset': random.uniform(-2, 2)
        }

    def addLayer(self):
        if self.layers >= self.maxLayers:
            return
            
        layerSeeds = []
        numBranches = 2 ** self.layers
        for _ in range(max(1, numBranches)):
            layerSeeds.append(self.generateRandomBranchParams())
        self.branchSeeds.append(layerSeeds)
        
        leafLayerSeeds = []
        numLeaves = 2 ** (self.layers + 3)
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
        self._addBranch(self.baseX, self.baseY, self.baseTrunkLength, -90, 0, 0)
        
        for i in range(len(self.leaves)):
            self.visibleLeaves.add(i)

    #====Recursive Tree Branch Generation:Original Code written individually but debugged by Claude 3.5 due to complexity====
    '''
    sample tree structure:
    Layer 0:     |      (trunk)
    Layer 1:    / \     (2 branches)
    Layer 2:   / \ / \  (4 branches)
    '''
    def _addBranch(self, startX, startY, length, angle, depth, branchIndex):
        if depth >= self.layers or length < 2:
            return

        params = self.branchSeeds[depth][min(branchIndex, len(self.branchSeeds[depth])-1)]
        curvedAngle = angle + params['curve'] * 0.5
        scaledLength = length * self.scale
        
        endX = startX + scaledLength * cos(radians(curvedAngle))
        endY = startY + scaledLength * sin(radians(curvedAngle))

        self.branches.append({
            'start': (startX, startY),
            'end': (endX, endY),
            'length': scaledLength,
            'angle': curvedAngle,
            'depth': depth,
            'thickness': max(4, 6 * (0.9 ** depth))
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
    #====Recursive Tree Branch Generation:Original Code written individually but debugged by Claude 3.5 due to complexity====
    
    def _addLeafCluster(self, x, y, branchAngle, depth, leafParams, count, clusterType):
        for i in range(count):
            if clusterType == 'main':
                angleSpread = 180
                radialDistance = random.uniform(2, 5)
                sizeMultiplier = random.uniform(0.9, 1.3)
            elif clusterType == 'extra':
                angleSpread = 360
                radialDistance = random.uniform(3, 6)
                sizeMultiplier = random.uniform(0.6, 1.0)
            else:
                angleSpread = 120
                radialDistance = random.uniform(2, 5)
                sizeMultiplier = random.uniform(0.7, 1.1)
            # cluster around a point
            # ===== leaf clustering methods reference from conversation with Claude 3.5 ====
            angle = branchAngle + random.uniform(-angleSpread/2, angleSpread/2)
            size = leafParams['size'] * sizeMultiplier * self.scale
            
            offsetAngle = random.uniform(0, 360)

            leafX = x + radialDistance * cos(radians(offsetAngle)) * self.scale
            leafY = y + radialDistance * sin(radians(offsetAngle)) * self.scale
            # ===== leaf clustering methods reference from conversation with Claude 3.5 ====
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
        
        minMain = max(self.minLeavesPerBranch,
                      int(random.randint(*self.leafClusterSize['main']) * 
                          self.treeStyle['leafDensity']))
        minExtra = max(self.minLeavesPerBranch // 2,
                       int(random.randint(*self.leafClusterSize['extra']) * 
                           self.treeStyle['leafDensity']))

        self._addLeafCluster(x, y, branchAngle, depth, leafParams, minMain, 'main')
        self._addLeafCluster(x, y, branchAngle, depth, leafParams, minExtra, 'extra')
        self._addLeafCluster(x, y, branchAngle, depth, leafParams, 
                            int(minExtra * 0.5), 'connecting')

    def updateTreeLife(self, surroundingLifeRatios):
        if not surroundingLifeRatios:
            return
        
        self.lifeRatio = sum(surroundingLifeRatios) / len(surroundingLifeRatios)
        
        if self.lifeRatio <= self.growthPhaseEnd:
            growthProgress = self.lifeRatio / self.growthPhaseEnd
            targetLayers = int(growthProgress * self.maxLayers)
            
            while self.layers < targetLayers and self.layers < self.maxLayers:
                self.addLayer()
        
        self._updateLeafAppearance()

    def _updateLeafAppearance(self):
        if self.lifeRatio > self.colorChangeStart:
            if self.lifeRatio < self.colorChangeEnd:
                progress = (self.lifeRatio - self.colorChangeStart) / (self.colorChangeEnd - self.colorChangeStart)
                
                if progress < 0.5:
                    self.treeStyle['leafColors'] = self.leafColors['yellow']
                else:
                    self.treeStyle['leafColors'] = self.leafColors['red']
            
            if self.lifeRatio >= self.leafFallStart:
                fallProgress = (self.lifeRatio - self.leafFallStart) / (self.leafFallEnd - self.leafFallStart)
                targetLeafCount = int(len(self.leaves) * (1 - fallProgress))
                
                while len(self.visibleLeaves) > targetLeafCount:
                    if self.visibleLeaves:
                        self.visibleLeaves.remove(random.choice(list(self.visibleLeaves)))

    def drawTree(self, game):
        if not game:
            print("Warning: game context is None in drawTree")
            return
        
        try:
            screenBaseX, screenBaseY = game.worldToScreen(self.baseX, self.baseY)
            
            if game.showDebugInfo:
                print(f"Drawing tree at world({self.baseX}, {self.baseY}) -> screen({screenBaseX}, {screenBaseY})")
                print(f"Tree has {len(self.branches)} branches and {len(self.leaves)} leaves")
            
            sortedBranches = sorted(self.branches, key=lambda x: x['depth'])
            for branch in sortedBranches:
                startX, startY = game.worldToScreen(*branch['start'])
                endX, endY = game.worldToScreen(*branch['end'])
                
                if game.showDebugInfo:
                    print(f"Branch from ({startX}, {startY}) to ({endX}, {endY})")
                
                drawLine(startX, startY, endX, endY,
                        fill='white',
                        lineWidth=branch['thickness'])
            
            visibleLeaves = [leaf for leaf in self.leaves if leaf['id'] in self.visibleLeaves]
            for leaf in sorted(visibleLeaves, key=lambda x: x['y']):
                leafX, leafY = game.worldToScreen(leaf['x'], leaf['y'])
                drawCircle(leafX, leafY, leaf['size'],
                          fill=leaf['color'],
                          rotateAngle=leaf['angle'])
                          
        except Exception as e:
            print(f"Error drawing tree: {str(e)}")
                    