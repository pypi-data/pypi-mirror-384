﻿import cythonpackage
cythonpackage.init(__name__)
from ._slurm import SlurmFunction as _SlurmFunction


__all__ = ["_SlurmFunction"]
