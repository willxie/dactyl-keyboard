import os

script_template = """
import FreeCAD
import ImportGui
import Mesh

def closeDocs():
    documentList = App.listDocuments()

    for doc in documentList:
        App.closeDocument(doc)

def process_item(filename):
    closeDocs()
    ImportGui.open(filename + '.step')
    Gui.Selection.addSelection("Unnamed", 'Solid')
    obj = Gui.Selection.getSelection()
    Mesh.export(obj, filename + '.stl')

files = [ %filenames% ]

documentList = App.listDocuments()

for doc in documentList:
    App.closeDocument(doc)


for file in files:
    try:
        process_item(file)
    except Exception as err:
        print(f"Error {err=}, {type(err)=}")


print('Done')
"""


def generate_freecad_script(target_dir, filenames):
    full_filenames = ','.join(['"' + os.path.join(target_dir, x) + '"' for x in filenames])
    full_filenames = str.replace(full_filenames, "\\", "\\\\")
    print(full_filenames)
    script = script_template.replace('%filenames%', full_filenames)
    script_file = os.path.join(target_dir, 'freecad.py')
    if os.path.exists(script_file):
        os.remove(script_file)
    f = open(script_file, "a")
    f.write(script)
    f.close()

