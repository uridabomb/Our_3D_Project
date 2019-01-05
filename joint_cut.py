import bpy

VIOLET_MATERIAL = bpy.data.materials.new("PKHG")
VIOLET_MATERIAL.diffuse_color = (.5, 0, 1)

CYAN_MATERIAL = bpy.data.materials.new("PKHG")
CYAN_MATERIAL.diffuse_color = (1, 2, 3)

WHITE_MATERIAL = bpy.data.materials.new("PKHG")
WHITE_MATERIAL.diffuse_color = (5, 5, 5)

GOLD_MATERIAL = bpy.data.materials.new("PKHG")
GOLD_MATERIAL.diffuse_color = (3, 2, 1)

GREEN_MATERIAL = bpy.data.materials.new("PKHG")
GREEN_MATERIAL.diffuse_color = (1, 4, 2)


def groupify(named, objs):
    groups = bpy.data.groups

    # alias existing group, or generate new group and alias that
    group = groups.get(named, groups.new(named))

    for obj in objs:
        if obj.name not in group.objects:
            group.objects.link(obj)

    scene = bpy.context.scene
    group = bpy.data.groups[named]
    instance = bpy.data.objects.new(named, None)
    # instance.dupli_type = 'GROUP'
    # instance.dupli_group = group
    scene.objects.link(instance)

    for obj in objs:
        obj.parent = instance

    return group, instance


def add_cylinder(z1, z2, radius=.2, name='Cylinder', material=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius,
                                        depth=z2-z1,
                                        location=(0, 0, (z1+z2)/2))

    bpy.context.active_object.name = name
    cylinder = bpy.data.objects[name]

    if material:
        cylinder.active_material = material

    return cylinder


def add_sphere(size, location, name='Sphere', hide=False, material=None):
    bpy.ops.mesh.primitive_uv_sphere_add(size=size, location=location)
    bpy.context.active_object.name = name
    sphere = bpy.data.objects[name]

    if hide:
        sphere.hide = True
        sphere.hide_render = True

    if material:
        sphere.active_material = material

    return sphere


def add_cube(scale, location, name='Cube', hide=False):
    bpy.ops.mesh.primitive_cube_add(radius=1, location=location)
    bpy.context.active_object.name = name
    cube = bpy.data.objects[name]
    cube.scale = scale

    if hide:
        cube.hide = True
        cube.hide_render = True

    return cube


def add_difference_modifier(target, subtructor, name='Modifier'):
    modifier = target.modifiers.new(type='BOOLEAN', name=name)
    modifier.object = subtructor
    modifier.operation = 'DIFFERENCE'


def add_ball_and_socket(z, constraint_x, constraint_y, name='_BallAndSocket', size=1.0):
    size_socket = size
    size_ball = .95 * size
    size_wrapper = (size_socket + size_ball) / 2
    size_snap = .1 * size
    radius_safety = .02 * size

    socket_ball_diff = size_socket - size_ball
    socket_wrapper_diff = size_socket - size_ball
    snap_diff = (size_socket + size_ball) / 2 - 0.95 * size_snap

    z_socket = z
    z_ball = z_socket + socket_ball_diff
    z_wrapper = z_socket + socket_wrapper_diff
    y_snap = snap_diff

    ball_bottom = z_ball - size_ball
    socket_bottom = z_socket - size_socket
    z_ball_socket_middle = (ball_bottom + socket_bottom) / 2
    z1_safety = z_ball_socket_middle
    z2_safety = ball_bottom
    length_safety = z2_safety - z1_safety

    constraint_depth = 1.1 * length_safety
    constraint_scale = (constraint_x, constraint_y, constraint_depth)

    location_socket = (0, 0, z_socket)
    location_ball = (0, 0, z_ball)
    location_wrapper = (0, 0, z_wrapper)
    location_snap = (0, y_snap, 0)
    location_constraint = (0, 0, ball_bottom)

    socket = add_sphere(size_socket, location_socket, '__Socket', material=CYAN_MATERIAL)
    ball = add_sphere(size_ball, location_ball, '__Ball', material=VIOLET_MATERIAL)
    ball_wrapper = add_sphere(size_wrapper, location_wrapper, '__BallWrapper', hide=True)
    add_difference_modifier(target=socket, subtructor=ball_wrapper, name='BallWrapperModifier')
    safety = add_cylinder(z1_safety, z2_safety, radius_safety, '__Safety', material=VIOLET_MATERIAL)
    constraint = add_cube(constraint_scale, location_constraint, '__Constraint', hide=True)
    add_difference_modifier(target=socket, subtructor=constraint, name='ConstraintModifier')
    snap = add_sphere(size_snap, location_snap, '__Snap', material=VIOLET_MATERIAL)
    add_difference_modifier(target=ball, subtructor=snap, name='SnapModifier')

    objs = (socket, ball, ball_wrapper, safety, constraint, snap)
    _, ball_and_socket = groupify(name, objs)

    return ball_and_socket, objs


def cut_objs(objs):
    bpy.ops.mesh.primitive_cube_add(radius=2, location=(2, 0, 0))
    bpy.context.active_object.name = '__Cut'
    cut = bpy.data.objects['__Cut']
    cut.scale = (1, 100, 100)
    cut.hide = True
    cut.hide_render = True

    for obj in objs:
        modifier = obj.modifiers.new(type='BOOLEAN', name='CutModifier')
        modifier.object = cut
        modifier.operation = 'DIFFERENCE'


_, (socket, ball, ball_wrapper, safety, constraint, snap) = add_ball_and_socket(0, 0.04, 0.04)
cut_objs((socket, ball, safety, snap))

