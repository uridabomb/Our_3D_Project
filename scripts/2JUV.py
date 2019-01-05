import bpy
import math

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


def calc_distance(x1, y1, z1, x2, y2, z2):
    vx, vy, vz = x2 - x1, y2 - y1, z2 - z1
    return math.sqrt(vx * vx + vy * vy + vz * vz)


def calc_rotation(x1, y1, z1, x2, y2, z2):
    vx, vy, vz = x2 - x1, y2 - y1, z2 - z1
    distance = math.sqrt(vx * vx + vy * vy + vz * vz)

    phi = math.atan2(vy, vx)
    theta = math.acos(vz / distance)

    return phi, theta


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


def add_ball_and_socket(z, constraint_x, constraint_y, name='_BallAndSocket', prefix='', size=1.0):
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


def create_bond(length, constraints, size=1.0, name='_Bond'):
    """
    :param length: the length of the joint
    :param constraints: itarable[Tuple] of length 3, pairs of contraint_x, constraint_y
    :param size: size of each ball-and-socket
    :param name: name of the joint
    :return: joint
    """
    z1, z2, z3 = 0, length/2, length

    constraint_x, constraint_y = constraints[0]
    lower_joint, lower_joint_objs = add_ball_and_socket(0, constraint_x, constraint_y,
                                                        name='_LowerBallAndSocket',
                                                        size=size)

    constraint_x, constraint_y = constraints[1]
    middle_joint, middle_joint_objs = add_ball_and_socket(length/2, constraint_x, constraint_y,
                                                          name='_MiddleBallAndSocket',
                                                          size=size)

    constraint_x, constraint_y = constraints[2]
    upper_joint, upper_joint_objs = add_ball_and_socket(length, constraint_x, constraint_y,
                                                        name='_UpperBallAndSocket',
                                                        size=size)

    eps = 0.01
    lower_cylinder = add_cylinder(z1+size-eps, z2-size+eps,
                                  radius=.2*size,
                                  name='_LowerCylinder',
                                  material=GOLD_MATERIAL)

    upper_cylinder = add_cylinder(z2+size-eps, z3-size+eps,
                                  radius=.2*size,
                                  name='_UpperCylinder',
                                  material=GOLD_MATERIAL)

    objs = (lower_joint, middle_joint, upper_joint, lower_cylinder, upper_cylinder)
    _, bond = groupify(name, objs)

    return bond, objs


def place_bond(obj, x1, y1, z1, x2, y2, z2):
    phi, theta = calc_rotation(x1, y1, z1, x2, y2, z2)

    obj.location = (x1, y1, z1)
    obj.rotation_euler[1] = theta
    obj.rotation_euler[2] = phi


# 2JUV
bonds = [((8.944999694824219, -3.2330000400543213, 0.10499999672174454), (9.781000137329102, 0.8730000257492065, 0.9900000095367432))]
all_constraints = [[(0.09361107001102507, 0.09681973071390952), (0.036765104309912644, 0.024223583174299002), (0.08417934608423264, 0.10170988356889787)]]

_bond, _objs = None, None
for ((x1, y1, z1), (x2, y2, z2)), _constraints in zip(bonds, all_constraints):
    length = calc_distance(x1, y1, z1, x2, y2, z2)
    _bond, _objs = create_bond(length, _constraints)
    place_bond(_bond, x1, y1, z1, x2, y2, z2)
