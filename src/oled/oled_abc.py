import json
import os
import numpy as np
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from abc import ABC
from typing import Any, Sequence, Tuple, Optional
# from src.dactyl_manuform import ParametersBase

def debugprint(data):
    pass
    # print

def rad2deg(rad: float) -> float:
    return rad * 180 / 3.14159

@dataclass_json
@dataclass
class OLEDBaseParameters:
# class OLEDBaseParameters(ParametersBase):

    package: str = 'oled.oled_abc'
    class_name: str = 'OLEDBase'

    name: str = 'OLED_ABC'

    vertical: bool = True
    mount_width: float = 12.5  # whole OLED width
    mount_height: float = 39.0  # whole OLED length
    mount_rim: float = 2.0
    mount_depth: float = 7.0
    mount_cut_depth: float = 20.0

    center_row: Optional[float] = 1.25  # if not None, this will override the oled_mount_location_xyz and oled_mount_rotation_xyz settings
    translation_offset: Sequence[float] = (0, 0, 4)  # Z offset tweaks are expected depending on curvature and OLED mount choice.
    rotation_offset: Sequence[float] = (0, 0, 0)

    # only used of center row not defined
    mount_location_xyz: Sequence[float] = (-78.0, 20.0, 42.0)  # will be overwritten if center_row is not None
    mount_rotation_xyz: Sequence[float] = (12.0, 0.0, -6.0)  # will be overwritten if center_row is not None

    # values override default configs
    left_wall_lower_y_offset: Optional[float] = 12.0
    left_wall_lower_z_offset: Optional[float] = 5.0
    left_wall_x_offset: Optional[float] = 24.0
    left_wall_z_offset: Optional[float] = 0.0




class OLEDBase(ABC):
    parameter_type = OLEDBaseParameters

    def __init__(self, parent, o_parameters=None):
        self.g = parent.g
        self.p = parent.p
        self.parent = parent
        self.sh = parent.sh

        if o_parameters is None:
            o_parameters = self.parameter_type()

        self.op = o_parameters
        self.process_parameters()
        self.set_overrides()


    def set_overrides(self):
        if self.op.left_wall_lower_y_offset is not None:
            self.p.left_wall_lower_y_offset = self.op.left_wall_lower_y_offset

        if self.op.left_wall_lower_z_offset is not None:
            self.p.left_wall_lower_z_offset = self.op.left_wall_lower_z_offset

        if self.op.left_wall_x_offset is not None:
            self.p.left_wall_x_offset = self.op.left_wall_x_offset

        if self.op.left_wall_z_offset is not None:
            self.p.left_wall_z_offset = self.op.left_wall_z_offset


    def process_parameters(self):
        if self.op.center_row is not None:
            base_pt1 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.op.center_row - 1
            )
            base_pt2 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.op.center_row + 1
            )
            base_pt0 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0,
                self.op.center_row
            )

            mount_location_xyz = np.array(self.op.mount_location_xyz)
            mount_location_xyz = (np.array(base_pt1) + np.array(base_pt2)) / 2. + np.array(
                ((-self.p.left_wall_x_offset / 2), 0, 0)) + np.array(self.op.translation_offset)

            mount_location_xyz[2] = (mount_location_xyz[2] + base_pt0[2]) / 2
            self.op.mount_location_xyz = mount_location_xyz

            angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
            angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])

            self.op.mount_rotation_xyz = (rad2deg(angle_x), 0, -rad2deg(angle_z)) + np.array(
                self.op.rotation_offset)


    @staticmethod
    def name():
        return "ABC"

    def oled_position_rotation(self):
        if self.op.center_row is not None:

            base_pt1 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, self.op.center_row - 1
            )
            base_pt2 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, self.op.center_row + 1
            )
            base_pt0 = self.parent.key_position(
                list(np.array([-self.p.mount_width / 2, 0, 0]) + np.array([0, (self.p.mount_height / 2), 0])), 0, self.op.center_row
            )

            oled_mount_location_xyz = (np.array(base_pt1) + np.array(base_pt2)) / 2. + np.array(
                ((-self.p.left_wall_x_offset / 2), 0, 0)) + np.array(self.op.translation_offset)
            oled_mount_location_xyz[2] = (oled_mount_location_xyz[2] + base_pt0[2]) / 2

            angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
            angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])

            if self.op.vertical:
                oled_mount_rotation_xyz = (rad2deg(angle_x), 0, -rad2deg(angle_z)) + np.array(self.op.rotation_offset)
            else:
                oled_mount_rotation_xyz = (0, rad2deg(angle_x), -90) + np.array(self.op.rotation_offset)

            return oled_mount_location_xyz, oled_mount_rotation_xyz

        else:
            
            return self.op.mount_location_xyz, self.op.mount_rotation_xyz



    def oled_mount_frame(self):
        hole = self.g.box(1, 1, 1)
        shape = self.g.box(1, 1, 1)
        return hole, shape

    def extra_parts(self):
        pass





