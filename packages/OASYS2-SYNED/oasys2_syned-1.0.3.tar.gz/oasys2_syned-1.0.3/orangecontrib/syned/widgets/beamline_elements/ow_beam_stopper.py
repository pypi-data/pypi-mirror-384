
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.syned.widgets.gui.ow_optical_element import OWOpticalElementWithBoundaryShape

from syned.beamline.optical_elements.absorbers.beam_stopper import BeamStopper

class OWBeamStopper(OWOpticalElementWithBoundaryShape):

    name = "Beam Stopper"
    description = "Syned: Beam Stopper"
    icon = "icons/beam_stopper.png"
    priority = 1

    def __init__(self):
        super().__init__(allow_angle_radial=False, allow_angle_azimuthal=False)

    def get_optical_element(self):
        return BeamStopper(name=self.oe_name,
                            boundary_shape=self.get_boundary_shape())

add_widget_parameters_to_module(__name__)