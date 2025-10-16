import numpy
import os, h5py

from scipy.interpolate import RectBivariateSpline

def read_surface_file(file_name):
    if not os.path.isfile(file_name): raise ValueError("File " + file_name + " not existing")

    file = h5py.File(file_name, 'r')
    xx = file["surface_file/X"][()]
    yy = file["surface_file/Y"][()]
    zz = file["surface_file/Z"][()]

    return xx, yy, zz

def add_thickness_error_to_thickness_profile(thickness_profile,
                                             thickness_error_profile_file,
                                             scaling_factor=1.0,
                                             x_range=[-1e-3, 1e-3],
                                             y_range=[-1e-3, 1e-3],
                                             n_points_x=100,
                                             n_points_y=100):
    xx, yy, zz = read_surface_file(thickness_error_profile_file)
    interpolator = RectBivariateSpline(xx, yy, (zz.T) * scaling_factor)

    xx_t = numpy.linspace(x_range[0], x_range[1], n_points_x)
    yy_t = numpy.linspace(y_range[0], y_range[1], n_points_y)

    for i in range(n_points_x):
        for j in range(n_points_y):
            thickness_profile[i, j] += interpolator.ev(xx_t[i], yy_t[j])

def add_thickness_error_transmission(srwlopt_t, n_points_x, n_points_y,
                                     error_transmission_amplitudes, error_transmission_optical_path_difference):
    ofst = 0
    for iy in range(n_points_y):
        for ix in range(n_points_x):
            srwlopt_t.arTr[ofst] *= error_transmission_amplitudes[ix, iy]
            srwlopt_t.arTr[ofst + 1] += error_transmission_optical_path_difference[ix, iy]
            ofst += 2

def get_transmission_amplitudes(thickness_profile, attenuation_length):
    return numpy.exp(-0.5*thickness_profile/attenuation_length)

def get_transmission_optical_path_difference(thickness_profile, delta):
    return -delta*thickness_profile
