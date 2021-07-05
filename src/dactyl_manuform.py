import solid as sl
import numpy as np
from numpy import pi
import os.path as path
import os
import json

def deg2rad(degrees: float) -> float:
    return degrees * pi / 180


def rad2deg(rad: float) -> float:
    return rad * 180 / pi



## IMPORT DEFAULT CONFIG IN CASE NEW PARAMETERS EXIST
import src.generate_configuration as cfg
for item in cfg.shape_config:
    locals()[item] = cfg.shape_config[item]

## LOAD RUN CONFIGURATION FILE
with open('run_config.json', mode='r') as fid:
    data = json.load(fid)
for item in data:
    locals()[item] = data[item]

if oled_mount_type is not None:
    for item in oled_configurations[oled_mount_type]:
        locals()[item] = oled_configurations[oled_mount_type][item]

if nrows > 5:
    column_style = column_style_gt5

centerrow = nrows - centerrow_offset

lastrow = nrows - 1
cornerrow = lastrow - 1
lastcol = ncols - 1

# Derived values
if plate_style in ['NUB', 'HS_NUB']:
    keyswitch_height = nub_keyswitch_height
    keyswitch_width = nub_keyswitch_width
elif plate_style in ['UNDERCUT', 'HS_UNDERCUT']:
    keyswitch_height = undercut_keyswitch_height
    keyswitch_width = undercut_keyswitch_width
else:
    keyswitch_height = hole_keyswitch_height
    keyswitch_width = hole_keyswitch_width

if plate_style in ['HS_UNDERCUT', 'HS_NUB', 'HS_HOLE']:
    symmetry = "asymmetric"
    plate_file = path.join("..", "src", r"hot_swap_plate.stl")
    plate_offset = 0.0

mount_width = keyswitch_width + 3
mount_height = keyswitch_height + 3
mount_thickness = plate_thickness

if oled_mount_type is not None:
    left_wall_x_offset = oled_left_wall_x_offset_override
    left_wall_z_offset = oled_left_wall_z_offset_override


spath =  path.join("..", "things", save_dir)
if not path.isdir(spath):
    os.mkdir(spath)

def column_offset(column: int) -> list:
    return column_offsets[column]


def single_plate(cylinder_segments=100, side="right"):
    if plate_style in ['NUB', 'HS_NUB']:
        top_wall = sl.cube([mount_width, 1.5, plate_thickness], center=True)
        top_wall = sl.translate(
            (0, (1.5 / 2) + (keyswitch_height / 2), plate_thickness / 2)
        )(top_wall)

        left_wall = sl.cube([1.5, mount_height, plate_thickness], center=True)
        left_wall = sl.translate(
            ((1.5 / 2) + (keyswitch_width / 2), 0, plate_thickness / 2)
        )(left_wall)

        side_nub = sl.cylinder(1, 2.75, segments=cylinder_segments, center=True)
        side_nub = sl.rotate(rad2deg(pi / 2), [1, 0, 0])(side_nub)
        side_nub = sl.translate((keyswitch_width / 2, 0, 1))(side_nub)
        nub_cube = sl.cube([1.5, 2.75, plate_thickness], center=True)
        nub_cube = sl.translate(
            ((1.5 / 2) + (keyswitch_width / 2), 0, plate_thickness / 2)
        )(nub_cube)

        side_nub = sl.hull()(side_nub, nub_cube)

        plate_half1 = top_wall + left_wall + side_nub
        plate_half2 = plate_half1
        plate_half2 = sl.mirror([0, 1, 0])(plate_half2)
        plate_half2 = sl.mirror([1, 0, 0])(plate_half2)

        plate = plate_half1 + plate_half2


    else:  # 'HOLE' or default, square cutout for non-nub designs.
        plate = sl.cube([mount_width, mount_height, mount_thickness], center=True)
        plate = sl.translate((0.0, 0.0, mount_thickness / 2.0))(plate)
        shape_cut = sl.cube([keyswitch_width, keyswitch_height, mount_thickness * 2], center=True)
        shape_cut = sl.translate((0.0, 0.0, mount_thickness))(shape_cut)
        plate = sl.difference()(plate, shape_cut)

    if plate_style in ['UNDERCUT', 'HS_UNDERCUT']:
        undercut = sl.cube([
            keyswitch_width + 2 * clip_undercut,
            keyswitch_height + 2 * clip_undercut,
            mount_thickness
        ], center=True)

        undercut = sl.translate((0.0, 0.0, -clip_thickness + mount_thickness / 2.0))(undercut)

        plate = sl.difference()(plate, undercut)

    if plate_file is not None:
        socket = sl.import_(plate_file)
        socket = sl.translate([0.0, 0.0, plate_thickness + plate_offset])(socket)

        plate = sl.union()(plate, socket)

    if side == "left":
        plate = sl.mirror([-1, 0, 0])(plate)

    return plate


################
## SA Keycaps ##
################

sa_length = 18.25
sa_double_length = 37.5


def sa_cap(Usize=1):
    # MODIFIED TO NOT HAVE THE ROTATION.  NEEDS ROTATION DURING ASSEMBLY
    sa_length = 18.25

    if Usize == 1:
        bl2 = 18.5/2
        bw2 = 18.5/2
        m = 17 / 2
        pl2 = 6
        pw2 = 6

    elif Usize == 2:
        bl2 = sa_length
        bw2 = sa_length / 2
        m = 0
        pl2 = 16
        pw2 = 6

    elif Usize == 1.5:
        bl2 = sa_length / 2
        bw2 = 27.94 / 2
        m = 0
        pl2 = 6
        pw2 = 11


    k1 = sl.polygon([[bw2, bl2], [bw2, -bl2], [-bw2, -bl2], [-bw2, bl2]])
    k1 = sl.linear_extrude(height=0.1, twist=0, convexity=0, center=True)(k1)
    k1 = sl.translate([0, 0, 0.05])(k1)
    k2 = sl.polygon([[pw2, pl2], [pw2, -pl2], [-pw2, -pl2], [-pw2, pl2]])
    k2 = sl.linear_extrude(height=0.1, twist=0, convexity=0, center=True)(k2)
    k2 = sl.translate([0, 0, 12.0])(k2)
    if m > 0:
        m1 = sl.polygon([[m, m], [m, -m], [-m, -m], [-m, m]])
        m1 = sl.linear_extrude(height=0.1, twist=0, convexity=0, center=True)(m1)
        m1 = sl.translate([0, 0, 6.0])(m1)
        key_cap = sl.hull()(k1, k2, m1)
    else:
        key_cap = sl.hull()(k1, k2)

    # key_cap = sl.translate([0, 0, 5 + plate_thickness])(key_cap)
    key_cap = sl.color([220 / 255, 163 / 255, 163 / 255, 1])(key_cap)

    return key_cap


#########################
## Placement Functions ##
#########################


def rotate_around_x(position, angle):
    # print((position, angle))
    t_matrix = np.array(
        [
            [1, 0, 0],
            [0, np.cos(angle), -np.sin(angle)],
            [0, np.sin(angle), np.cos(angle)],
        ]
    )
    return np.matmul(t_matrix, position)


def rotate_around_y(position, angle):
    # print((position, angle))
    t_matrix = np.array(
        [
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)],
        ]
    )
    return np.matmul(t_matrix, position)


cap_top_height = plate_thickness + sa_profile_key_height
row_radius = ((mount_height + extra_height) / 2) / (np.sin(alpha / 2)) + cap_top_height
column_radius = (
                        ((mount_width + extra_width) / 2) / (np.sin(beta / 2))
                ) + cap_top_height
column_x_delta = -1 - column_radius * np.sin(beta)
column_base_angle = beta * (centercol - 2)

def offset_for_column(col, row):
    if pinky_1_5U and (
           col == lastcol and row <= last_1_5U and row >= first_1_5U
    ):
        return 4.7625
    else:
        return 0

def apply_key_geometry(
        shape,
        translate_fn,
        rotate_x_fn,
        rotate_y_fn,
        column,
        row,
        column_style=column_style,
):
    column_angle = beta * (centercol - column)

    if column_style == "orthographic":
        column_z_delta = column_radius * (1 - np.cos(column_angle))
        shape = translate_fn(shape, [0, 0, -row_radius])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius])
        shape = rotate_y_fn(shape, column_angle)
        shape = translate_fn(
            shape, [-(column - centercol) * column_x_delta, 0, column_z_delta]
        )
        shape = translate_fn(shape, column_offset(column))

    elif column_style == "fixed":
        shape = rotate_y_fn(shape, fixed_angles[column])
        shape = translate_fn(shape, [fixed_x[column], 0, fixed_z[column]])
        shape = translate_fn(shape, [0, 0, -(row_radius + fixed_z[column])])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius + fixed_z[column]])
        shape = rotate_y_fn(shape, fixed_tenting)
        shape = translate_fn(shape, [0, column_offset(column)[1], 0])

    else:
        shape = translate_fn(shape, [offset_for_column(column, row), 0, -row_radius])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius])
        shape = translate_fn(shape, [0, 0, -column_radius])
        shape = rotate_y_fn(shape, column_angle)
        shape = translate_fn(shape, [0, 0, column_radius])
        shape = translate_fn(shape, column_offset(column))

    shape = rotate_y_fn(shape, tenting_angle)
    shape = translate_fn(shape, [0, 0, keyboard_z_offset])

    return shape


