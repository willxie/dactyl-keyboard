from helpers import helpers_abc
import os.path as path
import numpy as np

class TrackballShapes:
    g: helpers_abc

    def __init__(self, parent):
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


    # cutter_fin = socket_bearing_fin(7, 3, 2, 7, -35)
    # main_fin = socket_bearing_fin(10, 7, 5, 10, -25)

    # result = self.g.difference(main_fin, [cutter_fin])



