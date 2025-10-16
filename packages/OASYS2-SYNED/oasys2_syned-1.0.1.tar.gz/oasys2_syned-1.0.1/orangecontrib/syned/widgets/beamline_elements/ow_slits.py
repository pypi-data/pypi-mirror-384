from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.syned.widgets.gui.ow_optical_element import OWOpticalElementWithBoundaryShape

from syned.beamline.optical_elements.absorbers.slit import Slit

class OWSlit(OWOpticalElementWithBoundaryShape):

    name = "Slit"
    description = "Syned: Slit"
    icon = "icons/slit.png"
    priority = 2

    def __init__(self):
        super().__init__(allow_angle_radial=False, allow_angle_azimuthal=False)

    def get_optical_element(self):
        return Slit(name=self.oe_name,
                    boundary_shape=self.get_boundary_shape())


add_widget_parameters_to_module(__name__)
