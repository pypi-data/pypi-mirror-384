__author__ = 'labx'

import sys, numpy

from AnyQt.QtWidgets import QMessageBox
from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Input, Output

from oasys2.widget.widget import OWAction
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.util.widget_util import EmittingStream
from oasys2.widget.util.widget_objects import TriggerOut
from oasys2.widget.gui import ConfirmDialog

from syned.beamline.optical_elements.absorbers.slit import Slit
from syned.storage_ring.light_source import ElectronBeam, LightSource
from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.shape import Rectangle

from wofrysrw.propagator.wavefront2D.srw_wavefront import WavefrontParameters, WavefrontPrecisionParameters, PolarizationComponent
from wofrysrw.storage_ring.srw_electron_beam import SRWElectronBeam
from wofrysrw.beamline.srw_beamline import SRWBeamline

from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

class OWSRWSource(SRWWavefrontViewer, WidgetDecorator):
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    class Inputs:
        syned_data = WidgetDecorator.syned_input_data(multi_input=True)
        trigger    = Input("Trigger", TriggerOut, id="Trigger", default=True, auto_summary=False)

    class Outputs:
        srw_data = Output("SRWData", SRWData, id="SRWData", default=True, auto_summary=False)

    want_main_area=1

    source_name = None

    electron_energy_in_GeV = Setting(6.0)
    electron_energy_spread = Setting(0.00138)
    ring_current = Setting(0.2)
    electron_beam_size_h = Setting(1.48e-05)
    electron_beam_size_v = Setting(3.7e-06)
    electron_beam_divergence_h = Setting(2.8e-06)
    electron_beam_divergence_v = Setting(1.5e-06)

    moment_x = Setting(0.0)
    moment_y = Setting(0.0)
    moment_z = Setting(0.0)
    moment_xp = Setting(0.0)
    moment_yp = Setting(0.0)

    moment_xx           = Setting((1.48e-05)**2)
    moment_xxp          = Setting(0.0)
    moment_xpxp         = Setting((2.8e-06)**2)
    moment_yy           = Setting((3.7e-06)**2)
    moment_yyp          = Setting(0.0)
    moment_ypyp         = Setting((1.5e-06)**2)

    horizontal_emittance = Setting(0.0)
    horizontal_beta      = Setting(0.0)
    horizontal_alpha     = Setting(0.0)
    horizontal_eta       = Setting(0.0)
    horizontal_etap      = Setting(0.0)
    vertical_emittance   = Setting(0.0)
    vertical_beta        = Setting(0.0)
    vertical_alpha       = Setting(0.0)
    vertical_eta         = Setting(0.0)
    vertical_etap        = Setting(0.0)

    type_of_properties = Setting(1)
    type_of_initialization = Setting(0)

    wf_energy_type = Setting(0)
    wf_photon_energy = Setting(8000.0)
    wf_photon_energy_to=Setting(8100.0)
    wf_photon_energy_points=Setting(11)
    wf_h_slit_gap = Setting(0.001)
    wf_v_slit_gap =Setting( 0.001)
    wf_h_slit_c = Setting(0.0)
    wf_v_slit_c =Setting( 0.0)
    wf_h_slit_points=Setting(100)
    wf_v_slit_points=Setting(100)
    wf_distance = Setting(10.0)
    wf_units = Setting(1)

    wf_sr_method = Setting(1)
    wf_relative_precision = Setting(0.01)
    wf_start_integration_longitudinal_position = Setting(0.0) 
    wf_end_integration_longitudinal_position = Setting(0.0) 
    wf_number_of_points_for_trajectory_calculation = Setting(50000)
    wf_use_terminating_terms = Setting(1)
    wf_sampling_factor_for_adjusting_nx_ny = Setting(0.0)

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

    def __init__(self):
        super().__init__(show_general_option_box=False, show_automatic_box=False)

        self.runaction = OWAction("Run SRW", self)
        self.runaction.triggered.connect(self.runSRWSource)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run SRW Source", callback=self.runSRWSource)
        button.setStyleSheet("color: darkblue; font-weight: bold; height: 45px;")

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        button.setStyleSheet("color: darkred; font-weight: bold; font-style: italic; height: 45px; width: 150px;")

        gui.separator(self.controlArea)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_source = oasysgui.createTabPage(self.tabs_setting, "Light Source Setting")

        left_box_1 = oasysgui.widgetBox(self.tab_source, "Electron Beam Parameters", addSpace=True, orientation="vertical", height=380)

        oasysgui.lineEdit(left_box_1, self, "electron_energy_in_GeV", "Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal", callback=self.callback_electron_energy)
        oasysgui.lineEdit(left_box_1, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "ring_current", "Ring Current [A]", labelWidth=260, valueType=float, orientation="horizontal")

        tab_electron = oasysgui.tabWidget(left_box_1)

        tab_beam = oasysgui.createTabPage(tab_electron, "Beam")
        tab_traj = oasysgui.createTabPage(tab_electron, "Trajectory")

        gui.comboBox(tab_beam, self, "type_of_properties", label="Electron Beam Properties", labelWidth=350,
                     items=["From 2nd Moments", "From Size/Divergence", "From Twiss"],
                     callback=self.set_TypeOfProperties,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_2_1 = oasysgui.widgetBox(tab_beam, "", addSpace=False, orientation="vertical", height=190)

        gui.separator(self.left_box_2_1, height=2)

        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xx", "\u03c3x\u22c5\u03c3x   [m\u00b2]",     labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xxp", "\u03c3x\u22c5\u03c3x'  [m\u22c5rad]", labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xpxp", "\u03c3x'\u22c5\u03c3x' [rad\u00b2]", labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yy", "\u03c3y\u22c5\u03c3y   [m\u00b2]",     labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yyp", "\u03c3y\u22c5\u03c3y'  [m\u22c5rad]", labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_ypyp", "\u03c3y'\u22c5\u03c3y' [rad\u00b2]", labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        lbl = oasysgui.widgetLabel(self.left_box_2_1, "Note: 2nd Moments do not include dispersion")
        lbl.setStyleSheet("color: darkblue; font-weight: bold;")

        self.left_box_2_2 = oasysgui.widgetBox(tab_beam, "", addSpace=False, orientation="vertical", height=190)

        gui.separator(self.left_box_2_2, height=2)

        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_h",       "\u03c3x [m]",    labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_v",       "\u03c3y [m]",    labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_h", "\u03c3x' [rad]", labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_v", "\u03c3y' [rad]", labelWidth=200, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        lbl = oasysgui.widgetLabel(self.left_box_2_2, "Note: Size/Divergence do not include dispersion")
        lbl.setStyleSheet("color: darkblue; font-weight: bold;")

        self.left_box_2_3 = oasysgui.widgetBox(tab_beam, "", addSpace=False, orientation="horizontal", height=190)

        left_box_2_3_l = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical", height=190)
        left_box_2_3_r = oasysgui.widgetBox(self.left_box_2_3, "", addSpace=False, orientation="vertical", height=190)

        gui.separator(left_box_2_3_l, height=2)
        gui.separator(left_box_2_3_r, height=2)

        oasysgui.lineEdit(left_box_2_3_l, self, "horizontal_emittance", "Emittance x [m]",   labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_l, self, "horizontal_alpha"    , "\u03B1x [rad]"    , labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_l, self, "horizontal_beta"     , "\u03B2x [m]"    ,   labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_l, self, "horizontal_eta"      , "\u03B7x [m]"    ,   labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_l, self, "horizontal_etap"     , "\u03B7x' [rad]"   , labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_r, self, "vertical_emittance"  , "Emittance y [m]",   labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_r, self, "vertical_alpha"      , "\u03B1y [rad]"    , labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_r, self, "vertical_beta"       , "\u03B2y [m]"    ,   labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_r, self, "vertical_eta"        , "\u03B7y [m]"    ,   labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)
        oasysgui.lineEdit(left_box_2_3_r, self, "vertical_etap"       , "\u03B7y' [rad]"   , labelWidth=100, valueType=float, orientation="horizontal", callback=self._electron_beam_modified)

        self.left_box_2_4 = oasysgui.widgetBox(tab_beam, "", addSpace=False, orientation="horizontal", height=190)

        self.set_TypeOfProperties()

        gui.comboBox(tab_traj, self, "type_of_initialization", label="Trajectory Initialization", labelWidth=140,
                     items=["Automatic", "At Fixed Position", "Sampled from Phase Space"],
                     callback=self.set_TypeOfInitialization,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_3_1 = oasysgui.widgetBox(tab_traj, "", addSpace=False, orientation="vertical", height=160)
        self.left_box_3_2 = oasysgui.widgetBox(tab_traj, "", addSpace=False, orientation="vertical", height=160)

        oasysgui.lineEdit(self.left_box_3_1, self, "moment_x", "x\u2080 [m]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_3_1, self, "moment_y", "y\u2080 [m]", labelWidth=200, valueType=float, orientation="horizontal")

        box = oasysgui.widgetBox(self.left_box_3_1, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(box, self, "moment_z", "z\u2080 [m]", labelWidth=160, valueType=float, orientation="horizontal")
        gui.button(box, self, "Auto", width=35, callback=self.set_z0Default)


        oasysgui.lineEdit(self.left_box_3_1, self, "moment_xp", "x'\u2080 [rad]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_3_1, self, "moment_yp", "y'\u2080 [rad]", labelWidth=200, valueType=float, orientation="horizontal")

        self.set_TypeOfInitialization()

        self.tab_plots = oasysgui.createTabPage(self.tabs_setting, "Wavefront Setting")

        self.tabs_plots_setting = oasysgui.tabWidget(self.tab_plots)
        
        # PROPAGATION -------------------------------------------
        
        tab_wav = oasysgui.createTabPage(self.tabs_plots_setting, "Propagation")

        wav_box = oasysgui.widgetBox(tab_wav, "Wavefront Parameters", addSpace=True, orientation="vertical", height=285)

        self.build_wf_photon_energy_box(wav_box)
        box = oasysgui.widgetBox(wav_box, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(box, self, "wf_h_slit_gap", "H Slit Gap [m]", labelWidth=130, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "wf_h_slit_c", "  Center [m]", labelWidth=50, valueType=float, orientation="horizontal")
        box = oasysgui.widgetBox(wav_box, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(box, self, "wf_v_slit_gap", "V Slit Gap [m]", labelWidth=130, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "wf_v_slit_c", "  Center [m]", labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_h_slit_points", "H Slit Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_v_slit_points", "V Slit Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_distance", "Propagation Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(wav_box, self, "wf_units", label="Intensity Units", labelWidth=90,
                     items=["Arbitrary", "phot/s/0.1%bw/mm\u00B2", "J/eV/mm\u00B2 (frequency) or W/mm\u00B2 (time)"],
                     sendSelectedValue=False, orientation="horizontal")

        pre_box = oasysgui.widgetBox(tab_wav, "Precision Parameters", addSpace=False, orientation="vertical")

        gui.comboBox(pre_box, self, "wf_sr_method", label="Calculation Method",
                     items=self.get_calculation_method_items(), labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(pre_box, self, "wf_relative_precision", "Relative Precision", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(pre_box, self, "wf_start_integration_longitudinal_position", "Longitudinal position to start integration\n(effective if < zEndInteg) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(pre_box, self, "wf_end_integration_longitudinal_position", "Longitudinal position to finish integration\n(effective if > zStartInteg) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(pre_box, self, "wf_number_of_points_for_trajectory_calculation", "Number of points for trajectory calculation", labelWidth=260, valueType=int, orientation="horizontal")

        gui.comboBox(pre_box, self, "wf_use_terminating_terms", label="Use \"terminating terms\" or not",
                     items=["No", "Yes"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(pre_box, self, "wf_sampling_factor_for_adjusting_nx_ny", "Sampling factor for adjusting nx/ny\n(effective if > 0)", labelWidth=260, valueType=float, orientation="horizontal")

        gui.rubber(self.controlArea)

    def get_calculation_method_items(self):
        return ["Manual", "Auto-Undulator", "Auto-Wiggler"]

    def set_TypeOfProperties(self):
        self.left_box_2_1.setVisible(self.type_of_properties==0)
        self.left_box_2_2.setVisible(self.type_of_properties==1)
        self.left_box_2_3.setVisible(self.type_of_properties==2)
        self.left_box_2_4.setVisible(self.type_of_properties==3)

    def set_TypeOfInitialization(self):
        self.left_box_3_1.setVisible(self.type_of_initialization==1)
        self.left_box_3_2.setVisible(self.type_of_initialization!=1)

    def build_wf_photon_energy_box(self, box):
        gui.comboBox(box, self, "wf_energy_type", label="Energy Setting",
                     items=["Single Value", "Range"], labelWidth=260,
                     callback=self.set_WFEnergyType, sendSelectedValue=False, orientation="horizontal")

        self.energy_type_box_1 = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", height=50)
        oasysgui.lineEdit(self.energy_type_box_1, self, "wf_photon_energy", "Photon Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        self.energy_type_box_2 = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", height=50)
        energy_box = oasysgui.widgetBox(self.energy_type_box_2, "", addSpace=False, orientation="horizontal", height=25)
        oasysgui.lineEdit(energy_box, self, "wf_photon_energy", "Photon Energy from [eV]", labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(energy_box, self, "wf_photon_energy_to", "to", labelWidth=20, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.energy_type_box_2, self, "wf_photon_energy_points", "Nr. of Energy values", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_WFEnergyType()

    def set_WFEnergyType(self):
        self.energy_type_box_1.setVisible(self.wf_energy_type==0)
        self.energy_type_box_2.setVisible(self.wf_energy_type==1)

    def runSRWSource(self):
        self.setStatusMessage("")
        self.progressBarInit()

        try:
            self.check_data()
            electron_beam = self.get_electron_beam()

            if not electron_beam is None: # User decided to stop the calculation of the twiss from momenta or size/div
                srw_source      = self.get_srw_source(electron_beam)
                srw_source.name = self.source_name if not self.source_name is None else self.windowTitle(),

                self.progressBarSet(10)
                self.setStatusMessage("Running SRW")
                sys.stdout = EmittingStream(textWritten=self.writeStdOut)
                self.print_specific_infos(srw_source)
                self.progressBarSet(20)
                self.setStatusMessage("")

                beamline = SRWBeamline(light_source=srw_source)
                self.output_wavefront = self.calculate_wavefront_propagation(srw_source)

                if self.is_do_plots():
                    self.setStatusMessage("Plotting Results")
                    tickets = []
                    self.run_calculation_for_plots(tickets, 50)
                    self.plot_results(tickets, 80)

                self.setStatusMessage("")

                self.Outputs.srw_data.send(SRWData(srw_beamline=beamline, srw_wavefront=self.output_wavefront))

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

    @Inputs.trigger
    def sendNewWavefront(self, trigger):
        if trigger and trigger.new_object == True:
            self.runSRWSource()

    def get_electron_beam(self):
        if self.type_of_initialization == 2:
            electron_beam = SRWElectronBeam(energy_in_GeV=numpy.random.normal(self.electron_energy_in_GeV,
                                                                              self.electron_energy_spread*self.electron_energy_in_GeV),
                                            energy_spread=self.electron_energy_spread,
                                            current=self.ring_current)
        else:
            electron_beam = SRWElectronBeam(energy_in_GeV=self.electron_energy_in_GeV,
                                            energy_spread=self.electron_energy_spread,
                                            current=self.ring_current)
        
        # initialization of second moments
        if self.type_of_properties == 0:
            electron_beam.set_moments_all(moment_xx   = self.moment_xx,
                                          moment_xxp  = self.moment_xxp,
                                          moment_xpxp = self.moment_xpxp,
                                          moment_yy   = self.moment_yy,
                                          moment_yyp  = self.moment_yyp,
                                          moment_ypyp = self.moment_ypyp)
        elif self.type_of_properties == 1:
            electron_beam.set_sigmas_all(sigma_x  = self.electron_beam_size_h,
                                         sigma_y  = self.electron_beam_size_v,
                                         sigma_xp = self.electron_beam_divergence_h,
                                         sigma_yp = self.electron_beam_divergence_v)
        elif self.type_of_properties == 2:
            electron_beam.set_twiss_all(emittance_x = self.horizontal_emittance,
                                        alpha_x     = self.horizontal_alpha,
                                        beta_x      = self.horizontal_beta,
                                        emittance_y = self.vertical_emittance,
                                        alpha_y     = self.vertical_alpha,
                                        beta_y      = self.vertical_beta)
            electron_beam.set_dispersion_all(eta_x  = self.horizontal_eta,
                                             etap_x = self.horizontal_etap,
                                             eta_y  = self.vertical_eta,
                                             etap_y = self.vertical_etap)

        if self._check_dispersion_reset():
            # Trajectory intialization
            if self.type_of_initialization == 0: # zero
                self.moment_x  = 0.0
                self.moment_y  = 0.0
                self.moment_z  = self.get_default_initial_z()
                self.moment_xp = 0.0
                self.moment_yp = 0.0
            elif self.type_of_initialization == 2: # sampled
                self.moment_x  = numpy.random.normal(0.0, self.electron_beam_size_h)
                self.moment_y  = numpy.random.normal(0.0, self.electron_beam_size_v)
                self.moment_z  = self.get_default_initial_z()
                self.moment_xp = numpy.random.normal(0.0, self.electron_beam_divergence_h)
                self.moment_yp = numpy.random.normal(0.0, self.electron_beam_divergence_v)

            electron_beam.set_first_moments_all(self.moment_x,
                                                self.moment_xp,
                                                self.moment_y,
                                                self.moment_yp,
                                                self.moment_z)

            self.populate_fields_from_electron_beam(electron_beam)

            print("\n", "Electron Trajectory Initialization:")
            print("X0: ",  self.moment_x)
            print("Y0: ",  self.moment_y)
            print("Z0: ",  self.moment_z)
            print("XP0: ", self.moment_xp)
            print("YP0: ", self.moment_yp)
            print("E0: ",  self.electron_energy_in_GeV, "\n")

            return electron_beam
        else:
            return None

    def set_z0Default(self):
        self.moment_z = self.get_default_initial_z()

    def get_default_initial_z(self):
        return NotImplementedError()

    def get_srw_source(self, electron_beam=ElectronBeam()):
        raise NotImplementedError()

    def check_data(self):
        self.check_electron_beam()
        self.check_light_source_specific_fields()
        self.check_wavefront_fields()

        congruence.checkStrictlyPositiveNumber(self.wf_h_slit_gap, "Wavefront Propagation H Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.wf_v_slit_gap, "Wavefront Propagation V Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.wf_h_slit_points, "Wavefront Propagation H Slit Points")
        congruence.checkStrictlyPositiveNumber(self.wf_v_slit_points, "Wavefront Propagation V Slit Points")
        congruence.checkGreaterOrEqualThan(self.wf_distance, self.get_minimum_propagation_distance(),
                                           "Wavefront Propagation Distance", "Minimum Distance out of the Source: " + str(self.get_minimum_propagation_distance()))

        congruence.checkStrictlyPositiveNumber(self.wf_relative_precision, "Wavefront Propagation Relative Precision")
        congruence.checkStrictlyPositiveNumber(self.wf_number_of_points_for_trajectory_calculation, "Wavefront Propagation Number of points for trajectory calculation")
        congruence.checkPositiveNumber(self.wf_sampling_factor_for_adjusting_nx_ny, "Wavefront Propagation Sampling Factor for adjusting nx/ny")

    def check_electron_beam(self):
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV, "Energy")
        congruence.checkPositiveNumber(self.electron_energy_spread, "Energy Spread")
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
            congruence.checkPositiveNumber(self.horizontal_emittance, "Horizontal Emittance")
            congruence.checkPositiveNumber(self.vertical_emittance, "Vertical Emittance")
        if self.type_of_initialization == 2:
            congruence.checkNumber(self.moment_x, "x0")
            congruence.checkNumber(self.moment_xp, "xp0")
            congruence.checkNumber(self.moment_y, "y0")
            congruence.checkNumber(self.moment_yp, "yp0")
            congruence.checkNumber(self.moment_z, "z0")

    def check_light_source_specific_fields(self):
        raise NotImplementedError()

    def check_wavefront_fields(self):
        congruence.checkStrictlyPositiveNumber(self.wf_photon_energy, "Wavefront Propagation Photon Energy")

        if self.wf_energy_type == 1:
            self.wf_photon_energy_to     = congruence.checkStrictlyPositiveNumber(self.wf_photon_energy_to, "Photon Energy To")
            self.wf_photon_energy_points = congruence.checkStrictlyPositiveNumber(self.wf_photon_energy_points, "Nr. Energy Values")
            congruence.checkGreaterThan(self.wf_photon_energy_to, self.wf_photon_energy, "Photon Energy To", "Photon Energy From")

    def run_calculation_for_plots(self, tickets, progress_bar_value):
        if not self.output_wavefront is None:
            if self.view_type == 1:
                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=False)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

                self.progressBarSet(progress_bar_value)

                e, h, v, p = self.output_wavefront.get_phase()

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, p, tickets, int_phase=1)

                self.progressBarSet(progress_bar_value + 10)

                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=True)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

                self.progressBarSet(progress_bar_value + 20)
            elif self.view_type == 2:
                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=False, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_HORIZONTAL)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

                self.progressBarSet(progress_bar_value)

                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=False, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_VERTICAL)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

                #--

                e, h, v, p = self.output_wavefront.get_phase(polarization_component_to_be_extracted=PolarizationComponent.LINEAR_HORIZONTAL)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, p, tickets, int_phase=1)

                self.progressBarSet(progress_bar_value + 10)

                e, h, v, p = self.output_wavefront.get_phase(polarization_component_to_be_extracted=PolarizationComponent.LINEAR_VERTICAL)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, p, tickets, int_phase=1)

                #--

                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=True, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_HORIZONTAL)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

                self.progressBarSet(progress_bar_value + 20)

                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=True, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_VERTICAL)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

    def get_automatic_sr_method(self):
        return self.wf_sr_method

    def calculate_wavefront_propagation(self, srw_source):
        photon_energy_min, photon_energy_max,  photon_energy_points = self.get_photon_energy_for_wavefront_propagation(srw_source)

        wf_parameters = WavefrontParameters(photon_energy_min = photon_energy_min,
                                            photon_energy_max = photon_energy_max,
                                            photon_energy_points=photon_energy_points,
                                            h_slit_gap = self.wf_h_slit_gap,
                                            v_slit_gap = self.wf_v_slit_gap,
                                            h_slit_points=self.wf_h_slit_points,
                                            v_slit_points=self.wf_v_slit_points,
                                            h_position=self.wf_h_slit_c,
                                            v_position=self.wf_v_slit_c,
                                            distance = self.wf_distance,
                                            electric_field_units = self.wf_units,
                                            wavefront_precision_parameters=WavefrontPrecisionParameters(sr_method=0 if self.wf_sr_method == 0 else self.get_automatic_sr_method(),
                                                                                                        relative_precision=self.wf_relative_precision,
                                                                                                        start_integration_longitudinal_position=self.wf_start_integration_longitudinal_position,
                                                                                                        end_integration_longitudinal_position=self.wf_end_integration_longitudinal_position,
                                                                                                        number_of_points_for_trajectory_calculation=self.wf_number_of_points_for_trajectory_calculation,
                                                                                                        use_terminating_terms=self.wf_use_terminating_terms,
                                                                                                        sampling_factor_for_adjusting_nx_ny=self.wf_sampling_factor_for_adjusting_nx_ny))
        return srw_source.get_SRW_Wavefront(source_wavefront_parameters=wf_parameters)

    def get_photon_energy_for_wavefront_propagation(self, srw_source):
        if self.wf_energy_type == 0:
            return self.wf_photon_energy, self.wf_photon_energy, 1
        else:
            return self.wf_photon_energy, self.wf_photon_energy_to, self.wf_photon_energy_points

    def get_minimum_propagation_distance(self):
        return round(self.get_source_length()*1.01, 6)

    def get_source_length(self):
        raise NotImplementedError()

    @Inputs.syned_data
    def set_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.insert
    def insert_syned_data(self, index, syned_data):
        self.receive_syned_data(syned_data)

    @Inputs.syned_data.remove
    def remove_syned_data(self, index):
        pass

    def receive_syned_data(self, data):
        if not data is None:
            try:
                if data.get_beamline_elements_number() > 0:
                    slit_element = data.get_beamline_element_at(0)
                    slit = slit_element.get_optical_element()
                    coordinates = slit_element.get_coordinates()

                    if isinstance(slit, Slit) and isinstance(slit.get_boundary_shape(), Rectangle):
                        rectangle = slit.get_boundary_shape()

                        self.wf_h_slit_gap = rectangle._x_right - rectangle._x_left
                        self.wf_v_slit_gap = rectangle._y_top - rectangle._y_bottom
                        self.wf_distance = coordinates.p()

                        self.int_h_slit_gap = rectangle._x_right - rectangle._x_left
                        self.int_v_slit_gap = rectangle._y_top - rectangle._y_bottom
                        self.int_distance = coordinates.p()

                        self.spe_h_slit_gap = rectangle._x_right - rectangle._x_left
                        self.spe_v_slit_gap = rectangle._y_top - rectangle._y_bottom
                        self.spe_distance = coordinates.p()
                elif not data._light_source is None and isinstance(data._light_source, LightSource):
                    light_source = data._light_source

                    self.source_name = light_source._name
                    electron_beam    = light_source._electron_beam
                    
                    self.populate_fields_from_electron_beam(electron_beam)
                    self.receive_specific_syned_data(data)

                    self.type_of_properties = 2 if self._check_dispersion_presence() else 1
                    self.set_TypeOfProperties()
                else:
                    raise ValueError("Syned data not correct")
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

    def receive_specific_syned_data(self, data):
        raise NotImplementedError()

    def callback_electron_energy(self):
        pass

    def populate_fields_from_electron_beam(self, electron_beam):
        self.electron_energy_in_GeV = electron_beam.energy()
        self.electron_energy_spread = electron_beam._energy_spread
        self.ring_current           = electron_beam.current()

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

        if isinstance(electron_beam, SRWElectronBeam):
            moment_x,\
            moment_xp,\
            moment_y,\
            moment_yp,\
            moment_z = electron_beam.get_first_moments_all()

            self.moment_x  = round(moment_x, 10)
            self.moment_y  = round(moment_y, 10)
            self.moment_z  = round(moment_z, 10)
            self.moment_xp = round(moment_xp, 10)
            self.moment_yp = round(moment_yp, 10)

        x, xp, y, yp                 = electron_beam.get_sigmas_all()
        ex, ax, bx, ey, ay, by,      = electron_beam.get_twiss_all()
        eta_x, etap_x, eta_y, etap_y = electron_beam.get_dispersion_all()

        self.electron_beam_size_h       = round(x, 10)
        self.electron_beam_size_v       = round(y, 10)
        self.electron_beam_divergence_h = round(xp, 10)
        self.electron_beam_divergence_v = round(yp, 10)
        self.horizontal_emittance       = round(ex, 16)
        self.vertical_emittance         = round(ey, 16)
        self.horizontal_alpha           = round(ax, 6)
        self.vertical_alpha             = round(ay, 6)
        self.horizontal_beta            = round(bx, 6)
        self.vertical_beta              = round(by, 6)
        self.horizontal_eta             = round(eta_x, 8)
        self.vertical_eta               = round(eta_y, 8)
        self.horizontal_etap            = round(etap_x, 8)
        self.vertical_etap              = round(etap_y, 8)

    def _check_dispersion_presence(self):
        return self.horizontal_eta != 0.0 or \
               self.vertical_eta != 0.0 or \
               self.horizontal_etap != 0.0 or \
               self.vertical_etap != 0.0

    def _check_dispersion_reset(self):
        proceed = True
        if self.type_of_properties in [0, 1, 3] and self._check_dispersion_presence():
            if not ConfirmDialog.confirmed(parent=self, message="Dispersion parameters \u03B7, \u03B7' will be reset to zero, proceed?"):
                proceed = False
                self.type_of_properties = 2
                self.set_TypeOfProperties()
        return proceed

    def _electron_beam_modified(self):
        try:
            self.check_electron_beam()
            if self._check_dispersion_reset():
                self.populate_fields_from_electron_beam(self.get_electron_beam())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)
            if self.IS_DEVELOP: raise e
