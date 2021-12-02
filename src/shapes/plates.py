# import numpy as np
# import os.path as path
# import os
# import copy
# import importlib
from helpers import helpers_abc
from math import pi
from dataclasses import dataclass
import os.path as path
import copy
from typing import Any, Sequence, Tuple, Optional
import dactyl_manuform as dm

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

debug_trace=False

def deg2rad(degrees: float) -> float:
    return degrees * pi / 180


def rad2deg(rad: float) -> float:
    return rad * 180 / pi


def usize_dimension(Usize=1.5):
    sa_length = 18.5
    return Usize * sa_length


def debugprint(info):
    if debug_trace:
        print(info)


@dataclass
class PlateParameters:
    package: str = 'shapes.plates'
    class_name: str = 'PlateShapes'

    has_usb: bool = True
    has_rj9: bool = True
    has_teensy: bool = True

    teensy_width: float = 20
    teensy_height: float = 12
    teensy_length: float = 33
    teensy2_length: float = 53
    teensy_pcb_thickness: float = 2
    teensy_offset_height: float = 5
    teensy_holder_top_length: float = 18

    usb_holder_size: Sequence[float] = (6.5, 10.0, 13.6)
    usb_holder_thickness: float = 4


class PlateShapes:
    parameter_type = PlateParameters
    g: helpers_abc
    # parent: dm.DactylBase

    def __init__(self, parent, p_parameters=None):
        self._parent = parent
        self.p = parent.p
        self.g = parent.g

        self.pp = p_parameters

        self._plate = None

    def single_plate(self):
        if self._plate is None:
            if self.p.plate_style in ['NUB', 'HS_NUB']:
                plate = self.nub_plate()
            else:
                plate = self.plate_square_hole()

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
                    plate,
                    plate_holes_width=self.p.plate_holes_width, plate_holes_height=self.p.plate_holes_height,
                    plate_holes_xy_offset=self.p.plate_holes_xy_offset,
                    plate_holes_diameter=self.p.plate_holes_diameter, plate_holes_depth=self.p.plate_holes_depth
                )

            self._plate = plate

        else:
            plate = self._plate

        if self._parent.side == "left":
            plate = self.g.mirror(self._plate, 'YZ')

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
            self, plate,
            plate_holes_width=None, plate_holes_height=None, plate_holes_xy_offset=None,
            plate_holes_diameter=None, plate_holes_depth=None
    ):
        half_width = plate_holes_width / 2.
        half_height = plate_holes_height / 2.

        if self._parent.side == 'right':
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

    def plate_pcb_cutout(self):
        shape = self.g.box(*self.p.plate_pcb_size)
        shape = self.g.translate(shape, (0, 0, -self.p.plate_pcb_size[2] / 2))
        shape = self.g.translate(shape, self.p.plate_pcb_offset)

        if self._parent.side == "left":
            shape = self.g.mirror(shape, 'YZ')

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
        width = usize_dimension(Usize=Uwidth)
        height = usize_dimension(Usize=Uheight)
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