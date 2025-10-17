# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""MQT SyReC library.

This file is part of the MQT SyReC library released under the MIT license.
See README.md or go to https://github.com/munich-quantum-toolkit/syrec for more information.
"""

from __future__ import annotations

import sys

# under Windows, make sure to add the appropriate DLL directory to the PATH
if sys.platform == "win32":

    def _dll_patch() -> None:
        """Add the DLL directory to the PATH."""
        import os
        import sysconfig
        from pathlib import Path

        bin_dir = Path(sysconfig.get_paths()["purelib"]) / "mqt" / "core" / "bin"
        os.add_dll_directory(str(bin_dir))

    _dll_patch()
    del _dll_patch

from ._version import version as __version__
from .pysyrec import (
    annotatable_quantum_computation,
    configurable_options,
    cost_aware_synthesis,
    inlined_qubit_information,
    integer_constant_truncation_operation,
    line_aware_synthesis,
    n_bit_values_container,
    program,
    qubit_inlining_stack,
    qubit_inlining_stack_entry,
    qubit_label_type,
    simple_simulation,
    statistics,
)

__all__ = [
    "__version__",
    "annotatable_quantum_computation",
    "configurable_options",
    "cost_aware_synthesis",
    "inlined_qubit_information",
    "integer_constant_truncation_operation",
    "line_aware_synthesis",
    "n_bit_values_container",
    "program",
    "qubit_inlining_stack",
    "qubit_inlining_stack_entry",
    "qubit_label_type",
    "simple_simulation",
    "statistics",
]
