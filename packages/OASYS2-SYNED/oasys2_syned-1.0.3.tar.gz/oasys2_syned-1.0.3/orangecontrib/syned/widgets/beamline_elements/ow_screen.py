from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.syned.widgets.gui.ow_optical_element import OWOpticalElement

from syned.beamline.optical_elements.ideal_elements.screen import Screen

class OWScreen(OWOpticalElement):

    name = "Screen"
    description = "Syned: Screen"
    icon = "icons/screen.png"
    priority = 4

    def __init__(self):
        super().__init__(allow_angle_radial=False, allow_angle_azimuthal=False)

    def draw_specific_box(self):
        pass

    def get_optical_element(self):
        return Screen(name=self.oe_name)


add_widget_parameters_to_module(__name__)

