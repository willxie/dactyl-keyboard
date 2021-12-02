from helpers import helpers_abc
import os.path as path
import numpy as np
from dataclasses import dataclass
import copy
from typing import Any, Sequence, Tuple, Optional
import dactyl_manuform as dm

debug_trace = False
def debugprint(info):
    if debug_trace:
        print(info)


@dataclass
class OriginalControllerParameters:
    package: str = 'shapes.controllers'
    class_name: str = 'OriginalController'

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

class OriginalController:
    parameter_type = OriginalControllerParameters
    g: helpers_abc
    parent: dm.DactylBase

    def __init__(self, parent, c_parameters=None):
        self.parent = parent
        self.p = parent.p
        self.g = parent.g

        if c_parameters is None:
            self.cp = self.parameter_type()
        else:
            self.cp = c_parameters



    def generate_controller_mount(self, shape):
        if self.cp.has_teensy:
            self.teensy_config()
            shape = self.g.union([shape, self.teensy_holder()])

        if self.cp.has_usb:
            self.usb_config()
            shape = self.g.union([shape, self.usb_holder()])
            shape = self.g.difference(shape, [self.usb_holder_hole()])

        if self.cp.has_rj9:
            self.rj9_config()
            shape = self.g.difference(shape, [self.rj9_space()])
            shape = self.g.union([shape, self.rj9_holder()])

        return shape

    def teensy_config(self):
        self.cp.teensy_holder_width = 7 + self.cp.teensy_pcb_thickness
        self.cp.teensy_holder_height = 6 + self.cp.teensy_width

    def rj9_config(self):
        self.cp.rj9_start = list(
            np.array([0, -3, 0])
            + np.array(
                self.parent.key_position(
                    list(np.array(self.parent.wall_locate3(0, 1)) + np.array([0, (self.p.mount_height / 2), 0])),
                    0,
                    0,
                )
            )
        )

        self.cp.rj9_position = (self.cp.rj9_start[0], self.cp.rj9_start[1], 11)

    def usb_config(self):
        self.cp.usb_holder_position = self.parent.key_position(
            list(np.array(self.parent.wall_locate2(0, 1)) + np.array([0, (self.p.mount_height / 2), 0])), 1, 0
        )


    def rj9_cube(self):
        debugprint('rj9_cube()')
        shape = self.g.box(14.78, 13, 22.38)

        return shape

    def rj9_space(self):
        debugprint('rj9_space()')
        return self.g.translate(self.rj9_cube(), self.cp.rj9_position)

    def rj9_holder(self):
        print('rj9_holder()')
        shape = self.g.union([
            self.g.translate(self.g.box(10.78, 9, 18.38), (0, 2, 0)),
            self.g.translate(self.g.box(10.78, 13, 5), (0, 0, 5))
        ])
        shape = self.g.difference(self.rj9_cube(), [shape])
        shape = self.g.translate(shape, self.cp.rj9_position)

        return shape

    def usb_holder(self):
        print('usb_holder()')
        shape = self.g.box(
            self.cp.usb_holder_size[0] + self.cp.usb_holder_thickness,
            self.cp.usb_holder_size[1],
            self.cp.usb_holder_size[2] + self.cp.usb_holder_thickness,
        )
        shape = self.g.translate(shape,
                          (
                              self.cp.usb_holder_position[0],
                              self.cp.usb_holder_position[1],
                              (self.cp.usb_holder_size[2] + self.cp.usb_holder_thickness) / 2,
                          )
                          )
        return shape

    def usb_holder_hole(self):
        debugprint('usb_holder_hole()')
        shape = self.g.box(*self.cp.usb_holder_size)
        shape = self.g.translate(shape,
                          (
                              self.cp.usb_holder_position[0],
                              self.cp.usb_holder_position[1],
                              (self.cp.usb_holder_size[2] + self.cp.usb_holder_thickness) / 2,
                          )
                          )
        return shape

    def teensy_holder(self):
        print('teensy_holder()')
        teensy_top_xy = self.parent.key_position(self.parent.wall_locate3(-1, 0), 0, self.p.centerrow - 1)
        teensy_bot_xy = self.parent.key_position(self.parent.wall_locate3(-1, 0), 0, self.p.centerrow + 1)
        teensy_holder_length = teensy_top_xy[1] - teensy_bot_xy[1]
        teensy_holder_offset = -teensy_holder_length / 2
        teensy_holder_top_offset = (self.cp.teensy_holder_top_length / 2) - teensy_holder_length

        s1 = self.g.box(3, teensy_holder_length, 6 + self.cp.teensy_width)
        s1 = self.g.translate(s1, [1.5, teensy_holder_offset, 0])

        s2 = self.g.box(self.cp.teensy_pcb_thickness, teensy_holder_length, 3)
        s2 = self.g.translate(s2,
                       (
                           (self.cp.teensy_pcb_thickness / 2) + 3,
                           teensy_holder_offset,
                           -1.5 - (self.cp.teensy_width / 2),
                       )
                       )

        s3 = self.g.box(self.cp.teensy_pcb_thickness, self.cp.teensy_holder_top_length, 3)
        s3 = self.g.translate(s3,
                       [
                           (self.cp.teensy_pcb_thickness / 2) + 3,
                           teensy_holder_top_offset,
                           1.5 + (self.cp.teensy_width / 2),
                       ]
                       )

        s4 = self.g.box(4, self.cp.teensy_holder_top_length, 4)
        s4 = self.g.translate(s4,
                       [self.cp.teensy_pcb_thickness + 5, teensy_holder_top_offset, 1 + (self.cp.teensy_width / 2)]
                       )

        shape = self.g.union((s1, s2, s3, s4))

        shape = self.g.translate(shape, [-self.cp.teensy_holder_width, 0, 0])
        shape = self.g.translate(shape, [-1.4, 0, 0])
        shape = self.g.translate(shape,
                          [teensy_top_xy[0], teensy_top_xy[1] - 1, (6 + self.cp.teensy_width) / 2]
                          )

        return shape


