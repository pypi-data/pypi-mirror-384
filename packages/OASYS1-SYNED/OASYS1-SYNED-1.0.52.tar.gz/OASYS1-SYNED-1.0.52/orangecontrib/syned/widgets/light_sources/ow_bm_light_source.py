import sys

from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.storage_ring.magnetic_structures.bending_magnet import BendingMagnet

from orangecontrib.syned.widgets.gui import ow_light_source

class OWBMLightSource(ow_light_source.OWLightSource):

    name = "BM Light Source"
    description = "Syned: BM Light Source"
    icon = "icons/bm.png"
    priority = 1

    radius         = Setting(0.0)
    magnetic_field = Setting(0.0)
    length         = Setting(0.0)

    def __init__(self):
        super().__init__()

        left_box_1 = oasysgui.widgetBox(self.tab_sou, "BM Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "radius", "Radius [m]", callback=self.calculateMagneticField, labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "magnetic_field", "Magnetic Field [T]", callback=self.calculateMagneticRadius, labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "length", "Length [m]", labelWidth=260, valueType=float, orientation="horizontal")

    def check_magnetic_structure(self):
        congruence.checkNumber(self.radius , "Radius")
        congruence.checkNumber(self.magnetic_field, "Magnetic Field")
        congruence.checkStrictlyPositiveNumber(self.length, "Length")

    def get_magnetic_structure(self):
        return BendingMagnet(radius=self.radius,
                             magnetic_field=self.magnetic_field,
                             length=self.length)

    def calculateMagneticField(self):
        if self.radius > 0:
           self.magnetic_field=BendingMagnet.calculate_magnetic_field(self.radius, self.electron_energy_in_GeV)

    def calculateMagneticRadius(self):
        if self.magnetic_field > 0:
           self.radius=BendingMagnet.calculate_magnetic_radius(self.magnetic_field, self.electron_energy_in_GeV)

    def check_magnetic_structure_instance(self, magnetic_structure):
        if not isinstance(magnetic_structure, BendingMagnet):
            raise ValueError("Magnetic Structure is not a Bending Magnet")

    def populate_magnetic_structure(self, magnetic_structure):
        self.radius = magnetic_structure._radius
        self.magnetic_field = magnetic_structure._magnetic_field
        self.length = magnetic_structure._length

from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = OWBMLightSource()
    ow.show()
    a.exec_()
    #ow.saveSettings()
