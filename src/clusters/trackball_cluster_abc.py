import clusters.cluster_abc as ca
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Any, Sequence, Tuple



def debugprint(data):
    pass
    # print

@dataclass_json
@dataclass
class TrackballClusterParametersBase(ca.ClusterParametersBase):
    name: str = 'NONE'
    package: str = 'clusters.trackball_cluster_abc'
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

    def thumb_post_tr(self):
        debugprint('thumb_post_tr()')
        return self.g.translate(self.sh.web_post(),
                         [(self.p.mount_width / 2) - self.p.post_adj, ((self.p.mount_height / 2) + self.sh.pp.double_plate_height) - self.p.post_adj, 0]
                         )

    def thumb_post_tl(self):
        debugprint('thumb_post_tl()')
        return self.g.translate(self.sh.web_post(),
                         [-(self.p.mount_width / 2) + self.p.post_adj, ((self.p.mount_height / 2) + self.sh.pp.double_plate_height) - self.p.post_adj, 0]
                         )

    def thumb_post_bl(self):
        debugprint('thumb_post_bl()')
        return self.g.translate(self.sh.web_post(),
                         [-(self.p.mount_width / 2) + self.p.post_adj, -((self.p.mount_height / 2) + self.sh.pp.double_plate_height) + self.p.post_adj, 0]
                         )

    def thumb_post_br(self):
        debugprint('thumb_post_br()')
        return self.g.translate(self.sh.web_post(),
                         [(self.p.mount_width / 2) - self.p.post_adj, -((self.p.mount_height / 2) + self.sh.pp.double_plate_height) + self.p.post_adj, 0]
                         )