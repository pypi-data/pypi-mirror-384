import numpy


from syned.beamline.optical_elements.absorbers.filter import Filter
from wofrysrw.beamline.optical_elements.absorbers.srw_transmission import SRWTransmission
from wofrysrw.util.srw_absorption import get_transmission_amplitudes, get_transmission_optical_path_difference, add_thickness_error_to_thickness_profile

class SRWFilter(Filter, SRWTransmission):
    def __init__(self,
                 name="Undefined",
                 material="Be",
                 thickness=1e-3,
                 attenuation_length=1.0,
                 delta=1e-6,
                 x_range=[-1e-3, 1e-3],
                 y_range=[-1e-3, 1e-3],
                 n_points_x=100,
                 n_points_y=100,
                 energy=15000,
                 thickness_error_profile_file=None,
                 scaling_factor=1.0):
        Filter.__init__(self, name=name, material=material, thickness=thickness)

        thickness_profile = numpy.ones((n_points_x, n_points_y))*self.get_thickness()

        if not thickness_error_profile_file is None: add_thickness_error_to_thickness_profile(thickness_profile,
                                                                                              thickness_error_profile_file,
                                                                                              scaling_factor,
                                                                                              x_range,
                                                                                              y_range,
                                                                                              n_points_x,
                                                                                              n_points_y)

        SRWTransmission.__init__(self,
                                 x_range=x_range,
                                 y_range=y_range,
                                 transmission_amplitudes=get_transmission_amplitudes(thickness_profile, attenuation_length),
                                 transmission_optical_path_difference=get_transmission_optical_path_difference(thickness_profile, delta),
                                 energy=energy)



