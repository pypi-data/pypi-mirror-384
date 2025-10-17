
from orangewidget.settings import Setting

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence

from syned.storage_ring.magnetic_structures import insertion_device

from orangecontrib.syned.widgets.gui.ow_light_source import OWLightSource

class OWInsertionDevice(OWLightSource):

    K_horizontal       = Setting(1.0)
    K_vertical         = Setting(1.0)
    period_length      = Setting(0.010)
    number_of_periods  = Setting(10)

    def __init__(self):
        super().__init__()

        left_box_1 = oasysgui.widgetBox(self.tab_sou, "ID Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "K_horizontal", "Horizontal K", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "K_vertical", "Vertical K", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "period_length", "Period Length [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "number_of_periods", "Number of Periods", labelWidth=260, valueType=float, orientation="horizontal")

    def check_magnetic_structure(self):
        congruence.checkPositiveNumber(self.K_horizontal, "Horizontal K")
        congruence.checkPositiveNumber(self.K_vertical, "Vertical K")
        congruence.checkStrictlyPositiveNumber(self.period_length, "Period Length")
        congruence.checkStrictlyPositiveNumber(self.number_of_periods, "Number of Periods")

    def get_magnetic_structure(self):
        return insertion_device.InsertionDevice(K_horizontal=self.K_horizontal,
                                                K_vertical=self.K_vertical,
                                                period_length=self.period_length,
                                                number_of_periods=self.number_of_periods)
