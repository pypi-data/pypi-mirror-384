import numpy

from wofrysrw.beamline.optical_elements.srw_optical_element import SRWOpticalElement
from wofrysrw.util.srw_util import numpyArraysToSRWArray, SRWArrayToNumpyArrays

from wofrysrw.util.srw import SRWLOptT

class SRWTransmission(SRWOpticalElement):
    def __init__(self,
                 x_range=None,
                 y_range=None,
                 transmission_amplitudes=None,
                 transmission_optical_path_difference=None,
                 energy=15000):
        SRWOpticalElement.__init__(self)

        self.energy                               = energy
        self.x_range                              = x_range
        self.y_range                              = y_range
        self.transmission_amplitudes              = transmission_amplitudes
        self.transmission_optical_path_difference = transmission_optical_path_difference

    def toSRWLOpt(self):
        nx = self.transmission_amplitudes.shape[0]
        ny = self.transmission_amplitudes.shape[1]
        transmission_array = numpyArraysToSRWArray(numpy_array_re=self.transmission_amplitudes,
                                                   numpy_array_im=self.transmission_optical_path_difference,
                                                   type='d')

        return SRWLOptT(_nx=nx,
                        _ny=ny,
                        _x=0.5*(self.x_range[1]+self.x_range[0]),
                        _y=0.5*(self.y_range[1]+self.y_range[0]),
                        _rx=self.x_range[1] - self.x_range[0],
                        _ry=self.y_range[1] - self.y_range[0],
                        _arTr=transmission_array,
                        _extTr=1,
                        _ne=1,
                        _eStart=self.energy,
                        _eFin=self.energy)

    def fromSRWLOpt(self, srwlopt=SRWLOptT()):
        if not isinstance(srwlopt, SRWLOptT):
            raise ValueError("SRW object is not a SRWLOptT object")

        energy  = 0.5*(srwlopt.mesh.eFin + srwlopt.mesh.eStart)
        x_range = [srwlopt.mesh.xStart, srwlopt.mesh.xFin]
        y_range = [srwlopt.mesh.yStart, srwlopt.mesh.yFin]
        transmission_amplitudes, transmission_optical_path_difference = SRWArrayToNumpyArrays(srw_array=srwlopt.arTr,
                                                                                              dim_x=srwlopt.mesh.nx,
                                                                                              dim_y=srwlopt.mesh.ny,
                                                                                              number_energies=1,
                                                                                              polarized=False)
        self.__init__(x_range=x_range,
                      y_range=y_range,
                      energy=energy,
                      transmission_amplitudes=transmission_amplitudes,
                      transmission_optical_path_difference=transmission_optical_path_difference)

    def to_python_code(self, data=None):
        oe_name = data[0]

        nx = self.transmission_amplitudes.shape[0]
        ny = self.transmission_amplitudes.shape[1]
        transmission_array = numpyArraysToSRWArray(numpy_array_re=self.transmission_amplitudes,
                                                   numpy_array_im=self.transmission_optical_path_difference)

        def to_string(srw_array):
            text = "["
            for element in srw_array: text += str(element) + ", "
            return text[:-2] + "]"

        text_code = "transmission_array = array('d', " + to_string(transmission_array) + ")\n\n"
        text_code += oe_name + "=" + "SRWLOptT(_nx=" + str(nx) + "," + "\n"
        text_code += "               _ny=" + str(ny) +  "," + "\n"
        text_code += "               _x=" + str(0.5*(self.x_range[1]+self.x_range[0])) + "," + "\n"
        text_code += "               _y=" + str(0.5*(self.y_range[1]+self.y_range[0])) + "," + "\n"
        text_code += "               _rx=" + str(self.x_range[1]-self.x_range[0]) + "," + "\n"
        text_code += "               _ry=" + str(self.y_range[1]-self.y_range[0]) + "," + "\n"
        text_code += "               _arTr=transmission_array,\n"
        text_code += "               _extTr=1,\n"
        text_code += "               _ne=1,\n"
        text_code += "               _eStart=" + str(self.energy) + "," + "\n"
        text_code += "               _eFin=" + str(self.energy) + ")" + "\n"

        return text_code
