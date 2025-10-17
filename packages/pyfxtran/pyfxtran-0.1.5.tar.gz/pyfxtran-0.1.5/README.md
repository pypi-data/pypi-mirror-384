# pyfxtran

This package is a lightweight wrapper around [fxtran](https://github.com/pmarguinaud/fxtran).

The goal is to produce a python package that can be distributed via PyPI.
A better way would be to write a real python binding around fxtran.

## Installation:
Standard installation from PyPI: ```pip install pyfxtran```

Note that pyfxtran is distributed on PyPI in a binary form for X86\_64 architectures
and as a source distribution that is compiled during the installation. This build process
has been succesfully tested on X86\_64 and aarch64 architectures.

## Usage:
```
import fxtran
result = fxtran.run(filename, kwargs)
```

## Documentation:
The wrapper does not add any functionality over fxtran. Full documentation can
be found with the fxtran tool.

## Installtion from git:
```
git clone https://github.com/SebastienRietteMTO/pyfxtran.git
cd pyfxtran
pip install -e .
```
On first use, pyfxtran will download fxtran and compile it. The executable is then stored
in the user's directory, its name begins with .fxtran and is followed by the fxtran version number.

Instead of downloading fxtran, if the ```FXTRAN_FOR_PYFXTRAN``` environment variable is set, on the
first use the ```git clone``` command will be replaced by a symlink to the directory pointed by this
variable and a cleaning will be done.
