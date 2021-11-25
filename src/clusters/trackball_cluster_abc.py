import json
import os
import numpy as np
import clusters.cluster_abc as ca
from dataclasses import dataclass
from abc import ABC
from typing import Any, Sequence, Tuple

def debugprint(data):
    pass
    # print

@dataclass
class TrackballClusterParametersBase(ca.ClusterParametersBase):
    thumb_style: str = 'NONE'
    package: str = 'trackball_cluster_abc'
    class_name: str = 'TrackballClusterBase'

    track_rotation: Sequence[float] = (0, 0, 0)
    track_position: Sequence[float] = (-15, -60, -12)


class TrackballClusterBase(ca.ClusterBase):
    parameter_type = TrackballClusterParametersBase
    num_keys = 5
    is_tb = True

    def __init__(self, parent, t_parameters=None):
        self.g = parent.g
        self.p = parent.p
        self.parent = parent
        self.sh = parent.sh

        if t_parameters is None:
            t_parameters = self.parameter_type()

        self.tp = t_parameters

        self.set_overrides()


    def set_overrides(self):
        pass

    @staticmethod
    def name():
        return "TRACKBALL_ABC"

    def track_place(self, shape):
        shape = self.g.rotate(shape, self.tp.track_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.track_position)
        return shape

    def tl_place(self, shape):
        debugprint('tl_place()')
        shape = self.g.rotate(shape, self.tp.tl_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.tl_position)
        return shape

    def tr_place(self, shape):
        debugprint('tr_place()')
        shape = self.g.rotate(shape, self.tp.tr_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.tr_position)
        return shape

    def mr_place(self, shape):
        debugprint('mr_place()')
        shape = self.g.rotate(shape, self.tp.mr_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.mr_position)
        return shape

    def ml_place(self, shape):
        debugprint('ml_place()')
        shape = self.g.rotate(shape, self.tp.ml_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.ml_position)
        return shape

    def br_place(self, shape):
        debugprint('br_place()')
        shape = self.g.rotate(shape,  self.tp.br_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.br_position)
        return shape

    def bl_place(self, shape):
        debugprint('bl_place()')
        shape = self.g.rotate(shape, self.tp.bl_rotation)
        shape = self.g.translate(shape, self.thumborigin())
        shape = self.g.translate(shape, self.tp.bl_position)
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


    def thumb_1x_layout(self, shape, cap=False):
        return shape

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        return shape

    def thumbcaps(self, side='right'):
        return self.sh.sa_cap(1)

    def thumb(self, side="right"):
        return self.sh.single_plate(side=side)

    def thumb_connectors(self, side="right"):
        return self.sh.web_post_tl()


    def walls(self, side="right", skeleton=False):
        return self.sh.web_post_tl()

    def connection(self, side='right', skeleton=False):
        return self.sh.web_post_tl()


    def screw_positions(self):
        position = [self.thumborigin()]
        return position

    def get_extras(self, shape, pos):
        return shape

    def thumb_pcb_plate_cutouts(self, side="right"):
        return self.sh.plate_pcb_cutout(side=side)
