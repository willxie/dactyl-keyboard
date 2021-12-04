from helpers import helpers_abc
import os.path as path
import numpy as np
from dataclasses_json import dataclass_json
from dataclasses import dataclass

from typing import Any, Sequence, Tuple


@dataclass_json
@dataclass
class TrackballParameters:
    package: str = 'shapes.trackball'
    class_name: str = 'Trackball'

    ###################################
    ## Trackball General             ##
    ###################################
    trackball_modular: bool = False  # Added, creates a hole with space for the lip size listed below.
    trackball_modular_lip_width: float = 3.0  # width of lip cleared out in ring location
    trackball_modular_ball_height: float = 3.0  # height of ball from ring , used to create identical position to fixed.
    trackball_modular_ring_height: float = 10.0  # height mount ring down from ball height. Covers gaps on elevated ball.
    trackball_modular_clearance: float = 0.5  # height of ball from ring, used to create identical position to fixed.

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



class Trackball:
    g: helpers_abc

    def __init__(self, parent, t_parameters):
        self._parent = parent
        self.p = parent.p
        self.g = parent.g

    def trackball_cutout(self, segments=100):
        if self.p.trackball_modular:
            hole_diameter = self.p.ball_diameter + 2 * (
                    self.p.ball_gap + self.p.ball_wall_thickness + self.p.trackball_modular_clearance + self.p.trackball_modular_lip_width) - .1
            shape = self.g.cylinder(self.p.hole_diameter / 2, self.p.trackball_hole_height)
        else:
            shape = self.g.cylinder(self.p.trackball_hole_diameter / 2, self.p.trackball_hole_height)
        return shape

    def trackball_socket(self, segments=100):
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

    def trackball_ball(self, segments=100):
        shape = self.g.sphere(self.p.ball_diameter / 2)
        return shape

    def get_ball(self, with_space=False):
        diam = self.p.ball_diam
        if with_space:
            diam += self.p.ball_space
        return self.g.sphere(diam / 2)

    def gen_holder(self):
        # PMW3360 dimensions
        # 28mm x 21mm
        l = 28  # not used for now, fudged with base_shape build
        w = 22
        h = 5.9

        # 24mm between screw centers
        screw_dist = 24
        # Screw holes 2.44mm, 2.2mm for snug tapped fit
        screw_hole_d = 2.2

        # circles at either side
        cyl1 = self.g.translate(self.g.cylinder(w / 2, h, 100), (0, 5, 0))
        cyl2 = self.g.translate(self.g.cylinder(w / 2, h, 100), (0, -5, 0))

        # tape those bits together
        base_shape = self.g.hull_from_shapes([cyl1, cyl2])

        # Ball with 2mm space extra diameter for socket
        ball = self.g.translate(self.get_ball(True), (0, 0, 15))

        # Screw holes with a bit of extra height to subtract cleanly
        # May need to be offset by one, as per the bottom hole...?
        screw1 = self.g.translate(self.g.cylinder(screw_hole_d / 2, h + 1, 20), (0, screw_dist / 2, 0))
        screw2 = self.g.translate(self.g.cylinder(screw_hole_d / 2, h + 1, 20), (0, -(screw_dist / 2), 0))

        # Attempt at bottom hole, numbers mostly fudged but seems in ballpark
        bottom_hole = self.g.union([self.g.translate(self.g.box(4.5, 4, 6), (0, -2, 0)), self.g.translate(self.g.cylinder(2.25, 6, 40), (0, 0, 0))])

        final = self.g.difference(base_shape, [ball, screw1, screw2, bottom_hole])

        return final



    def generate_trackball_components(self, pos, rot):
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


    def coords(self, angle, dist):
        x = np.sin(angle) * dist
        y = np.cos(angle) * dist
        return x, y


    def gen_socket_shape(self, radius, wall):
        diam = radius * 2
        ball = self.g.sphere(radius)
        socket_base = self.g.difference(ball, [self.g.translate(self.g.box(diam + 1, diam + 1, diam), (0, 0, diam / 2))])
        top_cylinder = self.g.translate(self.g.difference(self.g.cylinder(radius, 4), [self.g.cylinder(radius - wall, 6)]), (0, 0, 2))
        socket_base = self.g.union([socket_base, top_cylinder])

        return socket_base


    def socket_bearing_fin(self, outer_r, outer_depth, axle_r, axle_depth, cut_offset, groove):
        pi3 = (np.pi / 2)
        l = 20

        x, y = self.coords(0, l)
        t1 = self.g.translate(self.g.cylinder(outer_r, outer_depth), (x, y, 0))

        x, y = self.coords(pi3, l)
        t2 = self.g.translate(self.g.cylinder(outer_r, outer_depth), (x, y, 0))

        x, y = self.coords(pi3 * 2, l)
        t3 = self.g.translate(self.g.cylinder(outer_r, outer_depth), (x, y, 0))

        big_triangle = self.g.hull_from_shapes([t1, t2, t3])

        x, y = self.coords(0, l)
        t4 = self.g.translate(self.g.cylinder(axle_r, axle_depth), (x, y, 0))

        x, y = self.coords(pi3, l)
        t5 = self.g.translate(self.g.cylinder(axle_r, axle_depth), (x, y, 0))

        x, y = self.coords(pi3 * 2, l)
        t6 = self.g.translate(self.g.cylinder(axle_r, axle_depth), (x, y, 0))

        if groove:
            t6 = t4

        axle_shaft = self.g.hull_from_shapes([t4, t5, t6])
        base_shape = self.g.union([big_triangle, axle_shaft])
        cutter = self.g.rotate(self.g.translate(self.g.box(80, 80, 20), (0, cut_offset, 0)), (0, 0, 15))

        return self.g.rotate(self.g.difference(base_shape, [cutter]), (0, -90, 0))


    def track_outer(self):
        wall = 4
        ball = self.gen_socket_shape((self.p.ball_diam + wall) / 2, wall / 2)
        outer_radius = 4
        outer_width = 5
        axle_radius = 3
        axle_width = 8
        base_fin = self.socket_bearing_fin(outer_radius, outer_width, axle_radius, axle_width, -22, False)
        offsets = (0, -2, -6)

        cutter1 = self.g.translate(base_fin, offsets)
        cutter2 = self.g.rotate(self.g.translate(base_fin, offsets), (0, 0, 120))
        cutter3 = self.g.rotate(self.g.translate(base_fin, offsets), (0, 0, 240))

        return self.g.union([ball, cutter1, cutter2, cutter3])


    def track_cutter(self):
        wall = 4
        ball = self.gen_socket_shape(self.p.ball_diam / 2, wall / 2)
        outer_radius = 2.5
        outer_width = 3
        axle_radius = 1.5
        axle_width = 6.5
        base_fin = self.socket_bearing_fin(outer_radius, outer_width, axle_radius, axle_width, -25, True)
        offsets = (0, -2, -6)

        cutter1 = self.g.translate(base_fin, offsets)
        cutter2 = self.g.rotate(self.g.translate(base_fin, offsets), (0, 0, 120))
        cutter3 = self.g.rotate(self.g.translate(base_fin, offsets), (0, 0, 240))

        return self.g.union([ball, cutter1, cutter2, cutter3])


    def gen_track_socket(self):
        return self.g.difference(self.track_outer(), [self.track_cutter()])

    def test_socket(self):
        self.g.export_file(shape=self.gen_track_socket(), fname=path.join("..", "things", "play"))

    def generate_trackball(self, shape):
        tbprecut, tb, tbcutout, sensor, ball = self.generate_trackball_components()
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

        return shape



    # cutter_fin = socket_bearing_fin(7, 3, 2, 7, -35)
    # main_fin = socket_bearing_fin(10, 7, 5, 10, -25)

    # result = self.g.difference(main_fin, [cutter_fin])



