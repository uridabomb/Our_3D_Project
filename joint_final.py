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


def calc_direction(x1, y1, z1, x2, y2, z2):
    vx, vy, vz = x2 - x1, y2 - y1, z2 - z1
    length = math.sqrt(vx * vx + vy * vy + vz * vz)
    return vx / length, vy / length, vz / length


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


def create_joint(length, constraint_x, constraint_y, size=1.0, cut=False):  # old...
    x1, y1, z1 = 0, 0, 0
    x2, y2, z2 = 0, 0, length
    dx, dy, dz = 0, 0, 1

    size_socket = size
    size_ball = .95 * size
    size_wrapper = (size_socket + size_ball) / 2

    size_snap = .1 * size
    snap_diff = (size_socket + size_ball) / 2 - 0.95 * size_snap

    socket_ball_diff = size_socket - size_ball
    socket_wrapper_diff = size_socket - size_ball

    # creates ball and socket
    sdx, sdy, sdz = (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2
    x_socket, y_socket, z_socket = x1 + sdx, y1 + sdy, z1 + sdz
    location_socket = (x_socket, y_socket, z_socket)

    bdx, bdy, bdz = dx * socket_ball_diff, dy * socket_ball_diff, dz * socket_ball_diff
    x_ball, y_ball, z_ball = x_socket + bdx, y_socket + bdy, z_socket + bdz
    location_ball = (x_ball, y_ball, z_ball)

    wdx, wdy, wdz = dx * socket_wrapper_diff, dy * socket_wrapper_diff, dz * socket_wrapper_diff
    x_wrapper, y_wrapper, z_wrapper = x_socket + wdx, y_socket + wdy, z_socket + wdz
    location_wrapper = (x_wrapper, y_wrapper, z_wrapper)

    bpy.ops.mesh.primitive_uv_sphere_add(size=size_socket, location=location_socket)
    bpy.context.active_object.name = '__Socket'
    socket = bpy.data.objects['__Socket']

    bpy.ops.mesh.primitive_uv_sphere_add(size=size_ball, location=location_ball)
    bpy.context.active_object.name = '__Ball'
    ball = bpy.data.objects['__Ball']

    bpy.ops.mesh.primitive_uv_sphere_add(size=size_wrapper, location=location_wrapper)
    bpy.context.active_object.name = '__BallWrapper'
    ball_wrapper = bpy.data.objects['__BallWrapper']
    ball_wrapper.hide = True
    ball_wrapper.hide_render = True

    modifier = socket.modifiers.new(type='BOOLEAN', name='BallModifier')
    modifier.object = ball_wrapper
    modifier.operation = 'DIFFERENCE'

    # ball cylinder
    radius = .2 * size

    tdx, tdy, tdz = dx * size_ball, dy * size_ball, dz * size_ball
    tx, ty, tz = x_ball + tdx, y_ball + tdy, z_ball + tdz
    top_ball_x, top_ball_y, top_ball_z = tx, ty, tz
    distance = calc_distance(tx, ty, tz, x2, y2, z2)
    x, y, z = (tx + x2) / 2, (ty + y2) / 2, (tz + z2) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=radius,
                                        depth=distance,
                                        location=(x, y, z))
    bpy.context.active_object.name = '__BallCylinder'
    ball_cylinder = bpy.data.objects['__BallCylinder']

    # socket cylinder
    radius = .2 * size

    tdx, tdy, tdz = -dx * size_socket, -dy * size_socket, -dz * size_socket
    tx, ty, tz = x_socket + tdx, y_socket + tdy, z_socket + tdz
    bottom_socket_x, bottom_socket_y, bottom_socket_z = tx, ty, tz
    distance = calc_distance(x1, y1, z1, tx, ty, tz)
    x, y, z = (tx + x1) / 2, (ty + x1) / 2, (tz + x1) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=radius,
                                        depth=distance,
                                        location=(x, y, z))
    bpy.context.active_object.name = '__SocketCylinder'
    socket_cylinder = bpy.data.objects['__SocketCylinder']

    # safety
    radius = .02 * size
    tdx, tdy, tdz = -dx * size_ball, -dy * size_ball, -dz * size_ball
    tx, ty, tz = x_ball + tdx, y_ball + tdy, z_ball + tdz
    bottom_ball_x, bottom_ball_y, bottom_ball_z = tx, ty, tz
    middle_x, middle_y, middle_z = (bottom_ball_x + bottom_socket_x) / 2, (bottom_ball_y + bottom_socket_y) / 2, (
            bottom_ball_z + bottom_socket_z) / 2
    distance = calc_distance(bottom_ball_x, bottom_ball_y, bottom_ball_z, middle_x, middle_y, middle_z)
    safety_depth = distance
    x, y, z = (bottom_ball_x + middle_x) / 2, (bottom_ball_y + middle_y) / 2, (bottom_ball_z + middle_z) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=distance, location=(x, y, z))
    bpy.context.active_object.name = '__Safety'
    safety = bpy.data.objects['__Safety']

    # constraint (safety space)
    constraint_depth = 1.1 * safety_depth
    bpy.ops.mesh.primitive_cube_add(radius=1, location=(bottom_ball_x, bottom_ball_y, bottom_ball_z))
    bpy.context.active_object.name = '__Constraint'
    constraint = bpy.data.objects['__Constraint']
    constraint.scale = (constraint_x, constraint_y, constraint_depth)
    constraint.hide = True
    constraint.hide_render = True

    modifier = socket.modifiers.new(type='BOOLEAN', name='ConstraintModifier')
    modifier.object = constraint
    modifier.operation = 'DIFFERENCE'

    # snap
    _dx, _dy, _dz = 0, snap_diff, 0
    x_snap, y_snap, z_snap = x_ball + _dx, y_ball + _dy, z_ball + _dz
    location_snap = (x_snap, y_snap, z_snap)

    bpy.ops.mesh.primitive_uv_sphere_add(size=size_snap, location=location_snap)
    bpy.context.active_object.name = '__Snap'
    snap = bpy.data.objects['__Snap']

    modifier = socket.modifiers.new(type='BOOLEAN', name='SnapModifier')
    modifier.object = snap
    modifier.operation = 'DIFFERENCE'

    objs = (socket, ball, ball_wrapper, ball_cylinder, socket_cylinder, safety, constraint, snap)
    _, joint = groupify('_Joint', objs)

    socket.active_material = CYAN_MATERIAL
    socket_cylinder.active_material = CYAN_MATERIAL
    ball.active_material = VIOLET_MATERIAL
    ball_cylinder.active_material = VIOLET_MATERIAL
    safety.active_material = VIOLET_MATERIAL
    snap.active_material = VIOLET_MATERIAL

    if cut:
        cut_objs((socket, ball, ball_cylinder, socket_cylinder, safety, snap))

    return joint, objs


