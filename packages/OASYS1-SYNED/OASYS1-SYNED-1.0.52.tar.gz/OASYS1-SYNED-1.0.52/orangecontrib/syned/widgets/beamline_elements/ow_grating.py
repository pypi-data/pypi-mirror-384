
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.syned.widgets.gui.ow_optical_element import OWOpticalElementWithSurfaceShape
from orangewidget import gui

from syned.beamline.optical_elements.gratings.grating import Grating, GratingVLS, GratingBlaze, GratingLamellar

from numpy import pi


class OWGrating(OWOpticalElementWithSurfaceShape):

    name = "Grating"
    description = "Syned: Grating"
    icon = "icons/grating.png"
    priority = 8

    ruling_at_center = Setting(800e3)

    coating_flag = 0
    coating_material = Setting("Pt")
    coating_thickness = Setting(0.0)

    grating_kind = 0 # 0=Undefined, 1=Lamellar, 2=Blaze
    ruling_type = 0 # 0=constant, 1=VLS
    vls_coeff_1 = Setting(0.0)
    vls_coeff_2 = Setting(0.0)
    vls_coeff_3 = Setting(0.0)
    vls_coeff_4 = Setting(0.0)

    lamellar_height = 1e-6
    lamellar_ratio = 0.5
    angle_blaze_deg = 0.2
    angle_antiblaze_deg = 90.0

    def __init__(self):
        super().__init__()

    def draw_specific_box(self):

        self.tab_shape = oasysgui.createTabPage(self.tabs_setting, "Surface Shape")
        self.tab_gra = oasysgui.createTabPage(self.tabs_setting, "Grating Setting")

        super().draw_specific_box(self.tab_shape)

        self.ruling_box = oasysgui.widgetBox(self.tab_gra, "Ruling", addSpace=True, orientation="vertical")



        gui.comboBox(self.ruling_box, self, "ruling_type", label="Ruling type", labelWidth=350,
                     items=["Constant", "Variable Line Spacing (VLS)"],
                     callback=self.set_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.ruling_box, self, "ruling_at_center", "Ruling at Center [lines/m]", labelWidth=180, valueType=float, orientation="horizontal")


        self.ruling_subbox = oasysgui.widgetBox(self.ruling_box, "", addSpace=False, orientation="horizontal",)
        ruling_subbox_left = oasysgui.widgetBox(self.ruling_subbox, "", addSpace=False, orientation="vertical",)
        ruling_subbox_right = oasysgui.widgetBox(self.ruling_subbox, "", addSpace=False, orientation="vertical",)

        oasysgui.lineEdit(ruling_subbox_left,  self, "vls_coeff_1", "b1 lines/m^2", labelWidth=115, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(ruling_subbox_left,  self, "vls_coeff_2", "b2 lines/m^3", labelWidth=115, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(ruling_subbox_right, self, "vls_coeff_3", "b3 lines/m^4", labelWidth=115, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(ruling_subbox_right, self, "vls_coeff_4", "b4 lines/m^5", labelWidth=115, valueType=float, orientation="horizontal")


        self.coating_box = oasysgui.widgetBox(self.tab_gra, "Coating", addSpace=True, orientation="vertical")

        gui.comboBox(self.coating_box, self, "coating_flag", label="Define coating", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        self.coating_subbox = oasysgui.widgetBox(self.coating_box, "", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(self.coating_subbox, self, "coating_material", "Material [Chemical Formula]", labelWidth=260, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.coating_subbox, self, "coating_thickness", "Thickness [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.kind_box = oasysgui.widgetBox(self.tab_gra, "Kind", addSpace=True, orientation="vertical")

        gui.comboBox(self.kind_box, self, "grating_kind", label="Ruling Shape", labelWidth=350,
                     items=["Undefined", "Lamellar", "Blaze"],
                     callback=self.set_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        self.kind_box_lamellar = oasysgui.widgetBox(self.kind_box, "", addSpace=True, orientation="vertical")
        self.kind_box_blaze = oasysgui.widgetBox(self.kind_box, "", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.kind_box_lamellar, self, "lamellar_height", "Heigh [m]", labelWidth=180, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.kind_box_lamellar, self, "lamellar_ratio", "Valley/period ratio [m]", labelWidth=180, valueType=str, orientation="horizontal")

        oasysgui.lineEdit(self.kind_box_blaze, self, "angle_blaze_deg", "Blaze angle [deg]", labelWidth=180, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.kind_box_blaze, self, "angle_antiblaze_deg", "Antiblaze angle [deg]", labelWidth=180, valueType=str, orientation="horizontal")

        self.set_visibility()

    def set_visibility(self):
        self.kind_box_lamellar.setVisible(self.grating_kind == 1)
        self.kind_box_blaze.setVisible(self.grating_kind == 2)

        self.ruling_subbox.setVisible(self.ruling_type == 1)
        self.coating_subbox.setVisible(self.coating_flag == 1)

    def get_optical_element(self):

        if self.ruling_type == 0:
            b1 = 0.0
            b2 = 0.0
            b3 = 0.0
            b4 = 0.0
        else:
            b1 = self.vls_coeff_1
            b2 = self.vls_coeff_2
            b3 = self.vls_coeff_3
            b4 = self.vls_coeff_4

        if self.coating_flag == 0:
            coating_material = None
            coating_thickness = None
        else:
            coating_material = self.coating_material
            coating_thickness = self.coating_thickness


        if self.grating_kind == 0:  # undefined grating type
            if self.coating_flag == 0:   # for compatibility with previous versions
                return Grating(name=self.oe_name,
                    boundary_shape=self.get_boundary_shape(),
                    surface_shape=self.get_surface_shape(),
                    ruling=self.ruling_at_center)
            else:
                return GratingVLS(name=self.oe_name,
                    boundary_shape=self.get_boundary_shape(),
                    surface_shape=self.get_surface_shape(),
                    ruling=self.ruling_at_center,
                    ruling_coeff_linear=b1,
                    ruling_coeff_quadratic=b2,
                    ruling_coeff_cubic=b3,
                    ruling_coeff_quartic=b4,
                    coating=coating_material,
                    coating_thickness=coating_thickness,
                    )
        elif self.grating_kind == 1:
            return GratingLamellar(name=self.oe_name,
                boundary_shape=self.get_boundary_shape(),
                surface_shape=self.get_surface_shape(),
                ruling=self.ruling_at_center,
                ruling_coeff_linear=b1,
                ruling_coeff_quadratic=b2,
                ruling_coeff_cubic=b3,
                ruling_coeff_quartic=b4,
                coating=coating_material,
                coating_thickness=coating_thickness,
                height=self.lamellar_height,
                ratio_valley_to_period=self.lamellar_ratio)
        elif self.grating_kind == 2:
            return GratingBlaze(name=self.oe_name,
                boundary_shape=self.get_boundary_shape(),
                surface_shape=self.get_surface_shape(),
                ruling=self.ruling_at_center,
                ruling_coeff_linear=b1,
                ruling_coeff_quadratic=b2,
                ruling_coeff_cubic=b3,
                ruling_coeff_quartic=b4,
                coating=coating_material,
                coating_thickness=coating_thickness,
                blaze_angle=self.angle_blaze_deg*pi/180,
                antiblaze_angle=self.angle_antiblaze_deg*pi/180)

    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.ruling_at_center, "Ruling at Center")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    a = QApplication(sys.argv)
    ow = OWGrating()

    ow.show()
    a.exec_()

