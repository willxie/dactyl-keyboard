import os
import json
import dactyl_manuform

json_template = """
{
  "ENGINE": "cadquery",
  "override_name": "",
  "save_dir": "/mnt/c/Users/nethe/OneDrive/Sales/Models/Generated",
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

out_file = "/mnt/c/Users/nethe/OneDrive/Sales/Models/Generated/bulk_config.json"

engine = "cadquery"
default = "DEFAULT"
trackball = "TRACKBALL_WILD"
hotswap = "HS_NUB"
normal = "NUB"

def write_config(rows, cols, engine, thumb1, plate, last_rows):
    config = json.loads(json_template)
    name = str(rows) + "_x_" + str(cols) + "_" + plate  + "_" + last_rows  + "_" + thumb1
    config["save_dir"] = os.path.join(config["save_dir"], str(rows) + "_x_" + str(cols), plate, last_rows)
    print("Generating: ", name)
    config["save_name"] = name
    config["override_name"] = thumb1
    config["engine"] = engine
    config["nrows"] = rows
    config["ncols"] = cols
    config["plate_style"] = "NUB" if plate is "normal" else "HS_NUB"
    config["thumb_style"] = thumb1
    config["other_thumb"] = thumb1
    config["full_last_rows"] = True if last_rows is "full" else False
    config["ball_side"] = "both"

    if os.path.exists(out_file):
        os.remove(out_file)
    f = open(out_file, "a")
    f.write(json.dumps(config))
    f.close()

# i = 1

# for rows in range(4, 7): # 4, 5, 6 rows
rows = 6
# next is
# cols = 7
# for rows in range(4, 7):
for cols in range(6, 7): # 6, 7 cols
    for last_row in ["normal", "full"]:
        for plate in ["normal", "hotswap"]:
            for thumb1 in [default, trackball]:
                write_config(rows, cols, "cadquery", thumb1, plate, last_row)
                # print("Wrote file " + str(i))
                dactyl_manuform.make_dactyl()




