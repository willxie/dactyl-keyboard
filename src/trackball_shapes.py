from helpers_solid import *
import os.path as path

ball_diam = 34  # ball diameter
ball_space = 1  # additional room around ball in socket, 1mm


def get_ball(with_space: False):
    diam = ball_diam
    if with_space:
        diam += ball_space
    return sphere(diam / 2)


def gen_holder():
    # PMW3360 dimensions
    # 28mm x 21mm
    l = 28  # not used, fudged with base_shape build
    w = 22
    h = 5.9

    # 24mm between screw centers
    screw_dist = 24
    # Screw holes 2.44mm, 2.2mm for snug tapped fit
    screw_hole_d = 2.2

    # middle box
    shape = box(w, 10, h)
    # circles at either side
    cyl1 = translate(cylinder(w / 2, h, 100), (0, 5, 0))
    cyl2 = translate(cylinder(w / 2, h, 100), (0, -5, 0))

    # tape those bits together
    base_shape = union([cyl1, cyl2, shape])

    # Ball with 2mm space extra diameter for socket
    ball = translate(get_ball(True), (0, 0, 15))

    # Screw holes with a bit of extra height to subtract cleanly
    # May need to be offset by one, as per the bottom hole...?
    screw1 = translate(cylinder(screw_hole_d / 2, h + 1, 20), (0, screw_dist / 2, 0))
    screw2 = translate(cylinder(screw_hole_d / 2, h + 1, 20), (0, -(screw_dist / 2), 0))

    # Attempt at bottom hole, numbers mostly fudged but seems in ballpark
    bottom_hole = union([translate(box(4.5, 4, 6), (0, -2, 0)), translate(cylinder(2.25, 6, 40), (0, 0, 0))])

    final = difference(base_shape, [ball, screw1, screw2, bottom_hole])

    return final


export_file(shape=gen_holder(), fname=path.join(".", "parts", "generated_sensor_holder"))

