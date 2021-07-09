import os
import copy
import importlib
from generate_configuration import *

ENGINE = 'solid'
# ENGINE = 'cadquery'

base = shape_config

configurations = [
    {
        'config_name': '4x5_OLED_CtrlTray',
        'save_dir': '4x5_OLED_CtrlTray',
        'nrows': 4,  # key rows
        'ncols': 5,  # key columns
        'oled_mount_type': 'CLIP',
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '4x6_OLED_CtrlTray',
        'save_dir': '4x6_OLED_CtrlTray',
        'nrows': 4,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type':  'CLIP',
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '5x6_OLED_CtrlTray',
        'save_dir': '5x6_OLED_CtrlTray',
        'nrows': 5,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type': 'CLIP',
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '6x6_OLED_CtrlTray',
        'save_dir': '6x6_OLED_CtrlTray',
        'nrows': 6,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type': 'CLIP',
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '4x5_CtrlTray',
        'save_dir': '4x5_CtrlTray',
        'nrows': 4,  # key rows
        'ncols': 5,  # key columns
        'oled_mount_type': None,
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '4x6_CtrlTray',
        'save_dir': '4x6_CtrlTray',
        'nrows': 4,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type': None,
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '5x6_CtrlTray',
        'save_dir': '5x6_CtrlTray',
        'nrows': 5,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type': None,
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '6x6_CtrlTray',
        'save_dir': '6x6_CtrlTray',
        'nrows': 6,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type': 'CLIP',
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '4x5_Basic',
        'save_dir': '4x5_Basic',
        'nrows': 4,  # key rows
        'ncols': 5,  # key columns
        'oled_mount_type': None,
        'controller_mount_type': 'EXTERNAL',
    },
    {
        'config_name': '4x6_Basic',
        'save_dir': '4x6_Basic',
        'nrows': 4,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type': None,
        'controller_mount_type': 'RJ9_USB_WALL',
    },
    {
        'config_name': '5x6_Basic',
        'save_dir': '5x6_Basic',
        'nrows': 5,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type': None,
        'controller_mount_type': 'RJ9_USB_WALL',
    },
    {
        'config_name': '6x6_Basic',
        'save_dir': '6x6_Basic',
        'nrows': 6,  # key rows
        'ncols': 6,  # key columns
        'oled_mount_type': None,
        'controller_mount_type': 'RJ9_USB_WALL',
    }
]

init = True

for config in configurations:
    shape_config = copy.deepcopy(base)
    for item in config:
        shape_config[item] = config[item]


    with open('run_config.json', mode='w') as fid:
        json.dump(shape_config, fid, indent=4)

        if init:
            import dactyl_manuform as dactyl_manuform
        else:
            importlib.reload(dactyl_manuform)

    init = False
