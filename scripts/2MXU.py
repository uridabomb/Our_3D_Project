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


# 2MXU
bonds = [((-21.26099967956543, 16.527000427246094, 7.392000198364258), (-19.195999145507812, 12.52299976348877, 6.507999897003174)), ((-15.201000213623047, -6.315999984741211, 16.506000518798828), (-19.339000701904297, -4.692999839782715, 18.3439998626709)), ((-17.54199981689453, -0.22699999809265137, -5.322000026702881), (-21.834999084472656, 0.878000020980835, -3.437000036239624)), ((-10.234000205993652, 9.961000442504883, -13.11400032043457), (-13.949999809265137, 11.734999656677246, -10.611000061035156)), ((-12.14799976348877, 6.614999771118164, -13.152000427246094), (-8.444999694824219, 4.614999771118164, -15.454999923706055)), ((-4.064000129699707, 0.2160000056028366, -14.743000030517578), (-7.968999862670898, 2.0420000553131104, -12.595999717712402)), ((-0.06800000369548798, -10.800999641418457, 0.9860000014305115), (2.497999906539917, -14.835000038146973, 1.559000015258789)), ((4.113999843597412, -12.404000282287598, -0.9810000061988831), (6.671999931335449, -16.400999069213867, -0.47200000286102295)), ((10.704000473022461, -18.013999938964844, -2.63700008392334), (8.263999938964844, -13.968000411987305, -3.0350000858306885)), ((14.78600025177002, -19.70199966430664, -4.74399995803833), (12.354000091552734, -15.64900016784668, -5.223999977111816)), ((16.398000717163086, -17.448999404907227, -7.459000110626221), (18.774999618530273, -21.499000549316406, -6.833000183105469))]
all_constraints = [[(0.02765253194215636, 0.023805964522232083), (0.11969935051506363, 0.04388196023714608), (0.02028146952188285, 0.025299527174068956)], [(0.027246277562640607, 0.02067577661426371), (0.08742507892598161, 0.06518180020767367), (0.03664488649810774, 0.028035992560988186)], [(0.020172628319308356, 0.021311652554153994), (0.11403560346802387, 0.04937303077201671), (0.028991376668264603, 0.02849586298026959)], [(0.029617594477068968, 0.032312747778000236), (0.11316608215814983, 0.09417996627382755), (0.03184512892374407, 0.02393703508546011)], [(0.033376425366790446, 0.03811953962071981), (0.1157773360967616, 0.045757975316337685), (0.027337891090528706, 0.03155686523202797)], [(0.02315254293708688, 0.026576319709844542), (0.03369628327587181, 0.08769296667128995), (0.02538452773719199, 0.020511100691648854)], [(0.023140187879060952, 0.027586320760926066), (0.11997794397136519, 0.0595635300063669), (0.023542521655252384, 0.024334421847189452)], [(0.023140187879060952, 0.027586320760926066), (0.11677869760301604, 0.0430709026212847), (0.023542521655252384, 0.024334421847189452)], [(0.038870347846896275, 0.02205176315795876), (0.06366881672387452, 0.04050790345203194), (0.02018872207103106, 0.022081933390775542)], [(0.038870347846896275, 0.02205176315795876), (0.08008469265375157, 0.052310653921956524), (0.02018872207103106, 0.022081933390775542)], [(0.023140187879060952, 0.027586320760926066), (0.10695596434802382, 0.04291181473261174), (0.023542521655252384, 0.024334421847189452)]]

_bond, _objs = None, None
for ((x1, y1, z1), (x2, y2, z2)), _constraints in zip(bonds, all_constraints):
    length = calc_distance(x1, y1, z1, x2, y2, z2)
    _bond, _objs = create_bond(length, _constraints)
    place_bond(_bond, x1, y1, z1, x2, y2, z2)