def translate(shape, xyz):
    return sl.translate(xyz)(shape)


def x_rot(shape, angle):
    return sl.rotate(rad2deg(angle), [1, 0, 0])(shape)


def y_rot(shape, angle):
    return sl.rotate(rad2deg(angle), [0, 1, 0])(shape)


def key_place(shape, column, row):
    return apply_key_geometry(shape, translate, x_rot, y_rot, column, row)


def add_translate(shape, xyz):
    vals = []
    for i in range(len(shape)):
        vals.append(shape[i] + xyz[i])
    return vals


def key_position(position, column, row):
    return apply_key_geometry(
        position, add_translate, rotate_around_x, rotate_around_y, column, row
    )


def key_holes(side="right"):
    hole = single_plate(side=side)
    holes = []
    for column in range(ncols):
        for row in range(nrows):
            if (column in [2, 3]) or (not row == lastrow):
                holes.append(key_place(hole, column, row))

    return sl.union()(*holes)


def caps():
    caps = []
    for column in range(ncols):
        for row in range(nrows):
            if (column in [2, 3]) or (not row == lastrow):
                caps.append(key_place(sa_cap(), column, row))

    return sl.union()(*caps)


####################
## Web Connectors ##
####################


def web_post():
    post = sl.cube([post_size, post_size, web_thickness], center=True)
    post = sl.translate([0, 0, plate_thickness - (web_thickness / 2)])(post)
    return post


post_adj = post_size / 2


def web_post_tr(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return sl.translate(
            [(mount_width / w_divide) - post_adj, (mount_height / 2) - post_adj, 0]
        )(web_post())

def web_post_tl(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return sl.translate(
        [-(mount_width / w_divide) + post_adj, (mount_height / 2) - post_adj, 0]
    )(web_post())


def web_post_bl(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return sl.translate(
        [-(mount_width / w_divide) + post_adj, -(mount_height / 2) + post_adj, 0]
    )(web_post())


def web_post_br(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return sl.translate(
        [(mount_width / w_divide) - post_adj, -(mount_height / 2) + post_adj, 0]
    )(web_post())




def triangle_hulls(shapes):
    hulls = []
    for i in range(len(shapes) - 2):
        hulls.append(sl.hull()(*shapes[i: (i + 3)]))

    return sl.union()(*hulls)


def connectors():
    hulls = []
    for column in range(ncols - 1):
        for row in range(lastrow):  # need to consider last_row?
            # for row in range(nrows):  # need to consider last_row?
            places = []
            places.append(key_place(web_post_tl(), column + 1, row))
            places.append(key_place(web_post_tr(), column, row))
            places.append(key_place(web_post_bl(), column + 1, row))
            places.append(key_place(web_post_br(), column, row))
            hulls.append(triangle_hulls(places))

    for column in range(ncols):
        # for row in range(nrows-1):
        for row in range(cornerrow):
            places = []
            places.append(key_place(web_post_bl(), column, row))
            places.append(key_place(web_post_br(), column, row))
            places.append(key_place(web_post_tl(), column, row + 1))
            places.append(key_place(web_post_tr(), column, row + 1))
            hulls.append(triangle_hulls(places))

    for column in range(ncols - 1):
        # for row in range(nrows-1):  # need to consider last_row?
        for row in range(cornerrow):  # need to consider last_row?
            places = []
            places.append(key_place(web_post_br(), column, row))
            places.append(key_place(web_post_tr(), column, row + 1))
            places.append(key_place(web_post_bl(), column + 1, row))
            places.append(key_place(web_post_tl(), column + 1, row + 1))
            hulls.append(triangle_hulls(places))

    return sl.union()(*hulls)


############
## Thumbs ##
############


def thumborigin():
    origin = key_position([mount_width / 2, -(mount_height / 2), 0], 1, cornerrow)
    for i in range(len(origin)):
        origin[i] = origin[i] + thumb_offsets[i]
    return origin


def thumb_tr_place(shape):
    shape = sl.rotate(10, [1, 0, 0])(shape)
    shape = sl.rotate(-23, [0, 1, 0])(shape)
    shape = sl.rotate(10, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-12, -16, 3])(shape)
    return shape


def thumb_tl_place(shape):
    shape = sl.rotate(10, [1, 0, 0])(shape)
    shape = sl.rotate(-23, [0, 1, 0])(shape)
    shape = sl.rotate(10, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-32, -15, -2])(shape)
    return shape


def thumb_mr_place(shape):
    shape = sl.rotate(-6, [1, 0, 0])(shape)
    shape = sl.rotate(-34, [0, 1, 0])(shape)
    shape = sl.rotate(48, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-29, -40, -13])(shape)
    return shape


def thumb_ml_place(shape):
    shape = sl.rotate(6, [1, 0, 0])(shape)
    shape = sl.rotate(-34, [0, 1, 0])(shape)
    shape = sl.rotate(40, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-51, -25, -12])(shape)
    return shape


def thumb_br_place(shape):
    shape = sl.rotate(-16, [1, 0, 0])(shape)
    shape = sl.rotate(-33, [0, 1, 0])(shape)
    shape = sl.rotate(54, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-37.8, -55.3, -25.3])(shape)
    return shape


def thumb_bl_place(shape):
    shape = sl.rotate(-4, [1, 0, 0])(shape)
    shape = sl.rotate(-35, [0, 1, 0])(shape)
    shape = sl.rotate(52, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-56.3, -43.3, -23.5])(shape)
    return shape


def thumb_1x_layout(shape):
    return sl.union()(
        thumb_mr_place(shape),
        thumb_ml_place(shape),
        thumb_br_place(shape),
        thumb_bl_place(shape),
    )


def thumb_15x_layout(shape):
    return sl.union()(thumb_tr_place(shape), thumb_tl_place(shape), )


def double_plate_half():
    plate_height = (sa_double_length - mount_height) / 3
    # plate_height = (2*sa_length-mount_height) / 3
    top_plate = sl.cube([mount_width, plate_height, web_thickness], center=True)
    top_plate = sl.translate(
        [0, (plate_height + mount_height) / 2, plate_thickness - (web_thickness / 2)]
    )(top_plate)

    return top_plate


def double_plate():
    # plate_height = (sa_double_length - mount_height) / 3
    # # plate_height = (2*sa_length-mount_height) / 3
    # top_plate = sl.cube([mount_width, plate_height, web_thickness], center=True)
    # top_plate = sl.translate(
    #     [0, (plate_height + mount_height) / 2, plate_thickness - (web_thickness / 2)]
    # )(top_plate)
    top_plate = double_plate_half()
    return sl.union()(top_plate, sl.mirror([0, 1, 0])(top_plate))


def thumb(side="right"):
    if thumb_style == "MINI":
        return mini_thumb(side)
    elif thumb_style == "CARBONFET":
        return carbonfet_thumb(side)
    else:
        return default_thumb(side)


def thumbcaps():
    if thumb_style == "MINI":
        return mini_thumbcaps()
    elif thumb_style == "CARBONFET":
        return carbonfet_thumbcaps()
    else:
        return default_thumbcaps()

def thumb_connectors():
    if thumb_style == "MINI":
        return mini_thumb_connectors()
    elif thumb_style == "CARBONFET":
        return carbonfet_thumb_connectors()
    else:
        return default_thumb_connectors()


def default_thumbcaps():
    t1 = thumb_1x_layout(sa_cap(1))
    t15 = thumb_15x_layout(sl.rotate(pi / 2, [0, 0, 1])(sa_cap(1.5)))
    return t1 + t15



def default_thumb(side="right"):

    shape = thumb_1x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    shape += thumb_15x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    shape += thumb_15x_layout(double_plate())

    # shape = thumb_1x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    # shape += thumb_tr_place(sl.rotate([0.0, 0.0, 90])(single_plate(side=side)))
    # shape += thumb_tr_place(double_plate(side=side))
    # shape += thumb_tl_place(sl.rotate([0.0, 0.0, 90])(single_plate(side=side)))
    # shape += thumb_tl_place(double_plate(side=side))

    return shape


def thumb_post_tr():
    return sl.translate(
        [(mount_width / 2) - post_adj, (mount_height / 1.15) - post_adj, 0]
    )(web_post())


