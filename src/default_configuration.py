import sys
import getopt
import os
import json
from dataclasses import dataclass
from typing import Any, Sequence

pi = 3.14159
d2r = pi / 180
r2d = 180 / pi


# Generic class with special parameters.
@dataclass
class OLEDConfiguration:
    oled_configuration_name: str = 'BASE'
    oled_mount_width: float = 12.5  # whole OLED width
    oled_mount_height: float = 39.0  # whole OLED length
    oled_mount_rim: float = 2.0
    oled_mount_depth: float = 7.0
    oled_mount_cut_depth: float = 20.0
    oled_mount_location_xyz: Sequence[float] = (-78.0, 20.0, 42.0)  # will be overwritten if oled_center_row is not None
    oled_mount_rotation_xyz: Sequence[float] = (12.0, 0.0, -6.0)  # will be overwritten if oled_center_row is not None
    oled_left_wall_x_offset_override: float = 24.0
    oled_left_wall_z_offset_override: float = 0.0
    oled_left_wall_lower_y_offset: float = 12.0
    oled_left_wall_lower_z_offset: float = 5.0


@dataclass
class OLEDUndercut(OLEDConfiguration):
    oled_configuration_name: str = 'UNDERCUT'
    # Common parameters
    oled_mount_width: float = 15.0
    oled_mount_height: float = 35.0
    oled_mount_rim: float = 3.0
    oled_mount_depth: float = 6.0
    oled_mount_cut_depth: float = 20.0
    oled_mount_location_xyz: Sequence[float] = (-80.0, 20.0, 45.0)  # will be overwritten if oled_center_row is not None
    oled_mount_rotation_xyz: Sequence[float] = (13.0, 0.0, -6.0)  # will be overwritten if oled_center_row is not None
    oled_left_wall_x_offset_override: float = 28.0
    oled_left_wall_z_offset_override: float = 0.0
    oled_left_wall_lower_y_offset: float = 12.0
    oled_left_wall_lower_z_offset: float = 5.0
    # 'UNDERCUT' Parameters
    oled_mount_undercut: float = 1.0
    oled_mount_undercut_thickness: float = 2.0


@dataclass
class OLEDSliding(OLEDConfiguration):
    oled_configuration_name: str = 'SLIDING'
    # Common parameters
    oled_mount_width: float = 12.5  # width of OLED, plus clearance
    oled_mount_height: float = 25.0  # length of screen
    oled_mount_rim: float = 2.5
    oled_mount_depth: float = 8.0
    oled_mount_cut_depth: float = 20.0
    oled_mount_location_xyz: Sequence[float] = (-78.0, 10.0, 41.0)  # will be overwritten if oled_center_row is not None
    oled_mount_rotation_xyz: Sequence[float] = (6.0, 0.0, -3.0)  # will be overwritten if oled_center_row is not None
    oled_left_wall_x_offset_override: float = 24.0
    oled_left_wall_z_offset_override: float = 0.0
    oled_left_wall_lower_y_offset: float = 12.0
    oled_left_wall_lower_z_offset: float = 5.0

    # 'SLIDING' Parameters
    oled_thickness: float = 4.2  # thickness of OLED, plus clearance.  Must include components
    oled_edge_overlap_end: float = 6.5  # length from end of viewable screen to end of PCB
    oled_edge_overlap_connector: float = 5.5  # length from end of viewable screen to end of PCB on connection side.
    oled_edge_overlap_thickness: float = 2.5  # thickness of material over edge of PCB
    oled_edge_overlap_clearance: float = 2.5  # Clearance to insert PCB before laying down and sliding.
    oled_edge_chamfer: float = 2.0


