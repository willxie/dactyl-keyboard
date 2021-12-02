import os
import json
import sys
import dactyl_manuform

json_template = """
{
  "ENGINE": "cadquery",
  "overrides": "",
  "override_name": "",
  "save_dir": "",
  "save_name": null,
  "show_caps": false,
  "nrows": 6,
  "ncols": 6,
  "plate_style": "NUB",
  "full_last_rows": false,
  "thumb_style": "DEFAULT",
  "other_thumb": "DEFAULT",
  "ball_side": "right"
}
"""

gen_dir = sys.argv[1]

try:
    print(gen_dir)
except NameError:
    print("Must provide target directory for generating bulk models")
    sys.exit(-1)

out_file = os.path.join(gen_dir, "bulk_config.json")

engine = "cadquery"
default = "DEFAULT"
trackball = "TRACKBALL_WILD"
hotswap = "HS_NUB"
normal = "NUB"
run_config = os.path.join(r"..", 'run_config.json')

def write_file(file_path, data):
    if os.path.exists(file_path):
        os.remove(file_path)
    f = open(file_path, "a")
    f.write(json.dumps(data, indent=2))
    f.close()


def set_overrides(override):
    with open(run_config, mode='r') as fid:
        data = json.load(fid)
    previous_overrides = data["overrides"]
    data["overrides"] = override
    write_file(run_config, data)
    return previous_overrides

previous_overrides = set_overrides(out_file)

def finished():
    set_overrides(previous_overrides)
    sys.exit(0)


def write_config(rows, cols, engine, thumb1, plate, last_rows):
    config = json.loads(json_template)
    name = str(rows) + "_x_" + str(cols) + "_" + plate  + "_" + last_rows  + "_" + thumb1
    config["save_dir"] = os.path.join(gen_dir, str(rows) + "_x_" + str(cols), plate, last_rows)
    print("Generating: ", name)
    config["overrides"] = out_file
    config["save_name"] = name
    config["override_name"] = thumb1
    config["engine"] = engine
    config["nrows"] = rows
    config["ncols"] = cols
    config["plate_style"] = "NUB" if plate == "normal" else "HS_NUB"
    config["thumb_style"] = thumb1
    config["other_thumb"] = thumb1
    config["full_last_rows"] = True if last_rows == "full" else False
    config["ball_side"] = "both"

    write_file(out_file, config)

for rows in range(4, 7): #4, 5, 6
    for cols in range(6, 8): # 6, 7 cols
        for last_row in ["normal", "full"]:
            for plate in ["normal", "hotswap"]:
                for thumb1 in [default, trackball]:
                    write_config(rows, cols, "cadquery", thumb1, plate, last_row)
                    # print("Wrote file " + str(i))
                    dactyl_manuform.make_dactyl()

finished()