def thumb_post_tl():
    return sl.translate(
        [-(mount_width / 2) + post_adj, (mount_height / 1.15) - post_adj, 0]
    )(web_post())


def thumb_post_bl():
    return sl.translate(
        [-(mount_width / 2) + post_adj, -(mount_height / 1.15) + post_adj, 0]
    )(web_post())


def thumb_post_br():
    return sl.translate(
        [(mount_width / 2) - post_adj, -(mount_height / 1.15) + post_adj, 0]
    )(web_post())


def default_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                thumb_tl_place(thumb_post_tr()),
                thumb_tl_place(thumb_post_br()),
                thumb_tr_place(thumb_post_tl()),
                thumb_tr_place(thumb_post_bl()),
            ]
        )
    )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                thumb_br_place(web_post_tr()),
                thumb_br_place(web_post_br()),
                thumb_mr_place(web_post_tl()),
                thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                thumb_br_place(web_post_tr()),
                thumb_br_place(web_post_br()),
                thumb_mr_place(web_post_tl()),
                thumb_mr_place(web_post_bl()),
            ]
        )
    )
    # centers of the bottom four
    hulls.append(
        triangle_hulls(
            [
                thumb_bl_place(web_post_tr()),
                thumb_bl_place(web_post_br()),
                thumb_ml_place(web_post_tl()),
                thumb_ml_place(web_post_bl()),
            ]
        )
    )

    # top two to the middle two, starting on the left
    hulls.append(
        triangle_hulls(
            [
                thumb_br_place(web_post_tl()),
                thumb_bl_place(web_post_bl()),
                thumb_br_place(web_post_tr()),
                thumb_bl_place(web_post_br()),
                thumb_mr_place(web_post_tl()),
                thumb_ml_place(web_post_bl()),
                thumb_mr_place(web_post_tr()),
                thumb_ml_place(web_post_br()),
            ]
        )
    )

    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                thumb_tl_place(thumb_post_tl()),
                thumb_ml_place(web_post_tr()),
                thumb_tl_place(thumb_post_bl()),
                thumb_ml_place(web_post_br()),
                thumb_tl_place(thumb_post_br()),
                thumb_mr_place(web_post_tr()),
                thumb_tr_place(thumb_post_bl()),
                thumb_mr_place(web_post_br()),
                thumb_tr_place(thumb_post_br()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                thumb_tl_place(thumb_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                thumb_tl_place(thumb_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                thumb_tr_place(thumb_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                thumb_tr_place(thumb_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                thumb_tr_place(thumb_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                thumb_tr_place(thumb_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    return sl.union()(*hulls)


############################
# MINI THUMB CLUSTER
############################


def mini_thumb_tr_place(shape):
    shape = sl.rotate(14, [1, 0, 0])(shape)
    shape = sl.rotate(-15, [0, 1, 0])(shape)
    shape = sl.rotate(10, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-15, -10, 5])(shape)
    return shape


def mini_thumb_tl_place(shape):
    shape = sl.rotate(10, [1, 0, 0])(shape)
    shape = sl.rotate(-23, [0, 1, 0])(shape)
    shape = sl.rotate(25, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-35, -16, -2])(shape)
    return shape


def mini_thumb_mr_place(shape):
    shape = sl.rotate(10, [1, 0, 0])(shape)
    shape = sl.rotate(-23, [0, 1, 0])(shape)
    shape = sl.rotate(25, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-23, -34, -6])(shape)
    return shape


def mini_thumb_br_place(shape):
    shape = sl.rotate(6, [1, 0, 0])(shape)
    shape = sl.rotate(-34, [0, 1, 0])(shape)
    shape = sl.rotate(35, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-39, -43, -16])(shape)
    return shape


def mini_thumb_bl_place(shape):
    shape = sl.rotate(6, [1, 0, 0])(shape)
    shape = sl.rotate(-32, [0, 1, 0])(shape)
    shape = sl.rotate(35, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-51, -25, -11.5])(shape)
    return shape


def mini_thumb_1x_layout(shape):
    return sl.union()(
        mini_thumb_mr_place(shape),
        mini_thumb_br_place(shape),
        mini_thumb_tl_place(shape),
        mini_thumb_bl_place(shape),
    )


def mini_thumb_15x_layout(shape):
    return sl.union()(mini_thumb_tr_place(shape))


def mini_thumbcaps():
    t1 = mini_thumb_1x_layout(sa_cap(1))
    t15 = mini_thumb_15x_layout(sl.rotate(pi / 2, [0, 0, 1])(sa_cap(1)))
    return t1 + t15


def mini_thumb(side="right"):

    # shape = thumb_1x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    # shape += thumb_15x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    shape = mini_thumb_1x_layout(single_plate(side=side))
    shape += mini_thumb_15x_layout(single_plate(side=side))

    return shape


def mini_thumb_post_tr():
    return sl.translate(
        [(mount_width / 2) - post_adj, (mount_height / 2) - post_adj, 0]
    )(web_post())


def mini_thumb_post_tl():
    return sl.translate(
        [-(mount_width / 2) + post_adj, (mount_height / 2) - post_adj, 0]
    )(web_post())


def mini_thumb_post_bl():
    return sl.translate(
        [-(mount_width / 2) + post_adj, -(mount_height / 2) + post_adj, 0]
    )(web_post())


def mini_thumb_post_br():
    return sl.translate(
        [(mount_width / 2) - post_adj, -(mount_height / 2) + post_adj, 0]
    )(web_post())


def mini_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tr()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_tr_place(mini_thumb_post_tl()),
                mini_thumb_tr_place(mini_thumb_post_bl()),
            ]
        )
    )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_br_place(web_post_tr()),
                mini_thumb_br_place(web_post_br()),
                mini_thumb_mr_place(web_post_tl()),
                mini_thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_mr_place(web_post_br()),
                mini_thumb_tr_place(mini_thumb_post_br()),
            ]
        )
    )

    # between top and bottom row
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_br_place(web_post_tl()),
                mini_thumb_bl_place(web_post_bl()),
                mini_thumb_br_place(web_post_tr()),
                mini_thumb_bl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tl()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_tr_place(web_post_bl()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tr_place(web_post_br()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tl()),
                mini_thumb_bl_place(web_post_tr()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_bl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tr()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                mini_thumb_tl_place(web_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                mini_thumb_tr_place(mini_thumb_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                mini_thumb_tr_place(mini_thumb_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                mini_thumb_tr_place(mini_thumb_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                mini_thumb_tr_place(mini_thumb_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    # hulls.append(
    #     triangle_hulls(
    #         [
    #             key_place(web_post_tr(), 3, lastrow),
    #             key_place(web_post_br(), 3, lastrow),
    #             key_place(web_post_tr(), 3, lastrow),
    #             key_place(web_post_bl(), 4, cornerrow),
    #         ]
    #     )
    # )

    return sl.union()(*hulls)


############################
# Carbonfet THUMB CLUSTER
############################


def carbonfet_thumb_tl_place(shape):
    shape = sl.rotate(10, [1, 0, 0])(shape)
    shape = sl.rotate(-24, [0, 1, 0])(shape)
    shape = sl.rotate(10, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-13, -9.8, 4])(shape)

    return shape

def carbonfet_thumb_tr_place(shape):
    shape = sl.rotate(6, [1, 0, 0])(shape)
    shape = sl.rotate(-24, [0, 1, 0])(shape)
    shape = sl.rotate(10, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-7.5, -29.5, 0])(shape)
    return shape

def carbonfet_thumb_ml_place(shape):
    shape = sl.rotate(8, [1, 0, 0])(shape)
    shape = sl.rotate(-31, [0, 1, 0])(shape)
    shape = sl.rotate(14, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-30.5, -17, -6])(shape)
    return shape

def carbonfet_thumb_mr_place(shape):
    shape = sl.rotate(4, [1, 0, 0])(shape)
    shape = sl.rotate(-31, [0, 1, 0])(shape)
    shape = sl.rotate(14, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-22.2, -41, -10.3])(shape)
    return shape

def carbonfet_thumb_br_place(shape):
    shape = sl.rotate(2, [1, 0, 0])(shape)
    shape = sl.rotate(-37, [0, 1, 0])(shape)
    shape = sl.rotate(18, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-37, -46.4, -22])(shape)
    return shape

def carbonfet_thumb_bl_place(shape):
    shape = sl.rotate(6, [1, 0, 0])(shape)
    shape = sl.rotate(-37, [0, 1, 0])(shape)
    shape = sl.rotate(18, [0, 0, 1])(shape)
    shape = sl.translate(thumborigin())(shape)
    shape = sl.translate([-47, -23, -19])(shape)
    return shape


def carbonfet_thumb_1x_layout(shape):
    return sl.union()(
        # carbonfet_thumb_tr_place(sl.rotate(pi / 2, [0, 0, 1])(shape)),
        carbonfet_thumb_tr_place(shape),
        carbonfet_thumb_mr_place(shape),
        carbonfet_thumb_br_place(shape),
        # carbonfet_thumb_tl_place(sl.rotate(pi / 2, [0, 0, 1])(shape)),
        carbonfet_thumb_tl_place(shape),
    )


def carbonfet_thumb_15x_layout(shape):
    return sl.union()(
        carbonfet_thumb_bl_place(shape),
        carbonfet_thumb_ml_place(shape)
    )


def carbonfet_thumbcaps():
    t1 = carbonfet_thumb_1x_layout(sa_cap(1))
    t15 = carbonfet_thumb_15x_layout(sl.rotate(pi / 2, [0, 0, 1])(sa_cap(1.5)))
    return t1 + t15


def carbonfet_thumb(side="right"):
    # shape = thumb_1x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    # shape += thumb_15x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    shape = carbonfet_thumb_1x_layout(single_plate(side=side))
    shape += carbonfet_thumb_15x_layout(double_plate_half())
    shape += carbonfet_thumb_15x_layout(single_plate(side=side))

    return shape

def carbonfet_thumb_post_tr():
    return sl.translate(
        [(mount_width / 2) - post_adj, (mount_height / 1.15) - post_adj, 0]
    )(web_post())


def carbonfet_thumb_post_tl():
    return sl.translate(
        [-(mount_width / 2) + post_adj, (mount_height / 1.15) - post_adj, 0]
    )(web_post())


def carbonfet_thumb_post_bl():
    return sl.translate(
        [-(mount_width / 2) + post_adj, -(mount_height / 1.15) + post_adj, 0]
    )(web_post())


def carbonfet_thumb_post_br():
    return sl.translate(
        [(mount_width / 2) - post_adj, -(mount_height / 2) + post_adj, 0]
    )(web_post())

def carbonfet_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tl_place(web_post_tl()),
                carbonfet_thumb_tl_place(web_post_bl()),
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tr()),
                carbonfet_thumb_ml_place(web_post_br()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tl()),
                carbonfet_thumb_ml_place(web_post_bl()),
                carbonfet_thumb_bl_place(carbonfet_thumb_post_tr()),
                carbonfet_thumb_bl_place(web_post_br()),
            ]
        )
    )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_br_place(web_post_tr()),
                carbonfet_thumb_br_place(web_post_br()),
                carbonfet_thumb_mr_place(web_post_tl()),
                carbonfet_thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_mr_place(web_post_tr()),
                carbonfet_thumb_mr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tl()),
                carbonfet_thumb_tr_place(web_post_bl()),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_bl()),
                carbonfet_thumb_mr_place(web_post_br()),
            ]
        )
    )

    # between top and bottom row
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_br_place(web_post_tl()),
                carbonfet_thumb_bl_place(web_post_bl()),
                carbonfet_thumb_br_place(web_post_tr()),
                carbonfet_thumb_bl_place(web_post_br()),
                carbonfet_thumb_mr_place(web_post_tl()),
                carbonfet_thumb_ml_place(web_post_bl()),
                carbonfet_thumb_mr_place(web_post_tr()),
                carbonfet_thumb_ml_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tl()),
                carbonfet_thumb_tl_place(web_post_bl()),
                carbonfet_thumb_tr_place(web_post_tr()),
                carbonfet_thumb_tl_place(web_post_br()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                carbonfet_thumb_tl_place(web_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                carbonfet_thumb_tl_place(web_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                carbonfet_thumb_tl_place(web_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                carbonfet_thumb_tl_place(web_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                carbonfet_thumb_tl_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tr()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, lastrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tr()),
                key_place(web_post_bl(), 3, lastrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )


    return sl.union()(*hulls)

##########
## Case ##
##########


def bottom_hull(p, height=0.001):
    shape = None
    for item in p:
        proj = sl.projection()(p)
        t_shape = sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(
            proj
        )
        t_shape = sl.translate([0, 0, height / 2 - 10])(t_shape)
        if shape is None:
            shape = t_shape
        shape = sl.hull()(p, shape, t_shape)
    return shape


def left_key_position(row, direction):
    pos = np.array(
        key_position([-mount_width * 0.5, direction * mount_height * 0.5, 0], 0, row)
    )
    return list(pos - np.array([left_wall_x_offset, 0, left_wall_z_offset]))


def left_key_place(shape, row, direction):
    pos = left_key_position(row, direction)
    return sl.translate(pos)(shape)


def wall_locate1(dx, dy):
    return [dx * wall_thickness, dy * wall_thickness, -1]


def wall_locate2(dx, dy):
    return [dx * wall_x_offset, dy * wall_y_offset, -wall_z_offset]


def wall_locate3(dx, dy, back=False):
    if back:
        return [
            dx * (wall_x_offset + wall_base_x_thickness),
            dy * (wall_y_offset + wall_base_back_thickness),
            -wall_z_offset,
        ]
    else:
        return [
            dx * (wall_x_offset + wall_base_x_thickness),
            dy * (wall_y_offset + wall_base_y_thickness),
            -wall_z_offset,
        ]


def wall_brace(place1, dx1, dy1, post1, place2, dx2, dy2, post2, back=False):
    hulls = []

    hulls.append(place1(post1))
    hulls.append(place1(sl.translate(wall_locate1(dx1, dy1))(post1)))
    hulls.append(place1(sl.translate(wall_locate2(dx1, dy1))(post1)))
    hulls.append(place1(sl.translate(wall_locate3(dx1, dy1, back))(post1)))

    hulls.append(place2(post2))
    hulls.append(place2(sl.translate(wall_locate1(dx2, dy2))(post2)))
    hulls.append(place2(sl.translate(wall_locate2(dx2, dy2))(post2)))
    hulls.append(place2(sl.translate(wall_locate3(dx2, dy2, back))(post2)))
    shape1 = sl.hull()(*hulls)

    hulls = []
    hulls.append(place1(sl.translate(wall_locate2(dx1, dy1))(post1)))
    hulls.append(place1(sl.translate(wall_locate3(dx1, dy1, back))(post1)))
    hulls.append(place2(sl.translate(wall_locate2(dx2, dy2))(post2)))
    hulls.append(place2(sl.translate(wall_locate3(dx2, dy2, back))(post2)))
    shape2 = bottom_hull(hulls)

    return shape1 + shape2


def key_wall_brace(x1, y1, dx1, dy1, post1, x2, y2, dx2, dy2, post2, back=False):
    return wall_brace(
        (lambda shape: key_place(shape, x1, y1)),
        dx1,
        dy1,
        post1,
        (lambda shape: key_place(shape, x2, y2)),
        dx2,
        dy2,
        post2,
        back
    )


def back_wall():
    x = 0
    shape = key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True)
    for i in range(ncols - 1):
        x = i + 1
        shape += key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True)
        shape += key_wall_brace(
            x, 0, 0, 1, web_post_tl(), x - 1, 0, 0, 1, web_post_tr(), back=True
        )
    shape += key_wall_brace(
        lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr(), back=True
    )
    return shape


def right_wall():
    if pinky_1_5U:
        if first_1_5U_row > 0:
            shape = key_wall_brace(
                lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr())
        else:
            shape = key_wall_brace(
                lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 0, 1, web_post_tr(wide=True))
            shape += key_wall_brace(
                lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr(wide=True))

        shape += key_wall_brace(
            lastcol, 0, 0, -1, web_post_br(), lastcol, 0, 1, 0, web_post_br())

        if first_1_5U_row >= 2:
            for y in range(first_1_5U_row - 1):
                shape += key_wall_brace(
                    lastcol, y, 1, 0, web_post_tr(), lastcol, y, 1, 0, web_post_br())
                shape += key_wall_brace(
                    lastcol, y, 1, 0, web_post_br(), lastcol, y-1, 1, 0, web_post_tr())

        if first_1_5U_row >= 1:
            for i in range(2):
                y = first_1_5U_row - 1 + i
                shape += key_wall_brace(
                    lastcol, y, 1, 0, web_post_tr(), lastcol, y-1, 1, 0, web_post_tr(wide=True))

        for i in range(2):
            y = first_1_5U_row + i
            shape += key_wall_brace(
                lastcol, y, 1, 0, web_post_tr(wide=True), lastcol, y, 1, 0, web_post_br(wide=True))

        for i in range(first_1_5U_row - last_1_5U_row):
            y = first_1_5U_row + i
            shape += key_wall_brace(
                lastcol, y+1, 1, 0, web_post_tr(wide=True), lastcol, y, 1, 0, web_post_br(wide=True))

        if first_1_5U_row >= 1:
            for i in range(2):
                y = first_1_5U_row - 1 + i
                shape += key_wall_brace(
                    lastcol, y, 1, 0, web_post_tr(), lastcol, y-1, 1, 0, web_post_tr(wide=True))

    else:
        y = 0
        shape = key_wall_brace(
            lastcol, y, 1, 0, web_post_tr(), lastcol, y, 1, 0, web_post_br()
        )
        for i in range(lastrow - 1):
            y = i + 1
            shape += key_wall_brace(
                lastcol, y - 1, 1, 0, web_post_br(), lastcol, y, 1, 0, web_post_tr())

            shape += key_wall_brace(
                lastcol, y, 1, 0, web_post_tr(), lastcol, y, 1, 0, web_post_br())

        shape += key_wall_brace(
            lastcol, cornerrow, 0, -1, web_post_br(), lastcol, cornerrow, 1, 0, web_post_br())

    return shape


def left_wall():
    shape = wall_brace(
        (lambda sh: key_place(sh, 0, 0)),
        0,
        1,
        web_post_tl(),
        (lambda sh: left_key_place(sh, 0, 1)),
        0,
        1,
        web_post(),
    )

    shape += wall_brace(
        (lambda sh: left_key_place(sh, 0, 1)),
        0,
        1,
        web_post(),
        (lambda sh: left_key_place(sh, 0, 1)),
        -1,
        0,
        web_post(),
    )

    for i in range(lastrow):
        y = i
        temp_shape1 = wall_brace(
            (lambda sh: left_key_place(sh, y, 1)),
            -1,
            0,
            web_post(),
            (lambda sh: left_key_place(sh, y, -1)),
            -1,
            0,
            web_post(),
        )
        temp_shape2 = sl.hull()(
            key_place(web_post_tl(), 0, y),
            key_place(web_post_bl(), 0, y),
            left_key_place(web_post(), y, 1),
            left_key_place(web_post(), y, -1),
        )
        shape += temp_shape1 + temp_shape2

    for i in range(lastrow - 1):
        y = i + 1
        temp_shape1 = wall_brace(
            (lambda sh: left_key_place(sh, y - 1, -1)),
            -1,
            0,
            web_post(),
            (lambda sh: left_key_place(sh, y, 1)),
            -1,
            0,
            web_post(),
        )
        temp_shape2 = sl.hull()(
            key_place(web_post_tl(), 0, y),
            key_place(web_post_bl(), 0, y - 1),
            left_key_place(web_post(), y, 1),
            left_key_place(web_post(), y - 1, -1),
        )
        shape += temp_shape1 + temp_shape2

    return shape


def front_wall():
    shape = key_wall_brace(
        lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr()
    )
    shape += key_wall_brace(
        3, lastrow, 0, -1, web_post_bl(), 3, lastrow, 0.5, -1, web_post_br()
    )
    shape += key_wall_brace(
        3, lastrow, 0.5, -1, web_post_br(), 4, cornerrow, 1, -1, web_post_bl()
    )
    for i in range(ncols - 4):
        x = i + 4
        shape += key_wall_brace(
            x, cornerrow, 0, -1, web_post_bl(), x, cornerrow, 0, -1, web_post_br()
        )
    for i in range(ncols - 5):
        x = i + 5
        shape += key_wall_brace(
            x, cornerrow, 0, -1, web_post_bl(), x - 1, cornerrow, 0, -1, web_post_br()
        )

    return shape

def thumb_walls():
    if thumb_style == "MINI":
        return mini_thumb_walls()
    elif thumb_style == "CARBONFET":
        return carbonfet_thumb_walls()
    else:
        return default_thumb_walls()

def thumb_connection():
    if thumb_style == "MINI":
        return mini_thumb_connection()
    elif thumb_style == "CARBONFET":
        return carbonfet_thumb_connection()
    else:
        return default_thumb_connection()

def default_thumb_walls():
    # thumb, walls
    shape = wall_brace(thumb_mr_place, 0, -1, web_post_br(), thumb_tr_place, 0, -1, thumb_post_br())
    shape += wall_brace(thumb_mr_place, 0, -1, web_post_br(), thumb_mr_place, 0, -1, web_post_bl())
    shape += wall_brace(thumb_br_place, 0, -1, web_post_br(), thumb_br_place, 0, -1, web_post_bl())
    shape += wall_brace(thumb_ml_place, -0.3, 1, web_post_tr(), thumb_ml_place, 0, 1, web_post_tl())
    shape += wall_brace(thumb_bl_place, 0, 1, web_post_tr(), thumb_bl_place, 0, 1, web_post_tl())
    shape += wall_brace(thumb_br_place, -1, 0, web_post_tl(), thumb_br_place, -1, 0, web_post_bl())
    shape += wall_brace(thumb_bl_place, -1, 0, web_post_tl(), thumb_bl_place, -1, 0, web_post_bl())
    # thumb, corners
    shape += wall_brace(thumb_br_place, -1, 0, web_post_bl(), thumb_br_place, 0, -1, web_post_bl())
    shape += wall_brace(thumb_bl_place, -1, 0, web_post_tl(), thumb_bl_place, 0, 1, web_post_tl())
    # thumb, tweeners
    shape += wall_brace(thumb_mr_place, 0, -1, web_post_bl(), thumb_br_place, 0, -1, web_post_br())
    shape += wall_brace(thumb_ml_place, 0, 1, web_post_tl(), thumb_bl_place, 0, 1, web_post_tr())
    shape += wall_brace(thumb_bl_place, -1, 0, web_post_bl(), thumb_br_place, -1, 0, web_post_tl())
    shape += wall_brace(thumb_tr_place, 0, -1, thumb_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())

    return shape

def default_thumb_connection():
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = bottom_hull(
        [
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            thumb_ml_place(sl.translate(wall_locate2(-0.3, 1))(web_post_tr())),
            thumb_ml_place(sl.translate(wall_locate3(-0.3, 1))(web_post_tr())),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            thumb_ml_place(sl.translate(wall_locate2(-0.3, 1))(web_post_tr())),
            thumb_ml_place(sl.translate(wall_locate3(-0.3, 1))(web_post_tr())),
            thumb_tl_place(thumb_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(web_post(), cornerrow, -1),
            left_key_place(sl.translate(wall_locate1(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            thumb_tl_place(thumb_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(web_post(), cornerrow, -1),
            left_key_place(sl.translate(wall_locate1(-1, 0))(web_post()), cornerrow, -1),
            key_place(web_post_bl(), 0, cornerrow),
            # key_place(sl.translate(wall_locate1(-1, 0))(web_post_bl()), 0, cornerrow),
            key_place(sl.translate(wall_locate1(0, 0))(web_post_bl()), 0, cornerrow),
            thumb_tl_place(thumb_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            thumb_ml_place(web_post_tr()),
            thumb_ml_place(sl.translate(wall_locate1(-0.3, 1))(web_post_tr())),
            thumb_ml_place(sl.translate(wall_locate2(-0.3, 1))(web_post_tr())),
            thumb_ml_place(sl.translate(wall_locate3(-0.3, 1))(web_post_tr())),
            thumb_tl_place(thumb_post_tl()),
        ]
    )

    return shape


def mini_thumb_walls():
    # thumb, walls
    shape = wall_brace(mini_thumb_mr_place, 0, -1, web_post_br(), mini_thumb_tr_place, 0, -1, mini_thumb_post_br())
    shape += wall_brace(mini_thumb_mr_place, 0, -1, web_post_br(), mini_thumb_mr_place, 0, -1, web_post_bl())
    shape += wall_brace(mini_thumb_br_place, 0, -1, web_post_br(), mini_thumb_br_place, 0, -1, web_post_bl())
    shape += wall_brace(mini_thumb_bl_place, 0, 1, web_post_tr(), mini_thumb_bl_place, 0, 1, web_post_tl())
    shape += wall_brace(mini_thumb_br_place, -1, 0, web_post_tl(), mini_thumb_br_place, -1, 0, web_post_bl())
    shape += wall_brace(mini_thumb_bl_place, -1, 0, web_post_tl(), mini_thumb_bl_place, -1, 0, web_post_bl())
    # thumb, corners
    shape += wall_brace(mini_thumb_br_place, -1, 0, web_post_bl(), mini_thumb_br_place, 0, -1, web_post_bl())
    shape += wall_brace(mini_thumb_bl_place, -1, 0, web_post_tl(), mini_thumb_bl_place, 0, 1, web_post_tl())
    # thumb, tweeners
    shape += wall_brace(mini_thumb_mr_place, 0, -1, web_post_bl(), mini_thumb_br_place, 0, -1, web_post_br())
    shape += wall_brace(mini_thumb_bl_place, -1, 0, web_post_bl(), mini_thumb_br_place, -1, 0, web_post_tl())
    shape += wall_brace(mini_thumb_tr_place, 0, -1, mini_thumb_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())

    return shape

def mini_thumb_connection():
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = bottom_hull(
        [
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            mini_thumb_bl_place(sl.translate(wall_locate2(-0.3, 1))(web_post_tr())),
            mini_thumb_bl_place(sl.translate(wall_locate3(-0.3, 1))(web_post_tr())),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            mini_thumb_bl_place(sl.translate(wall_locate2(-0.3, 1))(web_post_tr())),
            mini_thumb_bl_place(sl.translate(wall_locate3(-0.3, 1))(web_post_tr())),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(web_post(), cornerrow, -1),
            left_key_place(sl.translate(wall_locate1(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(web_post(), cornerrow, -1),
            left_key_place(sl.translate(wall_locate1(-1, 0))(web_post()), cornerrow, -1),
            key_place(web_post_bl(), 0, cornerrow),
            # key_place(sl.translate(wall_locate1(-1, 0))(web_post_bl()), 0, cornerrow),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            mini_thumb_bl_place(web_post_tr()),
            mini_thumb_bl_place(sl.translate(wall_locate1(-0.3, 1))(web_post_tr())),
            mini_thumb_bl_place(sl.translate(wall_locate2(-0.3, 1))(web_post_tr())),
            mini_thumb_bl_place(sl.translate(wall_locate3(-0.3, 1))(web_post_tr())),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )

    return shape



def carbonfet_thumb_walls():
    # thumb, walls
    shape = wall_brace(carbonfet_thumb_mr_place, 0, -1, web_post_br(), carbonfet_thumb_tr_place, 0, -1, web_post_br())
    shape += wall_brace(carbonfet_thumb_mr_place, 0, -1, web_post_br(), carbonfet_thumb_mr_place, 0, -1.15, web_post_bl())
    shape += wall_brace(carbonfet_thumb_br_place, 0, -1, web_post_br(), carbonfet_thumb_br_place, 0, -1, web_post_bl())
    shape += wall_brace(carbonfet_thumb_bl_place, -.3, 1, thumb_post_tr(), carbonfet_thumb_bl_place, 0, 1, thumb_post_tl())
    shape += wall_brace(carbonfet_thumb_br_place, -1, 0, web_post_tl(), carbonfet_thumb_br_place, -1, 0, web_post_bl())
    shape += wall_brace(carbonfet_thumb_bl_place, -1, 0, thumb_post_tl(), carbonfet_thumb_bl_place, -1, 0, web_post_bl())
    # thumb, corners
    shape += wall_brace(carbonfet_thumb_br_place, -1, 0, web_post_bl(), carbonfet_thumb_br_place, 0, -1, web_post_bl())
    shape += wall_brace(carbonfet_thumb_bl_place, -1, 0, thumb_post_tl(), carbonfet_thumb_bl_place, 0, 1, thumb_post_tl())
    # thumb, tweeners
    shape += wall_brace(carbonfet_thumb_mr_place, 0, -1.15, web_post_bl(), carbonfet_thumb_br_place, 0, -1, web_post_br())
    # shape += wall_brace(thumb_ml_place, 0, 1, web_post_tl(), carbonfet_thumb_bl_place, 0, 1, web_post_tr())
    shape += wall_brace(carbonfet_thumb_bl_place, -1, 0, web_post_bl(), carbonfet_thumb_br_place, -1, 0, web_post_tl())
    shape += wall_brace(carbonfet_thumb_tr_place, 0, -1, web_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())
    return shape

def carbonfet_thumb_connection():
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = bottom_hull(
        [
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            carbonfet_thumb_bl_place(sl.translate(wall_locate2(-0.3, 1))(thumb_post_tr())),
            carbonfet_thumb_bl_place(sl.translate(wall_locate3(-0.3, 1))(thumb_post_tr())),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            carbonfet_thumb_bl_place(sl.translate(wall_locate2(-0.3, 1))(thumb_post_tr())),
            carbonfet_thumb_bl_place(sl.translate(wall_locate3(-0.3, 1))(thumb_post_tr())),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(web_post(), cornerrow, -1),
            left_key_place(sl.translate(wall_locate1(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate2(-1, 0))(web_post()), cornerrow, -1),
            left_key_place(sl.translate(wall_locate3(-1, 0))(web_post()), cornerrow, -1),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            left_key_place(web_post(), cornerrow, -1),
            left_key_place(sl.translate(wall_locate1(-1, 0))(web_post()), cornerrow, -1),
            key_place(web_post_bl(), 0, cornerrow),
            # key_place(sl.translate(wall_locate1(-1, 0))(web_post_bl()), 0, cornerrow),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )

    shape += sl.hull()(
        [
            carbonfet_thumb_bl_place(thumb_post_tr()),
            carbonfet_thumb_bl_place(sl.translate(wall_locate1(-0.3, 1))(thumb_post_tr())),
            carbonfet_thumb_bl_place(sl.translate(wall_locate2(-0.3, 1))(thumb_post_tr())),
            carbonfet_thumb_bl_place(sl.translate(wall_locate3(-0.3, 1))(thumb_post_tr())),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )

    return shape



def case_walls():
    return (
            back_wall()
            + left_wall()
            + right_wall()
            + front_wall()
            + thumb_walls()
            + thumb_connection()
    )


rj9_start = list(
    np.array([0, -3, 0])
    + np.array(
        key_position(
            list(np.array(wall_locate3(0, 1)) + np.array([0, (mount_height / 2), 0])),
            0,
            0,
        )
    )
)

rj9_position = [rj9_start[0], rj9_start[1], 11]


def rj9_cube():
    return sl.cube([14.78, 13, 22.38], center=True)


def rj9_space():
    return sl.translate(rj9_position)(rj9_cube())


def rj9_holder():
    shape = sl.union()(
        sl.translate([0, 2, 0])(sl.cube([10.78, 9, 18.38], center=True)),
        sl.translate([0, 0, 5])(sl.cube([10.78, 13, 5], center=True)),
    )
    shape = sl.difference()(rj9_cube(), shape)
    shape = sl.translate(rj9_position)(shape)
    return shape


usb_holder_position = key_position(
    list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2), 0])), 1, 0
)
usb_holder_size = [6.5, 10.0, 13.6]
usb_holder_thickness = 4


def usb_holder():
    shape = sl.cube(
        [
            usb_holder_size[0] + usb_holder_thickness,
            usb_holder_size[1],
            usb_holder_size[2] + usb_holder_thickness,
        ],
        center=True,
    )
    shape = sl.translate(
        [
            usb_holder_position[0],
            usb_holder_position[1],
            (usb_holder_size[2] + usb_holder_thickness) / 2,
        ]
    )(shape)
    return shape


def usb_holder_hole():
    shape = sl.cube(usb_holder_size, center=True)
    shape = sl.translate(
        [
            usb_holder_position[0],
            usb_holder_position[1],
            (usb_holder_size[2] + usb_holder_thickness) / 2,
        ]
    )(shape)
    return shape


external_start = list(
    np.array([external_holder_width / 2, 0, 0])
    + np.array(
        key_position(
            list(np.array(wall_locate3(0, 1)) + np.array([0, (mount_height / 2), 0])),
            0,
            0,
        )
    )
)


def external_mount_hole():
    print('external_mount_hole()')
    shape = sl.cube((external_holder_width, 20.0, external_holder_height), center=True)
    shape = sl.translate(
        (
            external_start[0] + external_holder_xoffset,
            external_start[1],
            external_holder_height / 2
        )
    )(shape)
    return shape


def oled_sliding_mount_frame():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_edge_overlap_end
            + oled_edge_overlap_connector + oled_edge_overlap_clearance
            + 2 * oled_mount_rim
    )
    mount_ext_up_height = oled_mount_height + 2 * oled_mount_rim
    top_hole_start = -mount_ext_height / 2.0 + oled_mount_rim + oled_edge_overlap_end + oled_edge_overlap_connector
    top_hole_length = oled_mount_height
    hole = sl.cube([mount_ext_width, mount_ext_up_height, oled_mount_cut_depth + .01], center=True)
    hole = sl.translate([0., top_hole_start + top_hole_length / 2, 0.])(hole)
    hole_down = sl.cube([mount_ext_width, mount_ext_height, oled_mount_depth + oled_mount_cut_depth / 2],
                        center=True)
    hole_down = sl.translate([0., 0., -oled_mount_cut_depth / 4])(hole_down)
    hole += hole_down

    shape = sl.cube([mount_ext_width, mount_ext_height, oled_mount_depth], center=True)

    conn_hole_start = -mount_ext_height / 2.0 + oled_mount_rim
    conn_hole_length = (
            oled_edge_overlap_end + oled_edge_overlap_connector
            + oled_edge_overlap_clearance + oled_thickness
    )
    conn_hole = sl.cube([oled_mount_width, conn_hole_length + .01, oled_mount_depth], center=True)
    conn_hole = sl.translate([
        0,
        conn_hole_start + conn_hole_length / 2,
        -oled_edge_overlap_thickness
    ])(conn_hole)

    end_hole_length = (
            oled_edge_overlap_end + oled_edge_overlap_clearance
    )
    end_hole_start = mount_ext_height / 2.0 - oled_mount_rim - end_hole_length
    end_hole = sl.cube([oled_mount_width, end_hole_length + .01, oled_mount_depth], center=True)
    end_hole = sl.translate([
        0,
        end_hole_start + end_hole_length / 2,
        -oled_edge_overlap_thickness
    ])(end_hole)

    top_hole_start = -mount_ext_height / 2.0 + oled_mount_rim + oled_edge_overlap_end + oled_edge_overlap_connector
    top_hole_length = oled_mount_height
    top_hole = sl.cube(
        [oled_mount_width, top_hole_length, oled_edge_overlap_thickness + oled_thickness - oled_edge_chamfer],
        center=True)
    top_hole = sl.translate([
        0,
        top_hole_start + top_hole_length / 2,
        (oled_mount_depth - oled_edge_overlap_thickness - oled_thickness - oled_edge_chamfer) / 2.0
    ])(top_hole)

    top_chamfer_1 = sl.cube([
        oled_mount_width,
        top_hole_length,
        0.01
    ], center=True)
    top_chamfer_2 = sl.cube([
        oled_mount_width + 2 * oled_edge_chamfer,
        top_hole_length + 2 * oled_edge_chamfer,
        0.01
    ], center=True)
    top_chamfer_1 = sl.translate([
        0,
        0,
        -oled_edge_chamfer - .05
    ])(top_chamfer_1)
    top_chamfer_1 = sl.hull()(top_chamfer_1, top_chamfer_2)

    top_chamfer_1 = sl.translate([
        0,
        top_hole_start + top_hole_length / 2,
        oled_mount_depth / 2.0 + .05
    ])(top_chamfer_1)
    top_hole += top_chamfer_1

    shape = sl.difference()(shape, conn_hole, top_hole, end_hole)

    shape = sl.rotate(oled_mount_rotation_xyz)(shape)
    shape = sl.translate(
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )(shape)

    hole = sl.rotate(oled_mount_rotation_xyz)(hole)
    hole = sl.translate(
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )(hole)
    return hole, shape


def oled_clip_mount_frame():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_clip_thickness
            + 2 * oled_clip_undercut + 2 * oled_clip_overhang + 2 * oled_mount_rim
    )
    hole = sl.cube([mount_ext_width, mount_ext_height, oled_mount_cut_depth + .01], center=True)

    shape = sl.cube([mount_ext_width, mount_ext_height, oled_mount_depth], center=True)
    shape -= sl.cube([oled_mount_width, oled_mount_height, oled_mount_depth + .1], center=True)

    clip_slot = sl.cube([
        oled_clip_width + 2 * oled_clip_width_clearance,
        oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang,
        oled_mount_depth + .1], center=True)

    shape -= clip_slot

    clip_undercut = sl.cube([
        oled_clip_width + 2 * oled_clip_width_clearance,
        oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang + 2 * oled_clip_undercut,
        oled_mount_depth + .1], center=True)

    clip_undercut = sl.translate((0., 0., oled_clip_undercut_thickness))(clip_undercut)
    shape -= clip_undercut

    plate = sl.cube([
        oled_mount_width + .1,
        oled_mount_height - 2 * oled_mount_connector_hole,
        oled_mount_depth - oled_thickness], center=True)
    plate = sl.translate((0., 0., -oled_thickness / 2.0))(plate)
    shape += plate

    shape = sl.rotate(oled_mount_rotation_xyz)(shape)
    shape = sl.translate(
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )(shape)

    hole = sl.rotate(oled_mount_rotation_xyz)(hole)
    hole = sl.translate(
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )(hole)

    return hole, shape


def oled_clip():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang
            + 2 * oled_clip_undercut + 2 * oled_mount_rim
    )

    oled_leg_depth = oled_mount_depth + oled_clip_z_gap

    shape = sl.cube([mount_ext_width - .1, mount_ext_height - .1, oled_mount_bezel_thickness], center=True)
    shape = sl.translate((0., 0., oled_mount_bezel_thickness / 2.))(shape)

    hole_1 = sl.cube([
        oled_screen_width + 2 * oled_mount_bezel_chamfer,
        oled_screen_length + 2 * oled_mount_bezel_chamfer,
        .01
    ], center=True)
    hole_2 = sl.cube([oled_screen_width, oled_screen_length, 2.05 * oled_mount_bezel_thickness], center=True)
    hole = sl.hull()(hole_1, hole_2)

    shape -= sl.translate((0., 0., oled_mount_bezel_thickness))(hole)

    clip_leg = sl.cube([oled_clip_width, oled_clip_thickness, oled_leg_depth], center=True)
    clip_leg = sl.translate((
        0.,
        0.,
        # (oled_mount_height+2*oled_clip_overhang+oled_clip_thickness)/2,
        -oled_leg_depth / 2.
    ))(clip_leg)

    latch_1 = sl.cube([
        oled_clip_width,
        oled_clip_overhang + oled_clip_thickness,
        .01
    ], center=True)
    latch_2 = sl.cube([
        oled_clip_width,
        oled_clip_thickness / 2,
        oled_clip_extension
    ], center=True)
    latch_2 = sl.translate((
        0.,
        -(-oled_clip_thickness / 2 + oled_clip_thickness + oled_clip_overhang) / 2,
        -oled_clip_extension / 2
    ))(latch_2)
    latch = sl.hull()(latch_1, latch_2)
    latch = sl.translate((
        0.,
        oled_clip_overhang / 2,
        -oled_leg_depth
    ))(latch)

    clip_leg += latch

    clip_leg = sl.translate((
        0.,
        (oled_mount_height + 2 * oled_clip_overhang + oled_clip_thickness) / 2 - oled_clip_y_gap,
        0.
    ))(clip_leg)

    shape += clip_leg
    shape += sl.mirror((0., 1., 0.))(clip_leg)

    return shape


def oled_undercut_mount_frame():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = oled_mount_height + 2 * oled_mount_rim
    hole = sl.cube([mount_ext_width, mount_ext_height, oled_mount_cut_depth + .01], center=True)

    shape = sl.cube([mount_ext_width, mount_ext_height, oled_mount_depth], center=True)
    shape = sl.difference()(
        shape,
        sl.cube([oled_mount_width, oled_mount_height, oled_mount_depth + .1], center=True)
    )
    undercut = sl.cube([
        oled_mount_width + 2 * oled_mount_undercut,
        oled_mount_height + 2 * oled_mount_undercut,
        oled_mount_depth], center=True)
    undercut = sl.translate((0., 0., -oled_mount_undercut_thickness))(undercut)
    shape = sl.difference()(shape, undercut)

    shape = sl.rotate(oled_mount_rotation_xyz)(shape)
    shape = sl.translate(
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )(shape)

    hole = sl.rotate(oled_mount_rotation_xyz)(hole)
    hole = sl.translate(
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )(hole)

    return hole, shape


teensy_width = 20
teensy_height = 12
teensy_length = 33
teensy2_length = 53
teensy_pcb_thickness = 2
teensy_holder_width = 7 + teensy_pcb_thickness
teensy_holder_height = 6 + teensy_width
teensy_offset_height = 5
teensy_holder_top_length = 18
teensy_top_xy = key_position(wall_locate3(-1, 0), 0, centerrow - 1)
teensy_bot_xy = key_position(wall_locate3(-1, 0), 0, centerrow + 1)
teensy_holder_length = teensy_top_xy[1] - teensy_bot_xy[1]
teensy_holder_offset = -teensy_holder_length / 2
teensy_holder_top_offset = (teensy_holder_top_length / 2) - teensy_holder_length


def teensy_holder():
    s1 = sl.cube([3, teensy_holder_length, 6 + teensy_width], center=True)
    s1 = sl.translate([1.5, teensy_holder_offset, 0])(s1)

    s2 = sl.cube([teensy_pcb_thickness, teensy_holder_length, 3], center=True)
    s2 = sl.translate(
        [
            (teensy_pcb_thickness / 2) + 3,
            teensy_holder_offset,
            -1.5 - (teensy_width / 2),
        ]
    )(s2)

    s3 = sl.cube([teensy_pcb_thickness, teensy_holder_top_length, 3], center=True)
    s3 = sl.translate(
        [
            (teensy_pcb_thickness / 2) + 3,
            teensy_holder_top_offset,
            1.5 + (teensy_width / 2),
        ]
    )(s3)

    s4 = sl.cube([4, teensy_holder_top_length, 4], center=True)
    s4 = sl.translate(
        [teensy_pcb_thickness + 5, teensy_holder_top_offset, 1 + (teensy_width / 2)]
    )(s4)

    shape = sl.union()(s1, s2, s3, s4)

    shape = sl.translate([-teensy_holder_width, 0, 0])(shape)
    shape = sl.translate([-1.4, 0, 0])(shape)
    shape = sl.translate(
        [teensy_top_xy[0], teensy_top_xy[1] - 1, (6 + teensy_width) / 2]
    )(shape)

    return shape


def screw_insert_shape(bottom_radius, top_radius, height):
    shape = sl.union()(
        sl.cylinder(r1=bottom_radius, r2=top_radius, h=height, center=True),
        sl.translate([0, 0, (height / 2)])(sl.sphere(top_radius)),
    )
    return shape


def screw_insert(column, row, bottom_radius, top_radius, height):
    shift_right = column == lastcol
    shift_left = column == 0
    shift_up = (not (shift_right or shift_left)) and (row == 0)
    shift_down = (not (shift_right or shift_left)) and (row >= lastrow)

    if screws_offset == 'INSIDE':
        # print('Shift Inside')
        shift_left_adjust = wall_base_x_thickness
        shift_right_adjust = -wall_base_x_thickness/2
        shift_down_adjust = -wall_base_y_thickness/2
        shift_up_adjust = -wall_base_y_thickness/3

    elif screws_offset == 'OUTSIDE':
        print('Shift Outside')
        shift_left_adjust = 0
        shift_right_adjust = wall_base_x_thickness/2
        shift_down_adjust = wall_base_y_thickness*2/3
        shift_up_adjust = wall_base_y_thickness*2/3

    else:
        # print('Shift Origin')
        shift_left_adjust = 0
        shift_right_adjust = 0
        shift_down_adjust = 0
        shift_up_adjust = 0

    if shift_up:
        position = key_position(
            list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2) + shift_up_adjust, 0])),
            column,
            row,
        )
    elif shift_down:
        position = key_position(
            list(np.array(wall_locate2(0, -1)) - np.array([0, (mount_height / 2) + shift_down_adjust, 0])),
            column,
            row,
        )
    elif shift_left:
        position = list(
            np.array(left_key_position(row, 0)) + np.array(wall_locate3(-1, 0)) + np.array((shift_left_adjust,0,0))
        )
    else:
        position = key_position(
            list(np.array(wall_locate2(1, 0)) + np.array([(mount_height / 2), 0, 0]) + np.array((shift_right_adjust,0,0))
                 ),
            column,
            row,
        )

    # add z height below 0 due to 0 thickness skin covering the hole.
    shape = screw_insert_shape(bottom_radius, top_radius, height + 5)
    shape = sl.translate((position[0], position[1], height / 2 - 2.5))(shape)

    return shape


def screw_insert_all_shapes(bottom_radius, top_radius, height):
    shape = sl.union()(
        screw_insert(0, 0, bottom_radius, top_radius, height),
        # screw_insert(0, lastrow, bottom_radius, top_radius, height),
        screw_insert(0, lastrow - 1, bottom_radius, top_radius, height),
        screw_insert(3, lastrow, bottom_radius, top_radius, height),
        screw_insert(3, 0, bottom_radius, top_radius, height),
        screw_insert(lastcol, 0, bottom_radius, top_radius, height),
        screw_insert(lastcol, lastrow - 1, bottom_radius, top_radius, height),
    )

    return shape


screw_insert_height = 3.8
screw_insert_bottom_radius = 5.31 / 2
screw_insert_top_radius = 5.1 / 2
screw_insert_holes = screw_insert_all_shapes(
    screw_insert_bottom_radius, screw_insert_top_radius, screw_insert_height
)
screw_insert_outers = screw_insert_all_shapes(
    screw_insert_bottom_radius + 1.6,
    screw_insert_top_radius + 1.6,
    screw_insert_height + 1.5,
)
screw_insert_screw_holes = screw_insert_all_shapes(1.7, 1.7, 350)

wire_post_height = 7
wire_post_overhang = 3.5
wire_post_diameter = 2.6


def wire_post(direction, offset):
    s1 = sl.cube(
        [wire_post_diameter, wire_post_diameter, wire_post_height], center=True
    )
    s1 = sl.translate([0, -wire_post_diameter * 0.5 * direction, 0])(s1)

    s2 = sl.cube(
        [wire_post_diameter, wire_post_overhang, wire_post_diameter], center=True
    )
    s2 = sl.translate(
        [0, -wire_post_overhang * 0.5 * direction, -wire_post_height / 2]
    )(s2)

    shape = sl.union()(s1, s2)
    shape = sl.translate([0, -offset, (-wire_post_height / 2) + 3])(shape)
    shape = sl.rotate(-alpha / 2, [1, 0, 0])(shape)
    shape = sl.translate([3, -mount_height / 2, 0])(shape)

    return shape


def wire_posts():
    shape = thumb_ml_place(sl.translate([-5, 0, -2])(wire_post(1, 0)))
    shape += thumb_ml_place(sl.translate([0, 0, -2.5])(wire_post(-1, 6)))
    shape += thumb_ml_place(sl.translate([5, 0, -2])(wire_post(1, 0)))

    for column in range(lastcol):
        for row in range(lastrow - 1):
            shape += sl.union()(
                key_place(sl.translate([-5, 0, 0])(wire_post(1, 0)), column, row),
                key_place(sl.translate([0, 0, 0])(wire_post(-1, 6)), column, row),
                key_place(sl.translate([5, 0, 0])(wire_post(1, 0)), column, row),
            )
    return shape


def model_side(side="right"):
    shape = sl.union()(key_holes(side=side), connectors(), thumb(side=side), thumb_connectors(), )
    pre_sub = []
    adders = []
    post_sub = [screw_insert_holes()]

    if controller_mount_type in ['RJ9_USB_TEENSY']:
        adders.append(teensy_holder())

    if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
        adders.append(usb_holder())
        post_sub.append(usb_holder_hole())

    if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
        pre_sub.append(rj9_space())
        adders.append(rj9_holder())

    if controller_mount_type in ['EXTERNAL']:
        post_sub.append(external_mount_hole())

    s2 = sl.union()(case_walls(), screw_insert_outers())
    s2 = sl.difference()(s2, *pre_sub)
    s2 = sl.union()(s2, *adders)
    shape = sl.union()(shape, s2)

    shape -= sl.translate([0, 0, -20])(sl.cube([350, 350, 40], center=True))

    shape = sl.difference()(shape, *post_sub)

    if oled_mount_type == "UNDERCUT":
        hole, frame = oled_undercut_mount_frame()
        shape -= hole
        shape += frame

    elif oled_mount_type == "SLIDING":
        hole, frame = oled_sliding_mount_frame()
        shape -= hole
        shape += frame

    elif oled_mount_type == "CLIP":
        hole, frame = oled_clip_mount_frame()
        shape -= hole
        shape += frame

    if side == "left":
        shape = sl.mirror([-1, 0, 0])(shape)

    return shape


mod_r = model_side(side="right")

sl.scad_render_to_file(mod_r, path.join(r"..", "things", save_dir, config_name + r"_right.scad"))

if symmetry == "asymmetric":
    mod_l = model_side(side="left")
    sl.scad_render_to_file(
        mod_l, path.join(r"..", "things", save_dir, config_name + r"_left.scad")
    )
else:
    sl.scad_render_to_file(
        sl.mirror([-1, 0, 0])(mod_r), path.join(r"..", "things", save_dir, config_name + r"_left.scad")
    )


def baseplate():
    shape = sl.union()(
        case_walls(),
        screw_insert_outers(),
    )

    tool = sl.translate([0, 0, -10])(screw_insert_screw_holes())

    shape = shape - tool

    shape = sl.translate([0, 0, -0.01])(shape)

    return sl.projection(cut=True)(shape)


sl.scad_render_to_file(baseplate(), path.join(r"..", "things", save_dir, config_name + r"_plate.scad"))

if oled_mount_type == 'UNDERCUT':
    sl.scad_render_to_file(oled_undercut_mount_frame()[1], path.join(r"..", "things", save_dir, config_name + r"_oled_undercut_test.scad"))

if oled_mount_type == 'SLIDING':
    sl.scad_render_to_file(oled_sliding_mount_frame()[1], path.join(r"..", "things", save_dir, config_name + r"_oled_sliding_test.scad"))

if oled_mount_type == 'CLIP':
    oled_mount_location_xyz = (0.0, 0.0, -oled_mount_depth / 2)
    oled_mount_rotation_xyz = (0.0, 0.0, 0.0)
    sl.scad_render_to_file(oled_clip(), path.join(r"..", "things", save_dir, config_name + r"_oled_clip.scad"))
    sl.scad_render_to_file(oled_clip_mount_frame()[1], path.join(r"..", "things", save_dir, config_name + r"_oled_clip_test.scad"))
    sl.scad_render_to_file(oled_clip_mount_frame()[1] + oled_clip(),
                           path.join(r"..", "things", save_dir, config_name + r"_oled_clip_assy_test.scad"))