@dataclass
class OLEDClip(OLEDConfiguration):
    oled_configuration_name: str = 'CLIP'
    oled_mount_width: float = 12.5  # whole OLED width
    oled_mount_height: float = 39.0  # whole OLED length
    oled_mount_rim: float = 2.0
    oled_mount_depth: float = 7.0
    oled_mount_cut_depth: float = 20.0
    oled_mount_location_xyz: Sequence[float] = (-78.0, 20.0, 42.0)  # will be overwritten if oled_center_row is not None
    oled_mount_rotation_xyz: Sequence[float] = (12.0, 0.0, -6.0)  # will be overwritten if oled_center_row is not None
    oled_left_wall_x_offset_override: float = 24.0
    oled_left_wall_z_offset_override: float = 0.0
    oled_left_wall_lower_y_offset: float = 12.0
    oled_left_wall_lower_z_offset: float = 5.0

    # 'CLIP' Parameters
    oled_thickness: float = 4.2  # thickness of OLED, plus clearance.  Must include components
    oled_mount_bezel_thickness: float = 3.5  # z thickness of clip bezel
    oled_mount_bezel_chamfer: float = 2.0  # depth of the 45 degree chamfer
    oled_mount_connector_hole: float = 6.0
    oled_screen_start_from_conn_end: float = 6.5
    oled_screen_length: float = 24.5
    oled_screen_width: float = 10.5
    oled_clip_thickness: float = 1.5
    oled_clip_width: float = 6.0
    oled_clip_overhang: float = 1.0
    oled_clip_extension: float = 5.0
    oled_clip_width_clearance: float = 0.5
    oled_clip_undercut: float = 0.5
    oled_clip_undercut_thickness: float = 2.5
    oled_clip_y_gap: float = .2
    oled_clip_z_gap: float = .2


OLED_LOOKUP = {
    'CLIP': OLEDClip,
    'SLIDING': OLEDSliding,
    'UNDERCUT': OLEDUndercut,
}


