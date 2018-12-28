import bpy
import math


def add_cilynder(x1, y1, z1, x2, y2, z2, r=.1):
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    dist = math.sqrt(dx**2 + dy**2 + dz**2)

    bpy.ops.mesh.primitive_cylinder_add(radius=r,
                                        depth=dist,
                                        location=(dx/2 + x1, dy/2 + y1, dz/2 + z1))

    phi = math.atan2(dy, dx)
    theta = math.acos(dz/dist)

    bpy.context.object.rotation_euler[1] = theta
    bpy.context.object.rotation_euler[2] = phi


def delete_element(name):
    # deselect all
    bpy.ops.object.select_all(action='DESELECT')

    # selection
    bpy.data.objects[name].select = True

    # remove it
    bpy.ops.object.delete()


def init_scene():
    delete_element('Cube')


if __name__ == '__main__':

    # filepath = '/Users/uriavron/Dropbox/School/MSc/3d/project/git/data/2JUV.pdb'
    # imported_object = bpy.ops.import_scene.obj(filepath=filepath)
    # obj = bpy.context.selected_objects[0]
    #
    # print('Imported name: ', obj.name)

    init_scene()
    add_cilynder(0.79, -6.38, -3.73, -2.86, 2.24, -2.94)


# cmd: blender data/2JUV.obj --python blender.py