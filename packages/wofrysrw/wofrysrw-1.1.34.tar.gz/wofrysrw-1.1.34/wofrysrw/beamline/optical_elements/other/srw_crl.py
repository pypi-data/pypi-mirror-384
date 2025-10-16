import numpy

from syned.beamline.shape import Ellipse, Rectangle
from wofrysrw.beamline.optical_elements.srw_optical_element import SRWOpticalElement
import wofrysrw.util.srw_absorption as srwa

from wofrysrw.util.srw import *

class PlaneOfFocusing:
    HORIZONTAL=1
    VERTICAL=2
    BOTH=3

    @classmethod
    def items(cls):
        return ["Horizontal", "Vertical", "Both"]

class CRLShape:
    PARABOLIC=1
    SPHERICAL=2

    @classmethod
    def items(cls):
        return ["Parabolic", "Spherical"]

class SRWCRL(SRWOpticalElement):
    """
    Setup Transmission type Optical Element which simulates Compound Refractive Lens (CRL)
    :param _foc_plane: plane of focusing: 1- horizontal, 2- vertical, 3- both
    :param _delta: refractive index decrement (can be one number of array vs photon energy)
    :param _atten_len: attenuation length [m] (can be one number of array vs photon energy)
    :param _shape: 1- parabolic, 2- circular (spherical)
    :param _apert_h: horizontal aperture size [m]
    :param _apert_v: vertical aperture size [m]
    :param _r_min: radius (on tip of parabola for parabolic shape) [m]
    :param _n: number of lenses (/"holes")
    :param _wall_thick: min. wall thickness between "holes" [m]
    :param _xc: horizontal coordinate of center [m]
    :param _yc: vertical coordinate of center [m]
    :param _void_cen_rad: flat array/list of void center coordinates and radii: [x1, y1, r1, x2, y2, r2,...]
    :param _e_start: initial photon energy
    :param _e_fin: final photon energy
    :param _nx: number of points vs horizontal position to represent the transmission element
    :param _ny: number of points vs vertical position to represent the transmission element
    :param _ang_rot_ex: angle [rad] of CRL rotation about horizontal axis
    :param _ang_rot_ey: angle [rad] of CRL rotation about vertical axis
    :param _ang_rot_ez: angle [rad] of CRL rotation about longitudinal axis
    :return: transmission (SRWLOptT) type optical element which simulates CRL
    """
    def __init__(self,
                 name="Undefined",
                 optical_element_displacement       = None,
                 plane_of_focusing=PlaneOfFocusing.BOTH,
                 delta=1e-6,
                 attenuation_length=1e-3,
                 shape=CRLShape.PARABOLIC,
                 horizontal_aperture_size=1e-3,
                 vertical_aperture_size=1e-3,
                 radius_of_curvature=5e-3,
                 number_of_lenses=10,
                 wall_thickness=5e-5,
                 horizontal_center_coordinate=0.0,
                 vertical_center_coordinate=0.0,
                 void_center_coordinates=None,
                 initial_photon_energy=8000,
                 final_photon_energy=8010,
                 horizontal_points=1001,
                 vertical_points=1001,
                 thickness_error_profile_files=None,
                 scaling_factor=1.0):
        SRWOpticalElement.__init__(self, optical_element_displacement=optical_element_displacement)

        self._name = name

        self.plane_of_focusing = plane_of_focusing
        self.delta = delta
        self.attenuation_length = attenuation_length
        self.shape = shape
        self.horizontal_aperture_size = horizontal_aperture_size
        self.vertical_aperture_size = vertical_aperture_size
        self.radius_of_curvature = radius_of_curvature
        self.number_of_lenses = number_of_lenses
        self.wall_thickness = wall_thickness
        self.horizontal_center_coordinate = horizontal_center_coordinate
        self.vertical_center_coordinate = vertical_center_coordinate
        self.void_center_coordinates = void_center_coordinates
        self.initial_photon_energy = initial_photon_energy
        self.final_photon_energy = final_photon_energy
        self.horizontal_points = horizontal_points
        self.vertical_points = vertical_points

        if not thickness_error_profile_files is None:
            self.has_error = True
            thickness_profile = numpy.zeros((self.horizontal_points, self.vertical_points))

            x_range = [self.horizontal_center_coordinate - self.horizontal_aperture_size/2,
                       self.horizontal_center_coordinate + self.horizontal_aperture_size/2]
            y_range = [self.vertical_center_coordinate - self.vertical_aperture_size/2,
                       self.vertical_center_coordinate + self.vertical_aperture_size/2]

            for thickness_error_profile_file in thickness_error_profile_files:
                srwa.add_thickness_error_to_thickness_profile(thickness_profile,
                                                              thickness_error_profile_file,
                                                              scaling_factor,
                                                              x_range,
                                                              y_range,
                                                              horizontal_points,
                                                              vertical_points)
            self.error_transmission_amplitudes              = srwa.get_transmission_amplitudes(thickness_profile, attenuation_length)
            self.error_transmission_optical_path_difference = srwa.get_transmission_optical_path_difference(thickness_profile, delta)
        else:
            self.has_error = False

    def toSRWLOpt(self):
        crl_opt = srwl_opt_setup_CRL(_foc_plane=self.plane_of_focusing,
                                     _delta=self.delta,
                                     _atten_len=self.attenuation_length,
                                     _shape=self.shape,
                                     _apert_h=self.horizontal_aperture_size,
                                     _apert_v=self.vertical_aperture_size,
                                     _r_min=self.radius_of_curvature,
                                     _n=self.number_of_lenses,
                                     _wall_thick=self.wall_thickness,
                                     _xc=self.horizontal_center_coordinate,
                                     _yc=self.vertical_center_coordinate,
                                     _void_cen_rad=self.void_center_coordinates,
                                     _e_start=self.initial_photon_energy,
                                     _e_fin=self.final_photon_energy,
                                     _nx=self.horizontal_points,
                                     _ny=self.vertical_points)

        if self.has_error:
            srwa.add_thickness_error_transmission(crl_opt, self.horizontal_points, self.vertical_points,
                                                  self.error_transmission_amplitudes, self.error_transmission_optical_path_difference)

        return crl_opt

    def fromSRWLOpt(self, srwlopt=None):
        if not srwlopt.input_params or not srwlopt.input_params["type"] == "crl":
            raise TypeError("SRW optical element is not a CRL")

        self.plane_of_focusing = srwlopt.input_params["focalPlane"]
        self.delta = srwlopt.input_params["refractiveIndex"]
        self.attenuation_length = srwlopt.input_params["attenuationLength"]
        self.shape = srwlopt.input_params["shape"]
        self.horizontal_aperture_size = srwlopt.input_params["horizontalApertureSize"]
        self.vertical_aperture_size = srwlopt.input_params["verticalApertureSize"]
        self.radius_of_curvature = srwlopt.input_params["radius"]
        self.number_of_lenses = srwlopt.input_params["numberOfLenses"]
        self.wall_thickness = srwlopt.input_params["wallThickness"]
        self.horizontal_center_coordinate = srwlopt.input_params["horizontalCenterCoordinate"]
        self.vertical_center_coordinate = srwlopt.input_params["verticalCenterCoordinate"]
        self.void_center_coordinates = srwlopt.input_params["voidCenterCoordinates"]
        self.initial_photon_energy = srwlopt.input_params["initialPhotonEnergy"]
        self.final_photon_energy = srwlopt.input_params["finalPhotonEnergy"]
        self.horizontal_points = srwlopt.input_params["horizontalPoints"]
        self.vertical_points = srwlopt.input_params["verticalPoints"]

    def to_python_code(self, data=None):
        text_code = data[0] + "=srwl_opt_setup_CRL(_foc_plane=" + str(self.plane_of_focusing) + ",\n"
        text_code += "                _delta=" + str(self.delta) + ",\n"
        text_code += "                _atten_len=" + str(self.attenuation_length) + ",\n"
        text_code += "                _shape=" + str(self.shape) + ",\n"
        text_code += "                _apert_h=" + str(self.horizontal_aperture_size) + ",\n"
        text_code += "                _apert_v=" + str(self.vertical_aperture_size) + ",\n"
        text_code += "                _r_min=" + str(self.radius_of_curvature) + ",\n"
        text_code += "                _n=" + str(self.number_of_lenses) + ",\n"
        text_code += "                _wall_thick=" + str(self.wall_thickness) + ",\n"
        text_code += "                _xc=" + str(self.horizontal_center_coordinate) + ",\n"
        text_code += "                _yc=" + str(self.vertical_center_coordinate) + ",\n"
        text_code += "                _void_cen_rad=" + str(self.void_center_coordinates) + ",\n"
        text_code += "                _e_start=" + str(self.initial_photon_energy) + ",\n"
        text_code += "                _e_fin=" + str(self.final_photon_energy) + ",\n"
        text_code += "                _nx=" + str(self.horizontal_points) + ",\n"
        text_code += "                _ny=" + str(self.vertical_points) + ")\n"

        if self.has_error:
            text_code += "\n\n"
            text_code += "def add_thickness_error_transmission(srwlopt_t, n_points_x, n_points_y,\n" + \
                         "                                     error_transmission_amplitudes, error_transmission_optical_path_difference):\n" + \
                         "    ofst = 0\n" + \
                         "    for iy in range(n_points_y):\n" + \
                         "        for ix in range(n_points_x):\n" + \
                         "            srwlopt_t.arTr[ofst]     *= error_transmission_amplitudes[ix, iy]\n" + \
                         "            srwlopt_t.arTr[ofst + 1] += error_transmission_optical_path_difference[ix, iy]\n" + \
                         "            ofst += 2\n\n"

            def to_string(numpy_array):
                text = "["
                for i in range(numpy_array.shape[0]):
                    for j in range(numpy_array.shape[1]):
                        text += ("[" if j == 0 else "") + str(numpy_array[i, j]) + ("]" if j == numpy_array.shape[1]-1 else ", ")
                    text += ", "
                return text[:-2] + "]"

            print(to_string(self.error_transmission_optical_path_difference))

            text_code += "error_transmission_amplitudes              = numpy.array(" + to_string(self.error_transmission_amplitudes) + ")\n"
            text_code += "error_transmission_optical_path_difference = numpy.array(" + to_string(self.error_transmission_optical_path_difference) + ")\n\n"

            text_code += "add_thickness_error_transmission(" + \
                         data[0] + ", " + \
                         str(self.horizontal_points) + ", " + \
                         str(self.vertical_points) + ", error_transmission_amplitudes, error_transmission_optical_path_difference)\n\n"

        return text_code

    def get_boundary_shape(self):
        if self.plane_of_focusing == PlaneOfFocusing.BOTH:
            return Ellipse(a_axis_min=self.horizontal_center_coordinate - self.horizontal_aperture_size/2,
                           a_axis_max=self.horizontal_center_coordinate + self.horizontal_aperture_size/2,
                           b_axis_min=self.vertical_center_coordinate + self.vertical_aperture_size/2,
                           b_axis_max=self.vertical_center_coordinate + self.vertical_aperture_size/2)
        else:
            return Rectangle(x_left=self.horizontal_center_coordinate - self.horizontal_aperture_size/2,
                             x_right=self.horizontal_center_coordinate + self.horizontal_aperture_size/2,
                             y_bottom=self.vertical_center_coordinate + self.vertical_aperture_size/2,
                             y_top=self.vertical_center_coordinate + self.vertical_aperture_size/2)
