import os.path as path
import re
import shutil
import copy

fname = "carbonfet.py"
fname = "mini.py"
fname = "default.py"
fname = "minidox.py"
# fname = "trackball_cj.py"
# fname = "trackball_orbyl.py"
# fname = "trackball_wilder.py"

fdir = r"."
fpath = path.join(fdir, fname)

with open(fpath, mode='r') as fid:
    fstr = fid.read()

# t_fname = "backup_" + fname
# t_fpath = path.join(fdir, t_fname)
#
# shutil.copyfile(fpath, t_fpath)

f_geom = [
    'box',
    'cylinder',
    'sphere',
    'cone',
    'rotate',
    'translate',
    'mirror',
    'union',
    'add',
    'difference',
    'intersect',
    'face_from_points',
    'hull_from_points',
    'hull_from_shapes',
    'tess_hull',
    'triangle_hulls',
    'bottom_hull',
    'polyline',
    'extrude_poly',
    'import_file',
    'export_stl',
    'export_file',
    'export_dxf',
]
f_param = [
    'mount_width',
    'mount_height',
    'post_adj',
    'double_plate_height',
    'cornerrow',
    'lastrow',
]
f_parent = [
    'key_place',
    'wall_brace',
    'wall_locate1',
    'wall_locate2',
    'wall_locate3',
    'left_key_place',
]
f_tparam = [
    'thumb_plate_tr_rotation',
    'thumb_plate_tl_rotation',
    'thumb_plate_mr_rotation',
    'thumb_plate_ml_rotation',
    'thumb_plate_br_rotation',
    'thumb_plate_bl_rotation',
    'thumb_offsets',
    'tl_rotation',
    'tl_position',
    'tr_rotation',
    'tr_position',
    'ml_rotation',
    'ml_position',
    'mr_rotation',
    'mr_position',
    'bl_rotation',
    'bl_position',
    'br_rotation',
    'br_position',
    'minidox_Usize',
]

f_shape = [
    'double_plate_half',
    'single_plate',
    'sa_cap',
    'double_plate',
    'web_post_tl',
    'web_post_tr',
    'web_post_bl',
    'web_post_br',
    'plate_pcb_cutout',
    'web_post',
    'adjustable_plate',
    'adjustable_plate_size',
]

func_find_re = r"([\s\)\(\[]){}\("

geom_find_re = r"([\s\)\(]){}\("
geom_repl = r"\1self.g.{}("

prnt_find_re = r"([\s\)\(]){}\("
prnt_repl = r"\1self.parent.{}("

shape_find_re = r"([\s\)\(]+){}\("
shape_repl = r"\1self.sh.{}("


param_find_re = r"([^\.]){}"
param_repl = r"\1self.p.{}"

tparam_find_re = r"([^\._]){}(^:)"
tparam_repl = r"\1self.tp.{}\2"

tparam2_find_re = r"self.{}"
tparam2_repl = r"self.tp.{}"


replacements = [
    {'name': 'geom', 'items': f_geom, 'find': func_find_re, 'repl': geom_repl},
    {'name': 'shape', 'items': f_shape, 'find': func_find_re, 'repl': shape_repl},
    {'name': 'parent', 'items': f_parent, 'find': func_find_re, 'repl': prnt_repl},
    {'name': 'params', 'items': f_param, 'find': param_find_re, 'repl': param_repl},
    {'name': 'tparams', 'items': f_tparam, 'find': tparam_find_re, 'repl': tparam_repl},
    {'name': 'tparams', 'items': f_tparam, 'find': tparam2_find_re, 'repl': tparam2_repl},
]


new_str = copy.deepcopy(fstr)
for repls in replacements:
    for item in repls['items']:
        re_pattern = repls['find'].format(item)
        repl_str = repls['repl'].format(item)
        # for fstr in fstrs:
        new_str,  nrepl = re.subn(re_pattern, repl_str, new_str)
        print("repl: {}, find: {}, rstr: {}, item: {}, nrepls: {}".format(repls['name'], re_pattern, repl_str, item, nrepl))


#fpath = path.join(fdir, "new_" + fname)
with open(fpath, mode='w') as fid:
    fid.write(new_str)