def place_bond(obj, x1, y1, z1, x2, y2, z2):
    phi, theta = calc_rotation(x1, y1, z1, x2, y2, z2)

    obj.location = (x1, y1, z1)
    obj.rotation_euler[1] = theta
    obj.rotation_euler[2] = phi


def add_joint(x1, y1, z1, x2, y2, z2, constraint_x, constraint_y):  # old...
    joint, _ = create_joint(calc_distance(x1, y1, z1, x2, y2, z2), constraint_x, constraint_y)
    place_bond(joint, x1, y1, z1, x2, y2, z2)

    return joint


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


# 2JUV
bonds = [((8.94, -3.23, 0.10), (9.78, 0.87, 0.99))]
constraint_lengths = [(0.036765104309912644, 0.024223583174299002)]

# 2LME
# bonds = [((12.89, 2.09, 1.05), (4.08, -7.50, -11.19)), ((11.04, -2.69, 5.87), (-3.16, 9.33, 3.85))]
# constraint_lengths = [(0.032320707846670356, 0.03387241769544769), (0.03765608586197319, 0.02557388080843659)]

# 2MP2 (bad...)
# bonds = [((287.49, -17.76, -9.81), (316.32, 7.43, 0.47)), ((307.54, -3.14, 11.58), (300.40, 6.65, -6.90))]
# constraint_lengths = [(0.03718777914339034, 0.020461723633181272), (0.1044583703008806, 0.03636753293866604)]

# 2MW2 (not bad at all)
# bonds = [((8.99, 6.01, 3.88), (-8.81, -11.17, 10.81)), ((9.04, -3.22, -6.70), (-9.48, -0.11, 12.23))]
# constraint_lengths = [(0.02369762393644306, 0.021934923197533828), (0.026038403128002662, 0.023316347828134354)]

# 2MXR (OK)
# bonds = [((3.74, -1.34, -2.70), (20.62, 0.35, 12.36))]
# constraint_lengths = [(0.0224145972639394, 0.02294503172530169)]

# 2RVB (bad...)
# bonds = [((-3.26, -6.94, 8.39), (-6.60, 2.19, -1.94))]
# constraint_lengths = [(0.0356540432182613, 0.02797159016840993)]

# _joint, _objs = None, None
# for ((x1, y1, z1), (x2, y2, z2)), (_constraint_x, _constraint_y) in zip(bonds, constraint_lengths):
#     _joint, _objs = create_joint(calc_distance(x1, y1, z1, x2, y2, z2), _constraint_x, _constraint_y, cut=False)
#     place_joint(_joint, x1, y1, z1, x2, y2, z2)


# add_ball_and_socket(0, 0.025, 0.025)

# _constraints = ((0.025, 0.025), (0.025, 0.025), (0.025, 0.025))
# create_bond(10, _constraints)

_bond, _objs = None, None
all_constraints = [((0.025, 0.025), (0.025, 0.025), (0.025, 0.025))]  # TODO: override! (edit constraint_lengths and use it)
for ((x1, y1, z1), (x2, y2, z2)), _constraints in zip(bonds, all_constraints):
    length = calc_distance(x1, y1, z1, x2, y2, z2)
    _bond, _objs = create_bond(length, _constraints)
    place_bond(_bond, x1, y1, z1, x2, y2, z2)

