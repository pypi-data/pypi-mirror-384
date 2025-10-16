import numpy
import os

from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from matplotlib import cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

import orangecanvas.resources as resources
from orangewidget import gui
from orangewidget.settings import Setting

from oasys2.widget.gui import FigureCanvas3D
from oasys2.widget import gui as oasysgui
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from shadow4.beamline.optical_elements.mirrors.s4_ellipsoid_mirror import S4EllipsoidMirror
from shadow4_advanced.benders.s4_fixed_rods_bender_ellipsoid_mirror import S4FixedRodsBenderEllipsoidMirrorElement, S4FixedRodsBenderEllipsoidMirror, \
    FixedRodsBenderFitParameters, BenderMovement, CalibrationParameters

from orangecontrib.shadow4.widgets.optics.ow_mirror import _OWMirror

import copy

class OWFixedRodsBenderMirror(_OWMirror):
    name        = "Fixed Rods Bender Mirror"
    description = "Fixed Rods Bender Mirror"
    icon        = "icons/fixed_rods_bender_mirror.png"

    priority = 1.2

    #########################################################
    # Bender
    #########################################################

    bender_bin_x     = Setting(100)
    bender_bin_y     = Setting(500)
    E                = Setting(131.0)
    h                = Setting(0.01)
    r                = Setting(0.012)
    l                = Setting(0.07)
    which_length     = Setting(0)
    optimized_length = Setting(0.0)
    n_fit_steps      = Setting(3)

    R0               = Setting(45)
    eta              = Setting(0.25)
    W2               = Setting(40.0)

    R0_out    = 0.0
    eta_out   = 0.0
    W2_out    = 0.0

    R0_fixed    = Setting(False)
    eta_fixed   = Setting(False)
    W2_fixed    = Setting(False)

    R0_min    = Setting(0.0)
    eta_min = Setting(0.0)
    W2_min     = Setting(0.0)

    R0_max    = Setting(1000.0)
    eta_max = Setting(10.0)
    W2_max     = Setting(1.0)

    alpha           = 0.0
    W0              = 0.0
    F_upstream      = 0.0
    F_downstream    = 0.0

    use_fitted_result_to_move_bender = Setting(0)
    use_calibration                  = Setting(0)

    q_downstream  = Setting(0.0)
    q_upstream    = Setting(0.0)

    p0_downstream = Setting(0.0)
    p1_downstream = Setting(0.0)
    p0_upstream   = Setting(0.0)
    p1_upstream   = Setting(0.0)

    pos_downstream = Setting(0.0)
    pos_upstream   = Setting(0.0)

    q_downstream_movement = 0.0
    q_upstream_movement   = 0.0

    F_upstream_movement = 0.0
    F_downstream_movement = 0.0

    show_bender_plots = Setting(0)

    help_path        = os.path.join(resources.package_dirname("orangecontrib.shadow4_advanced.widgets.tools"), "icons", "fixed_rods_bender_scheme.png")


    def __init__(self):
        super(OWFixedRodsBenderMirror, self).__init__(switch_icons=False)

        # FIXED SHAPE
        self.surface_shape_type       = 2 # Ellipsoid
        self.surface_shape_parameters = 0 # Internal
        self.surface_shape_tab_visibility(is_init=True)
        self.surface_shape_type_combo.setEnabled(False)
        self.surface_shape_parameters_combo.setEnabled(False)

        # FINITE DIMENSIONS
        self.is_infinite = 0
        self.dimensions_tab_visibility()
        self.is_infinite_combo.setEnabled(False)

        plot_tab = oasysgui.createTabPage(self.main_tabs, "Bender Plots")

        view_box = oasysgui.widgetBox(plot_tab, "Plotting Style", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box, self, "show_bender_plots", label="Show Plots", labelWidth=220,
                                            items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        bender_tabs = oasysgui.tabWidget(plot_tab)

        tabs = [oasysgui.createTabPage(bender_tabs, "Bender vs. Ideal (1D)"),
                oasysgui.createTabPage(bender_tabs, "Ideal - Bender (1D)"),
                oasysgui.createTabPage(bender_tabs, "Ideal - Bender (3D)"),
                oasysgui.createTabPage(bender_tabs, "Figure Error (3D)"),
                oasysgui.createTabPage(bender_tabs, "Ideal - Bender + Figure Error (3D)")]

        def create_figure_canvas(mode="3D"):
            figure = Figure(figsize=(100, 100))
            figure.patch.set_facecolor('white')
            if mode == "3D":
                ax = figure.add_subplot(111, projection='3d')
                figure_canvas = FigureCanvas3D(ax=ax, fig=figure)
            else:
                figure.add_subplot(111)
                figure_canvas = FigureCanvasQTAgg(figure)
            figure_canvas.setFixedWidth(self.IMAGE_WIDTH)
            figure_canvas.setFixedHeight(self.IMAGE_HEIGHT-10)

            return figure_canvas

        self.figure_canvas = [create_figure_canvas("1D"), create_figure_canvas("1D"),
                              create_figure_canvas("3D"), create_figure_canvas("3D"), create_figure_canvas("3D")]

        for tab, figure_canvas in zip(tabs, self.figure_canvas): tab.layout().addWidget(figure_canvas)

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def create_basic_settings_specific_subtabs(self, tabs_basic_setting): 
        specific_subtabs = [super(OWFixedRodsBenderMirror, self).create_basic_settings_specific_subtabs(tabs_basic_setting),
                            oasysgui.createTabPage(tabs_basic_setting, "Bender")]
        
        return specific_subtabs

    def populate_basic_settings_specific_subtabs(self, specific_subtabs):
        super(OWFixedRodsBenderMirror, self).populate_basic_settings_specific_subtabs(specific_subtabs[0])
        
        subtab_bender = specific_subtabs[1]

        #########################################################
        # Bender
        #########################################################
        self.populate_tab_bender(subtab_bender)
    
    def populate_tab_bender(self, subtab_bender):
        tabs = gui.tabWidget(subtab_bender)

        tab_bender = oasysgui.createTabPage(tabs, "Bender Setting")

        surface_box = oasysgui.widgetBox(tab_bender, "Surface Setting", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(surface_box, self, "bender_bin_x", "bins Sagittal", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(surface_box, self, "bender_bin_y", "bins Transversal", labelWidth=260, valueType=int, orientation="horizontal")

        material_box = oasysgui.widgetBox(tab_bender, "Bender Setting", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(material_box, self, "E", "Young's Modulus [GPa]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(material_box, self, "h", "Thickness [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(material_box, self, "l", "Inner Rods distance ", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(material_box, self, "r", "Inner/Outer Rods distance ", labelWidth=260, valueType=float, orientation="horizontal")

        help_box = oasysgui.widgetBox(tab_bender, "", addSpace=False, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.help_path).scaledToWidth(340))

        help_box.layout().addWidget(label)

        tab_fit = oasysgui.createTabPage(tabs, "Fit Setting")

        self.fit_box = oasysgui.widgetBox(tab_fit, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.fit_box, self, "n_fit_steps", "Nr. fit steps", labelWidth=250, valueType=int, orientation="horizontal")

        length_box = oasysgui.widgetBox(self.fit_box, "", addSpace=False, orientation="horizontal")

        self.cb_optimized_length = gui.comboBox(length_box, self, "which_length", label="Optimized Length ", items=["Total", "Partial"],
                                                labelWidth=150, orientation="horizontal", callback=self.set_which_length)
        self.le_optimized_length = oasysgui.lineEdit(length_box, self, "optimized_length", " ", labelWidth=10, valueType=float, orientation="horizontal")
        self.set_which_length()

        gui.separator(self.fit_box)

        def add_parameter_box(container_box, variable, label):
            box = oasysgui.widgetBox(container_box, "", addSpace=False, orientation="horizontal")
            oasysgui.lineEdit(box, self, variable, label, labelWidth=60, valueType=float, orientation="horizontal")
            gui.label(box, self, " ", labelWidth=58)

            box = oasysgui.widgetBox(container_box, "", addSpace=False, orientation="horizontal")

            setattr(self, "le_" + variable + "_min", oasysgui.lineEdit(box, self, variable + "_min", "Min", labelWidth=60, valueType=float, orientation="horizontal"))
            setattr(self, "le_" + variable + "_max", oasysgui.lineEdit(box, self, variable + "_max", "Max", labelWidth=35, valueType=float, orientation="horizontal"))

            gui.checkBox(box, self, variable + "_fixed", "Fixed", callback=getattr(self, "set_" + variable))

            box = oasysgui.widgetBox(container_box, "", addSpace=False, orientation="horizontal")

            le = oasysgui.lineEdit(box, self, variable + "_out", "Fitted", labelWidth=60, valueType=float, orientation="horizontal")
            le.setEnabled(False)
            le.setStyleSheet("color: blue; background-color: rgb(254, 244, 205); font:bold")

            def set_variable_fit(): setattr(self, variable, getattr(self, variable + "_out"))
            gui.button(box, self, "<- Use", width=58, callback=set_variable_fit)

            getattr(self, "set_" + variable)()

        R0_box = oasysgui.widgetBox(self.fit_box, "", addSpace=False, orientation="vertical")
        gui.separator(self.fit_box, 10)
        eta_box = oasysgui.widgetBox(self.fit_box, "", addSpace=False, orientation="vertical")
        gui.separator(self.fit_box, 10)
        W2_box = oasysgui.widgetBox(self.fit_box, "", addSpace=False, orientation="vertical")
        gui.separator(self.fit_box, 10)

        add_parameter_box(R0_box, "R0",   "R0 [m]")
        add_parameter_box(eta_box, "eta", "\u03b7")
        add_parameter_box(W2_box, "W2",   "W2 [m]")

        box = oasysgui.widgetBox(tab_fit, "", addSpace=False, orientation="vertical")

        gui.comboBox(box, self, "use_fitted_result_to_move_bender", label="Use Fit Result to move the Bender ", items=["No", "Yes"],
                     labelWidth=250, orientation="horizontal", callback=self.set_use_fitted_result_to_move_bender)

        self.tab_mov = oasysgui.createTabPage(tabs, "Movements")

        gui.comboBox(self.tab_mov, self, "use_calibration", label="Use calibration to move the Bender ", items=["No", "Yes"],
                     labelWidth=250, orientation="horizontal", callback=self.set_use_calibration)

        self.mov_box_nocal = oasysgui.widgetBox(self.tab_mov, "", addSpace=False, orientation="vertical")
        self.mov_box_cal   = oasysgui.widgetBox(self.tab_mov, "", addSpace=False, orientation="vertical")

        # ---- NO CALIBRATION

        self.mov_box_nocal_1 = oasysgui.widgetBox(self.mov_box_nocal, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.mov_box_nocal_1, self, "q_upstream", "Upstream Focus Position [m]", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mov_box_nocal_1, self, "q_downstream", "Downstream Focus Position [m]", labelWidth=250, valueType=float, orientation="horizontal")

        le = oasysgui.lineEdit(self.mov_box_nocal_1, self, "F_upstream_movement", "Fu [N]", labelWidth=250, valueType=float, orientation="horizontal")
        le.setEnabled(False)
        le.setStyleSheet("color: blue; background-color: rgb(254, 244, 205); font:bold")
        le = oasysgui.lineEdit(self.mov_box_nocal_1, self, "F_downstream_movement", "Fd [N]", labelWidth=250, valueType=float, orientation="horizontal")
        le.setEnabled(False)
        le.setStyleSheet("color: blue; background-color: rgb(254, 244, 205); font:bold")

        # ---- CALIBRATION

        self.mov_box_cal_1 = oasysgui.widgetBox(self.mov_box_cal, "", addSpace=False, orientation="vertical")

        box = oasysgui.widgetBox(self.mov_box_cal_1, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(box, self, "p0_upstream",  "Upstream 1/q = P0", labelWidth=130, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "p1_upstream", "\u00b7pos + P1", labelWidth=60, valueType=float, orientation="horizontal")

        box = oasysgui.widgetBox(self.mov_box_cal_1, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(box, self, "p0_downstream",  "Downstream 1/q = P0", labelWidth=130, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "p1_downstream", "\u00b7pos + P1", labelWidth=60, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.mov_box_cal_1, self, "pos_upstream", "Upstream Motor", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mov_box_cal_1, self, "pos_downstream", "Downstream Motor", labelWidth=250, valueType=float, orientation="horizontal")

        le = oasysgui.lineEdit(self.mov_box_cal_1, self, "F_upstream_movement", "Fu [N]", labelWidth=250, valueType=float, orientation="horizontal")
        le.setEnabled(False)
        le.setStyleSheet("color: blue; background-color: rgb(254, 244, 205); font:bold")
        le = oasysgui.lineEdit(self.mov_box_cal_1, self, "F_downstream_movement", "Fd [N]", labelWidth=250, valueType=float, orientation="horizontal")
        le.setEnabled(False)
        le.setStyleSheet("color: blue; background-color: rgb(254, 244, 205); font:bold")

        le = oasysgui.lineEdit(self.mov_box_cal_1, self, "q_upstream_movement", "Upstream Focus Position [m]", labelWidth=250, valueType=float, orientation="horizontal")
        le.setEnabled(False)
        le.setStyleSheet("color: blue; background-color: rgb(254, 244, 205); font:bold")
        le = oasysgui.lineEdit(self.mov_box_cal_1, self, "q_downstream_movement", "Downstream Focus Position [m]", labelWidth=250, valueType=float, orientation="horizontal")
        le.setEnabled(False)
        le.setStyleSheet("color: blue; background-color: rgb(254, 244, 205); font:bold")

        self.set_use_calibration()
        self.set_use_fitted_result_to_move_bender()

    def set_use_calibration(self):
        self.mov_box_nocal.setVisible(self.use_calibration==0)
        self.mov_box_cal.setVisible(self.use_calibration==1)

    def set_use_fitted_result_to_move_bender(self):
        self.fit_box.setEnabled(self.use_fitted_result_to_move_bender==0)
        self.tab_mov.setEnabled(self.use_fitted_result_to_move_bender==1)

    def set_which_length(self):
        self.le_optimized_length.setEnabled(self.which_length == 1)

    def set_R0(self):
        self.le_R0_min.setEnabled(self.R0_fixed == False)
        self.le_R0_max.setEnabled(self.R0_fixed == False)

    def set_eta(self):
        self.le_eta_min.setEnabled(self.eta_fixed == False)
        self.le_eta_max.setEnabled(self.eta_fixed == False)

    def set_W2(self):
        self.le_W2_min.setEnabled(self.W2_fixed == False)
        self.le_W2_max.setEnabled(self.W2_fixed == False)

    #########################################################
    # S4 objects
    #########################################################

    def _post_trace_operations(self, output_beam, footprint, element, beamline):
        bender_data = element.get_optical_element().get_bender_data()

        if self.use_fitted_result_to_move_bender == 0:
            self.R0_out  = round(bender_data.R0_out, 4)
            self.eta_out = round(bender_data.eta_out, 5)
            self.W2_out  = round(bender_data.W2_out, 5)
            # output
            self.alpha        = round(bender_data.alpha, 6)
            self.W0           = round(bender_data.W0, 5)
            self.F_upstream   = round(bender_data.F_upstream, 4)
            self.F_downstream = round(bender_data.F_downstream, 4)
        else:
            self.F_upstream_movement   = round(bender_data.F_upstream, 4)
            self.F_downstream_movement = round(bender_data.F_downstream, 4)

            if self.use_calibration==1:
                def get_q(pos, p0, p1): return round(1/(p0*pos + p1), 6)

                self.q_downstream_movement = get_q(self.pos_downstream, self.p0_downstream, self.p1_downstream)
                self.q_upstream_movement   = get_q(self.pos_upstream, self.p0_upstream, self.p1_upstream)

    def _plot_additional_results(self, output_beam, footprint, element, beamline):
        if self.show_bender_plots == 1:
            bender_data = element.get_optical_element().get_bender_data()

            self.plot1D(bender_data.y, bender_data.bender_profile, y_values_2=bender_data.ideal_profile,
                        index=0, title=bender_data.titles[0], um=1)
            self.plot1D(bender_data.y, bender_data.correction_profile,
                        index=1, title=bender_data.titles[1])

            self.plot3D(bender_data.x,
                        bender_data.y,
                        bender_data.z_bender_correction_no_figure_error,
                        index=2, title="Ideal - Bender Surfaces")

            if self.modified_surface > 0:
                self.plot3D(bender_data.x,
                            bender_data.y,
                            bender_data.z_figure_error,  index=3, title="Figure Error Surface")
                self.plot3D(bender_data.x,
                            bender_data.y,
                            bender_data.z_bender_correction, index=4, title="Ideal - Bender + Figure Error Surfaces")


    def get_optical_element_instance(self):
        if self.modified_surface: self.congruence_surface_data_file()

        reflectivity_source = self.reflectivity_source if self.reflectivity_source < 5 else 6 # no more xraylib

        ellipsoid_mirror = S4EllipsoidMirror(
                name="Flexural Hinge Bender Mirror",
                boundary_shape=self.get_boundary_shape(),
                surface_calculation=self.surface_shape_parameters, # INTERNAL = 0  EXTERNAL = 1
                is_cylinder=self.is_cylinder,
                cylinder_direction=self.cylinder_orientation, #  Direction:  TANGENTIAL = 0  SAGITTAL = 1
                convexity=numpy.logical_not(self.surface_curvature).astype(int), #  Convexity: NONE = -1  UPWARD = 0  DOWNWARD = 1
                min_axis=self.ellipse_hyperbola_semi_minor_axis * 2, # todo: check factor 2
                maj_axis=self.ellipse_hyperbola_semi_major_axis * 2, # todo: check factor 2
                pole_to_focus=self.angle_of_majax_and_pole, # todo: change variable name
                p_focus=self.get_focusing_p(),
                q_focus=self.get_focusing_q(),
                grazing_angle=self.get_focusing_grazing_angle(),
                # inputs related to mirror reflectivity
                f_reflec=self.reflectivity_flag,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                f_refl=reflectivity_source,  # 0=prerefl file
                                           # 1=electric susceptibility
                                           # 2=user defined file (1D reflectivity vs angle)
                                           # 3=user defined file (1D reflectivity vs energy)
                                           # 4=user defined file (2D reflectivity vs energy and angle)
                                           # 5=direct calculation using xraylib
                                           # 6=direct calculation using dabax
                file_refl=self.file_refl,  # preprocessor file fir f_refl=0,2,3,4
                refraction_index=1 - self.refraction_index_delta + 1j * self.refraction_index_beta,
                # refraction index (complex) for f_refl=1
                coating_material=self.coating_material,    # string with coating material formula for f_refl=5,6
                coating_density=self.coating_density,      # coating material density for f_refl=5,6
                coating_roughness=self.coating_roughness,  # coating material roughness in A for f_refl=5,6
                )

        if self.use_fitted_result_to_move_bender == 0:
            fit_to_focus_parameters = FixedRodsBenderFitParameters(optimized_length = self.optimized_length if self.which_length==1 else None,
                                                                   n_fit_steps      = self.n_fit_steps,
                                                                   R0               = self.R0,
                                                                   R0_max           = self.R0_max,
                                                                   R0_min           = self.R0_min,
                                                                   R0_fixed         = self.R0_fixed,
                                                                   eta              = self.eta,
                                                                   eta_max          = self.eta_max,
                                                                   eta_min          = self.eta_min,
                                                                   eta_fixed        = self.eta_fixed,
                                                                   W2               = self.W2,
                                                                   W2_max           = self.W2_max,
                                                                   W2_min           = self.W2_min,
                                                                   W2_fixed         = self.W2_fixed)

            return S4FixedRodsBenderEllipsoidMirror(ellipsoid_mirror=ellipsoid_mirror,
                                                    figure_error_data_file=self.ms_defect_file_name if self.modified_surface else None,
                                                    bender_bin_x=self.bender_bin_x,
                                                    bender_bin_y=self.bender_bin_y,
                                                    E=self.E*1e9,
                                                    h=self.h,
                                                    r=self.r,
                                                    l=self.l,
                                                    fit_to_focus_parameters=fit_to_focus_parameters)
        else:
            if self.use_calibration == 0:
                bender_movement = BenderMovement(position_upstream=self.q_upstream, position_downstream=self.q_downstream)

                return S4FixedRodsBenderEllipsoidMirror(ellipsoid_mirror=ellipsoid_mirror,
                                                        figure_error_data_file=self.ms_defect_file_name if self.modified_surface else None,
                                                        bender_bin_x=self.bender_bin_x,
                                                        bender_bin_y=self.bender_bin_y,
                                                        E=self.E*1e9,
                                                        h=self.h,
                                                        r=self.r,
                                                        l=self.l,
                                                        R0=self.R0,
                                                        eta=self.eta,
                                                        W2=self.W2,
                                                        bender_movement=bender_movement)
            else:
                calibration_parameters = CalibrationParameters(parameters_upstream=[self.p0_upstream, self.p1_upstream],
                                                               parameters_downstream=[self.p0_downstream, self.p1_downstream])

                bender_movement = BenderMovement(position_upstream=self.pos_upstream, position_downstream=self.pos_downstream)

                return S4FixedRodsBenderEllipsoidMirror(ellipsoid_mirror=ellipsoid_mirror,
                                                            figure_error_data_file=self.ms_defect_file_name if self.modified_surface else None,
                                                            bender_bin_x=self.bender_bin_x,
                                                            bender_bin_y=self.bender_bin_y,
                                                            E=self.E*1e9,
                                                            h=self.h,
                                                            r=self.r,
                                                            l=self.l,
                                                            R0=self.R0,
                                                            eta=self.eta,
                                                            W2=self.W2,
                                                            calibration_parameters=calibration_parameters,
                                                            bender_movement=bender_movement)

    def get_beamline_element_instance(self): return S4FixedRodsBenderEllipsoidMirrorElement()

    def plot1D(self, x_coords, y_values, y_values_2=None, index=0, title="", um=0):
        if self.show_bender_plots == 1:
            figure = self.figure_canvas[index].figure

            axis = figure.gca()
            axis.clear()

            axis.set_xlabel("Y [mm]")
            axis.set_ylabel("Z [" + ("nm" if um == 0 else "\u03bcm") + "]")
            axis.set_title(title)

            axis.plot(x_coords * 1e3, y_values * (1e9 if um == 0 else 1e6), color="blue", label="bender", linewidth=2)
            if not y_values_2 is None: axis.plot(x_coords * 1e3, y_values_2 * (1e9 if um == 0 else 1e6), "-.r", label="ideal")

            axis.legend(loc=0, fontsize='small')

            figure.canvas.draw()

    def plot3D(self, x_coords, y_coords, z_values, index, title=""):
        if self.show_bender_plots == 1:
            figure = self.figure_canvas[index].figure
            x_to_plot, y_to_plot = numpy.meshgrid(x_coords, y_coords)
            z_to_plot = z_values.T

            axis = figure.gca()
            axis.clear()

            axis.set_xlabel("X [mm]")
            axis.set_ylabel("Y [mm]")
            axis.set_zlabel("Z [nm]")
            axis.set_title(title)

            axis.plot_surface(x_to_plot * 1e3,
                              y_to_plot * 1e3 ,
                              z_to_plot * 1e9,
                              rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            figure.canvas.draw()

            axis.mouse_init()

add_widget_parameters_to_module(__name__)