@dataclass
class ShapeConfiguration:
    ENGINE = 'solid'  # 'solid' = solid python / OpenSCAD, 'cadquery' = cadquery / OpenCascade
    # ENGINE = 'cadquery'  # 'solid' = solid python / OpenSCAD, 'cadquery' = cadquery / OpenCascade

    ######################
    ## Shape parameters ##
    ######################

    save_dir: str = '.'
    config_name: str = "DM"

    show_caps: bool = False
    show_pcbs: bool = False  # only runs if caps are shown, easist place to initially inject geometry

    nrows = 5  # 5,  # key rows
    ncols = 6  # 6,  # key columns

    alpha: float = pi / 12.0  # curvature of the columns
    beta: float = pi / 36.0  # curvature of the rows
    centercol: int = 3  # controls left_right tilt / tenting (higher number is more tenting)
    centerrow_offset: int = 3  # rows from max, controls front_back tilt
    tenting_angle: float = pi / 12.0  # or, change this for more precise tenting control

    # symmetry states if it is a symmetric or asymmetric bui.  If asymmetric it doubles the generation time.
    symmetry: str = "symmetric"  # "asymmetric" or "symmetric"

    column_style_gt5: str = "orthographic"
    column_style: str = "standard"  # options include :standard, :orthographic, and :fixed
    reduced_outer_keys: bool = True

    thumb_offsets: Sequence[float] = (6, -3, 7)
    keyboard_z_offset: float = (11)  # controls overall height# original=9 with centercol=3# use 16 for centercol=2


    extra_width: float = 2.5  # extra space between the base of keys# original= 2
    extra_height: float = 1.0  # original= 0.5

    web_thickness: float = 4.0 + 1.1
    post_size: float = 0.1
    # post_adj =  post_size / 2
    post_adj: float = 0

    ##############################
    # THUMB PARAMETERS
    ##############################

    # 'DEFAULT' 6-key, 'MINI' 5-key, 'CARBONFET' 6-key, 'MINIDOX' 3-key, 'TRACKBALL_ORBYL', 'TRACKBALL_CJ'
    # thumb_style = 'DEFAULT'
    left_cluster: Any = None
    right_cluster: Any = None

    # Thumb key size.  May need slight oversizing, check w/ caps.  Additional spacing will be automatically added for larger keys.
    minidox_Usize: float = 1.6

    # Screw locations and extra screw locations for separable thumb, all from thumb origin
    # Pulled out of hardcoding as drastic changes to the geometry may require fixes to the screw mounts.
    # First screw in separable should be similar to the standard location as it will receive the same modifiers.

    # minidox_thumb_screw_xy_locations = [[-37, -34]]
    # minidox_separable_thumb_screw_xy_locations = [[-37, -34], [-62, 12], [10, -25]]
    # orbyl_thumb_screw_xy_locations = [[-53, -68]]
    # orbyl_separable_thumb_screw_xy_locations = [[-53, -68], [-66, 8], [10, -40]]
    # tbcj_thumb_screw_xy_locations = [[-40, -75]]
    # tbcj_separable_thumb_screw_xy_locations = [[-40, -75], [-63, 10], [15, -40]]

    # thumb_plate_tr_rotation = 0.0  # Top right plate rotation tweaks as thumb cluster is crowded for hot swap, etc.
    # thumb_plate_tl_rotation = 0.0  # Top left plate rotation tweaks as thumb cluster is crowded for hot swap, etc.
    # thumb_plate_mr_rotation = 0.0  # Mid right plate rotation tweaks as thumb cluster is crowded for hot swap, etc.
    # thumb_plate_ml_rotation = 0.0  # Mid left plate rotation tweaks as thumb cluster is crowded for hot swap, etc.
    # thumb_plate_br_rotation = 0.0  # Bottom right plate rotation tweaks as thumb cluster is crowded for hot swap, etc.
    # thumb_plate_bl_rotation = 0.0  # Bottom right plate rotation tweaks as thumb cluster is crowded for hot swap, etc.
    ##############################
    # EXPERIMENTAL
    separable_thumb: bool = False  # creates a separable thumb section with additional screws to hold it down.  Only attached at base.
    ##############################

    ###################################
    ## Trackball in Wall             ##
    ###################################
    trackball_in_wall: bool = False  # Separate trackball option, placing it in the OLED area
    tbiw_ball_center_row: float = 0.2  # up from cornerrow instead of down from top
    tbiw_translational_offset: Sequence[float] = (0.0, 0.0, 0.0)
    tbiw_rotation_offset: Sequence[float] = (0.0, 0.0, 0.0)
    tbiw_left_wall_x_offset_override: float = 50.0
    tbiw_left_wall_z_offset_override: float = 0.0
    tbiw_left_wall_lower_x_offset: float = 0.0
    tbiw_left_wall_lower_y_offset: float = 0.0
    tbiw_left_wall_lower_z_offset: float = 0.0

    tbiw_oled_center_row: float = .75  # not none, offsets are from this position
    tbiw_oled_translation_offset: Sequence[float] = (-3.5, 0, 1.5)  # Z offset tweaks are expected depending on curvature and OLED mount choice.
    tbiw_oled_rotation_offset: Sequence[float] = (0, 0, 0)

    ##########################################################################
    ## Finger Trackball in Wall EXPERIMENTAL WIP!!!!                        ##
    ##########################################################################
    finger_trackball_in_wall: bool = False  # Separate trackball option, placing it in the OLED area
    tbiw_ball_center_column: float = 0.2  # up from cornerrow instead of down from top
    tbiw_top_wall_translational_offset: Sequence[float] = (0.0, 0.0, 0.0)
    tbiw_top_wall_rotation_offset: Sequence[float] = (0.0, 0.0, 0.0)
    tbiw_top_wall_y_offset_override: float = 50.0
    tbiw_top_wall_z_offset_override: float = 0.0
    tbiw_top_wall_extension_cols: float = 4

    ###########################################
    ## Trackball JS / ORBYL Thumb Cluster    ##
    ###########################################
    other_thumb: str = 'DEFAULT'  # cluster used for second thumb except if ball_side == 'both'
    tbjs_key_diameter: float = 70
    tbjs_Uwidth: float = 1.2  # size for inner key near trackball
    tbjs_Uheight: float = 1.2  # size for inner key near trackball

    # Offsets are per key and are applied before rotating into place around the ball
    # X and Y act like Tangential and Radial around the ball
    # 'tbjs_translation_offset = (0, 0, 10)  # applied to the whole assy
    # 'tbjs_rotation_offset = (0, 10, 0)  # applied to the whole assy
    tbjs_translation_offset: Sequence[float] = (0, 0, 2)  # applied to the whole assy
    tbjs_rotation_offset: Sequence[float] = (0, -8, 0)  # applied to the whole assy
    tbjs_key_translation_offsets: Sequence[Sequence[float]] = (
        (0.0, 0.0, -3.0 - 5),
        (0.0, 0.0, -3.0 - 5),
        (0.0, 0.0, -3.0 - 5),
        (0.0, 0.0, -3.0 - 5),
    )
    tbjs_key_rotation_offsets: Sequence[Sequence[float]] = (
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    )

    ###################################
    ## Trackball CJ Thumb Cluster    ##
    ###################################
    tbcj_inner_diameter: float = 42
    tbcj_thickness: float = 2
    tbcj_outer_diameter: float = 53

    ###################################
    ## Trackball General             ##
    ###################################
    trackball_modular: bool = False  # Added, creates a hole with space for the lip size listed below.
    trackball_modular_lip_width: float = 3.0  # width of lip cleared out in ring location
    trackball_modular_ball_height: float = 3.0  # height of ball from ring , used to create identical position to fixed.
    trackball_modular_ring_height: float = 10.0  # height mount ring down from ball height. Covers gaps on elevated ball.
    trackball_modular_clearance: float = 0.5  # height of ball from ring, used to create identical position to fixed.

    ball_side: str = 'both'  # 'left', 'right', or 'both'
    ball_diameter: float = 34.0
    ball_wall_thickness: float = 3  # should not be changed unless the import models are changed.
    ball_gap: float = 1.0
    trackball_hole_diameter: float = 36.5
    trackball_hole_height: float = 40
    trackball_plate_thickness: float = 2
    trackball_plate_width: float = 2
    # Removed trackball_rotation, ball_z_offset. and trackball_sensor_rotation and added more flexibility.
    tb_socket_translation_offset: Sequence[float] = (0, 0, 2.0)  # applied to the socket and sensor, large values will cause web/wall issues.
    tb_socket_rotation_offset: Sequence[float] = (0, 0, 0)  # applied to the socket and sensor, large values will cause web/wall issues.
    tb_sensor_translation_offset: Sequence[float] = (0, 0, 0)  # deviation from socket offsets, for fixing generated geometry issues
    tb_sensor_rotation_offset: Sequence[float] = (0, 0, 0)  # deviation from socket offsets, for changing the sensor roll orientation

    ##############################
    # EXPERIMENTAL PARAMETERS
    ##############################
    pinky_1_5U: bool = False  # LEAVE AS FALSE, CURRENTLY BROKEN
    first_1_5U_row = 0
    last_1_5U_row = 5

    skeletal: bool = False
    ##############################

    wall_z_offset: float = 15  # length of the first downward_sloping part of the wall
    wall_x_offset: float = 5  # offset in the x and/or y direction for the first downward_sloping part of the wall (negative)
    wall_y_offset: float = 6  # offset in the x and/or y direction for the first downward_sloping part of the wall (negative)
    left_wall_x_offset: float = 12  # specific values for the left side due to the minimal wall.
    left_wall_z_offset: float = 3  # specific values for the left side due to the minimal wall.
    left_wall_lower_x_offset: float = 0  # specific values for the lower left corner.
    left_wall_lower_y_offset: float = 0  # specific values for the lower left corner.
    left_wall_lower_z_offset: float = 0
    wall_thickness: float = 4.5  # wall thickness parameter used on upper/mid stage of the wall
    wall_base_y_thickness: float = 4.5  # wall thickness at the lower stage
    wall_base_x_thickness: float = 4.5  # wall thickness at the lower stage

    wall_base_back_thickness: float = 4.5  # wall thickness at the lower stage in the specifically in back for interface.

    ## Settings for column_style == :fixed
    ## The defaults roughly match Maltron settings
    ##   http://patentimages.storage.googleapis.com/EP0219944A2/imgf0002.png
    ## fixed_z overrides the z portion of the column ofsets above.
    ## NOTE: THIS DOESN'T WORK QUITE LIKE I'D HOPED.
    fixed_angles: Sequence[float] = (d2r * 10, d2r * 10, 0, 0, 0, d2r * -15, d2r * -15)
    fixed_x: Sequence[float] = (-41.5, -22.5, 0, 20.3, 41.4, 65.5, 89.6)  # relative to the middle finger
    fixed_z: Sequence[float] = (12.1, 8.3, 0, 5, 10.7, 14.5, 17.5)
    fixed_tenting: float = d2r * 0

    #################
    ## Switch Hole ##
    #################

    # plate options are
    # 'HOLE' = a square hole.  Also useful for applying custom plate files.
    # 'NUB' = original side nubs.
    # 'UNDERCUT' = snap fit undercut.  May require CLIP_THICKNESS and possibly CLIP_UNDERCUT tweaking
    #       and/or filing to get proper snap.
    # 'NOTCH' = snap fit undercut only near switch clip.  May require CLIP_THICKNESS and possibly CLIP_UNDERCUT
    #       tweaking and/or filing to get proper snap.
    # 'HS_NUB' = hot swap underside with nubs.
    # 'HS_UNDERCUT' = hot swap underside with undercut. Does not generate properly.  Hot swap step needs to be modified.
    # 'HS_NOTCH' = hot swap underside with notch.  Does not generate properly.  Hot swap step needs to be modified.
    # 'plate_style = NUB'
    plate_style: str = 'NOTCH'

    hole_keyswitch_height: float = 14.0
    hole_keyswitch_width: float = 14.0

    nub_keyswitch_height: float = 14.4
    nub_keyswitch_width: float = 14.4

    undercut_keyswitch_height: float = 14.0
    undercut_keyswitch_width: float = 14.0
    notch_width: float = 6.0  # If using notch, it is identical to undecut, but only locally by the switch clip

    sa_profile_key_height: float = 12.7
    sa_length: float = 18.5
    sa_double_length: float = 37.5
    plate_thickness: float = 4 + 1.1

    plate_rim: float = 1.5 + 0.5
    # Undercut style dimensions
    clip_thickness: float = 1.1
    clip_undercut: float = 1.0
    undercut_transition: float = .2  # NOT FUNCTIONAL WITH OPENSCAD, ONLY WORKS WITH CADQUERY

    # Custom plate step file
    plate_file: bool = None
    plate_offset: float = 0.0

    ##########################
    ## OLED Mount Location
    ##########################
    # Initial pass will be manual placement.  Can be used to create other mounts as well.
    # Mount type options:
    # None or 'NONE' = No OLED mount
    # 'UNDERCUT' = Simple rectangle with undercut for clip in item
    # 'SLIDING' = Features to slide the OLED in place and use a pin or block to secure from underneath.
    # 'CLIP' = Features to set the OLED in a frame a snap a bezel down to hold it in place.

    oled_mount_type: str = 'CLIP'
    oled_center_row: float = 1.25  # if not None, this will override the oled_mount_location_xyz and oled_mount_rotation_xyz settings
    oled_translation_offset: Sequence[float] = (0, 0, 4)  # Z offset tweaks are expected depending on curvature and OLED mount choice.
    oled_rotation_offset: Sequence[float] = (0, 0, 0)

    oled_config: Any = OLED_LOOKUP[oled_mount_type]()

    screws_offset: str = 'INSIDE'  # 'OUTSIDE', 'INSIDE', 'ORIGINAL'

    screw_insert_height: float = 3.8

    # 'screw_insert_bottom_radius = 5.31 / 2  #Designed for inserts
    # 'screw_insert_top_radius = 5.1 / 2  #Designed for inserts

    screw_insert_bottom_radius: float = 2.5 / 2  # Designed for self tapping
    screw_insert_top_radius: float = 2.5 / 2  # Designed for self tapping

    screw_insert_outer_radius: float = 4.25  # Common to keep interface to base

    # Does anyone even use these?  I think they just get in the way.
    wire_post_height: float = 7
    wire_post_overhang: float = 3.5
    wire_post_diameter: float = 2.6

    ###################################
    ## Controller Mount / Connectors ##
    ###################################
    # connector options are
    # 'RJ9_USB_WALL' = Standard internal plate with RJ9 opening and square cutout for connection.
    # 'USB_WALL' = Standard internal plate with a square cutout for connection, no RJ9.
    # 'RJ9_USB_TEENSY' = Teensy holder
    # 'USB_TEENSY' = Teensy holder, no RJ9
    # 'EXTERNAL' = square cutout for a holder such as the one from lolligagger.
    # 'NONE' = No openings in the back.
    controller_mount_type: str = 'EXTERNAL'

    external_holder_height: float = 12.5
    external_holder_width: float = 28.75
    external_holder_xoffset: float = -5.0
    external_holder_yoffset: float = -4.5  # Tweak this value to get the right undercut for the tray engagement.

    # Offset is from the top inner corner of the top inner key.

    ###################################
    ## PCB Screw Mount               ##
    ###################################
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

    ###################################
    ## Bottom Plate Dimensions
    ###################################
    # COMMON DIMENSION
    screw_hole_diameter: float = 3
    # USED FOR CADQUERY ONLY
    base_thickness: float = 3.0  # thickness in the middle of the plate
    base_offset: float = 3.0  # Both start flat/flush on the bottom.  This offsets the base up (if positive)
    base_rim_thickness: float = 5.0  # thickness on the outer frame with screws
    screw_cbore_diameter: float = 6.0
    screw_cbore_depth: float = 2.5

    # Offset is from the top inner corner of the top inner key.

    ###################################
    ## HOLES ON PLATE FOR PCB MOUNT
    ###################################
    plate_holes: bool = True
    plate_holes_xy_offset: Sequence[float] = (0.0, 0.0)
    plate_holes_width: float = 14.3
    plate_holes_height: float = 14.3
    plate_holes_diameter: float = 1.6
    plate_holes_depth: float = 20.0

    ###################################
    ## EXPERIMENTAL
    plate_pcb_clear: bool = False
    plate_pcb_size: Sequence[float] = (18.5, 18.5, 5)
    plate_pcb_offset: Sequence[float] = (0, 0, 0)  # this is off of the back of the plate size.
    ###################################

    ###################################
    ## SHOW PCB FOR FIT CHECK
    ###################################
    pcb_width: float = 18.0
    pcb_height: float = 18.0
    pcb_thickness: float = 1.5
    pcb_hole_diameter: float = 2
    pcb_hole_pattern_width: float = 14.3
    pcb_hole_pattern_height: float = 14.3

    ###################################
    ## COLUMN OFFSETS
    ####################################

    column_offsets: Sequence[Sequence[float]] = (
        (0, 0, 0),
        (0, 0, 0),
        (0, 2.82, -4.5),
        (0, 0, 0),
        (0, -6, 5),  # REDUCED STAGGER
        (0, -6, 5),  # REDUCED STAGGER
        (0, -6, 5),  # NOT USED IN MOST FORMATS (7th column)
    )

    ####################################
    ## END CONFIGURATION SECTION
    ####################################
    def __post_init__(self):
        if self.left_cluster is None:
            import clusters.default as clust
            self.left_cluster = clust.DefaultClusterParameters()
        if self.right_cluster is None:
            import clusters.default as clust
            self.right_cluster = clust.DefaultClusterParameters()

