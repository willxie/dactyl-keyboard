import json
import os
import numpy as np

debugprint = print

class DefaultCluster(object):
    num_keys = 6
    is_tb = False
    thumb_offsets = [
        6,
        -3,
        7
    ]
    thumb_plate_tr_rotation = 0
    thumb_plate_tl_rotation = 0
    thumb_plate_mr_rotation = 0
    thumb_plate_ml_rotation = 0
    thumb_plate_br_rotation = 0
    thumb_plate_bl_rotation = 0

    def __init__(self, parent):
        self.g = parent.g
        self.p = parent.p
        self.parent = parent
        self.sh = parent.sh

    @staticmethod
    def name():
        return "DEFAULT"


    def get_config(self):
        with open(os.path.join(".", "clusters", "json", "DEFAULT.json"), mode='r') as fid:
            data = json.load(fid)
        for item in data:
            if not hasattr(self, str(item)):
                print(self.name() + ": NO MEMBER VARIABLE FOR " + str(item))
                continue
            setattr(self, str(item), data[item])
        return data

    # def __init__(self, parent_locals):
    #     for item in parent_locals:
    #         globals()[item] = parent_locals[item]
    #     self.get_config()
    #     print(self.name(), " built")

    def thumborigin(self):
        # debugprint('thumborigin()')
        origin = self.parent.key_position([self.p.mount_width / 2, -(self.p.mount_height / 2), 0], 1, self.p.cornerrow)

        for i in range(len(origin)):
            origin[i] = origin[i] + self.thumb_offsets[i]

        return origin

    def tl_place(self, shape):
        debugprint('tl_place()')
        shape = self.g.rotate(shape, [7.5, -18, 10])
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, [-32.5, -14.5, -2.5])
        return shape

    def tr_place(self, shape):
        debugprint('tr_place()')
        shape = self.g.rotate(shape, [10, -15, 10])
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, [-12, -16, 3])
        return shape

    def mr_place(self, shape):
        debugprint('mr_place()')
        shape = self.g.rotate(shape, [-6, -34, 48])
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, [-29, -40, -13])
        return shape

    def ml_place(self, shape):
        debugprint('ml_place()')
        shape = self.g.rotate(shape, [6, -34, 40])
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, [-51, -25, -12])
        return shape

    def br_place(self, shape):
        debugprint('br_place()')
        shape = self.g.rotate(shape, [-16, -33, 54])
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, [-37.8, -55.3, -25.3])
        return shape

    def bl_place(self, shape):
        debugprint('bl_place()')
        shape = self.g.rotate(shape, [-4, -35, 52])
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, [-56.3, -43.3, -23.5])
        return shape

    def thumb_1x_layout(self, shape, cap=False):
        debugprint('thumb_1x_layout()')
        if cap:
            shape_list = [
                self.mr_place(self.g.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
                self.ml_place(self.g.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
                self.br_place(self.g.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
                self.bl_place(self.g.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            ]

            if self.p.default_1U_cluster:
                shape_list.append(self.tr_place(
                    self.g.rotate(self.g.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation]))
                )
                shape_list.append(self.tr_place(
                    self.g.rotate(self.g.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation]))
                )
                shape_list.append(self.tl_place(
                    self.g.rotate(shape, [0, 0, self.thumb_plate_tl_rotation]))
                )
            shapes = self.g.add(shape_list)

        else:
            shape_list = [
                self.mr_place(self.g.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
                self.ml_place(self.g.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
                self.br_place(self.g.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
                self.bl_place(self.g.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            ]
            if self.p.default_1U_cluster:
                shape_list.append(self.tr_place(self.g.rotate(self.g.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
            shapes = self.g.union(shape_list)
        return shapes

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        debugprint('thumb_15x_layout()')
        if plate:
            if cap:
                shape = self.g.rotate(shape, (0, 0, 90))
                cap_list = [self.tl_place(self.g.rotate(shape, [0, 0, self.thumb_plate_tl_rotation]))]
                cap_list.append(self.tr_place(self.g.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])))
                return self.g.add(cap_list)
            else:
                shape_list = [self.tl_place(self.g.rotate(shape, [0, 0, self.thumb_plate_tl_rotation]))]
                if not self.p.default_1U_cluster:
                    shape_list.append(self.tr_place(self.g.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])))
                return self.g.union(shape_list)
        else:
            if cap:
                shape = self.g.rotate(shape, (0, 0, 90))
                shape_list = [self.tl_place(shape)]
                shape_list.append(self.tr_place(shape))

                return self.g.add(shape_list)
            else:
                shape_list = [
                    self.tl_place(shape),
                ]
                if not self.p.default_1U_cluster:
                    shape_list.append(self.tr_place(shape))

                return self.g.union(shape_list)

    def thumbcaps(self, side='right'):
        t1 = self.thumb_1x_layout(self.sh.sa_cap(1), cap=True)
        if not self.p.default_1U_cluster:
            t1.add(self.thumb_15x_layout(self.sh.sa_cap(1.5), cap=True))
        return t1

    def thumb(self, side="right"):
        print('thumb()')
        shape = self.thumb_1x_layout(self.g.rotate(self.sh.single_plate(side=side), (0, 0, -90)))
        shape = self.g.union([shape, self.thumb_15x_layout(self.g.rotate(self.sh.single_plate(side=side), (0, 0, -90)))])
        shape = self.g.union([shape, self.thumb_15x_layout(self.sh.double_plate(), plate=False)])

        return shape

    def thumb_post_tr(self):
        debugprint('thumb_post_tr()')
        return self.g.translate(self.sh.web_post(),
                         [(self.p.mount_width / 2) - self.p.post_adj, ((self.p.mount_height / 2) + self.p.double_plate_height) - self.p.post_adj, 0]
                         )

    def thumb_post_tl(self):
        debugprint('thumb_post_tl()')
        return self.g.translate(self.sh.web_post(),
                         [-(self.p.mount_width / 2) + self.p.post_adj, ((self.p.mount_height / 2) + self.p.double_plate_height) - self.p.post_adj, 0]
                         )

    def thumb_post_bl(self):
        debugprint('thumb_post_bl()')
        return self.g.translate(self.sh.web_post(),
                         [-(self.p.mount_width / 2) + self.p.post_adj, -((self.p.mount_height / 2) + self.p.double_plate_height) + self.p.post_adj, 0]
                         )

    def thumb_post_br(self):
        debugprint('thumb_post_br()')
        return self.g.translate(self.sh.web_post(),
                         [(self.p.mount_width / 2) - self.p.post_adj, -((self.p.mount_height / 2) + self.p.double_plate_height) + self.p.post_adj, 0]
                         )

    def thumb_connectors(self, side="right"):
        print('thumb_connectors()')
        hulls = []

        # Top two
        if self.p.default_1U_cluster:
            hulls.append(
                self.g.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tr()),
                        self.tl_place(self.thumb_post_br()),
                        self.tr_place(self.sh.web_post_tl()),
                        self.tr_place(self.sh.web_post_bl()),
                    ]
                )
            )
        else:
            hulls.append(
                self.g.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tr()),
                        self.tl_place(self.thumb_post_br()),
                        self.tr_place(self.thumb_post_tl()),
                        self.tr_place(self.thumb_post_bl()),
                    ]
                )
            )

        # bottom two on the right
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.br_place(self.sh.web_post_tr()),
                    self.br_place(self.sh.web_post_br()),
                    self.mr_place(self.sh.web_post_tl()),
                    self.mr_place(self.sh.web_post_bl()),
                ]
            )
        )

        # bottom two on the left
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.br_place(self.sh.web_post_tr()),
                    self.br_place(self.sh.web_post_br()),
                    self.mr_place(self.sh.web_post_tl()),
                    self.mr_place(self.sh.web_post_bl()),
                ]
            )
        )
        # centers of the bottom four
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.bl_place(self.sh.web_post_tr()),
                    self.bl_place(self.sh.web_post_br()),
                    self.ml_place(self.sh.web_post_tl()),
                    self.ml_place(self.sh.web_post_bl()),
                ]
            )
        )

        # top two to the middle two, starting on the left
        hulls.append(
            self.g.triangle_hulls(
                [
                    self.br_place(self.sh.web_post_tl()),
                    self.bl_place(self.sh.web_post_bl()),
                    self.br_place(self.sh.web_post_tr()),
                    self.bl_place(self.sh.web_post_br()),
                    self.mr_place(self.sh.web_post_tl()),
                    self.ml_place(self.sh.web_post_bl()),
                    self.mr_place(self.sh.web_post_tr()),
                    self.ml_place(self.sh.web_post_br()),
                ]
            )
        )

        if self.p.default_1U_cluster:
            hulls.append(
                self.g.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.ml_place(self.sh.web_post_tr()),
                        self.tl_place(self.thumb_post_bl()),
                        self.ml_place(self.sh.web_post_br()),
                        self.tl_place(self.thumb_post_br()),
                        self.mr_place(self.sh.web_post_tr()),
                        self.tr_place(self.sh.web_post_bl()),
                        self.mr_place(self.sh.web_post_br()),
                        self.tr_place(self.sh.web_post_br()),
                    ]
                )
            )
        else:
            # top two to the main keyboard, starting on the left
            hulls.append(
                self.g.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.ml_place(self.sh.web_post_tr()),
                        self.tl_place(self.thumb_post_bl()),
                        self.ml_place(self.sh.web_post_br()),
                        self.tl_place(self.thumb_post_br()),
                        self.mr_place(self.sh.web_post_tr()),
                        self.tr_place(self.thumb_post_bl()),
                        self.mr_place(self.sh.web_post_br()),
                        self.tr_place(self.thumb_post_br()),
                    ]
                )
            )

        if self.p.default_1U_cluster:
            hulls.append(
                self.g.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.parent.key_place(self.sh.web_post_bl(), 0, self.p.cornerrow),
                        self.tl_place(self.thumb_post_tr()),
                        self.parent.key_place(self.sh.web_post_br(), 0, self.p.cornerrow),
                        self.tr_place(self.sh.web_post_tl()),
                        self.parent.key_place(self.sh.web_post_bl(), 1, self.p.cornerrow),
                        self.tr_place(self.sh.web_post_tr()),
                        self.parent.key_place(self.sh.web_post_br(), 1, self.p.cornerrow),
                        self.parent.key_place(self.sh.web_post_bl(), 2, self.p.lastrow),
                        self.tr_place(self.sh.web_post_tr()),
                        self.parent.key_place(self.sh.web_post_bl(), 2, self.p.lastrow),
                        self.tr_place(self.sh.web_post_br()),
                        self.parent.key_place(self.sh.web_post_br(), 2, self.p.lastrow),
                        self.parent.key_place(self.sh.web_post_bl(), 3, self.p.lastrow),
                    ]
                )
            )
        else:
            hulls.append(
                self.g.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.parent.key_place(self.sh.web_post_bl(), 0, self.p.cornerrow),
                        self.tl_place(self.thumb_post_tr()),
                        self.parent.key_place(self.sh.web_post_br(), 0, self.p.cornerrow),
                        self.tr_place(self.thumb_post_tl()),
                        self.parent.key_place(self.sh.web_post_bl(), 1, self.p.cornerrow),
                        self.tr_place(self.thumb_post_tr()),
                        self.parent.key_place(self.sh.web_post_br(), 1, self.p.cornerrow),
                        self.parent.key_place(self.sh.web_post_tl(), 2, self.p.lastrow),
                        self.parent.key_place(self.sh.web_post_bl(), 2, self.p.lastrow),
                        self.tr_place(self.thumb_post_tr()),
                        self.parent.key_place(self.sh.web_post_bl(), 2, self.p.lastrow),
                        self.tr_place(self.thumb_post_br()),
                        self.parent.key_place(self.sh.web_post_br(), 2, self.p.lastrow),
                    ]
                )
            )

        # return add(hulls)
        return self.g.union(hulls)


    def walls(self, side="right", skeleton=False):
        print('thumb_walls()')
        # thumb, walls
        if self.p.default_1U_cluster:
            shape = self.g.union([self.parent.wall_brace(self.mr_place, 0, -1, self.sh.web_post_br(),
                                             self.tr_place, 0, -1, self.sh.web_post_br())])
        else:
            shape = self.g.union([self.parent.wall_brace(self.mr_place, 0, -1, self.sh.web_post_br(),
                                             self.tr_place, 0, -1, self.thumb_post_br())])
        shape = self.g.union([shape, self.parent.wall_brace(self.mr_place, 0, -1, self.sh.web_post_br(),
                                                self.mr_place, 0, -1, self.sh.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.br_place, 0, -1, self.sh.web_post_br(),
                                                self.br_place, 0, -1, self.sh.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, -0.3, 1, self.sh.web_post_tr(),
                                                self.ml_place, 0, 1, self.sh.web_post_tl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, 0, 1, self.sh.web_post_tr(),
                                                self.bl_place, 0, 1, self.sh.web_post_tl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.br_place, -1, 0, self.sh.web_post_tl(),
                                                self.br_place, -1, 0, self.sh.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, -1, 0, self.sh.web_post_tl(),
                                                self.bl_place, -1, 0, self.sh.web_post_bl())])
        # thumb, corners
        shape = self.g.union([shape, self.parent.wall_brace(self.br_place, -1, 0, self.sh.web_post_bl(),
                                                self.br_place, 0, -1, self.sh.web_post_bl())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, -1, 0, self.sh.web_post_tl(),
                                                self.bl_place, 0, 1, self.sh.web_post_tl())])
        # thumb, tweeners
        shape = self.g.union([shape, self.parent.wall_brace(self.mr_place, 0, -1, self.sh.web_post_bl(),
                                                self.br_place, 0, -1, self.sh.web_post_br())])
        shape = self.g.union([shape, self.parent.wall_brace(self.ml_place, 0, 1, self.sh.web_post_tl(),
                                                self.bl_place, 0, 1, self.sh.web_post_tr())])
        shape = self.g.union([shape, self.parent.wall_brace(self.bl_place, -1, 0, self.sh.web_post_bl(),
                                                self.br_place, -1, 0, self.sh.web_post_tl())])
        if self.p.default_1U_cluster:
            shape = self.g.union([shape,
                           self.parent.wall_brace(self.tr_place, 0, -1, self.sh.web_post_br(),
                                      (lambda sh: self.parent.key_place(sh, 3, self.p.lastrow)), 0,
                                      -1, self.sh.web_post_bl())])
        else:
            shape = self.g.union([shape, self.parent.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(),
                                             (lambda sh: self.parent.key_place(sh, 3, self.p.lastrow)), 0, -1, self.sh.web_post_bl())])

        return shape

    def connection(self, side='right', skeleton=False):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = None
        shape = self.g.union([shape, self.g.bottom_hull(
            [
                self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True, side=side),
                self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True, side=side),
                self.ml_place(self.g.translate(self.sh.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                self.ml_place(self.g.translate(self.sh.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.g.union([shape,
                       self.g.hull_from_shapes(
                           [
                               self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1,
                                              low_corner=True, side=side),
                               self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1,
                                              low_corner=True, side=side),
                               self.ml_place(self.g.translate(self.sh.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                               self.ml_place(self.g.translate(self.sh.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )
                       ])  # )

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True, side=side),
                self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate2(-1, 0)), self.p.cornerrow, -1, low_corner=True, side=side),
                self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate3(-1, 0)), self.p.cornerrow, -1, low_corner=True, side=side),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.parent.left_key_place(self.sh.web_post(), self.p.cornerrow, -1, low_corner=True, side=side),
                self.parent.left_key_place(self.g.translate(self.sh.web_post(), self.parent.wall_locate1(-1, 0)), self.p.cornerrow, -1, low_corner=True, side=side),
                self.parent.key_place(self.sh.web_post_bl(), 0, self.p.cornerrow),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.g.union([shape, self.g.hull_from_shapes(
            [
                self.ml_place(self.sh.web_post_tr()),
                self.ml_place(self.g.translate(self.sh.web_post_tr(), self.parent.wall_locate1(-0.3, 1))),
                self.ml_place(self.g.translate(self.sh.web_post_tr(), self.parent.wall_locate2(-0.3, 1))),
                self.ml_place(self.g.translate(self.sh.web_post_tr(), self.parent.wall_locate3(-0.3, 1))),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        return shape

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array([-21, -58, 0]))
        position[2] = 0

        return position

    def get_extras(self, shape, pos):
        return shape

    def thumb_pcb_plate_cutouts(self, side="right"):
        shape = self.thumb_1x_layout(self.sh.plate_pcb_cutout(side=side))
        shape = self.g.union([shape, self.thumb_15x_layout(self.sh.plate_pcb_cutout(side=side))])
        return shape