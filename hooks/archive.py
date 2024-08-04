import logging
import os
from flask import Flask, send_file, abort
from glob import iglob
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from zipfile import ZipFile, ZIP_DEFLATED
import tempfile

app = Flask(__name__)

# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mkdocs.material.examples")

def create_zip_folder(folder_path, zip_path):
    # Read files to ignore from .gitignore
    gitignore_path = os.path.join(folder_path, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            lines = f.read().splitlines()
            lines = [line for line in lines if line and not line.startswith("#")]
            spec = PathSpec.from_lines(GitWildMatchPattern, lines)
    else:
        spec = PathSpec([])

    # Create the archive
    log.info(f"Creating archive '{zip_path}'")
    with ZipFile(zip_path, "w", ZIP_DEFLATED, False) as f:
        for root, _, files in os.walk(folder_path):
            for file in files:
                path = os.path.join(root, file)
                if not spec.match_file(path):
                    arcname = os.path.relpath(path, folder_path)
                    log.debug(f"+ '{path}' as '{arcname}'")
                    f.write(path, arcname)

@app.route('/<path:folder>.zip')
def zip_and_download(folder):
    base_dir = "examples"
    folder_path = os.path.join(base_dir, folder)
    
    if not os.path.isdir(folder_path):
        abort(404, description="Folder not found")
    
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"{os.path.basename(folder)}.zip")
    create_zip_folder(folder_path, zip_path)
    
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