@dataclass
class ExternalControllerParameters:
    package: str = 'shapes.controllers'
    class_name: str = 'ExternalController'

    external_holder_height: float = 12.5
    external_holder_width: float = 28.75
    external_holder_xoffset: float = -5.0
    external_holder_yoffset: float = -4.5


class ExternalController:
    parameter_type = ExternalControllerParameters
    g: helpers_abc

    def __init__(self, parent, c_parameters=None):
        self.parent = parent
        self.p = parent.p
        self.g = parent.g

        if c_parameters is None:
            self.cp = self.parameter_type()
        else:
            self.cp = c_parameters

    def generate_controller_mount(self, shape):
        shape = self.g.difference(shape, [self.external_mount_hole()])
        return shape


    def external_holder_config(self):
        self.cp.external_start = list(
            # np.array([0, -3, 0])
            np.array([self.cp.external_holder_width / 2, 0, 0])
            + np.array(
                self.parent.key_position(
                    list(np.array(self.parent.wall_locate3(0, 1)) + np.array([0, (self.p.mount_height / 2), 0])),
                    0,
                    0,
                )
            )
        )


    def external_mount_hole(self):
        print('external_mount_hole()')
        self.external_holder_config()

        shape = self.g.box(self.cp.external_holder_width, 20.0, self.cp.external_holder_height + .1)
        undercut = self.g.box(self.cp.external_holder_width + 8, 10.0, self.cp.external_holder_height + 8 + .1)
        shape = self.g.union([shape, self.g.translate(undercut, (0, -5, 0))])

        shape = self.g.translate(shape,
                                 (
                                     self.cp.external_start[0] + self.cp.external_holder_xoffset,
                                     self.cp.external_start[1] + self.cp.external_holder_yoffset,
                                     self.cp.external_holder_height / 2 - .05,
                                 )
                                 )
        return shape




@dataclass
class PCBMountControllerParameters:
    package: str = 'shapes.controllers'
    class_name: str = 'PCBMountController'

    pcb_mount_ref_offset: Sequence[float] = (0, -5, 0)
    pcb_holder_size: Sequence[float] = (34.6, 7, 4)
    pcb_holder_offset: Sequence[float] = (8.9, 0, 0)

    pcb_usb_hole_size: Sequence[float] = (7.5, 10.0, 4)
    pcb_usb_hole_offset: Sequence[float] = (15, 0, 4.5)

    wall_thinner_size: Sequence[float] = (34, 7, 10)
    trrs_hole_size: Sequence[float] = (3, 20)
    trrs_offset: Sequence[float] = (0, 0, 1.5)

    pcb_screw_hole_size: Sequence[float] = (.5, 10)
    pcb_screw_x_offsets: Sequence[float] = (- 5.5, 7.75, 22)  # for the screw positions off of reference
    pcb_screw_y_offset: float = -2

    usb_holder_size: Sequence[float] = (6.5, 10.0, 13.6)
    usb_holder_thickness: float = 4


