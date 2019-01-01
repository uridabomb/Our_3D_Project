import bpy
import math

from mathutils import Euler, Vector


def add_cylinder(x1, y1, z1, x2, y2, z2, r=.1):
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    dist = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    bpy.ops.mesh.primitive_cylinder_add(radius=r,
                                        depth=dist,
                                        location=(dx / 2 + x1, dy / 2 + y1, dz / 2 + z1))

    phi = math.atan2(dy, dx)
    theta = math.acos(dz / dist)

    bpy.context.object.rotation_euler[1] = theta
    bpy.context.object.rotation_euler[2] = phi


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


def rotate(obj, phi, theta):
    obj.rotation_euler[1] = theta
    obj.rotation_euler[2] = phi


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


# TODO: need to get constraints (angles or height+width?) as well
# TODO: need to compute rotations and use them when creating the objects
#       use example in `add_cylinder` in blender.py
def create_joint(length, size=1.0):
    # distance = calc_distance(x1, y2, z1, x2, y2, z2)
    # direction = calc_direction(x1, y1, z1, x2, y2, z2)
    # phi, theta = calc_rotation(x1, y1, z1, x2, y2, z2)

    # target = bpy.data.objects.new('Target', None)

    # dx, dy, dz = direction
    # dvec = Vector(direction)

    x1, y1, z1 = 0, 0, 0
    x2, y2, z2 = 0, 0, length
    dx, dy, dz = 0, 0, 1

    size_socket = size
    size_ball = .9 * size
    size_wrapper = (size_socket + size_ball) / 2

    # NOTE: probably the size == radius...
    r_socket, r_ball, r_wrapper = size_socket / 2, size_ball / 2, size_wrapper / 2

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
    # rotate(socket, phi, theta)

    bpy.ops.mesh.primitive_uv_sphere_add(size=size_ball, location=location_ball)
    bpy.context.active_object.name = '__Ball'
    ball = bpy.data.objects['__Ball']
    # rotate(ball, phi, theta)

    bpy.ops.mesh.primitive_uv_sphere_add(size=size_wrapper, location=location_wrapper)
    bpy.context.active_object.name = '__BallWrapper'
    ball_wrapper = bpy.data.objects['__BallWrapper']
    ball_wrapper.hide = True
    ball_wrapper.hide_render = True
    # rotate(ball_wrapper, phi, theta)

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

    # _phi, _theta = calc_rotation(tx, ty, tz, x2, y2, z2)
    # rotate(ball_cylinder,  _phi, _theta)

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

    # _phi, _theta = calc_rotation(tx, ty, tz, x1, y1, z1)
    # rotate(socket_cylinder, _phi, _theta)

    # safety
    radius = .05 * size
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
    # rotate(safety, phi, theta)

    # constraint (safety space)
    # TODO: need to get height and width or compute them via angles & radius (of the ball?)
    # height, width = 1, 2
    depth = 1.5 * safety_depth
    bpy.ops.mesh.primitive_cube_add(radius=1, location=(bottom_ball_x, bottom_ball_y, bottom_ball_z))
    bpy.context.active_object.name = '__Constraint'
    constraint = bpy.data.objects['__Constraint']
    constraint.scale = (depth, depth, depth)  # TODO: need to use height and width
    constraint.hide = True
    constraint.hide_render = True
    # rotate(constraint, phi, theta)

    modifier = socket.modifiers.new(type='BOOLEAN', name='ConstraintModifier')
    modifier.object = constraint
    modifier.operation = 'DIFFERENCE'

    objs = (socket, ball, ball_wrapper, ball_cylinder, socket_cylinder, safety, constraint)

    # rotate?
    # for obj in objs:
    #    pass
    #    obj.rotation_mode = 'QUATERNION'
    #    obj.rotation_quaternion = dvec.to_track_quat('Z','Y')

    # group, dupligroup = groupify('_Joint', objs)

    # for obj in group.objects:
    # rotate(obj, phi, theta)
    # obj.rotation_euler = Euler(direction, 'XYZ')

    return objs


x1, y1, z1 = 1, 2, 3
x2, y2, z2 = 10, 0, 1

# x1, y1, z1 = 0, 0, 0
# x2, y2, z2 = 10, 0, 0


add_cylinder(x1, y1, z1, x2, y2, z2)

objs = create_joint(calc_distance(x1, y1, z1, x2, y2, z2))

groupify('_Joint', objs)

for obj in objs:
    obj.select = True

location = ((x1 + x2)/2, (y1 + y2)/2, (z1 + z2)/2)
bpy.ops.transform.translate(value=location)

