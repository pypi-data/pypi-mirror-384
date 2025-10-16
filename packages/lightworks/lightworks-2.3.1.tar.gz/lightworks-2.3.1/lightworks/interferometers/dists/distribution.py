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

from abc import ABC, abstractmethod


class Distribution(ABC):
    """
    Base class for all distributions. Enforces that any created distributions
    have the required value method, which returns a singular value on request.
    If the distribution requires randomness, then the set_random_seed method
    should be added, which accepts a seed and sets this for the rng to allow
    for repeatability where required.
    """

    @abstractmethod
    def value(self) -> float:
        """Returns a value from the distribution on request."""

    @abstractmethod
    def set_random_seed(self, seed: int | None) -> None:
        """
        Used for setting the random seed for the model. Can just pass in cases
        where a distribution does not feature a random component.
        """

    def __repr__(self) -> str:
        return "lightworks.interferometers.dists." + str(self)
