# System will run the current "run_config.json" file in the directory.
# Use generator configuration to create it, or edit it directly, depending on your
# preference.  You may want to back it up as another file name to prevent the generator from
# overwriting your config history.



ENGINE = 'solid'
# ENGINE = 'cadquery'

if ENGINE == 'solid':
    exec(open('dactyl_manuform.py').read())

if ENGINE == 'cadquery':
    exec(open('dactyl_manuform_cadquery.py').read())
