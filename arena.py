'''
BSD 3-Clause License

Copyright (c) 2021, Logan Bier.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

from direct.showbase.ShowBase import ShowBase
from direct.stdpy import threading2
from panda3d.core import load_prc_file_data
from panda3d.core import PointLight
from panda3d.core import BitMask32
from panda3d.core import Shader, ShaderAttrib
from panda3d.core import TransformState
from panda3d.core import Spotlight
from panda3d.core import PerspectiveLens
import sys
import random
import time
from panda3d.core import LPoint3f, Point3, Vec3, LVecBase3f, VBase4
from panda3d.core import WindowProperties
from direct.showbase.DirectObject import DirectObject
from direct.interval.IntervalGlobal import *
# gui imports
from direct.gui.DirectGui import *
from panda3d.core import TextNode
# new pbr imports
import simplepbr
import gltf
# local imports
import actorData


class app(ShowBase):
    def __init__(self):
        load_prc_file_data("", """
            win-size 1680 1050
            window-title Panda3D Arena Sample FPS Bullet Auto Colliders PBR HW Skinning
            show-frame-rate-meter #t
            framebuffer-srgb #t
            view-frustum-cull 0
            textures-power-2 none
            gl-depth-zero-to-one true
            interpolate-frames 1
            clock-frame-rate 60
            hardware-animated-vertices #t
            fullscreen #f
        """)

        # Initialize the showbase
        super().__init__()
        pipeline = simplepbr.init()
        pipeline.enable_shadows = True
        gltf.patch_loader(self.loader)
        
        props = WindowProperties()
        props.setMouseMode(WindowProperties.M_relative)
        base.win.requestProperties(props)
        
        self.camLens.set_fov(80)
        self.camLens.set_near_far(0.01, 90000)
        self.camLens.setFocalLength(7)
        # self.camera.setPos(0, 0, 2)

        # plight generator
        for x in range(0, 4):
            plight_1 = PointLight('plight')
            # add plight props here
            plight_1_node = self.render.attachNewNode(plight_1)
            # group the lights close to each other to create a sun effect
            plight_1_node.setPos(random.uniform(-20, -21), random.uniform(-20, -21), random.uniform(20, 21))
            self.render.setLight(plight_1_node)

        self.accept("f3", self.toggleWireframe)
        self.accept("escape", sys.exit, [0])

        self.camLens.set_fov(85)
        self.camLens.setFocalLength(7)

        self.game_start = 0
        
        from panda3d.bullet import BulletWorld
        from panda3d.bullet import BulletCharacterControllerNode
        from panda3d.bullet import ZUp
        from panda3d.bullet import BulletCapsuleShape
        from panda3d.bullet import BulletConvexHullShape
        from panda3d.bullet import BulletTriangleMesh
        from panda3d.bullet import BulletTriangleMeshShape
        from panda3d.bullet import BulletBoxShape
        from panda3d.bullet import BulletGhostNode
        from panda3d.bullet import BulletRigidBodyNode

        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        
        arena_1 = self.loader.loadModel('models/arena_1.gltf')
        arena_1.reparentTo(self.render)
        arena_1.setPos(0, 0, 0)
        
        def make_collision_from_model(input_model, node_number, mass, world, target_pos):
            # tristrip generation from static models
            # generic tri-strip collision generator begins
            geom_nodes = input_model.findAllMatches('**/+GeomNode')
            geom_nodes = geom_nodes.getPath(node_number).node()
            # print(geom_nodes)
            geom_target = geom_nodes.getGeom(0)
            # print(geom_target)
            output_bullet_mesh = BulletTriangleMesh()
            output_bullet_mesh.addGeom(geom_target)
            tri_shape = BulletTriangleMeshShape(output_bullet_mesh, dynamic=False)
            print(output_bullet_mesh)

            body = BulletRigidBodyNode('input_model_tri_mesh')
            np = self.render.attachNewNode(body)
            np.node().addShape(tri_shape)
            np.node().setMass(mass)
            np.node().setFriction(0.01)
            np.setPos(target_pos)
            np.setScale(1)
            # np.setH(180)
            # np.setR(180)
            # np.setP(180)
            np.setCollideMask(BitMask32.allOn())
            world.attachRigidBody(np.node())
        
        make_collision_from_model(arena_1, 0, 0, self.world, (arena_1.getPos()))

        # prototype hardware shader for Actor nodes
        actor_shader = Shader.load(Shader.SL_GLSL, "shaders/simplepbr_vert_mod_1.vert", "shaders/simplepbr_frag_mod_1.frag")
        actor_shader = ShaderAttrib.make(actor_shader)
        actor_shader = actor_shader.setFlag(ShaderAttrib.F_hardware_skinning, True)

        # initialize player character physics the Bullet way
        shape1 = BulletCapsuleShape(0.1, 0.5, ZUp)
        playerNode = BulletCharacterControllerNode(shape1, 50, 'Player')  # (shape, mass, player name)
        playerNP = self.render.attachNewNode(playerNode)
        playerNP.setPos(-20, -10, 30)
        playerNP.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(playerNP.node())
        # cast playerNP to self.player
        self.player = playerNP
        
        #############################################
        # reparent player character to render node
        fpCharacter = actorData.player_character
        fpCharacter.reparent_to(self.render)
        fpCharacter.setScale(1)
        # set the actor skinning hardware shader
        fpCharacter.setAttrib(actor_shader)

        self.camera.reparentTo(self.player)
        # reparent character to FPS cam
        fpCharacter.reparentTo(self.player)
        fpCharacter.setPos(0, 0, -0.4)
        # self.camera.setX(self.player, 1)
        self.camera.setY(self.player, 0.03)
        self.camera.setZ(self.player, 1.1)
        
        # player gun begins
        self.player_gun = self.loader.loadModel('models/handgun_1.gltf')
        self.player_gun.reparentTo(self.render)
        self.player_gun.reparentTo(self.camera)
        self.player_gun.setX(self.camera, 0.1)
        self.player_gun.setY(self.camera, 0.4)
        self.player_gun.setZ(self.camera, -0.1)
        
        # directly make a text node to display text
        text_1 = TextNode('text_1_node')
        text_1.setText("")
        text_1_node = aspect2d.attachNewNode(text_1)
        text_1_node.setScale(0.05)
        text_1_node.setPos(-1.4, 0, 0.92)
        # import font and set pixels per unit font quality
        nunito_font = loader.loadFont('fonts/Nunito/Nunito-Light.ttf')
        nunito_font.setPixelsPerUnit(100)
        nunito_font.setPageSize(512, 512)
        # apply font
        text_1.setFont(nunito_font)
        # small caps
        # text_1.setSmallCaps(True)

        # on-screen target dot for aiming
        target_dot = TextNode('target_dot_node')
        target_dot.setText(".")
        target_dot_node = aspect2d.attachNewNode(target_dot)
        target_dot_node.setScale(0.075)
        target_dot_node.setPos(0, 0, 0)
        # target_dot_node.hide()
        # apply font
        target_dot.setFont(nunito_font)
        target_dot.setAlign(TextNode.ACenter)
        # see the Task section for relevant dot update logic
        
        # directly make a text node to display text
        text_2 = TextNode('text_2_node')
        text_2.setText("Neutralize the NPC by shooting the head." + '\n' + "Press 'f' to activate the flashlight.")
        text_2_node = aspect2d.attachNewNode(text_2)
        text_2_node.setScale(0.04)
        text_2_node.setPos(-1.4, 0, 0.8)
        # import font and set pixels per unit font quality
        nunito_font = loader.loadFont('fonts/Nunito/Nunito-Light.ttf')
        nunito_font.setPixelsPerUnit(100)
        nunito_font.setPageSize(512, 512)
        # apply font
        text_2.setFont(nunito_font)
        text_2.setTextColor(0, 0.3, 1, 1)
        
        # print player position on mouse click
        def print_player_pos():
            print(self.player.getPos())

        beep = DirectObject()
        beep.accept('mouse1', print_player_pos)

        self.flashlight_state = 0

        def toggle_flashlight():
            current_flashlight = self.render.findAllMatches("**/flashlight")

            if self.flashlight_state == 0:
                if len(current_flashlight) == 0:
                    self.slight = 0
                    self.slight = Spotlight('flashlight')
                    self.slight.setShadowCaster(True, 512, 512)
                    self.slight.setColor(VBase4(0.5, 0.6, 0.6, 1))  # slightly bluish
                    lens = PerspectiveLens()
                    lens.setNearFar(0.005, 5000)
                    self.slight.setLens(lens)
                    self.slight.setAttenuation((0.5, 0, 0.0000005))
                    self.slight = self.render.attachNewNode(self.slight)
                    self.slight.setPos(-0.1, 0.2, -0.4)
                    self.slight.reparentTo(self.camera)
                    self.flashlight_state = 1
                    self.render.setLight(self.slight)

                elif len(current_flashlight) > 0:
                    self.render.setLight(self.slight)
                    self.flashlight_state = 1

            elif self.flashlight_state > 0:
                self.render.setLightOff(self.slight)
                self.flashlight_state = 0

        beep.accept('f', toggle_flashlight)
        
        # NPC_1 load-in
        compShape2 = BulletCapsuleShape(0.05, 0.01, ZUp)
        npc_Node = BulletCharacterControllerNode(compShape2, 0.2, 'NPC_A_node')  # (shape, mass, character name)
        np = self.render.attachNewNode(npc_Node)
        np.setPos(-40, -40, 5)
        np.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(np.node())
        np.setH(random.randint(0, 180))
        npc_model_1 = actorData.NPC_1
        npc_model_1.reparentTo(np)
        # set the actor skinning hardware shader
        npc_model_1.setAttrib(actor_shader)
        # get the separate head model
        npc_1_head = self.loader.loadModel('models/npc_1_head.gltf')
        npc_1_head.reparentTo(actorData.NPC_1.getParent())
        
        # npc base animation loop
        npc_1_control = actorData.NPC_1.getAnimControl('walking')
        if not npc_1_control.isPlaying():
            actorData.NPC_1.stop()
            actorData.NPC_1.loop("walking")
            actorData.NPC_1.setPlayRate(6.0, 'walking')
        
        # create special hit areas
        # use Task section for npc collision movement logic
        # special head node size
        specialShape = BulletBoxShape(Vec3(0.1, 0.1, 0.1))
        # ghost npc node
        body = BulletGhostNode('specialNode_A')
        specialNode = self.render.attachNewNode(body)
        specialNode.node().addShape(specialShape, TransformState.makePos(Point3(0, 0, 0.4)))
        # specialNode.node().setMass(0)
        # specialNode.node().setFriction(0.5)
        specialNode.setCollideMask(BitMask32(0x0f))
        # turn on Continuous Collision Detection
        specialNode.node().setCcdMotionThreshold(0.000000007)
        specialNode.node().setCcdSweptSphereRadius(0.30)
        self.world.attachGhost(specialNode.node())
        
        # dynamic collision
        specialShape = BulletBoxShape(Vec3(0.2, 0.1, 0.6))
        # rigidbody npc node
        body = BulletRigidBodyNode('d_coll_A')
        d_coll = self.render.attachNewNode(body)
        d_coll.node().addShape(specialShape, TransformState.makePos(Point3(0, 0, 0.7)))
        # d_coll.node().setMass(0)
        d_coll.node().setFriction(0.5)
        d_coll.setCollideMask(BitMask32(0x0f))
        # turn on Continuous Collision Detection
        d_coll.node().setCcdMotionThreshold(0.000000007)
        d_coll.node().setCcdSweptSphereRadius(0.30)
        self.world.attachRigidBody(d_coll.node())
        
        # npc state variables
        self.npc_1_is_dead = False
        self.npc_1_move_increment = Vec3(0, 0, 0)
        self.gun_anim_is_playing = False
        
        # npc movement timer
        def npc_1_move_gen():
            while not self.npc_1_is_dead:
                m_incs = []
                for x in range(0, 2):
                    m_incs.append(random.uniform(0.03, 0.08))
                
                print('NPC_1 movement increments this cycle: ' + str(m_incs))
                self.npc_1_move_increment[0] = m_incs[0]
                self.npc_1_move_increment[1] = m_incs[1]
                time.sleep(3)
                self.npc_1_move_increment[0] = m_incs[0]
                self.npc_1_move_increment[1] = m_incs[1]
                time.sleep(3)
                self.npc_1_move_increment[0] = (-1 * m_incs[0]) * 2
                self.npc_1_move_increment[1] = (-1 * m_incs[1]) * 2
                time.sleep(3)
                self.npc_1_move_increment[0] = 0
                self.npc_1_move_increment[1] = 0
        
        # activate the movement timer in a dedicated thread to prevent lockup with .sleep()
        threading2._start_new_thread(npc_1_move_gen, ())
        
        def is_npc_1_shot():
            # animate the gun
            if not self.gun_anim_is_playing:
                self.gun_anim_is_playing = True
                
                def end_gun_anim(t):
                    t = t * 1
                    self.gun_anim_is_playing = False
                    
                lf_end = LerpFunc(end_gun_anim, fromData=2.5, toData=4, duration=0)
                
                gun_pos = self.player_gun.getPos()
                gun_hpr = self.player_gun.getHpr()
                gun_anim_1 = LerpPosHprInterval(self.player_gun, 0.05, (gun_pos[0] + 0.01, gun_pos[1] + 0.01, gun_pos[2] + 0.01), (gun_hpr[0], gun_hpr[1] + 10, gun_hpr[2]))
                gun_anim_2 = LerpPosHprInterval(self.player_gun, 0.1, (gun_pos), (gun_hpr))
                ga_list = Sequence()
                ga_list.append(gun_anim_1)
                ga_list.append(gun_anim_2)
                ga_list.append(lf_end)
                ga_list.start()
            
            # target dot ray test
            # get mouse data
            mouse_watch = base.mouseWatcherNode
            if mouse_watch.hasMouse():
                posMouse = base.mouseWatcherNode.getMouse()
                posFrom = Point3()
                posTo = Point3()
                base.camLens.extrude(posMouse, posFrom, posTo)
                posFrom = render.getRelativePoint(base.cam, posFrom)
                posTo = render.getRelativePoint(base.cam, posTo)
                rayTest = self.world.rayTestClosest(posFrom, posTo)
                target = rayTest.getNode()
                target_dot = self.aspect2d.findAllMatches("**/target_dot_node")

                if 'specialNode_A' in str(target):
                    # the head is hit, the npc is dead
                    self.npc_1_is_dead = True
                    text_2.setText('Congrats, you have won!')
                    npc_1_control = actorData.NPC_1.getAnimControl('walking')
                    if npc_1_control.isPlaying():
                        actorData.NPC_1.stop()
                    npc_1_control = actorData.NPC_1.getAnimControl('death')
                    if not npc_1_control.isPlaying():
                        actorData.NPC_1.play('death')
                        
                    # Bullet node removals
                    self.world.remove(target)
                    rigid_target = self.render.find('**/d_coll_A')
                    self.world.remove(rigid_target.node())
                            
        beep.accept('mouse1', is_npc_1_shot)                    
        
        # 3D player movement system begins
        self.keyMap = {"left": 0, "right": 0, "forward": 0, "backward": 0, "run": 0, "jump": 0}

        def setKey(key, value):
            self.keyMap[key] = value

        # define button map
        self.accept("a", setKey, ["left", 1])
        self.accept("a-up", setKey, ["left", 0])
        self.accept("d", setKey, ["right", 1])
        self.accept("d-up", setKey, ["right", 0])
        self.accept("w", setKey, ["forward", 1])
        self.accept("w-up", setKey, ["forward", 0])
        self.accept("s", setKey, ["backward", 1])
        self.accept("s-up", setKey, ["backward", 0])
        self.accept("shift", setKey, ["run", 1])
        self.accept("shift-up", setKey, ["run", 0])
        self.accept("space", setKey, ["jump", 1])
        self.accept("space-up", setKey, ["jump", 0])
        # disable mouse
        self.disableMouse()

        # the player movement speed
        self.movementSpeedForward = 2.5
        self.movementSpeedBackward = 2.5
        self.striveSpeed = 3
        self.ease = -10.0

        def move(Task):
            if self.game_start > 0:
                if not self.npc_1_is_dead:
                    npc_pos_1 = actorData.NPC_1.getParent().getPos()
                    # place head hit box
                    specialNode.setPos(npc_pos_1[0], npc_pos_1[1], npc_pos_1[2] + 1)
                    specialNode.setH(actorData.NPC_1.getH())
                    # dynamic collision node
                    d_coll.setPos(npc_pos_1[0], npc_pos_1[1], npc_pos_1[2])
                    d_coll.setH(actorData.NPC_1.getH())
                    # make the npc look at the player continuously
                    actorData.NPC_1.lookAt(self.player)
                    npc_1_head.lookAt(self.player)
                    m_inst = self.npc_1_move_increment
                    actorData.NPC_1.getParent().setPos(npc_pos_1[0] + m_inst[0], npc_pos_1[1] + m_inst[1], npc_pos_1[2])
                    
                if self.npc_1_is_dead:
                    npc_1_head.hide()
                
                # target dot ray test
                # turns the target dot red
                # get mouse data
                mouse_watch = base.mouseWatcherNode
                if mouse_watch.hasMouse():
                    posMouse = base.mouseWatcherNode.getMouse()
                    posFrom = Point3()
                    posTo = Point3()
                    base.camLens.extrude(posMouse, posFrom, posTo)
                    posFrom = render.getRelativePoint(base.cam, posFrom)
                    posTo = render.getRelativePoint(base.cam, posTo)
                    rayTest = self.world.rayTestClosest(posFrom, posTo)
                    target = rayTest.getNode()
                    target_dot = self.aspect2d.findAllMatches("**/target_dot_node")

                    if 'specialNode_A' in str(target):
                        # the npc is recognized, make the dot red
                        for dot in target_dot:
                            dot.node().setTextColor(0.9, 0.1, 0.1, 1)
                            
                    if 'd_coll_A' in str(target):
                        # the npc is recognized, make the dot red
                        for dot in target_dot:
                            dot.node().setTextColor(0.9, 0.1, 0.1, 1)
                    
                    if 'specialNode_A' not in str(target):
                        # no npc recognized, make the dot white
                        if 'd_coll_A' not in str(target):
                            for dot in target_dot:
                                dot.node().setTextColor(1, 1, 1, 1)
                            
                # get mouse data
                mouse_watch = base.mouseWatcherNode
                if mouse_watch.hasMouse():
                    pointer = base.win.getPointer(0)
                    mouseX = pointer.getX()
                    mouseY = pointer.getY()
                    
                # screen sizes
                window_Xcoord_halved = base.win.getXSize() // 2
                window_Ycoord_halved = base.win.getYSize() // 2
                # mouse speed
                mouseSpeedX = 0.2
                mouseSpeedY = 0.2
                # maximum and minimum pitch
                maxPitch = 90
                minPitch = -50
                # cam view target initialization
                camViewTarget = LVecBase3f()

                if base.win.movePointer(0, window_Xcoord_halved, window_Ycoord_halved):
                    p = 0

                    if mouse_watch.hasMouse():
                        # calculate the pitch of camera
                        p = camera.getP() - (mouseY - window_Ycoord_halved) * mouseSpeedY

                    # sanity checking
                    if p < minPitch:
                        p = minPitch
                    elif p > maxPitch:
                        p = maxPitch

                    if mouse_watch.hasMouse():
                        # directly set the camera pitch
                        camera.setP(p)
                        camViewTarget.setY(p)

                    # rotate the self.player's heading according to the mouse x-axis movement
                    if mouse_watch.hasMouse():
                        h = self.player.getH() - (mouseX - window_Xcoord_halved) * mouseSpeedX

                    if mouse_watch.hasMouse():
                        # sanity checking
                        if h < -360:
                            h += 360

                        elif h > 360:
                            h -= 360

                        self.player.setH(h)
                        camViewTarget.setX(h)
                        
                    # hide the gun if looking straight down
                    if p < -30:
                        self.player_gun.hide()
                    if p > -30:
                        self.player_gun.show()

                if self.keyMap["left"]:
                    self.player.setX(self.player, -self.striveSpeed * globalClock.getDt())

                if self.keyMap["right"]:
                    self.player.setX(self.player, self.striveSpeed * globalClock.getDt())

                if self.keyMap["forward"]:
                    self.player.setY(self.player, self.movementSpeedForward * globalClock.getDt())
                    
                    myAnimControl = actorData.player_character.getAnimControl('walking')
                    if not myAnimControl.isPlaying():
                        actorData.player_character.play("walking")
                        actorData.player_character.setPlayRate(4.0, 'walking')
                    
                if self.keyMap["forward"] != 1:
                    walkControl = actorData.player_character.getAnimControl('walking')
                    walkControl.stop()
                    
                if self.keyMap["backward"]:
                    self.player.setY(self.player, -self.movementSpeedBackward * globalClock.getDt())
                    '''
                    myBackControl = actorData.player_character.getAnimControl('backWalk')
                    if not myBackControl.isPlaying():
                        myBackControl.stop()
                        actorData.player_character.play('backWalk')
                        actorData.player_character.setPlayRate(-1.0, 'backWalk')
                    '''
                if self.keyMap["backward"] != 1:
                    pass
                    '''
                    walkControl = actorData.player_character.getAnimControl('backWalk')
                    walkControl.stop()
                    '''
            return Task.cont

        # infinite ground plane
        from panda3d.bullet import BulletPlaneShape
        from panda3d.bullet import BulletRigidBodyNode
        ground_plane = BulletPlaneShape(Vec3(0, 0, 1), 0)
        node = BulletRigidBodyNode('ground')
        node.addShape(ground_plane)
        node.setFriction(0.1)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, -1)
        self.world.attachRigidBody(node)

        # Bullet debugger
        from panda3d.bullet import BulletDebugNode
        debugNode = BulletDebugNode('Debug')
        debugNode.showWireframe(True)
        debugNode.showConstraints(True)
        debugNode.showBoundingBoxes(False)
        debugNode.showNormals(False)
        debugNP = self.render.attachNewNode(debugNode)
        self.world.setDebugNode(debugNP.node())

        # debug toggle function
        def toggleDebug():
            if debugNP.isHidden():
                debugNP.show()
            else:
                debugNP.hide()

        beep.accept('f1', toggleDebug)

        def update(Task):
            if self.game_start < 1:
                self.game_start = 1
            return Task.cont

        def physics_update(Task):
            dt = globalClock.getDt()
            self.world.doPhysics(dt)
            return Task.cont

        self.task_mgr.add(move)
        self.task_mgr.add(update)
        self.task_mgr.add(physics_update)

app().run()

