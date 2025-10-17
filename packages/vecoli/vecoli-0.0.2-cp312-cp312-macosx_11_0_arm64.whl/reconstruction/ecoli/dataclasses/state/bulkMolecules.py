"""
SimulationData for bulk molecules state
"""

import numpy as np

from reconstruction.ecoli.dataclasses.state.stateFunctions import addToStateCommon
from wholecell.utils import units
from wholecell.utils.unit_struct_array import UnitStructArray


class BulkMolecules:
    """BulkMolecules"""

    def __init__(self, raw_data, sim_data):
        bulkData = np.zeros(
            0,
            dtype=[
                ("id", "U50"),
                ("mass", f"{len(sim_data.submass_name_to_index)}f8"),
            ],
        )

        # Add units to values
        field_units = {
            "id": None,
            "mass": units.g / units.mol,
        }

        self.bulk_data = UnitStructArray(bulkData, field_units)

    def add_to_bulk_state(self, ids, masses):
        self.bulk_data = addToStateCommon(self.bulk_data, ids, masses)
