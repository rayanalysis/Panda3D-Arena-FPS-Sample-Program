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
from panda3d.core import load_prc_file_data, BitMask32, TransformState, ConfigVariableManager
from panda3d.core import FrameBufferProperties, AntialiasAttrib, InputDevice, Texture
import sys
import random
import time
from panda3d.core import LPoint3f, Point3, Vec3, Vec4, LVecBase3f, VBase4, LPoint2f
from panda3d.core import WindowProperties
from direct.showbase.DirectObject import DirectObject
from direct.interval.IntervalGlobal import *
# gui imports
from direct.gui.DirectGui import *
from panda3d.core import TextNode, NodePath
# new pbr imports
import complexpbr
# local imports
import actor_data
import arena_lighting


class app(ShowBase):
    def __init__(self):
        load_prc_file_data("", """
            win-size 1280 720
            window-title complexpbr Demo
            framebuffer-multisample 1
            multisamples 4
            hardware-animated-vertices #t
            cursor-hidden #t
        """)

        # initialize the showbase
        super().__init__()

        # lighting
        arena_lighting.lighting()
        arena_lighting.init_flashlight()
        self.accept('f', arena_lighting.toggle_flashlight)
        self.accept("gamepad-face_x", arena_lighting.toggle_flashlight)

        # complexpbr
        complexpbr.apply_shader(self.render, custom_dir='shaders/', shadow_boost=0.2)
        base.complexpbr_map_z = 0
        base.complexpbr_z_tracking = False
        
        for x in base.complexpbr_map.find_all_matches('**/+Camera'):
            x.node().get_lens().set_near_far(0.01, 3000)
            
        base.complexpbr_map_2 = NodePath('cuberig_2')
        base.complexpbr_map_2.reparent_to(base.render)
        base.cube_buffer_2 = base.win.make_cube_map('cubemap_2', 512, base.complexpbr_map_2)
        base.complexpbr_map_z_2 = 0
        
        def rotate_cubemap_2(task):
            base.complexpbr_map_2.set_h(base.render,base.cam.get_h(base.render))
            base.complexpbr_map_2.set_p(base.render,base.cam.get_p(base.render) + 90)
            cam_relative_pos = base.cam.get_pos(base.render)
            cam_relative_pos[2] = cam_relative_pos[2]-(2 * cam_relative_pos[2])
            base.complexpbr_map_2.set_pos(cam_relative_pos[0],cam_relative_pos[1],cam_relative_pos[2]+base.complexpbr_map_z_2)
        
            return task.cont

        def quality_mode():
            complexpbr.screenspace_init()
        
            base.screen_quad.set_shader_input("bloom_intensity", 0.25)
            base.screen_quad.set_shader_input("bloom_threshold", 0.3)
            base.screen_quad.set_shader_input("bloom_blur_width", 20)
            base.screen_quad.set_shader_input("bloom_samples", 2)
            base.screen_quad.set_shader_input('ssr_intensity', 2.0)
            base.screen_quad.set_shader_input('reflection_threshold', 1.6)  # subtracts from intensity
            base.screen_quad.set_shader_input('ssr_step', 5.75)  # helps determine reflect height
            base.screen_quad.set_shader_input('screen_ray_factor', 0.06)  # detail factor
            base.screen_quad.set_shader_input('ssr_samples', 1)  # determines total steps
            base.screen_quad.set_shader_input('ssr_depth_cutoff', 0.52)
            base.screen_quad.set_shader_input('ssr_depth_min', 0.49)
            base.screen_quad.set_shader_input('ssao_samples', 2)
            base.screen_quad.set_shader_input('hsv_r', 1.0)
            base.screen_quad.set_shader_input('hsv_g', 1.1)
            base.screen_quad.set_shader_input('hsv_b', 1.0)

            text_1.set_text("Quality Mode: On")

        self.accept_once('m', quality_mode)
        self.accept_once("gamepad-face_y", quality_mode)

        def save_screen():
            base.screenshot('arena_screen')
            
        self.accept('o', save_screen)
        
        # window props
        props = WindowProperties()
        props.set_mouse_mode(WindowProperties.M_relative)
        base.win.request_properties(props)
        base.set_background_color(0.5, 0.5, 0.8)
        
        self.camLens.set_fov(90)
        self.camLens.set_near_far(0.1, 5000)
        # ConfigVariableManager.getGlobalPtr().listVariables()

        self.accept("f3", self.toggle_wireframe)
        self.accept("escape", sys.exit, [0])
        
        self.game_start = 0
        
        # gamepad initialization
        self.gamepad = None
        devices = self.devices.get_devices(InputDevice.DeviceClass.gamepad)

        if int(str(devices)[0]) > 0:
            self.gamepad = devices[0]

        def do_nothing():
            print('Something should happen but I cannot effect it.')
            
        def gp_exit():
            sys.exit()[0]

        self.accept("gamepad-back", gp_exit)
        self.accept("gamepad-start", do_nothing)
        # self.accept("gamepad-face_x", do_nothing)
        # self.accept("gamepad-face_x-up", do_nothing)
        # self.accept("gamepad-face_a", do_nothing)
        # self.accept("gamepad-face_a-up", do_nothing)
        self.accept("gamepad-face_b", do_nothing)
        self.accept("gamepad-face_b-up", do_nothing)
        # self.accept("gamepad-face_y", do_nothing)
        # self.accept("gamepad-face_y-up", do_nothing)

        if int(str(devices)[0]) > 0:
            base.attach_input_device(self.gamepad, prefix="gamepad")
            
        self.right_trigger_val = 0.0
        self.left_trigger_val = 0.0
        # end gamepad initialization

        # begin physics environment
        from panda3d.bullet import BulletWorld
        from panda3d.bullet import BulletCharacterControllerNode
        from panda3d.bullet import ZUp
        from panda3d.bullet import BulletCapsuleShape
        from panda3d.bullet import BulletTriangleMesh
        from panda3d.bullet import BulletTriangleMeshShape
        from panda3d.bullet import BulletBoxShape, BulletSphereShape
        from panda3d.bullet import BulletGhostNode
        from panda3d.bullet import BulletRigidBodyNode
        from panda3d.bullet import BulletPlaneShape

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))
        
        arena_1 = self.loader.load_model('models/arena_1_mirror.glb')
        arena_1.reparent_to(self.render)
        arena_1.set_pos(0, 0, 0)
        # arena_1.flatten_strong()
        # we're using the secondary cubemap buffer cube_buffer_2 to render onto the floor
        # using the existing cubemaptex texture input already supplied by complexpbr
        arena_1.find('**/Plane').set_shader_input("cubemaptex", base.cube_buffer_2.get_texture())

        def make_collision_from_model(input_model, node_number, mass, world, target_pos):
            # tristrip generation from static models
            # generic tri-strip collision generator begins
            geom_nodes = input_model.find_all_matches('**/+GeomNode')
            geom_nodes = geom_nodes.get_path(node_number).node()
            # print(geom_nodes)
            geom_target = geom_nodes.get_geom(0)
            # print(geom_target)
            output_bullet_mesh = BulletTriangleMesh()
            output_bullet_mesh.add_geom(geom_target)
            tri_shape = BulletTriangleMeshShape(output_bullet_mesh, dynamic=False)
            print(output_bullet_mesh)

            body = BulletRigidBodyNode('input_model_tri_mesh')
            np = self.render.attach_new_node(body)
            np.node().add_shape(tri_shape)
            np.node().set_mass(mass)
            np.node().set_friction(0.01)
            np.set_pos(target_pos)
            np.set_scale(1)
            # np.set_h(180)
            # np.set_p(180)
            # np.set_r(180)
            np.set_collide_mask(BitMask32.allOn())
            world.attach_rigid_body(np.node())
        
        # make_collision_from_model(arena_1, 0, 0, self.world, (arena_1.get_pos()))
        arena_walls = arena_1.find('**/walls')
        # print(arena_walls)
        make_collision_from_model(arena_walls, 0, 0, self.world, (arena_1.get_pos()))

        # initialize player character physics the Bullet way
        shape_1 = BulletCapsuleShape(0.75, 0.5, ZUp)
        player_node = BulletCharacterControllerNode(shape_1, 0.1, 'Player')  # (shape, mass, player name)
        player_np = self.render.attach_new_node(player_node)
        player_np.set_pos(-20, -10, 30)
        player_np.set_collide_mask(BitMask32.allOn())
        self.world.attach_character(player_np.node())
        # cast player_np to self.player
        self.player = player_np

        # reparent player character to render node
        fp_character = actor_data.player_character
        fp_character.reparent_to(self.render)
        fp_character.set_scale(1)
        # set the complexpbr actor skinning
        complexpbr.skin(fp_character)

        self.camera.reparent_to(self.player)
        # reparent character to FPS cam
        fp_character.reparent_to(self.player)
        fp_character.set_pos(0, 0, -0.95)
        # self.camera.set_x(self.player, 1)
        self.camera.set_y(self.player, 0.03)
        self.camera.set_z(self.player, 0.5)
        
        # player gun begins
        self.player_gun = actor_data.arm_handgun
        self.player_gun.reparent_to(self.render)
        self.player_gun.reparent_to(self.camera)
        # set the complexpbr actor skinning
        complexpbr.skin(self.player_gun)
        self.player_gun.set_light_off(base.render.find('**/slight_1'))
        self.player_gun.set_x(self.camera, 0.1)
        self.player_gun.set_y(self.camera, 0.4)
        self.player_gun.set_z(self.camera, -0.1)
        self.player_gun.set_shader_input('shadow_boost', 0.1)
        
        # directly make a text node to display text
        text_1 = TextNode('text_1_node')
        text_1.set_text("Quality Mode: Off  (Press 'm' to turn on.)")
        if int(str(devices)[0]) > 0:
            text_1.set_text("Quality Mode: Off  (Press 'Y' to turn on.)")
        # text_1.set_text("Quality Mode: Off  (Press 'm' to turn on.)")
        text_1_node = self.aspect2d.attach_new_node(text_1)
        text_1_node.set_scale(0.04)
        text_1_node.set_pos(-1.4, 0, 0.92)
        # import font and set pixels per unit font quality
        nunito_font = loader.load_font('fonts/Nunito/Nunito-Light.ttf')
        nunito_font.set_pixels_per_unit(100)
        nunito_font.set_page_size(512, 512)
        # apply font
        text_1.set_font(nunito_font)
        text_1.set_shadow(0.1)

        # on-screen target dot for aiming
        target_dot = TextNode('target_dot_node')
        target_dot.set_text(".")
        target_dot_node = self.aspect2d.attach_new_node(target_dot)
        target_dot_node.set_scale(0.075)
        target_dot_node.set_pos(0, 0, 0)
        # target_dot_node.hide()
        # apply font
        target_dot.set_font(nunito_font)
        target_dot.set_align(TextNode.ACenter)
        # see the Task section for relevant dot update logic
        
        # directly make a text node to display text
        text_2 = TextNode('text_2_node')
        text_2.set_text("Neutralize the NPC by shooting the head." + '\n' +
                        "Press 'f' to toggle the flashlight." + '\n' + "Right-click to jump.")
        if int(str(devices)[0]) > 0:
            text_2.set_text("Neutralize the NPC by shooting the head." + '\n' +
                            "Press 'X' to toggle the flashlight." + '\n' + "Press 'A' to jump.")
        text_2_node = self.aspect2d.attach_new_node(text_2)
        text_2_node.set_scale(0.04)
        text_2_node.set_pos(-1.4, 0, 0.8)
        # import font and set pixels per unit font quality
        nunito_font = self.loader.load_font('fonts/Nunito/Nunito-Light.ttf')
        nunito_font.set_pixels_per_unit(100)
        nunito_font.set_page_size(512, 512)
        # apply font
        text_2.set_font(nunito_font)
        text_2.set_text_color(0.9, 0.9, 0.9, 1)
        text_2.set_shadow(0.1)
        
        # print player position on mouse click
        def print_player_pos():
            print(self.player.get_pos())
            self.player.node().do_jump()

        self.accept('mouse3', print_player_pos)
        self.accept("gamepad-face_a", print_player_pos)

        # add a few random physics spheres
        for x in range(0, 30):
            # dynamic collision
            random_vec = Vec3(1, 1, 1)
            # special_shape = BulletBoxShape(random_vec)
            special_shape = BulletSphereShape(random_vec[0])
            # rigidbody
            body = BulletRigidBodyNode('random_prisms')
            d_coll = self.render.attach_new_node(body)
            d_coll.node().add_shape(special_shape)
            d_coll.node().set_mass(15)
            d_coll.node().set_friction(50)
            d_coll.set_collide_mask(BitMask32.allOn())
            # turn on Continuous Collision Detection
            d_coll.node().set_ccd_motion_threshold(0.000000007)
            d_coll.node().set_ccd_swept_sphere_radius(0.30)
            d_coll.node().set_deactivation_enabled(False)  # prevents stopping the physics simulation
            d_coll.set_pos(random.uniform(-60, -20), random.uniform(-60, -20), random.uniform(50, 800))
            sphere_choices = ['1m_sphere_black_marble','1m_sphere_purple_metal','1m_sphere_concrete_1','1m_sphere_bright_1']
            sphere_choice = random.choice(sphere_choices)
            box_model = self.loader.load_model('models/' + sphere_choice + '.bam')
            box_model.reparent_to(self.render)
            box_model.reparent_to(d_coll)
            # box_model.set_shader_input("cubemaptex", base.cube_buffer_2.get_texture())
            # box_model.set_pos(0,0,-1)

            if sphere_choice == '1m_sphere_concrete_1':
                dis_tex = Texture()
                dis_tex.read('textures/get_file_Concrete017_2K-PNG/Concrete017_2K_Displacement.png')
                box_model.set_shader_input('displacement_map', dis_tex)
                box_model.set_shader_input('displacement_scale', 0.03)

            if sphere_choice in ['1m_sphere_black_marble','1m_sphere_concrete_1','1m_sphere_bright_1']:
                box_model.set_shader_input('shadow_boost', 0.5)
                
            if sphere_choice in ['1m_sphere_purple_metal']:
                box_model.set_shader_input('shadow_boost', 0.3)
                
            self.world.attach_rigid_body(d_coll.node())

        # NPC_1 load-in
        comp_shape_1 = BulletCapsuleShape(0.05, 0.01, ZUp)
        npc_1_node = BulletCharacterControllerNode(comp_shape_1, 0.2, 'NPC_A_node')  # (shape, mass, character name)
        np = self.render.attach_new_node(npc_1_node)
        np.set_pos(-40, -40, 5)
        np.set_collide_mask(BitMask32.allOn())
        self.world.attach_character(np.node())
        np.set_h(random.randint(0, 180))
        npc_model_1 = actor_data.NPC_1
        npc_model_1.reparent_to(np)
        # set the complexpbr actor skinning
        complexpbr.skin(npc_model_1)
        # get the separate head model
        npc_1_head = self.loader.load_model('models/npc_1_head.bam')
        npc_1_head.reparent_to(actor_data.NPC_1.get_parent())
        
        # npc base animation loop
        npc_1_control = actor_data.NPC_1.get_anim_control('walking')
        if not npc_1_control.is_playing():
            actor_data.NPC_1.stop()
            actor_data.NPC_1.loop("walking", fromFrame = 60, toFrame = 180)
            actor_data.NPC_1.set_play_rate(6.0, 'walking')
        
        # create special hit areas
        # use Task section for npc collision movement logic
        # special head node size
        special_shape = BulletBoxShape(Vec3(0.1, 0.1, 0.1))
        # ghost npc node
        body = BulletGhostNode('special_node_A')
        special_node = self.render.attach_new_node(body)
        special_node.node().add_shape(special_shape, TransformState.makePos(Point3(0, 0, 0.4)))
        # special_node.node().set_mass(0)
        # special_node.node().set_friction(0.5)
        special_node.set_collide_mask(BitMask32(0x0f))
        # turn on Continuous Collision Detection
        special_node.node().set_deactivation_enabled(False)
        special_node.node().set_ccd_motion_threshold(0.000000007)
        special_node.node().set_ccd_swept_sphere_radius(0.30)
        self.world.attach_ghost(special_node.node())
        
        # dynamic collision
        special_shape = BulletBoxShape(Vec3(0.3, 0.15, 0.6))
        # rigidbody npc node
        body = BulletRigidBodyNode('d_coll_A')
        d_coll = self.render.attach_new_node(body)
        d_coll.node().add_shape(special_shape, TransformState.makePos(Point3(0, 0, 0.7)))
        # d_coll.node().set_mass(0)
        d_coll.node().set_friction(0.5)
        d_coll.set_collide_mask(BitMask32.allOn())
        # turn on Continuous Collision Detection
        d_coll.node().set_deactivation_enabled(False)
        d_coll.node().set_ccd_motion_threshold(0.000000007)
        d_coll.node().set_ccd_swept_sphere_radius(0.30)
        self.world.attach_rigid_body(d_coll.node())
        
        # npc state variables
        self.npc_1_is_dead = False
        self.npc_1_move_increment = Vec3(0, 0, 0)
        self.gun_anim_is_playing = False
        
        # npc movement timer
        def npc_1_move_gen():
            while not self.npc_1_is_dead:
                m_incs = []
                for x in range(0, 2):
                    m_incs.append(random.uniform(2, 5))
                
                # print('NPC_1 movement increments this cycle: ' + str(m_incs))
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

        def is_npc_1_shot_seq():
            def gun_anim():
                gun_ctrl = actor_data.arm_handgun.get_anim_control('shoot')
                if not gun_ctrl.is_playing():
                    actor_data.arm_handgun.stop()
                    actor_data.arm_handgun.play("shoot")
                    actor_data.arm_handgun.set_play_rate(12.0, 'shoot')
            
            seq = Sequence()
            seq.append(Func(gun_anim))
            seq.append(Wait(0.2))
            
            # target dot ray test
            # get mouse data
            mouse_watch = base.mouseWatcherNode
            if mouse_watch.has_mouse():
                posMouse = base.mouseWatcherNode.get_mouse()
                posFrom = Point3()
                posTo = Point3()
                base.camLens.extrude(posMouse, posFrom, posTo)
                posFrom = self.render.get_relative_point(base.cam, posFrom)
                posTo = self.render.get_relative_point(base.cam, posTo)
                rayTest = self.world.ray_test_closest(posFrom, posTo)
                target = rayTest.get_node()
                target_dot = self.aspect2d.find_all_matches("**/target_dot_node")

                if 'special_node_A' in str(target):
                    def npc_cleanup():
                        # the head is hit, the npc is dead
                        self.npc_1_is_dead = True
                        text_2.set_text('Congrats, you have won!')
                        npc_1_control = actor_data.NPC_1.get_anim_control('walking')
                        if npc_1_control.is_playing():
                            actor_data.NPC_1.stop()
                        npc_1_control = actor_data.NPC_1.get_anim_control('death')
                        if not npc_1_control.is_playing():
                            actor_data.NPC_1.play('death')
                        
                        # Bullet node removals
                        self.world.remove(target)
                        rigid_target = self.render.find('**/d_coll_A')
                        self.world.remove(rigid_target.node())
                        
                    seq.append(Func(npc_cleanup))
                    seq.start()
                    
                else:
                    seq.start()
        
        self.accept('mouse1', is_npc_1_shot_seq)

        self.gamepad_npc_cleanup_bool = False
        
        def gamepad_trigger_shoot_seq():
            def gun_anim():
                gun_ctrl = actor_data.arm_handgun.get_anim_control('shoot')
                if not gun_ctrl.is_playing():
                    actor_data.arm_handgun.stop()
                    actor_data.arm_handgun.play("shoot")
                    actor_data.arm_handgun.set_play_rate(12.0, 'shoot')
            
            seq = Sequence()
            seq.append(Func(gun_anim))
            seq.append(Wait(0.2))
                
            # target dot ray test
            # get mouse data
            def gamepad_npc_test_cleanup():
                posMouse = LPoint2f(0, 0)
                posFrom = Point3()
                posTo = Point3()
                base.camLens.extrude(posMouse, posFrom, posTo)
                posFrom = self.render.get_relative_point(base.cam, posFrom)
                posTo = self.render.get_relative_point(base.cam, posTo)
                rayTest = self.world.ray_test_closest(posFrom, posTo)
                target = rayTest.get_node()
                target_dot = self.aspect2d.find_all_matches("**/target_dot_node")

                if 'special_node_A' in str(target):
                    def npc_cleanup():
                        # the head is hit, the npc is dead
                        self.npc_1_is_dead = True
                        text_2.set_text('Congrats, you have won!')
                        npc_1_control = actor_data.NPC_1.get_anim_control('walking')
                        if npc_1_control.is_playing():
                            actor_data.NPC_1.stop()
                        npc_1_control = actor_data.NPC_1.get_anim_control('death')
                        if not npc_1_control.is_playing():
                            actor_data.NPC_1.play('death')
                        
                        # Bullet node removals
                        self.world.remove(target)
                        rigid_target = self.render.find('**/d_coll_A')
                        self.world.remove(rigid_target.node())
                        
                    seq.append(Func(npc_cleanup))
                    seq.start()
                    
                else:
                    seq.start()
            
            if not self.gamepad_npc_cleanup_bool:
                gamepad_npc_test_cleanup()

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
        self.disable_mouse()

        # the player movement speed
        self.movementSpeedForward = 5
        self.movementSpeedBackward = 5
        self.dropSpeed = -0.2
        self.striveSpeed = 6
        self.static_pos_bool = False
        self.static_pos = Vec3()

        def animate_player():
            myAnimControl = actor_data.player_character.get_anim_control('walking')
            if not myAnimControl.isPlaying():
                actor_data.player_character.play("walking")
                actor_data.player_character.set_play_rate(4.0, 'walking')

        def move_npc(Task):
            if self.game_start > 0:
                if not self.npc_1_is_dead:
                    npc_pos_1 = actor_data.NPC_1.get_parent().get_pos()
                    # place head hit box
                    special_node.set_pos(npc_pos_1[0], npc_pos_1[1], npc_pos_1[2] + 1)
                    special_node.set_h(actor_data.NPC_1.get_h())
                    # dynamic collision node
                    d_coll.set_pos(npc_pos_1[0], npc_pos_1[1], npc_pos_1[2])
                    d_coll.set_h(actor_data.NPC_1.get_h())
                    # make the npc look at the player continuously
                    actor_data.NPC_1.look_at(self.player)
                    npc_1_head.look_at(self.player)
                    
                    if actor_data.NPC_1.get_p() > 3:
                        actor_data.NPC_1.set_p(3)
                        
                    if npc_1_head.get_p() > 3:
                        npc_1_head.set_p(3)

                    m_inst = self.npc_1_move_increment
                    t_inst = globalClock.get_dt()
                    actor_data.NPC_1.get_parent().set_pos(npc_pos_1[0] + (m_inst[0] * t_inst), npc_pos_1[1] + (m_inst[1] * t_inst), npc_pos_1[2])
                    
                if self.npc_1_is_dead:
                    npc_1_head.hide()
                    inst_h = actor_data.NPC_1.get_h()
                    inst_p = actor_data.NPC_1.get_p()
                    actor_data.NPC_1.set_hpr(inst_h, inst_p, 0)
                    
            return Task.cont

        def move(Task):
            if self.game_start > 0:
                # target dot ray test
                # turns the target dot red
                # get mouse data
                mouse_watch = base.mouseWatcherNode
                if mouse_watch.has_mouse():
                    posMouse = base.mouseWatcherNode.get_mouse()
                    # print(posMouse)
                    posFrom = Point3()
                    posTo = Point3()
                    base.camLens.extrude(posMouse, posFrom, posTo)
                    posFrom = self.render.get_relative_point(base.cam, posFrom)
                    posTo = self.render.get_relative_point(base.cam, posTo)
                    rayTest = self.world.ray_test_closest(posFrom, posTo)
                    target = rayTest.get_node()
                    target_dot = self.aspect2d.find_all_matches("**/target_dot_node")

                    if 'special_node_A' in str(target):
                        # the npc is recognized, make the dot red
                        for dot in target_dot:
                            dot.node().set_text_color(0.9, 0.1, 0.1, 1)
                            
                    if 'd_coll_A' in str(target):
                        # the npc is recognized, make the dot red
                        for dot in target_dot:
                            dot.node().set_text_color(0.9, 0.1, 0.1, 1)
                    
                    if 'special_node_A' not in str(target):
                        # no npc recognized, make the dot white
                        if 'd_coll_A' not in str(target):
                            for dot in target_dot:
                                dot.node().set_text_color(1, 1, 1, 1)
                                
                # get mouse data
                pointer = base.win.get_pointer(0)
                if pointer.in_window:
                    mouseX = pointer.get_x()
                    mouseY = pointer.get_y()
                    
                # screen sizes
                window_Xcoord_halved = base.win.get_x_size() // 2
                window_Ycoord_halved = base.win.get_y_size() // 2
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

                    if mouse_watch.has_mouse():
                        # calculate the pitch of camera
                        p = self.camera.get_p() - (mouseY - window_Ycoord_halved) * mouseSpeedY

                    # sanity checking
                    if p < minPitch:
                        p = minPitch
                    elif p > maxPitch:
                        p = maxPitch

                    if mouse_watch.has_mouse():
                        # directly set the camera pitch
                        self.camera.set_p(p)
                        camViewTarget.set_y(p)

                    # rotate the self.player's heading according to the mouse x-axis movement
                    if mouse_watch.has_mouse():
                        h = self.player.get_h() - (mouseX - window_Xcoord_halved) * mouseSpeedX

                    if mouse_watch.has_mouse():
                        # sanity checking
                        if h < -360:
                            h += 360

                        elif h > 360:
                            h -= 360

                        self.player.set_h(h)
                        camViewTarget.set_x(h)
                        
                    # hide the gun if looking straight down
                    if p < -30:
                        self.player_gun.hide()
                    if p > -30:
                        self.player_gun.show()

                if self.keyMap["left"]:
                    if self.static_pos_bool:
                        self.static_pos_bool = False
                        
                    self.player.set_x(self.player, -self.striveSpeed * globalClock.get_dt())
                    
                    animate_player()
                        
                if not self.keyMap["left"]:
                    if not self.static_pos_bool:
                        self.static_pos_bool = True
                        self.static_pos = self.player.get_pos()
                        
                    self.player.set_x(self.static_pos[0])
                    self.player.set_y(self.static_pos[1])
                    # self.player.set_z(self.player, self.dropSpeed * globalClock.get_dt())

                if self.keyMap["right"]:
                    if self.static_pos_bool:
                        self.static_pos_bool = False
                        
                    self.player.set_x(self.player, self.striveSpeed * globalClock.get_dt())
                    
                    animate_player()
                        
                if not self.keyMap["right"]:
                    if not self.static_pos_bool:
                        self.static_pos_bool = True
                        self.static_pos = self.player.get_pos()
                        
                    self.player.set_x(self.static_pos[0])
                    self.player.set_y(self.static_pos[1])
                    # self.player.set_z(self.player, self.dropSpeed * globalClock.get_dt())

                if self.keyMap["forward"]:
                    if self.static_pos_bool:
                        self.static_pos_bool = False
                        
                    self.player.set_y(self.player, self.movementSpeedForward * globalClock.get_dt())
                    
                    animate_player()
                    
                if self.keyMap["forward"] != 1:
                    if not self.static_pos_bool:
                        self.static_pos_bool = True
                        self.static_pos = self.player.get_pos()
                        
                    self.player.set_x(self.static_pos[0])
                    self.player.set_y(self.static_pos[1])
                    # self.player.set_z(self.player, self.dropSpeed * globalClock.get_dt())
                    
                if self.keyMap["backward"]:
                    if self.static_pos_bool:
                        self.static_pos_bool = False
                        
                    self.player.set_y(self.player, -self.movementSpeedBackward * globalClock.get_dt())
                    
                    animate_player()
                
            return Task.cont
            
        def gp_move(Task):
            if self.game_start > 0:
                def gamepad_mouse_test():
                    posMouse = LPoint2f(0, 0)
                    posFrom = Point3()
                    posTo = Point3()
                    base.camLens.extrude(posMouse, posFrom, posTo)
                    posFrom = self.render.get_relative_point(base.cam, posFrom)
                    posTo = self.render.get_relative_point(base.cam, posTo)
                    rayTest = self.world.ray_test_closest(posFrom, posTo)
                    target = rayTest.get_node()
                    target_dot = self.aspect2d.find_all_matches("**/target_dot_node")

                    if 'special_node_A' in str(target):
                        # the npc is recognized, make the dot red
                        for dot in target_dot:
                            dot.node().set_text_color(0.9, 0.1, 0.1, 1)
                            
                    if 'd_coll_A' in str(target):
                        # the npc is recognized, make the dot red
                        for dot in target_dot:
                            dot.node().set_text_color(0.9, 0.1, 0.1, 1)
                    
                    if 'special_node_A' not in str(target):
                        # no npc recognized, make the dot white
                        if 'd_coll_A' not in str(target):
                            for dot in target_dot:
                                dot.node().set_text_color(1, 1, 1, 1)
                                
                gamepad_mouse_test()
            
            dt = globalClock.get_dt()
            
            right_trigger = self.gamepad.find_axis(InputDevice.Axis.right_trigger)
            left_trigger = self.gamepad.find_axis(InputDevice.Axis.left_trigger)
            self.right_trigger_val = right_trigger.value
            self.left_trigger_val = left_trigger.value
            
            if self.right_trigger_val > 0.2:
                gamepad_trigger_shoot_seq()
            
            xy_speed = 7
            p_speed = 60
            rotate_speed = 100
                
            r_stick_right_axis = self.gamepad.find_axis(InputDevice.Axis.left_y)
            r_stick_left_axis = self.gamepad.find_axis(InputDevice.Axis.left_x)
            l_stick_right_axis = self.gamepad.find_axis(InputDevice.Axis.right_y)
            l_stick_left_axis = self.gamepad.find_axis(InputDevice.Axis.right_x)

            if abs(r_stick_right_axis.value) >= 0.15 or abs(r_stick_left_axis.value) >= 0.15:
                if self.static_pos_bool:
                    self.static_pos_bool = False

                self.player.set_h(self.player, rotate_speed * dt * -r_stick_left_axis.value)
                self.player.set_y(self.player, xy_speed * dt * r_stick_right_axis.value)
                
                animate_player()
                
            if abs(r_stick_right_axis.value) < 0.15 or abs(r_stick_left_axis.value) < 0.15:
                if not self.static_pos_bool:
                    self.static_pos_bool = True
                    self.static_pos = self.player.get_pos()
                    
                self.player.set_y(self.static_pos[1])

            # reset camera roll
            self.camera.set_r(0)
            self.player.set_r(0)
            
            min_p = -49
            max_p = 80
            
            if abs(l_stick_right_axis.value) >= 0.15 or abs(l_stick_left_axis.value) >= 0.15:
                if self.static_pos_bool:
                    self.static_pos_bool = False
                           
                if self.camera.get_p() < max_p:
                    if self.camera.get_p() > min_p:
                        self.camera.set_p(self.camera, p_speed * dt * l_stick_right_axis.value)
                    if self.camera.get_p() < min_p:
                        self.camera.set_p(self.camera, p_speed * dt * -l_stick_right_axis.value)
                        
                if self.camera.get_p() >= max_p:
                    self.camera.set_p(79)
                    
                self.player.set_x(self.player, xy_speed * dt * l_stick_left_axis.value)
                
                animate_player()
                
            if abs(l_stick_right_axis.value) < 0.15 or abs(l_stick_left_axis.value) < 0.15:
                if not self.static_pos_bool:
                    self.static_pos_bool = True
                    self.static_pos = self.player.get_pos()
                    
                self.player.set_x(self.static_pos[0])
                
            # hide the gun if looking straight down
            if self.camera.get_p() < -30:
                self.player_gun.hide()
            if self.camera.get_p() > -30:
                self.player_gun.show()

            return Task.cont

        # infinite ground plane
        # the effective world-Z limit
        ground_plane = BulletPlaneShape(Vec3(0, 0, 1), 0)
        node = BulletRigidBodyNode('ground')
        node.add_shape(ground_plane)
        node.set_friction(0.1)
        np = self.render.attach_new_node(node)
        np.set_pos(0, 0, 0)
        self.world.attach_rigid_body(node)

        # Bullet debugger
        from panda3d.bullet import BulletDebugNode
        debugNode = BulletDebugNode('Debug')
        debugNode.show_wireframe(True)
        debugNode.show_constraints(True)
        debugNode.show_bounding_boxes(False)
        debugNode.show_normals(False)
        debugNP = self.render.attach_new_node(debugNode)
        self.world.set_debug_node(debugNP.node())

        # pre-initialize death animation to smooth out win-state animation
        # playing for the first time
        npc_1_control = actor_data.NPC_1.get_anim_control('death')
        if not npc_1_control.is_playing():
            actor_data.NPC_1.play('death')

        npc_1_control = actor_data.NPC_1.get_anim_control('walking')
        if not npc_1_control.is_playing():
            actor_data.NPC_1.loop('walking')

        # debug toggle function
        def toggle_debug():
            if debugNP.is_hidden():
                debugNP.show()
            else:
                debugNP.hide()

        self.accept('f1', toggle_debug)

        def update(Task):
            if self.game_start < 1:
                self.game_start = 1

            return Task.cont

        def physics_update(Task):
            dt = globalClock.get_dt()
            self.world.do_physics(dt)

            return Task.cont
            
        if self.gamepad is None:
            self.task_mgr.add(move)
            
        if int(str(devices)[0]) > 0:
            self.task_mgr.add(gp_move)
            
        self.task_mgr.add(update)
        self.task_mgr.add(move_npc)
        self.task_mgr.add(physics_update)
        self.task_mgr.add(rotate_cubemap_2)

app().run()
