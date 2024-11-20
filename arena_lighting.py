from panda3d.core import PointLight, Spotlight, AmbientLight, PerspectiveLens
from panda3d.core import LPoint3f, Point3, Vec3, Vec4, LVecBase3f, VBase4, LPoint2f


def lighting():
    # lighting entry point
    amb_light = AmbientLight('amblight')
    amb_light.set_color(Vec4(Vec3(1),1))
    amb_light_node = base.render.attach_new_node(amb_light)
    base.render.set_light(amb_light_node)

    slight_1 = Spotlight('slight_1')
    slight_1.set_color(Vec4(Vec3(8),1))
    slight_1.set_shadow_caster(True, 4096, 4096)
    # slight_1.set_attenuation((0.5,0,0.000005))
    lens = PerspectiveLens()
    slight_1.set_lens(lens)
    slight_1.get_lens().set_fov(120)
    slight_1_node = base.render.attach_new_node(slight_1)
    slight_1_node.set_pos(69, -49, 90)
    slight_1_node.look_at(0,0,0.5)
    base.render.set_light(slight_1_node)
    
    slight_2 = Spotlight('slight_2')
    slight_2.set_color(Vec4(Vec3(1),1))
    # slight_2.set_shadow_caster(True, 4096, 4096)
    # slight_2.set_attenuation((0.5,0,0.000005))
    lens = PerspectiveLens()
    slight_2.set_lens(lens)
    slight_2.get_lens().set_fov(40)
    slight_2_node = base.render.attach_new_node(slight_2)
    slight_2_node.set_pos(-69, -49, 90)
    slight_2_node.look_at(0,0,20)
    base.render.set_light(slight_2_node)

    env_light_1 = PointLight('env_light_1')
    env_light_1.set_color(Vec4(Vec3(6),1))
    env_light_1 = base.render.attach_new_node(env_light_1)
    env_light_1.set_pos(0,0,0)

    base_env = loader.load_model('models/daytime_skybox.bam')
    base_env.reparent_to(base.render)
    base_env.set_scale(1)
    base_env.set_pos(0,0,0)
    base_env.set_light(env_light_1)
    base_env.set_light_off(base.render.find('**/slight_1'))

def init_flashlight():
    base.slight = Spotlight('flashlight')
    # base.slight.setShadowCaster(True, 512, 512)
    base.slight.set_color(VBase4(5.5, 5.6, 5.6, 1))  # slightly bluish
    lens = PerspectiveLens()
    lens.set_near_far(0.5, 500)
    base.slight.set_lens(lens)
    base.slight.set_attenuation((0.5, 0, 0.0005))
    base.slight.get_lens().set_fov(35)
    base.slight = base.render.attach_new_node(base.slight)
    # base.render.set_light(base.slight)
    base.slight.reparent_to(base.cam)
    base.slight.set_pos(0,0.4,0.2)

def toggle_flashlight():
    if base.render.has_light(base.slight):
        base.render.set_light_off(base.slight)
    else:
        base.render.set_light(base.slight)
