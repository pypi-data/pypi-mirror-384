import os, sys

from orangewidget.settings import Setting
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.util.widget_util import ChemicalFormulaParser
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.syned.widgets.gui.ow_optical_element import OWOpticalElement

from syned.beamline.optical_elements.absorbers.filter import Filter

class OWFilter(OWOpticalElement):

    name = "Filter"
    description = "Syned: Filter"
    icon = "icons/filter.png"
    priority = 3

    thickness = Setting(1e-6)
    material = Setting("Si")

    def __init__(self):
        super().__init__(allow_angle_radial=False, allow_angle_azimuthal=False)

    def draw_specific_box(self):

        self.filter_box = oasysgui.widgetBox(self.tab_bas, "Filter Setting", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.filter_box, self, "material", "Material [Chemical Formula]", labelWidth=200, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "thickness", "Thickness [m]", labelWidth=260, valueType=float, orientation="horizontal")


    def get_optical_element(self):
        return Filter(name=self.oe_name,
                      material=self.material,
                      thickness=self.thickness)

    def check_data(self):
        super().check_data()

        congruence.checkEmptyString(self.material, "Material")
        ChemicalFormulaParser.parse_formula(self.material)
        congruence.checkStrictlyPositiveNumber(self.thickness, "Thickness")

add_widget_parameters_to_module(__name__)

