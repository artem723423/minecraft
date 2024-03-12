from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile
from panda3d.core import DirectionalLight, AmbientLight
from panda3d.core import TransparencyAttrib
from panda3d.core import WindowProperties
from panda3d.core import CollisionTraverser, CollisionNode, CollisionBox, CollisionRay, CollisionHandlerQueue
from direct.gui.OnscreenImage import OnscreenImage

loadPrcFile('settings.prc')

def degToRad(degrees):
    return degrees * (pi / 180.0)

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.selectedBlockType = 'dirt'

        self.loadModels()

        self.generateTerrain()
        self.Camera()
        self.Sky()
        self.captureMouse()
        self.Control()

        taskMgr.add(self.update, 'update')

    def update(self, task):
        dt = globalClock.getDt()

        playerMoveSpeed = 10

        x_movement = 0
        y_movement = 0
        z_movement = 0

        if self.keyMap['forward']:
            x_movement -= dt * playerMoveSpeed * sin(degToRad(camera.getH()))
            y_movement += dt * playerMoveSpeed * cos(degToRad(camera.getH()))
        if self.keyMap['backward']:
            x_movement += dt * playerMoveSpeed * sin(degToRad(camera.getH()))
            y_movement -= dt * playerMoveSpeed * cos(degToRad(camera.getH()))
        if self.keyMap['left']:
            x_movement -= dt * playerMoveSpeed * cos(degToRad(camera.getH()))
            y_movement -= dt * playerMoveSpeed * sin(degToRad(camera.getH()))
        if self.keyMap['right']:
            x_movement += dt * playerMoveSpeed * cos(degToRad(camera.getH()))
            y_movement += dt * playerMoveSpeed * sin(degToRad(camera.getH()))
        if self.keyMap['up']:
            z_movement += dt * playerMoveSpeed
        if self.keyMap['down']:
            z_movement -= dt * playerMoveSpeed

        camera.setPos(
            camera.getX() + x_movement,
            camera.getY() + y_movement,
            camera.getZ() + z_movement,
        )

        if self.cameraSwing:
            md = self.win.getPointer(0)
            mouseX = md.getX()
            mouseY = md.getY()

            mouseChangeX = mouseX - self.lastMouseX
            mouseChangeY = mouseY - self.lastMouseY

            self.cameraSwingFactor = 10

            currentH = self.camera.getH()
            currentP = self.camera.getP()

            self.camera.setHpr(
                currentH - mouseChangeX * dt * self.cameraSwingFactor,
                min(90, max(-90, currentP - mouseChangeY * dt * self.cameraSwingFactor)),
                0
            )

            self.lastMouseX = mouseX
            self.lastMouseY = mouseY

        return task.cont
    
    def Control(self):
        self.keyMap = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "up": False,
            "down": False,
        }

        self.accept('escape', self.releaseMouse)
        self.accept('mouse1', self.LeftClick)
        self.accept('mouse3', self.placeBlock)

        self.accept('w', self.updateKeyMap, ['forward', True])
        self.accept('w-up', self.updateKeyMap, ['forward', False])
        self.accept('a', self.updateKeyMap, ['left', True])
        self.accept('a-up', self.updateKeyMap, ['left', False])
        self.accept('s', self.updateKeyMap, ['backward', True])
        self.accept('s-up', self.updateKeyMap, ['backward', False])
        self.accept('d', self.updateKeyMap, ['right', True])
        self.accept('d-up', self.updateKeyMap, ['right', False])
        self.accept('space', self.updateKeyMap, ['up', True])
        self.accept('space-up', self.updateKeyMap, ['up', False])
        self.accept('lshift', self.updateKeyMap, ['down', True])
        self.accept('lshift-up', self.updateKeyMap, ['down', False])
        self.accept('1', self.SelectedBlock, ['dirt'])
        self.accept('2', self.SelectedBlock, ['sand'])
        self.accept('3', self.SelectedBlock, ['stone'])
        self.accept('4', self.SelectedBlock, ['desk'])
        self.accept('5', self.SelectedBlock, ['izumrud'])
        self.accept('6', self.SelectedBlock, ['almaz'])
        self.accept('7', self.SelectedBlock, ['gold'])
    
    def SelectedBlock(self, type):
        self.selectedBlockType = type
    
    def LeftClick(self):
        self.captureMouse()
        self.removeBlock()

    def removeBlock(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)

            hitNodePath = rayHit.getIntoNodePath()
            hitObject = hitNodePath.getPythonTag('owner')
            distanceFromPlayer = hitObject.getDistance(self.camera)

            if distanceFromPlayer < 12:
                hitNodePath.clearPythonTag('owner')
                hitObject.removeNode()

    def placeBlock(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            hitNodePath = rayHit.getIntoNodePath()
            normal = rayHit.getSurfaceNormal(hitNodePath)
            hitObject = hitNodePath.getPythonTag('owner')
            distanceFromPlayer = hitObject.getDistance(self.camera)

            if distanceFromPlayer < 14:
                hitBlockPos = hitObject.getPos()
                newBlockPos = hitBlockPos + normal * 2
                self.createNewBlock(newBlockPos.x, newBlockPos.y, newBlockPos.z, self.selectedBlockType)
    
    def updateKeyMap(self, key, value):
        self.keyMap[key] = value

    def captureMouse(self):
        self.cameraSwing = True

        md = self.win.getPointer(0)
        self.lastMouseX = md.getX()
        self.lastMouseY = md.getY()

        properties = WindowProperties()
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(properties)

    def releaseMouse(self):
        self.cameraSwing = False

        properties = WindowProperties()
        properties.setCursorHidden(False)
        properties.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(properties)

    def Camera(self):
        self.disableMouse()
        self.camera.setPos(0, 0, 3)
        self.camLens.setFov(80)

        crosshairs = OnscreenImage(
            image = 'crosshairs.png',
            pos = (0, 0, 0),
            scale = 0.05,
        )
        crosshairs.setTransparency(TransparencyAttrib.MAlpha)

        self.cTrav = CollisionTraverser()
        ray = CollisionRay()
        ray.setFromLens(self.camNode, (0, 0))
        rayNode = CollisionNode('line-of-sight')
        rayNode.addSolid(ray)
        rayNodePath = self.camera.attachNewNode(rayNode)
        self.rayQueue = CollisionHandlerQueue()
        self.cTrav.addCollider(rayNodePath, self.rayQueue)

    def Sky(self):
        skybox = loader.loadModel('sky/sky.egg')
        skybox.setScale(500)
        skybox.setBin('background', 1)
        skybox.setDepthWrite(0)
        skybox.setLightOff()
        skybox.reparentTo(render)
    
    def generateTerrain(self):
        for z in range(5):
            for y in range(30):
                for x in range(30):
                    self.createNewBlock(
                        x * 2 - 40,
                        y * 2 - 40,
                        -z * 2,
                        'dirt' if z == 0 else 'dirt'
                    )


    def createNewBlock(self, x, y, z, type):
        newBlockNode = render.attachNewNode('new-block-placeholder')
        newBlockNode.setPos(x, y, z)
        if type == 'dirt':
            self.dirtBlock.instanceTo(newBlockNode)
        elif type == 'sand':
            self.sandBlock.instanceTo(newBlockNode)
        elif type == 'stone':
            self.stoneBlock.instanceTo(newBlockNode)
        elif type == 'desk':
            self.deskBlock.instanceTo(newBlockNode)
        elif type == 'izumrud':
            self.izumrudBlock.instanceTo(newBlockNode)
        elif type == 'almaz':
            self.almazBlock.instanceTo(newBlockNode)
        elif type == 'gold':
            self.goldBlock.instanceTo(newBlockNode)

        blockSolid = CollisionBox((-1, -1, -1), (1, 1, 1))
        blockNode = CollisionNode('block-collision-node')
        blockNode.addSolid(blockSolid)
        collider = newBlockNode.attachNewNode(blockNode)
        collider.setPythonTag('owner', newBlockNode)

    def loadModels(self):
        self.dirtBlock = loader.loadModel('dirt-block.glb')
        self.stoneBlock = loader.loadModel('stone-block.glb')
        self.sandBlock = loader.loadModel('sand-block.glb')
        self.deskBlock = loader.loadModel('block_desk.glb')
        self.izumrudBlock = loader.loadModel('block_izumrud.glb')
        self.almazBlock = loader.loadModel('block_almaz.glb')
        self.goldBlock = loader.loadModel('block_gold.glb')


    
game = MyGame()
game.run()