import os
import subprocess
import time

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        super().initialize(version, build_data)

        if os.environ.get("AMZN_BUILD"):
            print("using peru hatch to build")

        # Get the project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        print(f'custom build, dir is {project_dir}')

    def finalize(self, version, build_data, artifact_directory):
        if not os.environ.get("AMZN_BUILD"):
            print("Not amazon build, skipping custom build finalize")
            return  # exit immediately if we are not in amazon build system

        print("building in amazon build system, executing a second time build to package external artifacts")
        skip_finally = False

        try:
            subprocess.run([
                "mv", "pyproject.toml", "pyproject.toml.backup"
            ], check=True)

            subprocess.run([
                "mv", "amzn.pyproject.toml", "pyproject.toml"
            ], check=True)

            subprocess.run([
                ".venv/bin/python3", "-m", "pip", "install", "hatch"
            ], check=True)

            time.sleep(7)

            subprocess.run([
                ".venv/bin/python3", "-m", "hatch", "build"
            ], check=True)

            # Restore the original pyproject.toml configuration

            subprocess.run([
                "mv", "pyproject.toml", "amzn.pyproject.toml"
            ], check=True)

            subprocess.run([
                "mv", "pyproject.toml.backup", "pyproject.toml"
            ], check=True) 

            skip_finally = True

        finally:
            # Restore the original pyproject.toml configuration
            if not skip_finally:
                subprocess.run([
                    "mv", "pyproject.toml", "amzn.pyproject.toml"
                ], check=True)

                subprocess.run([
                    "mv", "pyproject.toml.backup", "pyproject.toml"
                ], check=True)


