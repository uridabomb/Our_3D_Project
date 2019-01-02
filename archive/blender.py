import bpy
import math


def calc_direction(x1, y1, z1, x2, y2, z2):
    vx, vy, vz = x2-x1, y2-y1, z2-z1
    length = math.sqrt(vx*vx + vy*vy + vz*vz)
    return vz/length, vy/length, vz/length


class BlenderScene(object):
    def __init__(self):
        self.cylinders_count = 0
        self.spheres_count = 0
        self.boolean_modifiers_count = 0

        self.groups = {}
        self.joints = {}

        self.delete_element('Cube')

    def groupify(self, objs, name=None):
        name = name or 'Group_{}'.format(len(self.groups))
        groups = bpy.data.groups

        # alias existing group, or generate new group and alias that
        group = groups.get(name, groups.new(name))

        for obj in objs:
            if obj.name not in group.objects:
                group.objects.link(obj)

        group = bpy.data.groups[name]
        groupobj = bpy.data.objects.new(name, None)
        # groupobj.dupli_type = 'GROUP'
        # groupobj.dupli_group = group
        bpy.context.scene.objects.link(groupobj)

        for obj in objs:
            obj.parent = groupobj

        self.groups[name] = group, groupobj
        return group, groupobj

    def add_cilynder(self, x1, y1, z1, x2, y2, z2, r=.1, name=None):
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        dist = math.sqrt(dx**2 + dy**2 + dz**2)
        location = ((x1 + x2)/2, (y1 + y2)/2, (z1 + z2)/2)

        bpy.ops.mesh.primitive_cylinder_add(radius=r,
                                            depth=dist,
                                            location=location)

        name = name or 'cylinder_{}'.format(self.cylinders_count)
        self.cylinders_count += 1
        bpy.context.active_object.name = name

        phi = math.atan2(dy, dx)
        theta = math.acos(dz/dist)

        bpy.context.object.rotation_euler[1] = theta
        bpy.context.object.rotation_euler[2] = phi

        return bpy.data.objects[name]

    def add_sphere(self, x, y, z, r=.5, name=None):
        bpy.ops.mesh.primitive_uv_sphere_add(size=r,
                                             location=(x, y, z))

        name = name or 'sphere_{}'.format(self.spheres_count)
        self.spheres_count += 1

        bpy.context.active_object.name = name
        return bpy.data.objects[name]

    def add_joint(self, x1, y1, z1, x2, y2, z2, name=None):
        sphere_radius = .5
        cylinder_radius = .2
        hole_radius = .3

        c = self.add_cilynder(x1, y1, z1, x2, y2, z2, cylinder_radius)
        subtraction_cylinder = self.add_cilynder(x1, y1, z1, x2, y2, z2, hole_radius)
        s1 = self.add_sphere(x1, y1, z1, sphere_radius)
        s2 = self.add_sphere(x2, y2, z2, sphere_radius)

        m1 = self.add_boolean_modifier(s1, subtraction_cylinder)
        m2 = self.add_boolean_modifier(s2, subtraction_cylinder)

        subtraction_cylinder.hide = True
        subtraction_cylinder.hide_render = True

        name = name or 'joint_{}'.format(len(self.joints))
        self.joints[name] = (c, subtraction_cylinder, s1, m1, s2, m2)

        return self.joints[name]

    def add_ball_and_socket_joint(self, z1, y1, x2, y2, z2, name=None, color=(.5, .0, 1)):
        name = name or '_Joint_{}'.format(len(self.joints))
        # TODO
        pass

    def add_boolean_modifier(self, target_obj, subtraction_obj):
        name = 'bool_{}'.format(self.boolean_modifiers_count)
        modifier = target_obj.modifiers.new(type='BOOLEAN', name=name)
        modifier.object = subtraction_obj
        modifier.operation = 'DIFFERENCE'

        self.boolean_modifiers_count += 1
        return modifier

    def delete_element(self, name):
        # deselect all
        bpy.ops.object.select_all(action='DESELECT')

        # selection
        bpy.data.objects[name].select = True

        # remove it
        bpy.ops.object.delete()


if __name__ == '__main__':

    # filepath = '/Users/uriavron/Dropbox/School/MSc/3d/project/git/data/2JUV.pdb'
    # imported_object = bpy.ops.import_scene.obj(filepath=filepath)
    # obj = bpy.context.selected_objects[0]
    #
    # print('Imported name: ', obj.name)

    scene = BlenderScene()
    scene.add_joint(0.79, -6.38, -3.73, -2.86, 2.24, -2.94)



# cmd: blender data/2JUV.obj --python blender.py