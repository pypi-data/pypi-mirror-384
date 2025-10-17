# Copyright (C) 2025 Bloomberg LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  <http://www.apache.org/licenses/LICENSE-2.0>
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import functools
from dataclasses import dataclass


@dataclass(frozen=True)
class Cohort:
    name: str
    property_labels: frozenset[str]


class CohortSet:
    def __init__(self, cohorts: list[Cohort]):
        self.cohorts = cohorts
        self.cohort_map = {cohort.name: cohort for cohort in cohorts}

    def get_labels_by_cohort(self, cohort: str) -> frozenset[str]:
        c = self.cohort_map.get(cohort)
        if c is None:
            return frozenset()
        return c.property_labels

    @functools.lru_cache(maxsize=32)
    def get_cohort_by_labels(self, labels: frozenset[str]) -> str | None:
        # A worker is in a cohort if all of its labels are in the cohort's property labels
        for cohort in self.cohorts:
            if labels <= cohort.property_labels:
                return cohort.name
        return None
