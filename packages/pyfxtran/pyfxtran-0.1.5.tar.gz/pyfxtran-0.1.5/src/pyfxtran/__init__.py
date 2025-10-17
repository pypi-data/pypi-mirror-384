#!/usr/bin/env python3

"""
Lightweight wrapper around fxtran
"""

from pathlib import Path
import tempfile
import subprocess
import os
import shutil
import argparse

__version__ = '0.1.5'

FXTRAN_VERSION = '7b1686a286b885cf52369326e333ec783b0eeb3d'
FXTRAN_REPO = 'https://github.com/pmarguinaud/fxtran.git'


def run(filename, options=None, verbose=False):
    """
    Main function: installs fxtran if not available, runs it and return the result
    :param filename: name of the FORTRAN file
    :param options: options (dict) to give to fxtran
    """
    package_dir = os.path.dirname(os.path.realpath(__file__))

    # First we check if an executable is included in the package
    parser = os.path.join(package_dir, 'bin', 'fxtran')

    if not os.path.exists(parser):
        # If not included, we check if we already compiled it
        parser = os.path.join(Path.home(), f'.fxtran_{FXTRAN_VERSION}')

        if not os.path.exists(parser):
            # Executable not found, we build it
            out_stream = None if verbose else subprocess.DEVNULL
            with tempfile.TemporaryDirectory() as tempdir:
                fxtran_for_pyfxtran = os.environ.get('FXTRAN_FOR_PYFXTRAN', None)
                fxtran_dir = os.path.join(tempdir, 'fxtran')

                # get the repository, and checkout the right version
                if fxtran_for_pyfxtran is None:
                    subprocess.run(['git', 'clone', f'{FXTRAN_REPO}', fxtran_dir], cwd=tempdir,
                                   stdout=out_stream, stderr=out_stream, check=True)
                else:
                    os.symlink(fxtran_for_pyfxtran, fxtran_dir)
                subprocess.run(['git', 'checkout', f'{FXTRAN_VERSION}'], cwd=fxtran_dir,
                               stdout=out_stream, stderr=out_stream, check=True)

                # cleaning, if needed
                if fxtran_for_pyfxtran is not None:
                    # clean reports error
                    subprocess.run(['make', 'clean'], cwd=fxtran_dir,
                                   stdout=out_stream, stderr=out_stream, check=False)

                # Compilation is known to produce an error due to perl
                # We do not check status but only the existence of the executable
                make_options = subprocess.run(
                    ['bash', os.path.join(package_dir, '_get_make_options.sh')],
                    stdout=subprocess.PIPE, check=True).stdout.split(b' ')
                print(make_options)
                subprocess.run(['make'] + make_options + ['all'], cwd=fxtran_dir,
                               stdout=out_stream, stderr=out_stream, check=False)
                if not os.path.exists(os.path.join(fxtran_dir, 'bin/fxtran')):
                    raise RuntimeError('fxtran compilation has failed')
                shutil.move(os.path.join(fxtran_dir, 'bin/fxtran'), parser)

    # Execution
    return subprocess.run([parser, filename] + ([] if options is None else options),
                          stdout=subprocess.PIPE, check=True, encoding='UTF-8').stdout


def main():
    """
    Entry point to output on stdout the transformed version of a FORTRAN file
    :param filename: name of the FORTRAN file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='FORTRAN file name')
    parser.add_argument('--verbose', action='store_true',
                        help='Display details of the fxtran installation')
    args = parser.parse_args()
    print(run(args.filename, ['-o', '-'], args.verbose))
