# Copyright 2024 - 2025 Aegiq Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Lightworks Qubit
================

Enables the implementation of the gate-based paradigm of quantum computing
within linear optic photonic circuits. There is a number of gates, both single
and multi-qubit, and a set of converters for performing conversion from other
quantum programming languages.
"""

from .converter.qiskit_convert import qiskit_converter
from .gates.single_qubit_gates import (
    SX,
    H,
    I,
    P,
    Rx,
    Ry,
    Rz,
    S,
    Sadj,
    T,
    Tadj,
    X,
    Y,
    Z,
)
from .gates.three_qubit_gates import CCNOT, CCZ
from .gates.two_qubit_gates import CNOT, CZ, SWAP, CNOT_Heralded, CZ_Heralded

__all__ = [
    "CCNOT",
    "CCZ",
    "CNOT",
    "CZ",
    "SWAP",
    "SX",
    "CNOT_Heralded",
    "CZ_Heralded",
    "H",
    "I",
    "P",
    "Rx",
    "Ry",
    "Rz",
    "S",
    "Sadj",
    "T",
    "Tadj",
    "X",
    "Y",
    "Z",
    "qiskit_converter",
]
