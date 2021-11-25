import numpy as np
from numpy import pi
import os.path as path
import getopt
import sys
import json
import os
import copy
import shutil
import importlib
import helpers_abc
import default_configuration as cfg
from dataclasses import dataclass
from typing import Any

# from clusters.default_cluster import DefaultCluster
# from clusters.carbonfet import CarbonfetCluster
# from clusters.mini import MiniCluster
# from clusters.minidox import MinidoxCluster
# from clusters.trackball_orbyl import TrackballOrbyl
# from clusters.trackball_wilder import TrackballWild
# from clusters.trackball_cj import TrackballCJ
# from clusters.custom_cluster import CustomCluster

# CLUSTER_LOOKUP = {
#     'DEFAULT': {'package': 'default_cluster', 'class': 'DefaultCluster'},
#     'CARBONFET': {'package': 'carbonfet', 'class': 'CarbonfetCluster'},
#     'MINI': {'package': 'mini', 'class': 'MiniCluster'},
#     'MINIDOX': {'package': 'minidox', 'class': 'MinidoxCluster'},
#     'TRACKBALL_ORBYL': {'package': 'trackball_orbyl', 'class': 'TrackballOrbyl'},
#     'TRACKBALL_WILD': {'package': 'trackball_wilder', 'class': 'TrackballWild'},
#     'TRACKBALL_CJ': {'package': 'trackball_cj', 'class': 'TrackballCJ'},
#     'TRACKBALL_CUSTOM': {'package': 'custom_cluster', 'class': 'CustomCluster'},
# }

ENGINE_LOOKUP = {
    'solid': 'helpers_solid',
    'cadquery': 'helpers_cadquery',
}


debug_exports = False
debug_trace = False

@dataclass
class Override:
    obj_type: str  = 'base'  # base, cluster, oled, etc.  Should match object collection in default config.
    variable: str = 'default'  # needs to match variable name
    value: Any = None #  object to be assigned.  Can be nested if there are multiple levels.


def deg2rad(degrees: float) -> float:
    return degrees * pi / 180


def rad2deg(rad: float) -> float:
    return rad * 180 / pi


def usize_dimention(Usize=1.5):
    sa_length = 18.5
    return Usize * sa_length


def debugprint(info):
    if debug_trace:
        print(info)



dat = Override(obj_type='base', variable='double_plate_height', value=55)

## LISTING VARIABLES IN SHAPE CLASS FOR PARAMETER SEPARATION CONSIDERATIONS.
# shape_vars=[
########################
# PLATE INTERFACE DIMENSIONS
########################
# mount_thickness
# mount_width
# mount_height
# sa_length
# plate_thickness
# adjustable_plate_height
# double_plate_height

########################
# PLATE INTERNAL DIMENSIONS
########################
# keyswitch_width
# keyswitch_height

# clip_undercut
# undercut_transition
# notch_width
#
# plate_file
# plate_offset
# adjustable_plate_height
# double_plate_height
#
########################
# WEB AND POST GEOMETRIES
########################
# post_size
# web_thickness
# post_adj
#
#
########################
# PLATE HOLES FOR PCB MOUNT
########################
# plate_holes_width
# plate_holes_height
# plate_holes_xy_offset
# plate_holes_diameter
# plate_holes_depth
#
########################
# PLATE REPRESENTATION
########################
# plate_pcb_size
# plate_pcb_offset
# pcb_hole_diameter
# pcb_hole_pattern_width
# pcb_hole_pattern_height
# pcb_width
# pcb_height
# pcb_thickness
#
########################
# TRACKBALL GEOMETRIES
########################
# trackball_modular
# ball_diameter
# ball_gap
# ball_wall_thickness
# trackball_modular_clearance
# trackball_modular_lip_width
# trackball_hole_diameter
# trackball_hole_height
# hole_diameter
#
########################
# PARTS LOAD PATH
########################
# parts_path
#
# ]



class ShapeFunctions:
    def __init__(self, parent):
        self._parent = parent
        self.p = parent.p
        self.g = parent.g

    def single_plate(self,
                     # plate_style=None, mount_width=None, mount_height=None,
                     # keyswitch_width=None, keyswitch_height=None, plate_thickness=None, mount_thickness=None,
                     # clip_undercut=None,
                     cylinder_segments=100, side="right",
                     ):
        if self.p.plate_style in ['NUB', 'HS_NUB']:
            plate = self.nub_plate(
                # mount_width=mount_width, mount_height=mount_height,
                # keyswitch_width=keyswitch_width, keyswitch_height=keyswitch_height,
                # plate_thickness=plate_thickness, mount_thickness=mount_thickness
            )
        else:
            plate = self.plate_square_hole(
                # mount_width=mount_width, mount_height=mount_height,
                # keyswitch_width=keyswitch_width, keyswitch_height=keyswitch_height,
                # plate_thickness=plate_thickness, mount_thickness=mount_thickness
            )

        if self.p.plate_style in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
            if self.p.plate_style in ['UNDERCUT', 'HS_UNDERCUT']:
                undercut = self.plate_undercut(
                    keyswitch_width=self.p.keyswitch_width, keyswitch_height=self.p.keyswitch_height,
                    mount_thickness=self.p.mount_thickness,
                    clip_undercut=self.p.clip_undercut, undercut_transition=self.p.undercut_transition,
                )
            # if self.p.plate_style in ['NOTCH', 'HS_NOTCH']:
            else:
                undercut = self.plate_notch(
                    keyswitch_width=self.p.keyswitch_width, keyswitch_height=self.p.keyswitch_height,
                    mount_thickness=self.p.mount_thickness,
                    notch_width=self.p.notch_width, clip_undercut=self.p.clip_undercut,
                    undercut_transition=self.p.undercut_transition,
                )

            plate = self.g.difference(plate, [undercut])

        if self.p.plate_file is not None:
            socket = self.g.import_file(self.p.plate_file)
            socket = self.g.translate(socket, [0, 0, self.p.plate_thickness + self.p.plate_offset])
            plate = self.g.union([plate, socket])

        if self.p.plate_holes:
            plate = self.plate_screw_holes(
                plate, side=side,
                plate_holes_width=self.p.plate_holes_width, plate_holes_height=self.p.plate_holes_height,
                plate_holes_xy_offset=self.p.plate_holes_xy_offset,
                plate_holes_diameter=self.p.plate_holes_diameter, plate_holes_depth=self.p.plate_holes_depth
            )

        if side == "left":
            plate = self.g.mirror(plate, 'YZ')

        return plate

    def nub_plate(
            self, mount_width=None, mount_height=None,
            keyswitch_width=None, keyswitch_height=None, plate_thickness=None, mount_thickness=None,
    ):
        tb_border = (mount_height - keyswitch_height) / 2
        top_wall = self.g.box(mount_width, tb_border, plate_thickness)
        top_wall = self.g.translate(top_wall, (0, (tb_border / 2) + (keyswitch_height / 2), plate_thickness / 2))

        lr_border = (mount_width - keyswitch_width) / 2
        left_wall = self.g.box(lr_border, mount_height, plate_thickness)
        left_wall = self.g.translate(left_wall, ((lr_border / 2) + (keyswitch_width / 2), 0, plate_thickness / 2))

        side_nub = self.g.cylinder(radius=1, height=2.75)
        side_nub = self.g.rotate(side_nub, (90, 0, 0))
        side_nub = self.g.translate(side_nub, (keyswitch_width / 2, 0, 1))

        nub_cube = self.g.box(1.5, 2.75, plate_thickness)
        nub_cube = self.g.translate(nub_cube, ((1.5 / 2) + (keyswitch_width / 2), 0, plate_thickness / 2))

        side_nub2 = self.g.tess_hull(shapes=(side_nub, nub_cube))
        side_nub2 = self.g.union([side_nub2, side_nub, nub_cube])

        plate_half1 = self.g.union([top_wall, left_wall, side_nub2])
        plate_half2 = plate_half1
        plate_half2 = self.g.mirror(plate_half2, 'XZ')
        plate_half2 = self.g.mirror(plate_half2, 'YZ')

        plate = self.g.union([plate_half1, plate_half2])

        return plate

    def plate_square_hole(
            self, mount_width=None, mount_height=None,
            keyswitch_width=None, keyswitch_height=None, plate_thickness=None, mount_thickness=None
    ):
        plate = self.g.box(self.p.mount_width, self.p.mount_height, self.p.mount_thickness)
        plate = self.g.translate(plate, (0.0, 0.0, self.p.mount_thickness / 2.0))

        shape_cut = self.g.box(self.p.keyswitch_width, self.p.keyswitch_height, self.p.mount_thickness * 2 + .02)
        shape_cut = self.g.translate(shape_cut, (0.0, 0.0, self.p.mount_thickness - .01))

        plate = self.g.difference(plate, [shape_cut])

        return plate

    def plate_undercut(
            self, keyswitch_width=None, keyswitch_height=None, mount_thickness=None,
            clip_undercut=None, undercut_transition=None,
    ):
        undercut = self.g.box(
            self.p.keyswitch_width + 2 * self.p.clip_undercut,
            self.p.keyswitch_height + 2 * self.p.clip_undercut,
            self.p.mount_thickness
        )
        if self.p.ENGINE == 'cadquery' and self.p.undercut_transition > 0:
            undercut = undercut.faces("+Z").chamfer(self.p.undercut_transition, self.p.clip_undercut)

        return undercut

    def plate_notch(
            self, keyswitch_width=None, keyswitch_height=None, mount_thickness=None,
            notch_width=None, clip_undercut=None, undercut_transition=None
    ):
        undercut = self.g.box(
            self.p.notch_width,
            self.p.keyswitch_height + 2 * self.p.clip_undercut,
            self.p.mount_thickness
        )
        undercut = self.g.union([
            undercut,
            self.g.box(
                self.p.keyswitch_width + 2 * self.p.clip_undercut,
                self.p.notch_width,
                self.p.mount_thickness
            )
        ])

        undercut = self.g.translate(undercut, (0.0, 0.0, -self.p.clip_thickness + self.p.mount_thickness / 2.0))

        if self.p.ENGINE == 'cadquery' and self.p.undercut_transition > 0:
            undercut = undercut.faces("+Z").chamfer(self.p.undercut_transition, self.p.clip_undercut)

        return undercut

    def plate_screw_holes(
            self, plate, side='right',
            plate_holes_width=None, plate_holes_height=None, plate_holes_xy_offset=None,
            plate_holes_diameter=None, plate_holes_depth=None
    ):
        half_width = plate_holes_width / 2.
        half_height = plate_holes_height / 2.

        if side == 'right':
            x_off = plate_holes_xy_offset[0]
        else:
            x_off = -plate_holes_xy_offset[0]

        y_off = plate_holes_xy_offset[1]
        holes = [
            self.g.translate(
                self.g.cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                (x_off + half_width, y_off + half_height, plate_holes_depth / 2 - .01)
            ),
            self.g.translate(
                self.g.cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                (x_off - half_width, y_off + half_height, plate_holes_depth / 2 - .01)
            ),
            self.g.translate(
                self.g.cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                (x_off - half_width, y_off - half_height, plate_holes_depth / 2 - .01)
            ),
            self.g.translate(
                self.g.cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth + .01),
                (x_off + half_width, y_off - half_height, plate_holes_depth / 2 - .01)
            ),
        ]

        plate = self.g.difference(plate, holes)

        return plate

    def plate_pcb_cutout(self, side="right"):
        shape = self.g.box(*self.p.plate_pcb_size)
        shape = self.g.translate(shape, (0, 0, -self.p.plate_pcb_size[2] / 2))
        shape = self.g.translate(shape, self.p.plate_pcb_offset)

        if side == "left":
            shape = self.g.mirror(shape, 'YZ')

        return shape

    def trackball_cutout(self, segments=100, side="right"):
        if self.p.trackball_modular:
            hole_diameter = self.p.ball_diameter + 2 * (
                        self.p.ball_gap + self.p.ball_wall_thickness + self.p.trackball_modular_clearance + self.p.trackball_modular_lip_width) - .1
            shape = self.g.cylinder(self.p.hole_diameter / 2, self.p.trackball_hole_height)
        else:
            shape = self.g.cylinder(self.p.trackball_hole_diameter / 2, self.p.trackball_hole_height)
        return shape

    def trackball_socket(self, segments=100, side="right"):
        if self.p.trackball_modular:
            hole_diameter = self.p.ball_diameter + 2 * (
                        self.p.ball_gap + self.p.ball_wall_thickness + self.p.trackball_modular_clearance)
            ring_diameter = self.p.hole_diameter + 2 * self.p.trackball_modular_lip_width
            ring_height = self.p.trackball_modular_ring_height
            ring_z_offset = self.p.mount_thickness - self.p.trackball_modular_ball_height
            shape = self.g.cylinder(ring_diameter / 2, ring_height)
            shape = self.g.translate(shape, (0, 0, -ring_height / 2 + ring_z_offset))

            cutter = self.g.cylinder(hole_diameter / 2, ring_height + .2)
            cutter = self.g.translate(cutter, (0, 0, -ring_height / 2 + ring_z_offset))

            sensor = None

        else:
            tb_file = path.join(self.p.parts_path, r"trackball_socket_body_34mm")
            tbcut_file = path.join(self.p.parts_path, r"trackball_socket_cutter_34mm")
            sens_file = path.join(self.p.parts_path, r"trackball_sensor_mount")
            senscut_file = path.join(self.p.parts_path, r"trackball_sensor_cutter")

            shape = self.g.import_file(tb_file)
            sensor = self.g.import_file(sens_file)
            cutter = self.g.import_file(tbcut_file)
            cutter = self.g.union([cutter, self.g.import_file(senscut_file)])

        # return shape, cutter
        return shape, cutter, sensor

    def trackball_ball(self, segments=100, side="right"):
        shape = self.g.sphere(self.p.ball_diameter / 2)
        return shape

    ################
    ## SA Keycaps ##
    ################

    def sa_cap(self, Usize=1):
        # MODIFIED TO NOT HAVE THE ROTATION.  NEEDS ROTATION DURING ASSEMBLY
        # sa_length = 18.25

        if Usize == 1:
            bl2 = 18.5 / 2
            bw2 = 18.5 / 2
            m = 17 / 2
            pl2 = 6
            pw2 = 6

        elif Usize == 2:
            bl2 = self.p.sa_length
            bw2 = self.p.sa_length / 2
            m = 0
            pl2 = 16
            pw2 = 6

        elif Usize == 1.5:
            bl2 = self.p.sa_length / 2
            bw2 = 27.94 / 2
            m = 0
            pl2 = 6
            pw2 = 11

        k1 = self.g.polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
        k1 = self.g.extrude_poly(outer_poly=k1, height=0.1)
        k1 = self.g.translate(k1, (0, 0, 0.05))
        k2 = self.g.polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
        k2 = self.g.extrude_poly(outer_poly=k2, height=0.1)
        k2 = self.g.translate(k2, (0, 0, 12.0))
        if m > 0:
            m1 = self.g.polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
            m1 = self.g.extrude_poly(outer_poly=m1, height=0.1)
            m1 = self.g.translate(m1, (0, 0, 6.0))
            key_cap = self.g.hull_from_shapes((k1, k2, m1))
        else:
            key_cap = self.g.hull_from_shapes((k1, k2))

        key_cap = self.g.translate(key_cap, (0, 0, 5 + self.p.plate_thickness))

        if self.p.show_pcbs:
            key_cap = self.g.add([key_cap, self.key_pcb()])

        return key_cap

    def key_pcb(self):
        shape = self.g.box(self.p.pcb_width, self.p.pcb_height, self.p.pcb_thickness)
        shape = self.g.translate(shape, (0, 0, -self.p.pcb_thickness / 2))
        hole = self.g.cylinder(self.p.pcb_hole_diameter / 2, self.p.pcb_thickness + .2)
        hole = self.g.translate(hole, (0, 0, -(self.p.pcb_thickness + .1) / 2))
        holes = [
            self.g.translate(hole, (self.p.pcb_hole_pattern_width / 2, self.p.pcb_hole_pattern_height / 2, 0)),
            self.g.translate(hole, (-self.p.pcb_hole_pattern_width / 2, self.p.pcb_hole_pattern_height / 2, 0)),
            self.g.translate(hole, (-self.p.pcb_hole_pattern_width / 2, -self.p.pcb_hole_pattern_height / 2, 0)),
            self.g.translate(hole, (self.p.pcb_hole_pattern_width / 2, -self.p.pcb_hole_pattern_height / 2, 0)),
        ]
        shape = self.g.difference(shape, holes)

        return shape

    ####################
    ## Web Connectors ##
    ####################

    def web_post(self):
        debugprint('web_post()')
        post = self.g.box(self.p.post_size, self.p.post_size, self.p.web_thickness)
        post = self.g.translate(post, (0, 0, self.p.plate_thickness - (self.p.web_thickness / 2)))
        return post

    def web_post_tr(self, wide=False):
        mount_width = self.p.mount_width
        mount_height = self.p.mount_height
        post_adj = self.p.post_adj

        if wide:
            w_divide = 1.2
        else:
            w_divide = 2.0

        return self.g.translate(self.web_post(),
                                ((mount_width / w_divide) - post_adj, (mount_height / 2) - post_adj, 0))

    def web_post_br(self, wide=False):
        mount_width = self.p.mount_width
        mount_height = self.p.mount_height
        post_adj = self.p.post_adj
        if wide:
            w_divide = 1.2
        else:
            w_divide = 2.0
        return self.g.translate(self.web_post(), ((mount_width / w_divide) - post_adj, -(mount_height / 2) + post_adj, 0))

    def web_post_tl(self, wide=False):
        mount_width = self.p.mount_width
        mount_height = self.p.mount_height
        post_adj = self.p.post_adj
        if wide:
            w_divide = 1.2
        else:
            w_divide = 2.0
        return self.g.translate(self.web_post(), (-(mount_width / w_divide) + post_adj, (mount_height / 2) - post_adj, 0))

    def web_post_bl(self, wide=False):
        mount_width = self.p.mount_width
        mount_height = self.p.mount_height
        post_adj = self.p.post_adj
        if wide:
            w_divide = 1.2
        else:
            w_divide = 2.0
        return self.g.translate(self.web_post(), (-(mount_width / w_divide) + post_adj, -(mount_height / 2) + post_adj, 0))

    def adjustable_square_plate(self, Uwidth=1.5, Uheight=1.5):
        width = usize_dimention(Usize=Uwidth)
        height = usize_dimention(Usize=Uheight)
        print("width: {}, height: {}, thickness:{}".format(width, height, self.p.web_thickness))
        shape = self.g.box(width, height, self.p.web_thickness)
        shape = self.g.difference(shape, [self.g.box(self.p.mount_width - .01, self.p.mount_height - .01, 2 * self.p.web_thickness)])
        # shape = self.g.translate(shape, (0, 0, web_thickness / 2))
        shape = self.g.translate(shape, (0, 0, self.p.plate_thickness - (self.p.web_thickness / 2)))

        return shape

    def adjustable_plate_size(self, Usize=1.5):
        return (Usize * self.p.sa_length - self.p.mount_height) / 2

    def adjustable_plate_half(self, Usize=1.5):
        debugprint('double_plate()')
        adjustable_plate_height = self.adjustable_plate_size(Usize)
        top_plate = self.g.box(self.p.mount_width, adjustable_plate_height, self.p.web_thickness)
        top_plate = self.g.translate(top_plate,
                                     [0, (adjustable_plate_height + self.p.mount_height) / 2,
                                      self.p.plate_thickness - (self.p.web_thickness / 2)]
                                     )
        return top_plate

    def adjustable_plate(self, Usize=1.5):
        debugprint('double_plate()')
        top_plate = self.adjustable_plate_half(Usize)
        return self.g.union((top_plate, self.g.mirror(top_plate, 'XZ')))

    def double_plate_half(self):
        debugprint('double_plate()')

        top_plate = self.g.box(self.p.mount_width, self.p.double_plate_height, self.p.web_thickness)
        top_plate = self.g.translate(top_plate,
                                     [0, (self.p.double_plate_height + self.p.mount_height) / 2,
                                      self.p.plate_thickness - (self.p.web_thickness / 2)]
                                     )
        return top_plate

    def double_plate(self):
        debugprint('double_plate()')
        top_plate = self.double_plate_half()
        return self.g.union((top_plate, self.g.mirror(top_plate, 'XZ')))