# def save_config():
#     # Check to see if the user has specified an alternate config
#     opts, args = getopt.getopt(sys.argv[1:], "", ["config=", "update="])
#     got_opts = False
#     for opt, arg in opts:
#         if opt in ('--update'):
#             with open(os.path.join(r"..", "configs", arg + '.json'), mode='r') as fid:
#                 data = json.load(fid)
#                 shape_config.update(data)
#             got_opts = True
#
#     for opt, arg in opts:
#         if opt in ('--config'):
#             # If a config file was specified, set the config_name and save_dir
#             shape_config['save_dir'] = arg
#             shape_config['config_name'] = arg
#             got_opts = True
#
#     # Write the config to ./configs/<config_name>.json
#     if got_opts:
#         with open(os.path.join(r"..", "configs", shape_config['config_name'] + '.json'), mode='w') as fid:
#             json.dump(shape_config, fid, indent=4)
#
#     else:
#         with open(os.path.join(r".", 'run_config.json'), mode='w') as fid:
#             json.dump(shape_config, fid, indent=4)
#

if __name__ == '__main__':
    from dactyl_manuform import *
    import clusters.mini as clust

    db = DactylBase(ShapeConfiguration(
        # right_cluster=clust.MiniClusterParameters(),
        # left_cluster=clust.MiniClusterParameters(),
    ))
    db.run()

    ## HERE FOR QUICK TESTING, SHOULD BE COMMENTED ON COMMIT
    # from dactyl_manuform import *
    # run()
