import logging
import os
import posixpath
from glob import iglob
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from zipfile import ZipFile, ZIP_DEFLATED
from mkdocs.plugins import BasePlugin
from mkdocs.config.defaults import MkDocsConfig
from mergedeep import merge
from material.plugins.projects.structure import Project

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mkdocs.material.examples")

class ZipExamplesPlugin(BasePlugin):
    def on_post_build(self, config: MkDocsConfig):
        base_dir = "examples"

        for file in iglob(os.path.join(base_dir, "*/mkdocs.yml"), recursive=True):
            base = os.path.dirname(file)

            # Compute archive name and path
            example = os.path.basename(base)
            archive = os.path.join(config.site_dir, f"{example}.zip")

            self.create_zip_folder(base, archive)
            self.transform_config(base, config)

    def create_zip_folder(self, folder_path, zip_path):
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

    def transform_config(self, folder_path, root_config: MkDocsConfig):
        # Transform project configuration
        config_file_path = os.path.join(folder_path, 'mkdocs.yml')
        project = Project(config_file_path=config_file_path)

        base = os.path.dirname(config_file_path)
        name = os.path.basename(base)

        # Determine path of examples relative to root
        root = os.path.dirname(root_config.config_file_path)
        path = os.path.relpath(base, root)

        # Inherit settings for repository
        project.config.repo_name = root_config.repo_name
        project.config.repo_url = f"{root_config.repo_url}/tree/master/{path}"

        # Inherit settings for site URL and edit URI
        project.config.site_url = posixpath.join(root_config.site_url, name, "")
        project.config.edit_uri = f"{root_config.repo_url}/edit/master/{path}/docs/"

        # Inherit settings for theme
        if "features" in project.config.theme:
            project.config.theme["features"].extend(root_config.theme["features"])
        else:
            project.config.theme["features"] = root_config.theme["features"]

        if "icon" in project.config.theme:
            merge(project.config.theme["icon"], root_config.theme["icon"])
        else:
            project.config.theme["icon"] = root_config.theme["icon"]

        # Write back the modified config if necessary
        project.config_file_path = config_file_path
        project.save()

# -----------------------------------------------------------------------------
# Register Plugin
# -----------------------------------------------------------------------------
def get_plugin():
    return ZipExamplesPlugin()