# Generic class with special parameters.
# @dataclass_json
# class OLEDConfiguration:
#     oled_configuration_name: str = 'BASE'
#     oled_mount_width: float = 12.5  # whole OLED width
#     oled_mount_height: float = 39.0  # whole OLED length
#     oled_mount_rim: float = 2.0
#     oled_mount_depth: float = 7.0
#     oled_mount_cut_depth: float = 20.0
#     oled_mount_location_xyz: Sequence[float] = (-78.0, 20.0, 42.0)  # will be overwritten if center_row is not None
#     oled_mount_rotation_xyz: Sequence[float] = (12.0, 0.0, -6.0)  # will be overwritten if center_row is not None
#     oled_left_wall_x_offset_override: float = 24.0
#     oled_left_wall_z_offset_override: float = 0.0
#     oled_left_wall_lower_y_offset: float = 12.0
#     oled_left_wall_lower_z_offset: float = 5.0
#

# @dataclass_json
# class OLEDUndercut(OLEDConfiguration):
#     oled_configuration_name: str = 'UNDERCUT'
#     # Common parameters
#     oled_mount_width: float = 15.0
#     oled_mount_height: float = 35.0
#     oled_mount_rim: float = 3.0
#     oled_mount_depth: float = 6.0
#     oled_mount_cut_depth: float = 20.0
#     oled_mount_location_xyz: Sequence[float] = (-80.0, 20.0, 45.0)  # will be overwritten if center_row is not None
#     oled_mount_rotation_xyz: Sequence[float] = (13.0, 0.0, -6.0)  # will be overwritten if center_row is not None
#     oled_left_wall_x_offset_override: float = 28.0
#     oled_left_wall_z_offset_override: float = 0.0
#     oled_left_wall_lower_y_offset: float = 12.0
#     oled_left_wall_lower_z_offset: float = 5.0
#     # 'UNDERCUT' Parameters
#     oled_mount_undercut: float = 1.0
#     oled_mount_undercut_thickness: float = 2.0


# @dataclass_json
# class OLEDSliding(OLEDConfiguration):
#     oled_configuration_name: str = 'SLIDING'
#     # Common parameters
#     oled_mount_width: float = 12.5  # width of OLED, plus clearance
#     oled_mount_height: float = 25.0  # length of screen
#     oled_mount_rim: float = 2.5
#     oled_mount_depth: float = 8.0
#     oled_mount_cut_depth: float = 20.0
#     oled_mount_location_xyz: Sequence[float] = (-78.0, 10.0, 41.0)  # will be overwritten if center_row is not None
#     oled_mount_rotation_xyz: Sequence[float] = (6.0, 0.0, -3.0)  # will be overwritten if center_row is not None
#     oled_left_wall_x_offset_override: float = 24.0
#     oled_left_wall_z_offset_override: float = 0.0
#     oled_left_wall_lower_y_offset: float = 12.0
#     oled_left_wall_lower_z_offset: float = 5.0
#
#     # 'SLIDING' Parameters
#     oled_thickness: float = 4.2  # thickness of OLED, plus clearance.  Must include components
#     oled_edge_overlap_end: float = 6.5  # length from end of viewable screen to end of PCB
#     oled_edge_overlap_connector: float = 5.5  # length from end of viewable screen to end of PCB on connection side.
#     oled_edge_overlap_thickness: float = 2.5  # thickness of material over edge of PCB
#     oled_edge_overlap_clearance: float = 2.5  # Clearance to insert PCB before laying down and sliding.
#     oled_edge_chamfer: float = 2.0


# @dataclass_json
# class OLEDClip(OLEDConfiguration):
#     oled_configuration_name: str = 'CLIP'
#     oled_mount_width: float = 12.5  # whole OLED width
#     oled_mount_height: float = 39.0  # whole OLED length
#     oled_mount_rim: float = 2.0
#     oled_mount_depth: float = 7.0
#     oled_mount_cut_depth: float = 20.0
#     oled_mount_location_xyz: Sequence[float] = (-78.0, 20.0, 42.0)  # will be overwritten if center_row is not None
#     oled_mount_rotation_xyz: Sequence[float] = (12.0, 0.0, -6.0)  # will be overwritten if center_row is not None
#     oled_left_wall_x_offset_override: float = 24.0
#     oled_left_wall_z_offset_override: float = 0.0
#     oled_left_wall_lower_y_offset: float = 12.0
#     oled_left_wall_lower_z_offset: float = 5.0
#
#     # 'CLIP' Parameters
#     oled_thickness: float = 4.2  # thickness of OLED, plus clearance.  Must include components
#     oled_mount_bezel_thickness: float = 3.5  # z thickness of clip bezel
#     oled_mount_bezel_chamfer: float = 2.0  # depth of the 45 degree chamfer
#     oled_mount_connector_hole: float = 6.0
#     oled_screen_start_from_conn_end: float = 6.5
#     oled_screen_length: float = 24.5
#     oled_screen_width: float = 10.5
#     oled_clip_thickness: float = 1.5
#     oled_clip_width: float = 6.0
#     oled_clip_overhang: float = 1.0
#     oled_clip_extension: float = 5.0
#     oled_clip_width_clearance: float = 0.5
#     oled_clip_undercut: float = 0.5
#     oled_clip_undercut_thickness: float = 2.5
#     oled_clip_y_gap: float = .2
#     oled_clip_z_gap: float = .2

