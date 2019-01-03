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


def create_joint(length, constraint_x, constraint_y, size=1.0, cut=False):
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


def place_joint(joint, x1, y1, z1, x2, y2, z2):
    phi, theta = calc_rotation(x1, y1, z1, x2, y2, z2)

    joint.location = (x1, y1, z1)
    joint.rotation_euler[1] = theta
    joint.rotation_euler[2] = phi


def add_joint(x1, y1, z1, x2, y2, z2, constraint_x, constraint_y):
    joint, _ = create_joint(calc_distance(x1, y1, z1, x2, y2, z2), constraint_x, constraint_y)
    place_joint(joint, x1, y1, z1, x2, y2, z2)

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


bonds = [((0.79, -6.38, -3.73), (-2.86, 2.24, -2.94))]
constraint_lengths = [(0.021463302826165993, 0.02654762928946491)]

_joint, _objs = None, None
for ((x1, y1, z1), (x2, y2, z2)), (_constraint_x, _constraint_y) in zip(bonds, constraint_lengths):
    _joint, _objs = create_joint(calc_distance(x1, y1, z1, x2, y2, z2), _constraint_x, _constraint_y, cut=False)
    place_joint(_joint, x1, y1, z1, x2, y2, z2)