class PCBMountController:
    parameter_type = PCBMountControllerParameters
    g: helpers_abc

    def __init__(self, parent, c_parameters=None):
        self.parent = parent
        self.p = parent.p
        self.g = parent.g

        if c_parameters is None:
            self.cp = self.parameter_type()
        else:
            self.cp = c_parameters

        self.pcb_mount_config()

    def generate_controller_mount(self, shape):
        self.pcb_mount_config()
        shape = self.g.difference(shape, [self.pcb_usb_hole()])
        shape = self.g.difference(shape, [self.trrs_hole()])
        shape = self.g.union([shape, self.pcb_holder()])
        shape = self.g.difference(shape, [self.wall_thinner()])
        shape = self.g.difference(shape, self.pcb_screw_hole())

        return shape

    def pcb_mount_config(self):
        self.cp.pcb_mount_ref_position = self.parent.key_position(
            # TRRS POSITION IS REFERENCE BY CONVENIENCE
            list(np.array(self.parent.wall_locate3(0, 1)) + np.array([0, (self.p.mount_height / 2), 0])), 0, 0
        )

        self.cp.pcb_mount_ref_position[0] = self.cp.pcb_mount_ref_position[0] + self.cp.pcb_mount_ref_offset[0]
        self.cp.pcb_mount_ref_position[1] = self.cp.pcb_mount_ref_position[1] + self.cp.pcb_mount_ref_offset[1]
        self.cp.pcb_mount_ref_position[2] = 0.0 + self.cp.pcb_mount_ref_offset[2]

        self.cp.pcb_holder_position = copy.deepcopy(self.cp.pcb_mount_ref_position)
        self.cp.pcb_holder_position[0] = self.cp.pcb_holder_position[0] + self.cp.pcb_holder_offset[0]
        self.cp.pcb_holder_position[1] = self.cp.pcb_holder_position[1] + self.cp.pcb_holder_offset[1]
        self.cp.pcb_holder_position[2] = self.cp.pcb_holder_position[2] + self.cp.pcb_holder_offset[2]
        self.cp.pcb_holder_thickness = self.cp.pcb_holder_size[2]

        self.cp.pcb_screw_position = copy.deepcopy(self.cp.pcb_mount_ref_position)
        self.cp.pcb_screw_position[1] = self.cp.pcb_screw_position[1] + self.cp.pcb_screw_y_offset

    def pcb_usb_hole(self):
        debugprint('pcb_holder()')
        pcb_usb_position = copy.deepcopy(self.cp.pcb_mount_ref_position)
        pcb_usb_position[0] = pcb_usb_position[0] + self.cp.pcb_usb_hole_offset[0]
        pcb_usb_position[1] = pcb_usb_position[1] + self.cp.pcb_usb_hole_offset[1]
        pcb_usb_position[2] = pcb_usb_position[2] + self.cp.pcb_usb_hole_offset[2]

        shape = self.g.box(*self.cp.pcb_usb_hole_size)
        shape = self.g.translate(shape,
                                 (
                                     pcb_usb_position[0],
                                     pcb_usb_position[1],
                                     self.cp.pcb_usb_hole_size[2] / 2 + self.cp.usb_holder_thickness,
                                 )
                                 )
        return shape

    def pcb_holder(self):
        debugprint('pcb_holder()')
        shape = self.g.box(*self.cp.pcb_holder_size)
        shape = self.g.translate(shape,
                                 (
                                     self.cp.pcb_holder_position[0],
                                     self.cp.pcb_holder_position[1] - self.cp.pcb_holder_size[1] / 2,
                                     self.cp.pcb_holder_thickness / 2,
                                 )
                                 )
        return shape

    def wall_thinner(self):
        debugprint('wall_thinner()')
        shape = self.g.box(*self.cp.wall_thinner_size)
        shape = self.g.translate(shape,
                                 (
                                     self.cp.pcb_holder_position[0],
                                     self.cp.pcb_holder_position[1] - self.cp.wall_thinner_size[1] / 2,
                                     self.cp.wall_thinner_size[2] / 2 + self.cp.pcb_holder_thickness,
                                 )
                                 )
        return shape

    def trrs_hole(self):
        debugprint('trrs_hole()')
        trrs_position = copy.deepcopy(self.cp.pcb_mount_ref_position)
        trrs_position[0] = trrs_position[0] + self.cp.trrs_offset[0]
        trrs_position[1] = trrs_position[1] + self.cp.trrs_offset[1]
        trrs_position[2] = trrs_position[2] + self.cp.trrs_offset[2]

        trrs_hole_size = [3, 20]

        shape = self.g.cylinder(*trrs_hole_size)
        shape = self.g.rotate(shape, [0, 90, 90])
        shape = self.g.translate(shape,
                                 (
                                     trrs_position[0],
                                     trrs_position[1],
                                     trrs_hole_size[0] + self.cp.pcb_holder_thickness,
                                 )
                                 )
        return shape

    def pcb_screw_hole(self):
        debugprint('pcb_screw_hole()')
        holes = []
        hole = self.g.cylinder(*self.cp.pcb_screw_hole_size)
        hole = self.g.translate(hole, self.cp.pcb_screw_position)
        hole = self.g.translate(hole, (0, 0, self.cp.pcb_screw_hole_size[1] / 2 - .1))
        for offset in self.cp.pcb_screw_x_offsets:
            holes.append(self.g.translate(hole, (offset, 0, 0)))

        return holes
