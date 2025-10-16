from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QRect

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Output

from oasys2.widget.widget import OWWidget, OWAction
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.gui import ConfirmDialog

from syned.storage_ring.light_source import LightSource, ElectronBeam
from syned.beamline.beamline import Beamline
from syned.util.json_tools import load_from_json_file, load_from_json_url

class OWLightSource(OWWidget, openclass=True):
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Syned Light Sources"
    keywords = ["data", "file", "load", "read"]

    class Outputs:
        syned_data = Output(name="SynedData",
                            type=Beamline,
                            id="SynedData", default=True, auto_summary=False)

    syned_file_name = Setting("Select *.json file")
    file_action     = Setting(0)

    source_name         = Setting("Undefined")

    electron_energy_in_GeV = Setting(2.0)
    electron_energy_spread = Setting(0.001)
    ring_current           = Setting(0.4)
    number_of_bunches      = Setting(400)

    moment_xx           = Setting(0.0)
    moment_xxp          = Setting(0.0)
    moment_xpxp         = Setting(0.0)
    moment_yy           = Setting(0.0)
    moment_yyp          = Setting(0.0)
    moment_ypyp         = Setting(0.0)

    electron_beam_size_h       = Setting(0.0)
    electron_beam_divergence_h = Setting(0.0)
    electron_beam_size_v       = Setting(0.0)
    electron_beam_divergence_v = Setting(0.0)
    electron_beam_emittance_h  = Setting(0.0)
    electron_beam_emittance_v  = Setting(0.0)
    electron_beam_beta_h       = Setting(0.0)
    electron_beam_beta_v       = Setting(0.0)
    electron_beam_alpha_h      = Setting(0.0)
    electron_beam_alpha_v      = Setting(0.0)
    electron_beam_eta_h        = Setting(0.0)
    electron_beam_eta_v        = Setting(0.0)
    electron_beam_etap_h       = Setting(0.0)
    electron_beam_etap_v       = Setting(0.0)

    type_of_properties = Setting(0)

    want_main_area=0

    MAX_WIDTH = 460
    MAX_HEIGHT = 760

    TABS_AREA_HEIGHT = 655
    CONTROL_AREA_WIDTH = 450

    def __init__(self):
        super().__init__()

        self.runaction = OWAction("Send Data", self)
        self.runaction.triggered.connect(self.send_data)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Send Data", callback=self.send_data)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_sou = oasysgui.createTabPage(self.tabs_setting, "Light Source Setting")

        box_json =  oasysgui.widgetBox(self.tab_sou, "Read/Write File", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(box_json, "", addSpace=False, orientation="horizontal")

        self.le_syned_file_name = oasysgui.lineEdit(file_box, self, "syned_file_name", "Syned File Name/URL",
                                                    labelWidth=150, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.select_syned_file, width=25)

        button_box = oasysgui.widgetBox(box_json, "", addSpace=False, orientation="horizontal")

        self.cb_file_action = gui.comboBox(button_box, self, "file_action", label="Action", labelWidth=70,
                     items=["Read", "Write"], sendSelectedValue=False, orientation="horizontal")

        button = gui.button(button_box, self, "Execute", callback=self.execute_syned_file)
        button.setFixedHeight(25)

        oasysgui.lineEdit(self.tab_sou, self, "source_name", "Light Source Name", labelWidth=260, valueType=str, orientation="horizontal")

        self.electron_beam_box = oasysgui.widgetBox(self.tab_sou, "Electron Beam/Machine Parameters", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_in_GeV", "Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.electron_beam_box, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.electron_beam_box, self, "ring_current", "Ring Current [A]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.electron_beam_box, self, "type_of_properties", label="Electron Beam Properties", labelWidth=350,
                     items=["From 2nd Moments", "From Size/Divergence", "From Twiss parameters","Zero emittance"],
                     callback=self.set_TypeOfProperties,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_2_1 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=190)

        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xx",   "<x x>   [m^2]",   labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xxp",  "<x x'>  [m.rad]", labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xpxp", "<x' x'> [rad^2]", labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yy",   "<y y>   [m^2]",   labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yyp",  "<y y'>  [m.rad]", labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_ypyp", "<y' y'> [rad^2]", labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        gui.separator(self.left_box_2_1)
        lbl = oasysgui.widgetLabel(self.left_box_2_1, "Note: 2nd Moments do not include dispersion")
        lbl.setStyleSheet("color: darkblue; font-weight: bold;")

        self.left_box_2_2 = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="vertical", height=190)

        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_h",       "Horizontal Beam Size \u03c3x [m]",          labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_v",       "Vertical Beam Size \u03c3y [m]",            labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_h", "Horizontal Beam Divergence \u03c3'x [rad]", labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_v", "Vertical Beam Divergence \u03c3'y [rad]",   labelWidth=260, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        gui.separator(self.left_box_2_2)
        lbl = oasysgui.widgetLabel(self.left_box_2_2, "Note: Size/Divergence do not include dispersion")
        lbl.setStyleSheet("color: darkblue; font-weight: bold;")

        self.left_box_2_3   = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="horizontal",height=190)
        self.left_box_2_3_l = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")
        self.left_box_2_3_r = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_emittance_h", "\u03B5x [m.rad]",labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_alpha_h",     "\u03B1x",        labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_beta_h",      "\u03B2x [m]",    labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_eta_h",       "\u03B7x",        labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_l, self, "electron_beam_etap_h",      "\u03B7'x",       labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_emittance_v", "\u03B5y [m.rad]",labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_alpha_v",     "\u03B1y",        labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_beta_v",      "\u03B2y [m]",    labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_eta_v",       "\u03B7y",        labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_3_r, self, "electron_beam_etap_v",      "\u03B7'y",       labelWidth=75, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)

        self.left_box_2_4   = oasysgui.widgetBox(self.electron_beam_box, "", addSpace=False, orientation="horizontal",height=190)

        self.set_TypeOfProperties()

        gui.rubber(self.controlArea)

    def set_TypeOfProperties(self):
        self.left_box_2_1.setVisible(self.type_of_properties == 0)
        self.left_box_2_2.setVisible(self.type_of_properties == 1)
        self.left_box_2_3.setVisible(self.type_of_properties == 2)
        self.left_box_2_4.setVisible(self.type_of_properties == 3)

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self._reset_settings()
            except:
                pass

    def _electron_beam_modified(self):
        try:
            self.check_electron_beam()
            if self._check_dispersion_reset():
                self.populate_electron_beam(self.get_electron_beam())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)
            if self.IS_DEVELOP: raise e


    def check_data(self):
        self.check_electron_beam()
        self.check_magnetic_structure()

    def check_electron_beam(self):
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV, "Energy")
        congruence.checkStrictlyPositiveNumber(self.electron_energy_spread, "Energy Spread")
        congruence.checkStrictlyPositiveNumber(self.ring_current, "Ring Current")

        if self.type_of_properties == 0:
            congruence.checkPositiveNumber(self.moment_xx, "Moment xx")
            congruence.checkPositiveNumber(self.moment_xpxp, "Moment xpxp")
            congruence.checkPositiveNumber(self.moment_yy, "Moment yy")
            congruence.checkPositiveNumber(self.moment_ypyp, "Moment ypyp")
        elif self.type_of_properties == 1:
            congruence.checkPositiveNumber(self.electron_beam_size_h, "Horizontal Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_h, "Vertical Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_size_v, "Horizontal Beam Divergence")
            congruence.checkPositiveNumber(self.electron_beam_divergence_v, "Vertical Beam Divergence")
        elif self.type_of_properties == 2:
            congruence.checkPositiveNumber(self.electron_beam_emittance_h, "Horizontal Beam Emittance")
            congruence.checkPositiveNumber(self.electron_beam_emittance_v, "Vertical Beam Emittance")
            congruence.checkNumber(self.electron_beam_alpha_h, "Horizontal Beam Alpha")
            congruence.checkNumber(self.electron_beam_alpha_v, "Vertical Beam Alpha")
            congruence.checkNumber(self.electron_beam_beta_h, "Horizontal Beam Beta")
            congruence.checkNumber(self.electron_beam_beta_v, "Vertical Beam Beta")
            congruence.checkNumber(self.electron_beam_eta_h, "Horizontal Beam Dispersion Eta")
            congruence.checkNumber(self.electron_beam_eta_v, "Vertical Beam Dispersion Eta")
            congruence.checkNumber(self.electron_beam_etap_h, "Horizontal Beam Dispersion Eta'")
            congruence.checkNumber(self.electron_beam_etap_v, "Vertical Beam Dispersion Eta'")

    def get_electron_beam(self):
        electron_beam = ElectronBeam(energy_in_GeV=self.electron_energy_in_GeV,
                                     energy_spread=self.electron_energy_spread,
                                     current=self.ring_current,
                                     number_of_bunches=self.number_of_bunches)
        if self.type_of_properties == 0:
            electron_beam.set_moments_all(moment_xx=self.moment_xx,
                                          moment_xxp=self.moment_xxp,
                                          moment_xpxp=self.moment_xpxp,
                                          moment_yy=self.moment_yy,
                                          moment_yyp=self.moment_yyp,
                                          moment_ypyp=self.moment_ypyp)
        elif self.type_of_properties == 1:
            electron_beam.set_sigmas_all(sigma_x=self.electron_beam_size_h,
                                         sigma_y=self.electron_beam_size_v,
                                         sigma_xp=self.electron_beam_divergence_h,
                                         sigma_yp=self.electron_beam_divergence_v)
        elif self.type_of_properties == 2:
            electron_beam.set_twiss_all(self.electron_beam_emittance_h,
                                        self.electron_beam_alpha_h,
                                        self.electron_beam_beta_h,
                                        self.electron_beam_emittance_v,
                                        self.electron_beam_alpha_v,
                                        self.electron_beam_beta_v)
            electron_beam.set_dispersion_all(self.electron_beam_eta_h,
                                             self.electron_beam_etap_h,
                                             self.electron_beam_eta_v,
                                             self.electron_beam_etap_v)
        elif self.type_of_properties == 3:
            electron_beam.set_moments_all(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        return electron_beam

    def get_light_source(self):
        return LightSource(name=self.source_name,
                           electron_beam=self.get_electron_beam(),
                           magnetic_structure=self.get_magnetic_structure())

    def check_magnetic_structure(self):
        raise NotImplementedError("Shoudl be implemented in subclasses")

    def get_magnetic_structure(self):
        raise NotImplementedError("Shoudl be implemented in subclasses")

    def populate_fields(self, light_source):
        self.source_name = light_source._name

        self.populate_electron_beam(light_source._electron_beam)
        self.populate_magnetic_structure(light_source._magnetic_structure)

    def populate_electron_beam(self, electron_beam):
        self.electron_energy_in_GeV = electron_beam._energy_in_GeV
        self.electron_energy_spread = electron_beam._energy_spread
        self.ring_current           = electron_beam._current
        self.number_of_bunches      = electron_beam._number_of_bunches

        moment_xx,\
        moment_xxp,\
        moment_xpxp,\
        moment_yy,\
        moment_yyp,\
        moment_ypyp = electron_beam.get_moments_all()

        self.moment_xx              = round(moment_xx,   16)
        self.moment_xxp             = round(moment_xxp,  16)
        self.moment_xpxp            = round(moment_xpxp, 16)
        self.moment_yy              = round(moment_yy,   16)
        self.moment_yyp             = round(moment_yyp,  16)
        self.moment_ypyp            = round(moment_ypyp, 16)

        # calculated parameters from second moments
        x, xp, y, yp                 = electron_beam.get_sigmas_all()
        ex, ax, bx, ey, ay, by       = electron_beam.get_twiss_all()
        eta_x, etap_x, eta_y, etap_y = electron_beam.get_dispersion_all()

        self.electron_beam_size_h       = round(x, 10)
        self.electron_beam_size_v       = round(y, 10)
        self.electron_beam_divergence_h = round(xp, 10)
        self.electron_beam_divergence_v = round(yp, 10)
        self.electron_beam_emittance_h  = round(ex, 16)
        self.electron_beam_emittance_v  = round(ey, 16)
        self.electron_beam_alpha_h      = round(ax, 6)
        self.electron_beam_alpha_v      = round(ay, 6)
        self.electron_beam_beta_h       = round(bx, 6)
        self.electron_beam_beta_v       = round(by, 6)
        self.electron_beam_eta_h        = round(eta_x, 8)
        self.electron_beam_eta_v        = round(eta_y, 8)
        self.electron_beam_etap_h       = round(etap_x, 8)
        self.electron_beam_etap_v       = round(etap_y, 8)

    def check_magnetic_structure_instance(self, magnetic_structure):
        raise NotImplementedError()

    def populate_magnetic_structure(self, magnetic_structure):
        raise NotImplementedError()

    def _check_dispersion_presence(self):
        return self.electron_beam_eta_h != 0.0 or \
               self.electron_beam_eta_v != 0.0 or \
               self.electron_beam_etap_h != 0.0 or \
               self.electron_beam_etap_v != 0.0

    # -----------------------------------------------------
    # EXECUTION

    def send_data(self):
        try:
            self.check_data()
            light_source = self.get_light_source()

            if self._check_dispersion_reset():
                self.populate_fields(light_source)  # apply modifications from the typo of properties
                self.Outputs.syned_data.send(Beamline(light_source=light_source))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()

            if self.IS_DEVELOP: raise e

    def select_syned_file(self):
        if self.file_action == 0:   self.le_syned_file_name.setText(oasysgui.selectFileFromDialog(self, self.syned_file_name, "Open Syned File",
                                                                                                  file_extension_filter="JSON files (*.json)"))
        elif self.file_action == 1: self.le_syned_file_name.setText(oasysgui.selectSaveFileFromDialog(self, "Save Syned File",
                                                                                                      default_file_name="light_source.json",
                                                                                                      file_extension_filter="JSON files (*.json)"))

    def execute_syned_file(self):
        if self.file_action == 0:   self.read_syned_file()
        elif self.file_action == 1: self.write_syned_file()

    def read_syned_file(self):
        try:
            congruence.checkEmptyString(self.syned_file_name, "Syned File Name/Url")

            if (len(self.syned_file_name) > 7 and self.syned_file_name[:7] == "http://") or \
                (len(self.syned_file_name) > 8 and self.syned_file_name[:8] == "https://"):
                congruence.checkUrl(self.syned_file_name)
                is_remote = True
            else:
                congruence.checkFile(self.syned_file_name)
                is_remote = False

            try:
                if is_remote: content = load_from_json_url(self.syned_file_name)
                else:         content = load_from_json_file(self.syned_file_name)

                if isinstance(content, LightSource):                                      light_source = content
                elif isinstance(content, Beamline) and not content._light_source is None: light_source = content._light_source
                else:                                                                     raise Exception("json file must contain a SYNED LightSource")

                self.check_magnetic_structure_instance(light_source.get_magnetic_structure())
                self.populate_fields(light_source)

                self.type_of_properties = 2 if self._check_dispersion_presence() else 1
                self.set_TypeOfProperties()
            except Exception as e:
                raise Exception("Error reading SYNED LightSource from file: " + str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

    def write_syned_file(self):
        try:
            self.check_data()
            congruence.checkDir(self.syned_file_name)
            light_source = self.get_light_source()

            if self._check_dispersion_reset():
                self.populate_fields(light_source)
                light_source.to_json(self.syned_file_name)

                QMessageBox.information(self, "File Read", "JSON file correctly written to disk", QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

    def _check_dispersion_reset(self):
        proceed = True
        if self.type_of_properties in [0, 1, 3] and self._check_dispersion_presence():
            if not ConfirmDialog.confirmed(parent=self, message="Dispersion parameters \u03B7, \u03B7' will be reset to zero, proceed?"):
                proceed = False
                self.type_of_properties = 2
                self.set_TypeOfProperties()
        return proceed

