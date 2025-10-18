import sys

from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from syned.storage_ring.magnetic_structures.wiggler import Wiggler
from orangecontrib.syned.widgets.gui.ow_insertion_device import OWInsertionDevice

class OWWigglerLightSource(OWInsertionDevice):

    name = "Wiggler Light Source"
    description = "Syned: Wiggler Light Source"
    icon = "icons/wiggler.png"
    priority = 3

    def __init__(self):
        super().__init__()

    def get_magnetic_structure(self):
        return Wiggler(K_horizontal=self.K_horizontal,
                       K_vertical=self.K_vertical,
                       period_length=self.period_length,
                       number_of_periods=self.number_of_periods)

    def check_magnetic_structure_instance(self, magnetic_structure):
        if not isinstance(magnetic_structure, Wiggler):
            raise ValueError("Magnetic Structure is not a Wiggler")

    def populate_magnetic_structure(self, magnetic_structure):
        if not isinstance(magnetic_structure, Wiggler):
            raise ValueError("Magnetic Structure is not a Wiggler")

        self.K_horizontal = magnetic_structure._K_horizontal
        self.K_vertical = magnetic_structure._K_vertical
        self.period_length = magnetic_structure._period_length
        self.number_of_periods = magnetic_structure._number_of_periods


add_widget_parameters_to_module(__name__)