class DactylBase:

    def __init__(self, parameters):

        self.p = parameters

        # Below is used to allow IDE autofill from helpers_abc regardless of actual imported engine.
        if self.p.ENGINE is not None:
            self.g = importlib.import_module(ENGINE_LOOKUP[self.p.ENGINE])
        else:
            self.g = helpers_abc

        self.right_cluster = None
        self.left_cluster = None

        # self.p.right_thumb_style = self.p.right_cluster.thumb_style
        # self.p.left_thumb_style = self.p.left_cluster.thumb_style

        self.p.left_wall_x_offset = 8
        self.p.left_wall_z_offset = 3
        self.p.left_wall_lower_y_offset = 0
        self.p.left_wall_lower_z_offset = 0

        self.p.symmetry = None
        self.p.column_style = None

        self.p.save_name = None
        self.p.override_name = None

        self.p.parts_path = path.join(r"..", r"..", "src", "parts")

        self.p.full_last_rows = not self.p.reduced_outer_keys

        # if self.p.oled_mount_type is not None and self.p.oled_mount_type != "NONE":
        #     for item in self.p.oled_configurations[oled_mount_type]:
        #         globals()[item] = oled_configurations[oled_mount_type][item]

        if self.p.nrows > 5:
            self.p.column_style = 'column_style_gt5'

        self.p.lastrow = self.p.nrows - 1
        if self.p.reduced_outer_keys:
            self.p.cornerrow = self.p.lastrow - 1
        else:
            self.p.cornerrow = self.p.lastrow
        self.p.lastcol = self.p.ncols - 1

        self.p.centerrow = self.p.nrows - self.p.centerrow_offset

        self.p.plate_file = None

        # Derived values
        if self.p.plate_style in ['NUB', 'HS_NUB']:
            self.p.keyswitch_height = self.p.nub_keyswitch_height
            self.p.keyswitch_width = self.p.nub_keyswitch_width
        elif self.p.plate_style in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
            self.p.keyswitch_height = self.p.undercut_keyswitch_height
            self.p.keyswitch_width = self.p.undercut_keyswitch_width
        else:
            self.p.keyswitch_height = self.p.hole_keyswitch_height
            self.p.keyswitch_width = self.p.hole_keyswitch_width

        if 'HS_' in self.p.plate_style:
            self.p.symmetry = "asymmetric"
            pname = r"hot_swap_plate"
            if self.p.plate_file_name is not None:
                self.p.pname = self.p.plate_file_name
            self.p.plate_file = path.join(self.p.parts_path, self.p.pname)
            # plate_offset = 0.0 # this overwrote the config variable

        # if (self.p.trackball_in_wall or ('TRACKBALL' in self.p.thumb_style)) and not self.p.ball_side == 'both':
        if self.right_cluster != self.left_cluster:
            self.p.symmetry = "asymmetric"

        self.p.mount_width = self.p.keyswitch_width + 2 * self.p.plate_rim
        self.p.mount_height = self.p.keyswitch_height + 2 * self.p.plate_rim
        self.p.mount_thickness = self.p.plate_thickness

        self.p.double_plate_height = (self.p.sa_double_length - self.p.mount_height) / 3

        if self.p.oled_mount_type is not None and self.p.oled_mount_type != "NONE":
            self.p.left_wall_x_offset = self.p.oled_config.oled_left_wall_x_offset_override
            self.p.left_wall_z_offset = self.p.oled_config.oled_left_wall_z_offset_override
            self.p.left_wall_lower_y_offset = self.p.oled_config.oled_left_wall_lower_y_offset
            self.p.left_wall_lower_z_offset = self.p.oled_config.oled_left_wall_lower_z_offset

        self.p.cap_top_height = self.p.plate_thickness + self.p.sa_profile_key_height
        self.p.row_radius = ((self.p.mount_height + self.p.extra_height) / 2) / (
            np.sin(self.p.alpha / 2)) + self.p.cap_top_height
        self.p.column_radius = (
                                       ((self.p.mount_width + self.p.extra_width) / 2) / (np.sin(self.p.beta / 2))
                               ) + self.p.cap_top_height
        self.p.column_x_delta = -1 - self.p.column_radius * np.sin(self.p.beta)
        self.p.column_base_angle = self.p.beta * (self.p.centercol - 2)

        self.p.teensy_width = 20
        self.p.teensy_height = 12
        self.p.teensy_length = 33
        self.p.teensy2_length = 53
        self.p.teensy_pcb_thickness = 2
        self.p.teensy_offset_height = 5
        self.p.teensy_holder_top_length = 18
        self.p.teensy_holder_width = 7 + self.p.teensy_pcb_thickness
        self.p.teensy_holder_height = 6 + self.p.teensy_width

        self.p.save_path = path.join("..", "things", self.p.save_dir)
        if not path.isdir(self.p.save_path):
            os.mkdir(self.p.save_path)

        if self.p.override_name in ['', None, '.']:
            if self.p.save_dir in ['', None, '.']:
                self.p.save_path = path.join(r"..", "things")
                # parts_path = path.join(r"..", "src", "parts")
            else:
                self.p.save_path = path.join(r"..", "things", self.p.save_dir)
                # parts_path = path.join(r"..", r"..", "src", "parts")
            # parts_path = path.join(r"..", r"..", "src", "parts")
        else:
            self.p.save_path = path.join(self.p.save_dir, self.p.override_name)
            # parts_path = path.jo

        dir_exists = os.path.isdir(self.p.save_path)
        if not dir_exists:
            os.makedirs(self.p.save_path, exist_ok=True)

        self.sh = ShapeFunctions(self)
        self.set_clusters()


        ## TODO: RELOCATE ITEMS BELOW, TEMPORARILY MOVED TO INIT
        self.p.rj9_start = list(
            np.array([0, -3, 0])
            + np.array(
                self.key_position(
                    list(np.array(self.wall_locate3(0, 1)) + np.array([0, (self.p.mount_height / 2), 0])),
                    0,
                    0,
                )
            )
        )

        self.p.rj9_position = (self.p.rj9_start[0], self.p.rj9_start[1], 11)

        self.p.usb_holder_position = self.key_position(
            list(np.array(self.wall_locate2(0, 1)) + np.array([0, (self.p.mount_height / 2), 0])), 1, 0
        )
        self.p.usb_holder_size = [6.5, 10.0, 13.6]
        self.p.usb_holder_thickness = 4

        self.p.external_start = list(
            # np.array([0, -3, 0])
            np.array([self.p.external_holder_width / 2, 0, 0])
            + np.array(
                self.key_position(
                    list(np.array(self.wall_locate3(0, 1)) + np.array([0, (self.p.mount_height / 2), 0])),
                    0,
                    0,
                )
            )
        )

        self.p.pcb_mount_ref_position = self.key_position(
            # TRRS POSITION IS REFERENCE BY CONVENIENCE
            list(np.array(self.wall_locate3(0, 1)) + np.array([0, (self.p.mount_height / 2), 0])), 0, 0
        )

        self.p.pcb_mount_ref_position[0] = self.p.pcb_mount_ref_position[0] + self.p.pcb_mount_ref_offset[0]
        self.p.pcb_mount_ref_position[1] = self.p.pcb_mount_ref_position[1] + self.p.pcb_mount_ref_offset[1]
        self.p.pcb_mount_ref_position[2] = 0.0 + self.p.pcb_mount_ref_offset[2]

        self.p.pcb_holder_position = copy.deepcopy(self.p.pcb_mount_ref_position)
        self.p.pcb_holder_position[0] = self.p.pcb_holder_position[0] + self.p.pcb_holder_offset[0]
        self.p.pcb_holder_position[1] = self.p.pcb_holder_position[1] + self.p.pcb_holder_offset[1]
        self.p.pcb_holder_position[2] = self.p.pcb_holder_position[2] + self.p.pcb_holder_offset[2]
        self.p.pcb_holder_thickness = self.p.pcb_holder_size[2]

        self.p.pcb_screw_position = copy.deepcopy(self.p.pcb_mount_ref_position)
        self.p.pcb_screw_position[1] = self.p.pcb_screw_position[1] + self.p.pcb_screw_y_offset

        if self.p.oled_center_row is not None:
            base_pt1 = self.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.p.oled_center_row - 1
            )
            base_pt2 = self.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.p.oled_center_row + 1
            )
            base_pt0 = self.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.p.oled_center_row
            )

            self.p.oled_mount_location_xyz = (np.array(base_pt1) + np.array(base_pt2)) / 2. + np.array(
                ((-self.p.left_wall_x_offset / 2), 0, 0)) + np.array(self.p.oled_translation_offset)
            self.p.oled_mount_location_xyz[2] = (self.p.oled_mount_location_xyz[2] + base_pt0[2]) / 2

            angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
            angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])

            self.p.oled_mount_rotation_xyz = (rad2deg(angle_x), 0, -rad2deg(angle_z)) + np.array(
                self.p.oled_rotation_offset)

    def column_offset(self, column: int) -> list:
        result = self.p.column_offsets[column]
        # if (pinky_1_5U and column == lastcol):
        #     result[0] = result[0] + 1
        return result

    def cluster(self, side="right"):
        return self.right_cluster if side == "right" else self.left_cluster

    #########################
    ## Placement Functions ##
    #########################

    def rotate_around_x(self, position, angle):
        # debugprint('rotate_around_x()')
        t_matrix = np.array(
            [
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)

    def rotate_around_y(self, position, angle):
        # debugprint('rotate_around_y()')
        t_matrix = np.array(
            [
                [np.cos(angle), 0, np.sin(angle)],
                [0, 1, 0],
                [-np.sin(angle), 0, np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)

    def apply_key_geometry(
            self,
            shape,
            translate_fn,
            rotate_x_fn,
            rotate_y_fn,
            column,
            row,
            column_style=None,
    ):
        if column_style is None:
            column_style = self.p.column_style
        debugprint('apply_key_geometry()')

        column_angle = self.p.beta * (self.p.centercol - column)

        column_x_delta_actual = self.p.column_x_delta
        if self.p.pinky_1_5U and column == self.p.lastcol:
            if self.p.first_1_5U_row <= row <= self.p.last_1_5U_row:
                column_x_delta_actual = self.p.column_x_delta - 1.5
                column_angle = self.p.beta * (self.p.centercol - column - 0.27)

        if column_style == "orthographic":
            column_z_delta = self.p.column_radius * (1 - np.cos(column_angle))
            shape = translate_fn(shape, [0, 0, -self.p.row_radius])
            shape = rotate_x_fn(shape, self.p.alpha * (self.p.centerrow - row))
            shape = translate_fn(shape, [0, 0, self.p.row_radius])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(
                shape, [-(column - self.p.centercol) * column_x_delta_actual, 0, column_z_delta]
            )
            shape = translate_fn(shape, self.p.column_offset(column))

        elif column_style == "fixed":
            shape = rotate_y_fn(shape, self.p.fixed_angles[column])
            shape = translate_fn(shape, [self.p.fixed_x[column], 0, self.p.fixed_z[column]])
            shape = translate_fn(shape, [0, 0, -(self.p.row_radius + self.p.fixed_z[column])])
            shape = rotate_x_fn(shape, self.p.alpha * (self.p.centerrow - row))
            shape = translate_fn(shape, [0, 0, self.p.row_radius + self.p.fixed_z[column]])
            shape = rotate_y_fn(shape, self.p.fixed_tenting)
            shape = translate_fn(shape, [0, self.p.column_offset(column)[1], 0])

        else:
            shape = translate_fn(shape, [0, 0, -self.p.row_radius])
            shape = rotate_x_fn(shape, self.p.alpha * (self.p.centerrow - row))
            shape = translate_fn(shape, [0, 0, self.p.row_radius])
            shape = translate_fn(shape, [0, 0, -self.p.column_radius])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(shape, [0, 0, self.p.column_radius])
            shape = translate_fn(shape, self.column_offset(column))

        shape = rotate_y_fn(shape, self.p.tenting_angle)
        shape = translate_fn(shape, [0, 0, self.p.keyboard_z_offset])

        return shape

    def valid_key(self, column, row):
        if not self.p.reduced_outer_keys:
            # if (full_last_rows):
            return (not (column in [0, 1])) or (not row == self.p.lastrow)

        return (column in [2, 3]) or (not row == self.p.lastrow)

    def x_rot(self, shape, angle):
        # debugprint('x_rot()')
        return self.g.rotate(shape, [rad2deg(angle), 0, 0])

    def y_rot(self, shape, angle):
        # debugprint('y_rot()')
        return self.g.rotate(shape, [0, rad2deg(angle), 0])

    def key_place(self, shape, column, row):
        debugprint('key_place()')
        return self.apply_key_geometry(shape, self.g.translate, self.x_rot, self.y_rot, column, row)

    def add_translate(self, shape, xyz):
        debugprint('add_translate()')
        vals = []
        for i in range(len(shape)):
            vals.append(shape[i] + xyz[i])
        return vals

    def plate_pcb_cutouts(self, side="right"):
        debugprint('plate_pcb_cutouts()')
        # hole = single_plate()
        cutouts = []
        for column in range(self.p.ncols):
            for row in range(self.p.nrows):
                if (column in [2, 3]) or (not row == self.p.lastrow):
                    cutouts.append(self.key_place(self.sh.plate_pcb_cutout(side=side), column, row))

        # cutouts = self.g.union(cutouts)

        return cutouts

    def key_position(self, position, column, row):
        debugprint('key_position()')
        return self.apply_key_geometry(
            position, self.add_translate, self.rotate_around_x, self.rotate_around_y, column, row
        )

    def key_holes(self, side="right"):
        debugprint('key_holes()')
        holes = []
        for column in range(self.p.ncols):
            for row in range(self.p.nrows):
                if self.valid_key(column, row):
                    holes.append(self.key_place(self.sh.single_plate(side=side), column, row))

        shape = self.g.union(holes)

        return shape

    def caps(self):
        caps = None
        for column in range(self.p.ncols):
            size = 1
            if self.p.pinky_1_5U and column == self.p.lastcol:
                if row >= self.p.first_1_5U_row and row <= self.p.last_1_5U_row:
                    size = 1.5
            for row in range(self.p.nrows):
                if self.valid_key(column, row):
                    if caps is None:
                        caps = self.key_place(self.sh.sa_cap(size), column, row)
                    else:
                        caps = self.g.add([caps, self.key_place(self.sh.sa_cap(size), column, row)])

        return caps

    def get_torow(self, column):
        torow = self.p.lastrow
        if self.p.full_last_rows:
            torow = self.p.lastrow + 1
        if column in [0, 1]:
            torow = self.p.lastrow
        return torow

    def connectors(self):
        debugprint('connectors()')
        hulls = []
        for column in range(self.p.ncols - 1):
            if (column in [2]) or (not self.p.reduced_outer_keys):
                iterrows = self.p.lastrow + 1
            else:
                iterrows = self.p.lastrow
            for row in range(iterrows):  # need to consider last_row?
                # for row in range(nrows):  # need to consider last_row?
                places = []
                places.append(self.key_place(self.sh.web_post_tl(), column + 1, row))
                places.append(self.key_place(self.sh.web_post_tr(), column, row))
                places.append(self.key_place(self.sh.web_post_bl(), column + 1, row))
                places.append(self.key_place(self.sh.web_post_br(), column, row))
                hulls.append(self.g.triangle_hulls(places))

        for column in range(self.p.ncols):
            if (column in [2, 3]) or (not self.p.reduced_outer_keys):
                iterrows = self.p.lastrow
            else:
                iterrows = self.p.cornerrow
            for row in range(iterrows):
                places = []
                places.append(self.key_place(self.sh.web_post_bl(), column, row))
                places.append(self.key_place(self.sh.web_post_br(), column, row))
                places.append(self.key_place(self.sh.web_post_tl(), column, row + 1))
                places.append(self.key_place(self.sh.web_post_tr(), column, row + 1))
                hulls.append(self.g.triangle_hulls(places))

        for column in range(self.p.ncols - 1):
            if (column in [2]) or (not self.p.reduced_outer_keys):
                iterrows = self.p.lastrow
            else:
                iterrows = self.p.cornerrow
            for row in range(iterrows):
                places = []
                places.append(self.key_place(self.sh.web_post_br(), column, row))
                places.append(self.key_place(self.sh.web_post_tr(), column, row + 1))
                places.append(self.key_place(self.sh.web_post_bl(), column + 1, row))
                places.append(self.key_place(self.sh.web_post_tl(), column + 1, row + 1))
                hulls.append(self.g.triangle_hulls(places))

            if self.p.reduced_outer_keys:
                if column == 1:
                    places = []
                    places.append(self.key_place(self.sh.web_post_bl(), column + 1, iterrows))
                    places.append(self.key_place(self.sh.web_post_br(), column, iterrows))
                    places.append(self.key_place(self.sh.web_post_tl(), column + 1, iterrows + 1))
                    places.append(self.key_place(self.sh.web_post_bl(), column + 1, iterrows + 1))
                    hulls.append(self.g.triangle_hulls(places))
                if column == 3:
                    places = []
                    places.append(self.key_place(self.sh.web_post_br(), column, iterrows))
                    places.append(self.key_place(self.sh.web_post_bl(), column + 1, iterrows))
                    places.append(self.key_place(self.sh.web_post_tr(), column, iterrows + 1))
                    places.append(self.key_place(self.sh.web_post_br(), column, iterrows + 1))
                    hulls.append(self.g.triangle_hulls(places))

        return self.g.union(hulls)

    # def thumb_pcb_plate_cutouts(self, side='right', style_override=None):
    #     if style_override is None:
    #         _thumb_style = thumb_style
    #     else:
    #         _thumb_style = style_override
    #
    #     if _thumb_style == "MINI":
    #         return mini_thumb_pcb_plate_cutouts(side)
    #     elif _thumb_style == "MINIDOX":
    #         return minidox_thumb_pcb_plate_cutouts(side)
    #     elif _thumb_style == "CARBONFET":
    #         return carbonfet_thumb_pcb_plate_cutouts(side)
    #
    #     elif "TRACKBALL" in _thumb_style:
    #         if (side == ball_side or ball_side == 'both'):
    #             if _thumb_style == "TRACKBALL_ORBYL":
    #                 return tbjs_thumb_pcb_plate_cutouts(side)
    #             elif _thumb_style == "TRACKBALL_CJ":
    #                 return tbcj_thumb_pcb_plate_cutouts(side)
    #         else:
    #             return thumb_pcb_plate_cutouts(side, style_override=other_thumb)
    #
    #     else:
    #         return default_thumb_pcb_plate_cutouts(side)

    ##########
    ## Case ##
    ##########

    def left_key_position(self, row, direction, low_corner=False, side='right'):
        debugprint("left_key_position()")
        pos = np.array(
            self.key_position([-self.p.mount_width * 0.5, direction * self.p.mount_height * 0.5, 0], 0, row)
        )
        if self.p.trackball_in_wall and (side == self.p.ball_side or self.p.ball_side == 'both'):

            if low_corner:
                x_offset = self.p.tbiw_left_wall_lower_x_offset
                y_offset = self.p.tbiw_left_wall_lower_y_offset
                z_offset = self.p.tbiw_left_wall_lower_z_offset
            else:
                x_offset = 0.0
                y_offset = 0.0
                z_offset = 0.0

            return list(pos - np.array([
                self.p.tbiw_left_wall_x_offset_override - x_offset,
                -y_offset,
                self.p.tbiw_left_wall_z_offset_override + z_offset
            ]))

        if low_corner:
            x_offset = self.p.left_wall_lower_x_offset
            y_offset = self.p.left_wall_lower_y_offset
            z_offset = self.p.left_wall_lower_z_offset
        else:
            x_offset = 0.0
            y_offset = 0.0
            z_offset = 0.0

        return list(pos - np.array([self.p.left_wall_x_offset - x_offset, -y_offset, self.p.left_wall_z_offset + z_offset]))

    def left_key_place(self, shape, row, direction, low_corner=False, side='right'):
        debugprint("left_key_place()")
        pos = self.left_key_position(row, direction, low_corner=low_corner, side=side)
        return self.g.translate(shape, pos)

    def wall_locate1(self, dx, dy):
        debugprint("wall_locate1()")
        return [dx * self.p.wall_thickness, dy * self.p.wall_thickness, -1]

    def wall_locate2(self, dx, dy):
        debugprint("wall_locate2()")
        return [dx * self.p.wall_x_offset, dy * self.p.wall_y_offset, -self.p.wall_z_offset]

    def wall_locate3(self, dx, dy, back=False):
        debugprint("wall_locate3()")
        if back:
            return [
                dx * (self.p.wall_x_offset + self.p.wall_base_x_thickness),
                dy * (self.p.wall_y_offset + self.p.wall_base_back_thickness),
                -self.p.wall_z_offset,
            ]
        else:
            return [
                dx * (self.p.wall_x_offset + self.p.wall_base_x_thickness),
                dy * (self.p.wall_y_offset + self.p.wall_base_y_thickness),
                -self.p.wall_z_offset,
            ]

    def wall_brace(self, place1, dx1, dy1, post1, place2, dx2, dy2, post2, back=False, skeleton=False,
                   skel_bottom=False):
        debugprint("wall_brace()")
        hulls = []

        hulls.append(place1(post1))
        if not skeleton:
            hulls.append(place1(self.g.translate(post1, self.wall_locate1(dx1, dy1))))
            hulls.append(place1(self.g.translate(post1, self.wall_locate2(dx1, dy1))))
        if not skeleton or skel_bottom:
            hulls.append(place1(self.g.translate(post1, self.wall_locate3(dx1, dy1, back))))

        hulls.append(place2(post2))
        if not skeleton:
            hulls.append(place2(self.g.translate(post2, self.wall_locate1(dx2, dy2))))
            hulls.append(place2(self.g.translate(post2, self.wall_locate2(dx2, dy2))))

        if not skeleton or skel_bottom:
            hulls.append(place2(self.g.translate(post2, self.wall_locate3(dx2, dy2, back))))

        shape1 = self.g.hull_from_shapes(hulls)

        hulls = []
        if not skeleton:
            hulls.append(place1(self.g.translate(post1, self.wall_locate2(dx1, dy1))))
        if not skeleton or skel_bottom:
            hulls.append(place1(self.g.translate(post1, self.wall_locate3(dx1, dy1, back))))
        if not skeleton:
            hulls.append(place2(self.g.translate(post2, self.wall_locate2(dx2, dy2))))
        if not skeleton or skel_bottom:
            hulls.append(place2(self.g.translate(post2, self.wall_locate3(dx2, dy2, back))))

        if len(hulls) > 0:
            shape2 = self.g.bottom_hull(hulls)
            shape1 = self.g.union([shape1, shape2])
            # shape1 = add([shape1, shape2])

        return shape1

    def key_wall_brace(self, x1, y1, dx1, dy1, post1, x2, y2, dx2, dy2, post2, back=False, skeleton=False,
                       skel_bottom=False):
        debugprint("key_wall_brace()")
        return self.wall_brace(
            (lambda shape: self.key_place(shape, x1, y1)),
            dx1,
            dy1,
            post1,
            (lambda shape: self.key_place(shape, x2, y2)),
            dx2,
            dy2,
            post2,
            back,
            skeleton=skeleton,
            skel_bottom=False,
        )

    def back_wall(self, skeleton=False):
        print("back_wall()")
        x = 0
        shape = None
        shape = self.g.union([shape, self.key_wall_brace(
            x, 0, 0, 1, self.sh.web_post_tl(), x, 0, 0, 1, self.sh.web_post_tr(), back=True,
        )])
        for i in range(self.p.ncols - 1):
            x = i + 1
            shape = self.g.union([shape, self.key_wall_brace(
                x, 0, 0, 1, self.sh.web_post_tl(), x, 0, 0, 1, self.sh.web_post_tr(), back=True,
            )])

            skelly = skeleton and not x == 1
            shape = self.g.union([shape, self.key_wall_brace(
                x, 0, 0, 1, self.sh.web_post_tl(), x - 1, 0, 0, 1, self.sh.web_post_tr(), back=True,
                skeleton=skelly, skel_bottom=True,
            )])

        shape = self.g.union([shape, self.key_wall_brace(
            self.p.lastcol, 0, 0, 1, self.sh.web_post_tr(), self.p.lastcol, 0, 1, 0, self.sh.web_post_tr(), back=True,
            skeleton=skeleton, skel_bottom=True,
        )])
        if not skeleton:
            shape = self.g.union([shape,
                           self.key_wall_brace(
                               self.p.lastcol, 0, 0, 1, self.sh.web_post_tr(), self.p.lastcol, 0, 1, 0, self.sh.web_post_tr()
                           )
                           ])
        return shape

    def right_wall(self, skeleton=False):
        print("right_wall()")
        y = 0

        shape = None

        shape = self.g.union([shape, self.key_wall_brace(
            self.p.lastcol, y, 1, 0, self.sh.web_post_tr(), self.p.lastcol, y, 1, 0, self.sh.web_post_br(),
            skeleton=skeleton,
        )])

        for i in range(self.p.cornerrow):
            y = i + 1
            shape = self.g.union([shape, self.key_wall_brace(
                self.p.lastcol, y - 1, 1, 0, self.sh.web_post_br(), self.p.lastcol, y, 1, 0, self.sh.web_post_tr(),
                skeleton=skeleton,
            )])

            shape = self.g.union([shape, self.key_wall_brace(
                self.p.lastcol, y, 1, 0, self.sh.web_post_tr(), self.p.lastcol, y, 1, 0, self.sh.web_post_br(),
                skeleton=skeleton,
            )])
            # STRANGE PARTIAL OFFSET

        shape = self.g.union([
            shape,
            self.key_wall_brace(
                self.p.lastcol, self.p.cornerrow, 0, -1, self.sh.web_post_br(),
                self.p.lastcol, self.p.cornerrow, 1, 0, self.sh.web_post_br(),
                skeleton=skeleton
            ),
        ])

        return shape

    def left_wall(self, side='right', skeleton=False):
        print('left_wall()')
        shape = self.g.union([self.wall_brace(
            (lambda sh: self.key_place(sh, 0, 0)), 0, 1, self.sh.web_post_tl(),
            (lambda sh: self.left_key_place(sh, 0, 1, side=side)), 0, 1, self.sh.web_post(),
        )])

        shape = self.g.union([shape, self.wall_brace(
            (lambda sh: self.left_key_place(sh, 0, 1, side=side)), 0, 1, self.sh.web_post(),
            (lambda sh: self.left_key_place(sh, 0, 1, side=side)), -1, 0, self.sh.web_post(),
            skeleton=skeleton,
        )])

        # for i in range(lastrow):
        for i in range(self.p.cornerrow + 1):
            y = i
            low = (y == (self.p.cornerrow))
            temp_shape1 = self.wall_brace(
                (lambda sh: self.left_key_place(sh, y, 1, side=side)), -1, 0, self.sh.web_post(),
                (lambda sh: self.left_key_place(sh, y, -1, low_corner=low, side=side)), -1, 0, self.sh.web_post(),
                skeleton=skeleton and (y < (self.p.cornerrow)),
            )
            shape = self.g.union([shape, temp_shape1])

            temp_shape2 = self.g.hull_from_shapes((
                self.key_place(self.sh.web_post_tl(), 0, y),
                self.key_place(self.sh.web_post_bl(), 0, y),
                self.left_key_place(self.sh.web_post(), y, 1, side=side),
                self.left_key_place(self.sh.web_post(), y, -1, low_corner=low, side=side),
            ))

            shape = self.g.union([shape, temp_shape2])

        for i in range(self.p.cornerrow):
            y = i + 1
            low = (y == (self.p.cornerrow))
            temp_shape1 = self.wall_brace(
                (lambda sh: self.left_key_place(sh, y - 1, -1, side=side)), -1, 0, self.sh.web_post(),
                (lambda sh: self.left_key_place(sh, y, 1, side=side)), -1, 0, self.sh.web_post(),
                skeleton=skeleton and (y < (self.p.cornerrow)),
            )
            shape = self.g.union([shape, temp_shape1])

            temp_shape2 = self.g.hull_from_shapes((
                self.key_place(self.sh.web_post_tl(), 0, y),
                self.key_place(self.sh.web_post_bl(), 0, y - 1),
                self.left_key_place(self.sh.web_post(), y, 1, side=side),
                self.left_key_place(self.sh.web_post(), y - 1, -1, side=side),
            ))

            shape = self.g.union([shape, temp_shape2])

        return shape

    def front_wall(self, side='right', skeleton=False):
        print('front_wall()')
        shape = None

        shape = self.g.union([shape, self.key_wall_brace(
            3, self.p.lastrow, 0, -1, self.sh.web_post_bl(),
            3, self.p.lastrow, 0.5, -1, self.sh.web_post_br()
        )])

        shape = self.g.union([shape, self.key_wall_brace(
            3, self.p.lastrow, 0.5, -1, self.sh.web_post_br(),
            4, self.p.cornerrow, .5, -1, self.sh.web_post_bl()
        )])
        shape = self.g.union([shape, self.key_wall_brace(
            4, self.p.cornerrow, .5, -1, self.sh.web_post_bl(),
            4, self.p.cornerrow, 0, -1, self.sh.web_post_br()
        )])

        for i in range(self.p.ncols - 5):
            x = i + 5

            shape = self.g.union([shape, self.key_wall_brace(
                x, self.p.cornerrow, 0, -1, self.sh.web_post_bl(), 
                x, self.p.cornerrow, 0, -1, self.sh.web_post_br()
            )])

            shape = self.g.union([shape, self.key_wall_brace(
                x, self.p.cornerrow, 0, -1, self.sh.web_post_bl(), 
                x - 1, self.p.cornerrow, 0, -1, self.sh.web_post_br()
            )])

        return shape

    def case_walls(self, side='right', skeleton=False):
        print('case_walls()')
        return (
            self.g.union([
                self.back_wall(skeleton=skeleton),
                self.left_wall(side=side, skeleton=skeleton),
                self.right_wall(skeleton=skeleton),
                self.front_wall(skeleton=skeleton),
                # MOVED TO SEPARABLE THUMB SECTION
                # cluster(side=side).walls(side=side),
                # cluster(side=side).connection(side=side),
            ])
        )

    def rj9_cube(self):
        debugprint('rj9_cube()')
        shape = self.g.box(14.78, 13, 22.38)

        return shape

    def rj9_space(self):
        debugprint('rj9_space()')
        return self.g.translate(self.rj9_cube(), self.rj9_position)

    def rj9_holder(self):
        print('rj9_holder()')
        shape = self.g.union([
            self.g.translate(self.g.box(10.78, 9, 18.38), (0, 2, 0)),
            self.g.translate(self.g.box(10.78, 13, 5), (0, 0, 5))
        ])
        shape = self.g.difference(self.rj9_cube(), [shape])
        shape = self.g.translate(shape, self.self.p.rj9_position)

        return shape

    def usb_holder(self):
        print('usb_holder()')
        shape = self.g.box(
            self.p.usb_holder_size[0] + self.p.usb_holder_thickness,
            self.p.usb_holder_size[1],
            self.p.usb_holder_size[2] + self.p.usb_holder_thickness,
        )
        shape = self.g.translate(shape,
                          (
                              self.p.usb_holder_position[0],
                              self.p.usb_holder_position[1],
                              (self.p.usb_holder_size[2] + self.p.usb_holder_thickness) / 2,
                          )
                          )
        return shape

    def usb_holder_hole(self):
        debugprint('usb_holder_hole()')
        shape = self.g.box(*self.p.usb_holder_size)
        shape = self.g.translate(shape,
                          (
                              self.p.usb_holder_position[0],
                              self.p.usb_holder_position[1],
                              (self.p.usb_holder_size[2] + self.p.usb_holder_thickness) / 2,
                          )
                          )
        return shape

    def external_mount_hole(self):
        print('external_mount_hole()')
        shape = self.g.box(self.p.external_holder_width, 20.0, self.p.external_holder_height + .1)
        undercut = self.g.box(self.p.external_holder_width + 8, 10.0, self.p.external_holder_height + 8 + .1)
        shape = self.g.union([shape, self.g.translate(undercut, (0, -5, 0))])

        shape = self.g.translate(shape,
                                 (
                                     self.p.external_start[0] + self.p.external_holder_xoffset,
                                     self.p.external_start[1] + self.p.external_holder_yoffset,
                                     self.p.external_holder_height / 2 - .05,
                                 )
                                 )
        return shape

    def pcb_usb_hole(self):
        debugprint('pcb_holder()')
        pcb_usb_position = copy.deepcopy(self.p.pcb_mount_ref_position)
        pcb_usb_position[0] = pcb_usb_position[0] + self.p.pcb_usb_hole_offset[0]
        pcb_usb_position[1] = pcb_usb_position[1] + self.p.pcb_usb_hole_offset[1]
        pcb_usb_position[2] = pcb_usb_position[2] + self.p.pcb_usb_hole_offset[2]

        shape = self.g.box(*self.p.pcb_usb_hole_size)
        shape = self.g.translate(shape,
                          (
                              pcb_usb_position[0],
                              pcb_usb_position[1],
                              self.p.pcb_usb_hole_size[2] / 2 + self.p.usb_holder_thickness,
                          )
                          )
        return shape

    def pcb_holder(self):
        debugprint('pcb_holder()')
        shape = self.g.box(*self.p.pcb_holder_size)
        shape = self.g.translate(shape,
                          (
                              self.p.pcb_holder_position[0],
                              self.p.pcb_holder_position[1] - self.p.pcb_holder_size[1] / 2,
                              self.p.pcb_holder_thickness / 2,
                          )
                          )
        return shape

    def wall_thinner(self):
        debugprint('wall_thinner()')
        shape = self.g.box(*self.p.wall_thinner_size)
        shape = self.g.translate(shape,
                          (
                              self.p.pcb_holder_position[0],
                              self.p.pcb_holder_position[1] - self.p.wall_thinner_size[1] / 2,
                              self.p.wall_thinner_size[2] / 2 + self.p.pcb_holder_thickness,
                          )
                          )
        return shape

    def trrs_hole(self):
        debugprint('trrs_hole()')
        trrs_position = copy.deepcopy(self.p.pcb_mount_ref_position)
        trrs_position[0] = trrs_position[0] + self.p.trrs_offset[0]
        trrs_position[1] = trrs_position[1] + self.p.trrs_offset[1]
        trrs_position[2] = trrs_position[2] + self.p.trrs_offset[2]

        trrs_hole_size = [3, 20]

        shape = self.g.cylinder(*trrs_hole_size)
        shape = self.g.rotate(shape, [0, 90, 90])
        shape = self.g.translate(shape,
                          (
                              trrs_position[0],
                              trrs_position[1],
                              trrs_hole_size[0] + self.p.pcb_holder_thickness,
                          )
                          )
        return shape

    def pcb_screw_hole(self):
        debugprint('pcb_screw_hole()')
        holes = []
        hole = self.g.cylinder(*self.p.pcb_screw_hole_size)
        hole = self.g.translate(hole, self.p.pcb_screw_position)
        hole = self.g.translate(hole, (0, 0, self.p.pcb_screw_hole_size[1] / 2 - .1))
        for offset in self.p.pcb_screw_x_offsets:
            holes.append(self.g.translate(hole, (offset, 0, 0)))

        return holes

    def generate_trackball(self, pos, rot):
        precut = self.sh.trackball_cutout()
        precut = self.g.rotate(precut, self.p.tb_socket_rotation_offset)
        precut = self.g.translate(precut, self.p.tb_socket_translation_offset)
        precut = self.g.rotate(precut, rot)
        precut = self.g.translate(precut, pos)

        shape, cutout, sensor = self.sh.trackball_socket()

        shape = self.g.rotate(shape, self.p.tb_socket_rotation_offset)
        shape = self.g.translate(shape, self.p.tb_socket_translation_offset)
        shape = self.g.rotate(shape, rot)
        shape = self.g.translate(shape, pos)

        cutout = self.g.rotate(cutout, self.p.tb_socket_rotation_offset)
        cutout = self.g.translate(cutout, self.p.tb_socket_translation_offset)
        # cutout = self.g.rotate(cutout, tb_sensor_translation_offset)
        # cutout = self.g.translate(cutout, tb_sensor_rotation_offset)
        cutout = self.g.rotate(cutout, rot)
        cutout = self.g.translate(cutout, pos)

        # Small adjustment due to line to line surface / minute numerical error issues
        # Creates small overlap to assist engines in union function later
        sensor = self.g.rotate(sensor, self.p.tb_socket_rotation_offset)
        sensor = self.g.translate(sensor, self.p.tb_socket_translation_offset)
        # sensor = self.g.rotate(sensor, tb_sensor_translation_offset)
        # sensor = self.g.translate(sensor, tb_sensor_rotation_offset)
        sensor = self.g.translate(sensor, (0, 0, .005))
        sensor = self.g.rotate(sensor, rot)
        sensor = self.g.translate(sensor, pos)

        ball = self.sh.trackball_ball()
        ball = self.g.rotate(ball, self.p.tb_socket_rotation_offset)
        ball = self.g.translate(ball, self.p.tb_socket_translation_offset)
        ball = self.g.rotate(ball, rot)
        ball = self.g.translate(ball, pos)

        # return precut, shape, cutout, ball
        return precut, shape, cutout, sensor, ball

    def generate_trackball_in_cluster(self, cluster):
        pos, rot = cluster.position_rotation() if self.p.ball_side != "left" else self.left_cluster.position_rotation()
        return self.generate_trackball(pos, rot)

    def tbiw_position_rotation(self):
        base_pt1 = self.key_position(
            list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])),
            0, self.p.cornerrow - self.p.tbiw_ball_center_row - 1
        )
        base_pt2 = self.key_position(
            list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])),
            0, self.p.cornerrow - self.p.tbiw_ball_center_row + 1
        )
        base_pt0 = self.key_position(
            list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])),
            0, self.p.cornerrow - self.p.tbiw_ball_center_row
        )

        left_wall_x_offset = self.p.tbiw_left_wall_x_offset_override

        tbiw_mount_location_xyz = (
                (np.array(base_pt1) + np.array(base_pt2)) / 2.
                + np.array(((-left_wall_x_offset / 2), 0, 0))
                + np.array(self.p.tbiw_translational_offset)
        )

        # tbiw_mount_location_xyz[2] = (oled_translation_offset[2] + base_pt0[2])/2

        angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
        angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
        tbiw_mount_rotation_xyz = (rad2deg(angle_x), 0, rad2deg(angle_z)) + np.array(self.p.tbiw_rotation_offset)

        return tbiw_mount_location_xyz, tbiw_mount_rotation_xyz

    def generate_trackball_in_wall(self):
        pos, rot = self.tbiw_position_rotation()
        return self.generate_trackball(pos, rot)

    def oled_position_rotation(self, side='right'):
        _oled_center_row = None
        _oled_translation_offset = None
        if self.p.trackball_in_wall and (side == self.p.ball_side or self.p.ball_side == 'both'):
            _oled_center_row = self.p.tbiw_oled_center_row
            _oled_translation_offset = self.p.tbiw_oled_translation_offset
            _oled_rotation_offset = self.p.tbiw_oled_rotation_offset

        elif self.p.oled_center_row is not None:
            _oled_center_row = self.p.oled_center_row
            _oled_translation_offset = self.p.oled_translation_offset
            _oled_rotation_offset = self.p.oled_rotation_offset

        if _oled_center_row is not None:
            base_pt1 = self.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, _oled_center_row - 1
            )
            base_pt2 = self.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, _oled_center_row + 1
            )
            base_pt0 = self.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, _oled_center_row
            )

            if self.p.trackball_in_wall and (side == self.p.ball_side or self.p.ball_side == 'both'):
                _left_wall_x_offset = self.p.tbiw_left_wall_x_offset_override
            else:
                _left_wall_x_offset = self.p.left_wall_x_offset

            oled_mount_location_xyz = (np.array(base_pt1) + np.array(base_pt2)) / 2. + np.array(
                ((-_left_wall_x_offset / 2), 0, 0)) + np.array(_oled_translation_offset)
            oled_mount_location_xyz[2] = (oled_mount_location_xyz[2] + base_pt0[2]) / 2

            angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
            angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
            if self.p.trackball_in_wall and (side == self.p.ball_side or self.p.ball_side == 'both'):
                # oled_mount_rotation_xyz = (0, rad2deg(angle_x), -rad2deg(angle_z)-90) + np.array(oled_rotation_offset)
                # oled_mount_rotation_xyz = (rad2deg(angle_x)*.707, rad2deg(angle_x)*.707, -45) + np.array(oled_rotation_offset)
                oled_mount_rotation_xyz = (0, rad2deg(angle_x), -90) + np.array(_oled_rotation_offset)
            else:
                oled_mount_rotation_xyz = (rad2deg(angle_x), 0, -rad2deg(angle_z)) + np.array(_oled_rotation_offset)

        return oled_mount_location_xyz, oled_mount_rotation_xyz

    def oled_sliding_mount_frame(self, side='right'):
        mount_ext_width = self.p.oled_mount_width + 2 * self.p.oled_mount_rim
        mount_ext_height = (
                self.p.oled_mount_height + 2 * self.p.oled_edge_overlap_end
                + self.p.oled_edge_overlap_connector + self.p.oled_edge_overlap_clearance
                + 2 *self.p.oled_mount_rim
        )
        mount_ext_up_height = self.p.oled_mount_height + 2 * self.p.oled_mount_rim
        top_hole_start = -mount_ext_height / 2.0 + self.p.oled_mount_rim + self.p.oled_edge_overlap_end + self.p.oled_edge_overlap_connector
        top_hole_length = self.p.oled_mount_height

        hole = self.g.box(mount_ext_width, mount_ext_up_height, self.p.oled_mount_cut_depth + .01)
        hole = self.g.translate(hole, (0., top_hole_start + top_hole_length / 2, 0.))

        hole_down = self.g.box(mount_ext_width, mount_ext_height, self.p.oled_mount_depth + self.p.oled_mount_cut_depth / 2)
        hole_down = self.g.translate(hole_down, (0., 0., -self.p.oled_mount_cut_depth / 4))
        hole = self.g.union([hole, hole_down])

        shape = self.g.box(mount_ext_width, mount_ext_height, self.p.oled_mount_depth)

        conn_hole_start = -mount_ext_height / 2.0 + self.p.oled_mount_rim
        conn_hole_length = (
                self.p.oled_edge_overlap_end + self.p.oled_edge_overlap_connector
                + self.p.oled_edge_overlap_clearance + self.p.oled_thickness
        )
        conn_hole = self.g.box(self.p.oled_mount_width, conn_hole_length + .01, self.p.oled_mount_depth)
        conn_hole = self.g.translate(conn_hole, (
            0,
            conn_hole_start + conn_hole_length / 2,
            -self.p.oled_edge_overlap_thickness
        ))

        end_hole_length = (
                self.p.oled_edge_overlap_end + self.p.oled_edge_overlap_clearance
        )
        end_hole_start = mount_ext_height / 2.0 - self.p.oled_mount_rim - end_hole_length
        end_hole = self.g.box(self.p.oled_mount_width, end_hole_length + .01, self.p.oled_mount_depth)
        end_hole = self.g.translate(end_hole, (
            0,
            end_hole_start + end_hole_length / 2,
            -self.p.oled_edge_overlap_thickness
        ))

        top_hole_start = -mount_ext_height / 2.0 + self.p.oled_mount_rim + self.p.oled_edge_overlap_end + self.p.oled_edge_overlap_connector
        top_hole_length = self.p.oled_mount_height
        top_hole = self.g.box(self.p.oled_mount_width, top_hole_length,
                       self.p.oled_edge_overlap_thickness + self.p.oled_thickness - self.p.oled_edge_chamfer)
        top_hole = self.g.translate(top_hole, (
            0,
            top_hole_start + top_hole_length / 2,
            (self.p.oled_mount_depth - self.p.oled_edge_overlap_thickness - self.p.oled_thickness - self.p.oled_edge_chamfer) / 2.0
        ))

        top_chamfer_1 = self.g.box(
            self.p.oled_mount_width,
            top_hole_length,
            0.01
        )
        top_chamfer_2 = self.g.box(
            self.p.oled_mount_width + 2 * self.p.oled_edge_chamfer,
            top_hole_length + 2 * self.p.oled_edge_chamfer,
            0.01
        )
        top_chamfer_1 = self.g.translate(top_chamfer_1, (0, 0, -self.p.oled_edge_chamfer - .05))

        top_chamfer_1 = self.g.hull_from_shapes([top_chamfer_1, top_chamfer_2])

        top_chamfer_1 = self.g.translate(top_chamfer_1, (
            0,
            top_hole_start + top_hole_length / 2,
            self.p.oled_mount_depth / 2.0 + .05
        ))

        top_hole = self.g.union([top_hole, top_chamfer_1])

        shape = self.g.difference(shape, [conn_hole, top_hole, end_hole])

        oled_mount_location_xyz, oled_mount_rotation_xyz = self.oled_position_rotation(side=side)

        shape = self.g.rotate(shape, oled_mount_rotation_xyz)
        shape = self.g.translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = self.g.rotate(hole, oled_mount_rotation_xyz)
        hole = self.g.translate(hole,
                         (
                             oled_mount_location_xyz[0],
                             oled_mount_location_xyz[1],
                             oled_mount_location_xyz[2],
                         )
                         )
        return hole, shape

    def oled_clip_mount_frame(self, side='right'):
        mount_ext_width = self.p.oled_config.oled_mount_width + 2 * self.p.oled_config.oled_mount_rim
        mount_ext_height = (
                self.p.oled_config.oled_mount_height + 2 * self.p.oled_config.oled_clip_thickness
                + 2 * self.p.oled_config.oled_clip_undercut + 2 * self.p.oled_config.oled_clip_overhang + 2 * self.p.oled_config.oled_mount_rim
        )
        hole = self.g.box(mount_ext_width, mount_ext_height, self.p.oled_config.oled_mount_cut_depth + .01)

        shape = self.g.box(mount_ext_width, mount_ext_height, self.p.oled_config.oled_mount_depth)
        shape = self.g.difference(shape, [self.g.box(self.p.oled_config.oled_mount_width, self.p.oled_config.oled_mount_height, self.p.oled_config.oled_mount_depth + .1)])

        clip_slot = self.g.box(
            self.p.oled_config.oled_clip_width + 2 * self.p.oled_config.oled_clip_width_clearance,
            self.p.oled_config.oled_mount_height + 2 * self.p.oled_config.oled_clip_thickness + 2 * self.p.oled_config.oled_clip_overhang,
            self.p.oled_config.oled_mount_depth + .1
        )

        shape = self.g.difference(shape, [clip_slot])

        clip_undercut = self.g.box(
            self.p.oled_config.oled_clip_width + 2 * self.p.oled_config.oled_clip_width_clearance,
            self.p.oled_config.oled_mount_height + 2 * self.p.oled_config.oled_clip_thickness + 2 * self.p.oled_config.oled_clip_overhang + 2 * self.p.oled_config.oled_clip_undercut,
            self.p.oled_config.oled_mount_depth + .1
        )

        clip_undercut = self.g.translate(clip_undercut, (0., 0., self.p.oled_config.oled_clip_undercut_thickness))
        shape = self.g.difference(shape, [clip_undercut])

        plate = self.g.box(
            self.p.oled_config.oled_mount_width + .1,
            self.p.oled_config.oled_mount_height - 2 * self.p.oled_config.oled_mount_connector_hole,
            self.p.oled_config.oled_mount_depth - self.p.oled_config.oled_thickness
        )
        plate = self.g.translate(plate, (0., 0., -self.p.oled_config.oled_thickness / 2.0))
        shape = self.g.union([shape, plate])

        oled_mount_location_xyz, oled_mount_rotation_xyz = self.oled_position_rotation(side=side)

        shape = self.g.rotate(shape, oled_mount_rotation_xyz)
        shape = self.g.translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = self.g.rotate(hole, oled_mount_rotation_xyz)
        hole = self.g.translate(hole,
                         (
                             oled_mount_location_xyz[0],
                             oled_mount_location_xyz[1],
                             oled_mount_location_xyz[2],
                         )
                         )

        return hole, shape

    def oled_clip(self):
        mount_ext_width = self.p.oled_config.oled_mount_width + 2 * self.p.oled_config.oled_mount_rim
        mount_ext_height = (
                self.p.oled_config.oled_mount_height + 2 * self.p.oled_config.oled_clip_thickness + 2 * self.p.oled_config.oled_clip_overhang
                + 2 * self.p.oled_config.oled_clip_undercut + 2 * self.p.oled_config.oled_mount_rim
        )

        oled_leg_depth = self.p.oled_config.oled_mount_depth + self.p.oled_config.oled_clip_z_gap

        shape = self.g.box(mount_ext_width - .1, mount_ext_height - .1, self.p.oled_config.oled_mount_bezel_thickness)
        shape = self.g.translate(shape, (0., 0., self.p.oled_config.oled_mount_bezel_thickness / 2.))

        hole_1 = self.g.box(
            self.p.oled_config.oled_screen_width + 2 * self.p.oled_config.oled_mount_bezel_chamfer,
            self.p.oled_config.oled_screen_length + 2 * self.p.oled_config.oled_mount_bezel_chamfer,
            .01
        )
        hole_2 = self.g.box(self.p.oled_config.oled_screen_width, self.p.oled_config.oled_screen_length, 2.05 * self.p.oled_config.oled_mount_bezel_thickness)
        hole = self.g.hull_from_shapes([hole_1, hole_2])

        shape = self.g.difference(shape, [self.g.translate(hole, (0., 0., self.p.oled_config.oled_mount_bezel_thickness))])

        clip_leg = self.g.box(self.p.oled_config.oled_clip_width, self.p.oled_config.oled_clip_thickness, oled_leg_depth)
        clip_leg = self.g.translate(clip_leg, (
            0.,
            0.,
            # (oled_mount_height+2*oled_clip_overhang+oled_clip_thickness)/2,
            -oled_leg_depth / 2.
        ))

        latch_1 = self.g.box(
            self.p.oled_config.oled_clip_width,
            self.p.oled_config.oled_clip_overhang + self.p.oled_config.oled_clip_thickness,
            .01
        )
        latch_2 = self.g.box(
            self.p.oled_config.oled_clip_width,
            self.p.oled_config.oled_clip_thickness / 2,
            self.p.oled_config.oled_clip_extension
        )
        latch_2 = self.g.translate(latch_2, (
            0.,
            -(-self.p.oled_config.oled_clip_thickness / 2 + self.p.oled_config.oled_clip_thickness + self.p.oled_config.oled_clip_overhang) / 2,
            -self.p.oled_config.oled_clip_extension / 2
        ))
        latch = self.g.hull_from_shapes([latch_1, latch_2])
        latch = self.g.translate(latch, (
            0.,
            self.p.oled_config.oled_clip_overhang / 2,
            -oled_leg_depth
        ))

        clip_leg = self.g.union([clip_leg, latch])

        clip_leg = self.g.translate(clip_leg, (
            0.,
            (self.p.oled_config.oled_mount_height + 2 * self.p.oled_config.oled_clip_overhang + self.p.oled_config.oled_clip_thickness) / 2 - self.p.oled_config.oled_clip_y_gap,
            0.
        ))

        shape = self.g.union([shape, clip_leg, self.g.mirror(clip_leg, 'XZ')])

        return shape

    def oled_undercut_mount_frame(self, side='right'):
        mount_ext_width = self.p.oled_config.oled_mount_width + 2 * self.p.oled_config.oled_mount_rim
        mount_ext_height = self.p.oled_config.oled_mount_height + 2 * self.p.oled_config.oled_mount_rim
        hole = self.g.box(mount_ext_width, mount_ext_height, self.p.oled_config.oled_mount_cut_depth + .01)

        shape = self.g.box(mount_ext_width, mount_ext_height, self.p.oled_config.oled_mount_depth)
        shape = self.g.difference(shape, [self.g.box(self.p.oled_config.oled_mount_width, self.p.oled_config.oled_mount_height, self.p.oled_config.oled_mount_depth + .1)])
        undercut = self.g.box(
            self.p.oled_config.oled_mount_width + 2 * self.p.oled_config.oled_mount_undercut,
            self.p.oled_config.oled_mount_height + 2 * self.p.oled_config.oled_mount_undercut,
            self.p.oled_config.oled_mount_depth)
        undercut = self.g.translate(undercut, (0., 0., -self.p.oled_config.oled_mount_undercut_thickness))
        shape = self.g.difference(shape, [undercut])

        oled_mount_location_xyz, oled_mount_rotation_xyz = self.oled_position_rotation(side=side)

        shape = self.g.rotate(shape, oled_mount_rotation_xyz)
        shape = self.g.translate(shape, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                          )

        hole = self.g.rotate(hole, oled_mount_rotation_xyz)
        hole = self.g.translate(hole, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                         )

        return hole, shape

    def teensy_holder(self):
        print('teensy_holder()')
        teensy_top_xy = self.key_position(self.wall_locate3(-1, 0), 0, self.p.centerrow - 1)
        teensy_bot_xy = self.key_position(self.wall_locate3(-1, 0), 0, self.p.centerrow + 1)
        teensy_holder_length = teensy_top_xy[1] - teensy_bot_xy[1]
        teensy_holder_offset = -teensy_holder_length / 2
        teensy_holder_top_offset = (self.p.teensy_holder_top_length / 2) - teensy_holder_length

        s1 = self.g.box(3, teensy_holder_length, 6 + self.p.teensy_width)
        s1 = self.g.translate(s1, [1.5, teensy_holder_offset, 0])

        s2 = self.g.box(self.p.teensy_pcb_thickness, teensy_holder_length, 3)
        s2 = self.g.translate(s2,
                       (
                           (self.p.teensy_pcb_thickness / 2) + 3,
                           teensy_holder_offset,
                           -1.5 - (self.p.teensy_width / 2),
                       )
                       )

        s3 = self.g.box(self.p.teensy_pcb_thickness, self.p.teensy_holder_top_length, 3)
        s3 = self.g.translate(s3,
                       [
                           (self.p.teensy_pcb_thickness / 2) + 3,
                           teensy_holder_top_offset,
                           1.5 + (self.p.teensy_width / 2),
                       ]
                       )

        s4 = self.g.box(4, self.p.teensy_holder_top_length, 4)
        s4 = self.g.translate(s4,
                       [self.p.teensy_pcb_thickness + 5, teensy_holder_top_offset, 1 + (self.p.teensy_width / 2)]
                       )

        shape = self.g.union((s1, s2, s3, s4))

        shape = self.g.translate(shape, [-self.p.teensy_holder_width, 0, 0])
        shape = self.g.translate(shape, [-1.4, 0, 0])
        shape = self.g.translate(shape,
                          [teensy_top_xy[0], teensy_top_xy[1] - 1, (6 + self.p.teensy_width) / 2]
                          )

        return shape

    def screw_insert_shape(self, bottom_radius, top_radius, height):
        debugprint('screw_insert_shape()')
        if bottom_radius == top_radius:
            base = self.g.cylinder(radius=bottom_radius, height=height)
            # base = self.g.translate(cylinder(radius=bottom_radius, height=height),
            #                  (0, 0, -height / 2)
            #                  )
        else:
            base = self.g.translate(self.g.cone(r1=bottom_radius, r2=top_radius, height=height), (0, 0, -height / 2))

        shape = self.g.union((
            base,
            self.g.translate(self.g.sphere(top_radius), (0, 0, height / 2)),
        ))
        return shape

    def screw_insert(self, column, row, bottom_radius, top_radius, height, side='right'):
        debugprint('screw_insert()')
        shift_right = column == self.p.lastcol
        shift_left = column == 0
        shift_up = (not (shift_right or shift_left)) and (row == 0)
        shift_down = (not (shift_right or shift_left)) and (row >= self.p.lastrow)

        if self.p.screws_offset == 'INSIDE':
            # debugprint('Shift Inside')
            shift_left_adjust = self.p.wall_base_x_thickness
            shift_right_adjust = -self.p.wall_base_x_thickness / 2
            shift_down_adjust = -self.p.wall_base_y_thickness / 2
            shift_up_adjust = -self.p.wall_base_y_thickness / 3

        elif self.p.screws_offset == 'OUTSIDE':
            debugprint('Shift Outside')
            shift_left_adjust = 0
            shift_right_adjust = self.p.wall_base_x_thickness / 2
            shift_down_adjust = self.p.wall_base_y_thickness * 2 / 3
            shift_up_adjust = self.p.wall_base_y_thickness * 2 / 3

        else:
            # debugprint('Shift Origin')
            shift_left_adjust = 0
            shift_right_adjust = 0
            shift_down_adjust = 0
            shift_up_adjust = 0

        if shift_up:
            position = self.key_position(
                list(np.array(self.wall_locate2(0, 1)) + np.array([0, (self.p.mount_height / 2) + shift_up_adjust, 0])),
                column,
                row,
            )
        elif shift_down:
            position = self.key_position(
                list(np.array(self.wall_locate2(0, -1)) - np.array([0, (self.p.mount_height / 2) + shift_down_adjust, 0])),
                column,
                row,
            )
        elif shift_left:
            position = list(
                np.array(self.left_key_position(row, 0, side=side)) + np.array(self.wall_locate3(-1, 0)) + np.array(
                    (shift_left_adjust, 0, 0))
            )
        else:
            position = self.key_position(
                list(np.array(self.wall_locate2(1, 0)) + np.array([(self.p.mount_height / 2), 0, 0]) + np.array(
                    (shift_right_adjust, 0, 0))
                     ),
                column,
                row,
            )

        shape = self.screw_insert_shape(bottom_radius, top_radius, height)
        shape = self.g.translate(shape, [position[0], position[1], height / 2])

        return shape

    def screw_insert_thumb(self, bottom_radius, top_radius, height, side='right'):
        position = self.cluster(side).screw_positions()

        shape = self.screw_insert_shape(bottom_radius, top_radius, height)
        shape = self.g.translate(shape, [position[0], position[1], height / 2])
        return shape

    # def screw_insert_all_shapes(bottom_radius, top_radius, height, offset=0, side='right'):
    #     print('screw_insert_all_shapes()')
    #     shape = (
    #         self.g.translate(screw_insert(0, 0, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
    #         self.g.translate(screw_insert(0, lastrow - 1, bottom_radius, top_radius, height, side=side),
    #                   (0, left_wall_lower_y_offset, offset)),
    #         self.g.translate(screw_insert(3, lastrow, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
    #         self.g.translate(screw_insert(3, 0, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
    #         self.g.translate(screw_insert(lastcol, 0, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
    #         self.g.translate(screw_insert(lastcol, lastrow - 1, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
    #         self.g.translate(screw_insert_thumb(bottom_radius, top_radius, height, side=side), (0, 0, offset)),
    #     )

    #     return shape

    ## TODO: Check against thumb cluster definitions
    # def thumb_screw_insert(bottom_radius, top_radius, height, offset=None, side='right'):
    #     shape = screw_insert_shape(bottom_radius, top_radius, height)
    #     shapes = []
    #     if offset is None:
    #         offset = 0.0

    #     origin = thumborigin()

    #     if ('TRACKBALL' in thumb_style) and not (side == ball_side or ball_side == 'both'):
    #         _thumb_style = other_thumb
    #     else:
    #         _thumb_style = thumb_style

    #     if _thumb_style == 'MINI':
    #         if separable_thumb:
    #             xypositions = copy.deepcopy(mini_separable_thumb_screw_xy_locations)
    #         else:
    #             xypositions = copy.deepcopy(mini_thumb_screw_xy_locations)

    #     elif _thumb_style == 'MINIDOX':
    #         if separable_thumb:
    #             xypositions = copy.deepcopy(minidox_separable_thumb_screw_xy_locations)
    #         else:
    #             xypositions = copy.deepcopy(minidox_thumb_screw_xy_locations)
    #         xypositions[0][1] = xypositions[0][1] - .4 * (minidox_Usize - 1) * sa_length

    #     elif _thumb_style == 'CARBONFET':
    #         if separable_thumb:
    #             xypositions = copy.deepcopy(carbonfet_separable_thumb_screw_xy_locations)
    #         else:
    #             xypositions = copy.deepcopy(carbonfet_thumb_screw_xy_locations)

    #     elif _thumb_style == 'TRACKBALL_ORBYL':
    #         if separable_thumb:
    #             xypositions = copy.deepcopy(orbyl_separable_thumb_screw_xy_locations)
    #         else:
    #             xypositions = copy.deepcopy(orbyl_thumb_screw_xy_locations)

    #     elif _thumb_style == 'TRACKBALL_CJ':
    #         if separable_thumb:
    #             xypositions = copy.deepcopy(tbcj_separable_thumb_screw_xy_locations)
    #         else:
    #             xypositions = copy.deepcopy(tbcj_thumb_screw_xy_locations)

    #     else:
    #         if separable_thumb:
    #             xypositions = copy.deepcopy(default_separable_thumb_screw_xy_locations)
    #         else:
    #             xypositions = copy.deepcopy(default_thumb_screw_xy_locations)

    #     for xyposition in xypositions:
    #         position = list(np.array(origin) + np.array([*xyposition, -origin[2]]))
    #         shapes.append(translate(shape, [position[0], position[1], height / 2 + offset]))

    #     return shapes

    def screw_insert_all_shapes(self, bottom_radius, top_radius, height, offset=0, side='right'):
        print('screw_insert_all_shapes()')
        shape = (
            self.g.translate(self.screw_insert(0, 0, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
            self.g.translate(self.screw_insert(0, self.p.cornerrow, bottom_radius, top_radius, height, side=side),
                      (0, self.p.left_wall_lower_y_offset, offset)),
            self.g.translate(self.screw_insert(3, self.p.lastrow, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
            self.g.translate(self.screw_insert(3, 0, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
            self.g.translate(self.screw_insert(self.p.lastcol, 0, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
            self.g.translate(self.screw_insert(self.p.lastcol, self.p.cornerrow, bottom_radius, top_radius, height, side=side), (0, 0, offset)),
            # self.g.translate(screw_insert_thumb(bottom_radius, top_radius, height), (0, 0, offset)),
        )

        return shape

    def screw_insert_holes(self, side='right'):
        return self.screw_insert_all_shapes(
            self.p.screw_insert_bottom_radius, self.p.screw_insert_top_radius, self.p.screw_insert_height + .02, offset=-.01, side=side
        )

    # def screw_insert_outers(side='right'):
    #     return screw_insert_all_shapes(
    #         screw_insert_bottom_radius + 1.6,
    #         screw_insert_top_radius + 1.6,
    #         screw_insert_height + 1.5,
    #         side=side
    #     )

    def screw_insert_outers(self, offset=0.0, side='right'):
        # screw_insert_bottom_radius + screw_insert_wall
        # screw_insert_top_radius + screw_insert_wall
        bottom_radius = self.p.screw_insert_outer_radius
        top_radius = self.p.screw_insert_outer_radius
        height = self.p.screw_insert_height + 1.5
        return self.screw_insert_all_shapes(bottom_radius, top_radius, height, offset=offset, side=side)

    def screw_insert_screw_holes(self, side='right'):
        return self.screw_insert_all_shapes(1.7, 1.7, 350, side=side)

    ## TODO:  Find places to inject the thumb features.

    def model_side(self, side="right"):
        print('model_right()')
        if side == "left":
            cluster = self.left_cluster
        else:
            cluster = self.right_cluster

        # shape = add([key_holes(side=side)])
        shape = self.g.union([self.key_holes(side=side)])
        if debug_exports:
            self.g. self.g.export_file(shape=shape, fname=path.join(r"..", "things", r"debug_key_plates"))
        connector_shape = self.connectors()
        shape = self.g.union([shape, connector_shape])
        if debug_exports:
             self.g.export_file(shape=shape, fname=path.join(r"..", "things", r"debug_connector_shape"))
        walls_shape = self.case_walls(side=side, skeleton=self.p.skeletal)
        if debug_exports:
             self.g.export_file(shape=walls_shape, fname=path.join(r"..", "things", r"debug_walls_shape"))

        s2 = self.g.union([walls_shape])
        s2 = self.g.union([s2, *self.screw_insert_outers(side=side)])

        if self.p.controller_mount_type in ['RJ9_USB_TEENSY', 'USB_TEENSY']:
            s2 = self.g.union([s2, self.teensy_holder()])

        if self.p.controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL', 'USB_WALL', 'USB_TEENSY']:
            s2 = self.g.union([s2, self.usb_holder()])
            s2 = self.g.difference(s2, [self.usb_holder_hole()])

        if self.p.controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
            s2 = self.g.difference(s2, [self.rj9_space()])

        if self.p.controller_mount_type in ['EXTERNAL']:
            s2 = self.g.difference(s2, [self.external_mount_hole()])

        if self.p.controller_mount_type in ['PCB_MOUNT']:
            s2 = self.g.difference(s2, [self.pcb_usb_hole()])
            s2 = self.g.difference(s2, [self.trrs_hole()])
            s2 = self.g.union([s2, self.pcb_holder()])
            s2 = self.g.difference(s2, [self.wall_thinner()])
            s2 = self.g.difference(s2, self.pcb_screw_hole())

        if self.p.controller_mount_type in [None, 'None']:
            0  # do nothing, only here to expressly state inaction.

        s2 = self.g.difference(s2, [self.g.union(self.screw_insert_holes(side=side))])
        shape = self.g.union([shape, s2])

        if self.p.controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
            shape = self.g.union([shape, self.rj9_holder()])

        if self.p.oled_mount_type == "UNDERCUT":
            hole, frame = self.oled_undercut_mount_frame(side=side)
            shape = self.g.difference(shape, [hole])
            shape = self.g.union([shape, frame])

        elif self.p.oled_mount_type == "SLIDING":
            hole, frame = self.oled_sliding_mount_frame(side=side)
            shape = self.g.difference(shape, [hole])
            shape = self.g.union([shape, frame])

        elif self.p.oled_mount_type == "CLIP":
            hole, frame = self.oled_clip_mount_frame(side=side)
            shape = self.g.difference(shape, [hole])
            shape = self.g.union([shape, frame])

        if self.p.trackball_in_wall and (side == self.p.ball_side or self.p.ball_side == 'both') and self.p.separable_thumb:
            tbprecut, tb, tbcutout, sensor, ball = self.generate_trackball_in_wall()

            shape = self.g.difference(shape, [tbprecut])
            #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
            shape = self.g.union([shape, tb])
            #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
            shape = self.g.difference(shape, [tbcutout])
            #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
            #  self.g.export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
            shape = self.g.union([shape, sensor])

            if self.p.show_caps:
                shape = self.g.add([shape, ball])

        if self.p.plate_pcb_clear:
            shape = self.g.difference(shape, [self.plate_pcb_cutouts(side=side)])

        main_shape = shape

        # BUILD THUMB

        # thumb_shape = thumb(side=side)
        thumb_shape = cluster.thumb(side=side),

        if debug_exports:
             self.g.export_file(shape=thumb_shape, fname=path.join(r"..", "things", r"debug_thumb_shape"))
        thumb_connector_shape = cluster.thumb_connectors(side=side)
        if debug_exports:
             self.g.export_file(shape=thumb_connector_shape, fname=path.join(r"..", "things", r"debug_thumb_connector_shape"))

        thumb_wall_shape = cluster.walls(side=side, skeleton=self.p.skeletal)
        # TODO: FIX THUMB INSERTS
        # thumb_wall_shape = self.g.union([thumb_wall_shape, *cluster(side=side).thumb_screw_insert_outers(side=side)])
        thumb_connection_shape = cluster.connection(side=side, skeleton=self.p.skeletal)

        if debug_exports:
            thumb_test = self.g.union([thumb_shape, thumb_connector_shape, thumb_wall_shape, thumb_connection_shape])
            self.g.export_file(shape=thumb_test, fname=path.join(r"..", "things", r"debug_thumb_test_{}_shape".format(side)))

        thumb_section = self.g.union([thumb_shape, thumb_connector_shape, thumb_wall_shape, thumb_connection_shape])

        # TODO: FIX THUMB INSERTS
        # thumb_section = self.g.difference(thumb_section, [union(cluster(side=side).thumb_screw_insert_holes(side=side))])

        has_trackball = False
        if cluster.is_tb:
            print("Has Trackball")
            tbprecut, tb, tbcutout, sensor, ball = self.generate_trackball_in_cluster(cluster)
            has_trackball = True
            thumb_section = self.g.difference(thumb_section, [tbprecut])
            if debug_exports:
                 self.g.export_file(shape=thumb_section,
                            fname=path.join(r"..", "things", r"debug_thumb_test_1_shape".format(side)))
            thumb_section = self.g.union([thumb_section, tb])
            if debug_exports:
                 self.g.export_file(shape=thumb_section,
                            fname=path.join(r"..", "things", r"debug_thumb_test_2_shape".format(side)))
            thumb_section = self.g.difference(thumb_section, [tbcutout])
            if debug_exports:
                 self.g.export_file(shape=thumb_section,
                            fname=path.join(r"..", "things", r"debug_thumb_test_3_shape".format(side)))
            thumb_section = self.g.union([thumb_section, sensor])
            if debug_exports:
                 self.g.export_file(shape=thumb_section,
                            fname=path.join(r"..", "things", r"debug_thumb_test_4_shape".format(side)))

        if self.p.plate_pcb_clear:
            thumb_section = self.g.difference(thumb_section, [cluster.thumb_pcb_plate_cutouts(side=side)])

        block = self.g.box(350, 350, 40)
        block = self.g.translate(block, (0, 0, -20))
        main_shape = self.g.difference(main_shape, [block])
        thumb_section = self.g.difference(thumb_section, [block])
        if debug_exports:
             self.g.export_file(shape=thumb_section, fname=path.join(r"..", "things", r"debug_thumb_test_5_shape".format(side)))

        if self.p.separable_thumb:
            thumb_section = self.g.difference(thumb_section, [main_shape])
            if self.p.show_caps:
                thumb_section = self.g.add([thumb_section, cluster.thumbcaps(side=side)])
                if has_trackball:
                    thumb_section = self.g.add([thumb_section, ball])
        else:
            main_shape = self.g.union([main_shape, thumb_section])
            if debug_exports:
                 self.g.export_file(shape=main_shape,
                            fname=path.join(r"..", "things", r"debug_thumb_test_6_shape".format(side)))
            if self.p.show_caps:
                main_shape = self.g.add([main_shape, cluster.thumbcaps(side=side)])
                if has_trackball:
                    main_shape = self.g.add([main_shape, ball])

            if self.p.trackball_in_wall and (side == self.p.ball_side or self.p.ball_side == 'both') and not self.p.separable_thumb:
                tbprecut, tb, tbcutout, sensor, ball = self.generate_trackball_in_wall()

                main_shape = self.g.difference(main_shape, [tbprecut])
                #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
                main_shape = self.g.union([main_shape, tb])
                #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
                main_shape = self.g.difference(main_shape, [tbcutout])
                #  self.g.export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
                #  self.g.export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
                main_shape = self.g.union([main_shape, sensor])

                if self.p.show_caps:
                    main_shape = self.g.add([main_shape, ball])

        if self.p.show_caps:
            main_shape = self.g.add([main_shape, self.caps()])

        if side == "left":
            main_shape = self.g.mirror(main_shape, 'YZ')
            thumb_section = self.g.mirror(thumb_section, 'YZ')

        return main_shape, thumb_section

    def baseplate(self, wedge_angle=None, side='right'):
        if side == "left":
            cluster = self.left_cluster
        else:
            cluster = self.right_cluster
        if self.p.ENGINE == 'cadquery':
            cq = self.g.cq
            # shape = mod_r

            thumb_shape = cluster.thumb(side=side)
            thumb_wall_shape = cluster.walls(side=side, skeleton=self.p.skeletal)
            ## TODO: FIX INSERTS
            # thumb_wall_shape = self.g.union([thumb_wall_shape, *thumb_screw_insert_outers(side=side)])
            thumb_connector_shape = cluster.connectors(side=side)
            thumb_connection_shape = cluster.connection(side=side, skeleton=self.p.skeletal)
            thumb_section = self.g.union([thumb_shape, thumb_connector_shape, thumb_wall_shape, thumb_connection_shape])
            ## TODO: FIX INSERTS
            # thumb_section = self.g.difference(thumb_section, [union(cluster(side=side).thumb_screw_insert_holes(side=side))])

            shape = self.g.union([
                self.case_walls(side=side),
                *self.screw_insert_outers(side=side),
                thumb_section
            ])
            tool = self.screw_insert_all_shapes(screw_hole_diameter / 2., self.p.screw_hole_diameter / 2., 350, side=side)
            for item in tool:
                item = self.g.translate(item, [0, 0, -10])
                shape = self.g.difference(shape, [item])

            tool = self.thumb_screw_insert(self.p.screw_hole_diameter / 2., self.p.screw_hole_diameter / 2., 350, side=side)
            for item in tool:
                item = self.g.translate(item, [0, 0, -10])
                shape = self.g.difference(shape, [item])

            # shape = self.g.union([main_shape, thumb_shape])

            shape = self.g.translate(shape, (0, 0, -0.0001))

            square = self.g.cq.Workplane('XY').rect(1000, 1000)
            for wire in square.wires().objects:
                plane = self.g.cq.Workplane('XY').add(cq.Face.makeFromWires(wire))
            shape = self.g.intersect(shape, plane)

            outside = shape.vertices(cq.DirectionMinMaxSelector(cq.Vector(1, 0, 0), True)).objects[0]
            sizes = []
            max_val = 0
            inner_index = 0
            base_wires = shape.wires().objects
            for i_wire, wire in enumerate(base_wires):
                is_outside = False
                for vert in wire.Vertices():
                    if vert.toTuple() == outside.toTuple():
                        outer_wire = wire
                        outer_index = i_wire
                        is_outside = True
                        sizes.append(0)
                if not is_outside:
                    sizes.append(len(wire.Vertices()))
                if sizes[-1] > max_val:
                    inner_index = i_wire
                    max_val = sizes[-1]
            debugprint(sizes)
            inner_wire = base_wires[inner_index]

            # inner_plate = cq.Workplane('XY').add(cq.Face.makeFromWires(inner_wire))
            if wedge_angle is not None:
                cq.Workplane('XY').add(cq.Solid.revolve(outerWire, innerWires, angleDegrees, axisStart, axisEnd))
            else:
                inner_shape = cq.Workplane('XY').add(cq.Solid.extrudeLinear(outerWire=inner_wire, innerWires=[],
                                                                            vecNormal=cq.Vector(0, 0, base_thickness)))
                inner_shape = self.g.translate(inner_shape, (0, 0, -self.p.base_rim_thickness))

                holes = []
                for i in range(len(base_wires)):
                    if i not in [inner_index, outer_index]:
                        holes.append(base_wires[i])
                cutout = [*holes, inner_wire]

                shape = cq.Workplane('XY').add(
                    cq.Solid.extrudeLinear(outer_wire, cutout, cq.Vector(0, 0, self.p.base_rim_thickness)))
                hole_shapes = []
                for hole in holes:
                    loc = hole.Center()
                    hole_shapes.append(
                        self.g.translate(
                            self.g.cylinder(self.p.screw_cbore_diameter / 2.0, self.p.screw_cbore_depth),
                            (loc.x, loc.y, 0)
                            # (loc.x, loc.y, screw_cbore_depth/2)
                        )
                    )
                shape = self.g.difference(shape, hole_shapes)
                shape = self.g.translate(shape, (0, 0, -self.p.base_rim_thickness))
                shape = self.g.union([shape, inner_shape])
            return shape

        else:
            shape = self.g.union([
                self.case_walls(side=side),
                cluster.walls(side=side),
                ## TODO: FIX INSERTS
                # *screw_insert_outers(side=side),
                # *thumb_screw_insert_outers(side=side),
            ])
            tool = self.g.translate(self.g.union(self.screw_insert_screw_holes(side=side)), [0, 0, -10])
            base = self.g.box(1000, 1000, .01)
            shape = shape - tool
            shape = self.g.intersect(shape, base)

            shape = self.g.translate(shape, [0, 0, -0.001])

            return self.g.sl.projection(cut=True)(shape)

    def run(self):
        # self.right_cluster = self.get_cluster(self.p.thumb_style)

        # if self.right_cluster is not None:
        #     self.right_cluster = self.get_cluster(self.p.other_thumb)
        #     if self.p.ball_side == "both":
        #         self.left_cluster = self.right_cluster
        #     elif self.p.ball_side == "left":
        #         self.left_cluster = self.right_cluster
        #         self.right_cluster = self.get_cluster(self.p.other_thumb)
        #     else:
        #         self.left_cluster = self.get_cluster(self.p.other_thumb)
        # elif self.p.other_thumb != "DEFAULT" and self.p.other_thumb != self.p.thumb_style:
        #     self.left_cluster = self.get_cluster(self.p.other_thumb)
        # else:
        #     self.left_cluster = self.right_cluster  # this assumes thumb_style always overrides DEFAULT other_thumb

        self.config_name = "FIX_IT"
        mod_r, tmb_r = self.model_side(side="right")
        self.g.export_file(shape=mod_r, fname=path.join(self.p.save_path, self.p.config_name + r"_right"))
        self.g.export_file(shape=tmb_r, fname=path.join(self.p.save_path, self.p.config_name + r"_thumb_right"))

        # base = baseplate(mod_r, tmb_r, side='right')
        base = self.baseplate(side='right')
        self.g.export_file(shape=base, fname=path.join(self.p.save_path, self.p.config_name + r"_right_plate"))
        self.g.export_dxf(shape=base, fname=path.join(self.p.save_path, self.p.config_name + r"_right_plate"))

        if self.p.symmetry == "asymmetric":
            mod_l, tmb_l = self.model_side(side="left")
            self.g.export_file(shape=mod_l, fname=path.join(self.p.save_path, self.p.config_name + r"_left"))
            self.g.export_file(shape=tmb_l, fname=path.join(self.p.save_path, self.p.config_name + r"_thumb_left"))

            # base_l = mirror(baseplate(mod_l, tmb_l, side='left'), 'YZ')
            base_l = self.g.mirror(baseplate(side='left'), 'YZ')
            self.g.export_file(shape=base_l, fname=path.join(self.p.save_path, self.p.config_name + r"_left_plate"))
            self.g.export_dxf(shape=base_l, fname=path.join(self.p.save_path, self.p.config_name + r"_left_plate"))

        # mod_r = model_side(side="right")
        #  self.g.export_file(shape=mod_r, fname=path.join(save_path, config_name + r"_right"))
        #
        # base = baseplate(side='right')
        #  self.g.export_file(shape=base, fname=path.join(save_path, config_name + r"_right_plate"))
        # export_dxf(shape=base, fname=path.join(save_path, config_name + r"_right_plate"))
        #
        # if symmetry == "asymmetric":
        #
        #     mod_l = model_side(side="left")
        #      self.g.export_file(shape=mod_l, fname=path.join(save_path, config_name + r"_left"))
        #
        #     base_l = mirror(baseplate(side='left'), 'YZ')
        #      self.g.export_file(shape=base_l, fname=path.join(save_path, config_name + r"_left_plate"))
        #     export_dxf(shape=base_l, fname=path.join(save_path, config_name + r"_left_plate"))

        else:
            self.g.export_file(shape=self.g.mirror(mod_r, 'YZ'), fname=path.join(self.p.save_path, self.p.config_name + r"_left"))

            lbase = self.g.mirror(base, 'YZ')
            self.g.export_file(shape=lbase, fname=path.join(self.p.save_path, self.p.config_name + r"_left_plate"))
            self.g.export_dxf(shape=lbase, fname=path.join(self.p.save_path, self.p.config_name + r"_left_plate"))

        if self.p.ENGINE == 'cadquery':
            import freecad_that as freecad
            freecad.generate_freecad_script(path.abspath(self.p.save_path), [
                self.p.config_name + r"_right",
                self.p.config_name + r"_left",
                self.p.config_name + r"_right_plate",
                self.p.config_name + r"_left_plate"
            ])

        if self.p.oled_mount_type == 'UNDERCUT':
            self.g.export_file(shape=self.oled_undercut_mount_frame()[1],
                    fname=path.join(self.p.save_path, self.p.config_name + r"_oled_undercut_test"))

        if self.p.oled_mount_type == 'SLIDING':
            self.g.export_file(shape=self.oled_sliding_mount_frame()[1],
                    fname=path.join(self.p.save_path, self.p.config_name + r"_oled_sliding_test"))

        if self.p.oled_mount_type == 'CLIP':
            oled_mount_location_xyz = (0.0, 0.0, -self.p.oled_config.oled_mount_depth / 2)
            oled_mount_rotation_xyz = (0.0, 0.0, 0.0)
            self.g.export_file(shape=self.oled_clip(), fname=path.join(self.p.save_path, self.p.config_name + r"_oled_clip"))
            self.g.export_file(shape=self.oled_clip_mount_frame()[1],
                    fname=path.join(self.p.save_path, self.p.config_name + r"_oled_clip_test"))
            self.g.export_file(shape=self.g.union((self.oled_clip_mount_frame()[1], self.oled_clip())),
                    fname=path.join(self.p.save_path, self.p.config_name + r"_oled_clip_assy_test"))

    # def get_cluster(self, style):
    #     clust_lib = importlib.import_module('clusters.' + self.p.cluster_parameters.package)
    #     #from clusters.custom_cluster import CustomCluster
    #     clust = getattr(clust_lib, self.p.cluster_parameters.class_name)
    #     return clust(self)

    def set_clusters(self):
        print(self.p.right_cluster)
        print(self.p.left_cluster)
        clust_lib = importlib.import_module('clusters.' + self.p.right_cluster.package)
        #from clusters.custom_cluster import CustomCluster
        clust = getattr(clust_lib, self.p.right_cluster.class_name)
        self.right_cluster = clust(self, self.p.right_cluster)

        clust_lib = importlib.import_module('clusters.' + self.p.left_cluster.package)
        #from clusters.custom_cluster import CustomCluster
        clust = getattr(clust_lib, self.p.left_cluster.class_name)
        self.left_cluster = clust(self, self.p.left_cluster)

        print(self.right_cluster)
        print(self.left_cluster)

    def get_cluster(self, side='right'):
        if side=="right":
            return self.right_cluster
        else:
            return self.left_cluster

if __name__ == '__main__':
    pass

    # base = baseplate()
    #  self.g.export_file(shape=base, fname=path.join(save_path, config_name + r"_plate"))
