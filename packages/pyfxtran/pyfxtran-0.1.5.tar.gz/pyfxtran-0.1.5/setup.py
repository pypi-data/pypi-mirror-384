"""
setup.py module
All configuration is in the pyproject.toml file
Here are only the build procedure
"""

import subprocess
import os
import shutil
from setuptools import setup
from setuptools.command.build import build


class FxtranBuild(build):
    """
    Custom class to modify the build process
    """
    def run(self):
        """
        Method actually doing the build
        """
        # Normal build
        build.run(self)

        # compile fxtran, remove source
        build_dir = os.path.join(os.getcwd(), self.build_lib, 'pyfxtran')
        executable = os.path.join(build_dir, 'bin', 'fxtran')
        if not os.path.exists(executable):
            # This build process is needed only when a user
            # install the package from source. To Build a
            # wheel we use the make_wheels.sh script in order
            # to use a manylinux container.
            options = subprocess.run(['bash', os.path.join(build_dir, '_get_make_options.sh')],
                                     stdout=subprocess.PIPE, check=True).stdout.split(b' ')
            subprocess.run(['make'] + options + ['all'],
                           cwd=os.path.join(build_dir, 'fxtran'),
                           check=False)

            os.makedirs(os.path.join(build_dir, 'bin'))
            shutil.move(os.path.join(build_dir, 'fxtran', 'bin', 'fxtran'),
                        executable)
            shutil.rmtree(os.path.join(build_dir, 'fxtran'))


setup(cmdclass={"build": FxtranBuild})
