import numpy
from wofrysrw.util.srw import array as srw_array

def numpyComplexArrayToSRWArray(numpy_array, type='f'):
    """
    Converts a numpy.array to an array usable by SRW.
    :param numpy_array: a 2D numpy array
    :return: a 2D complex SRW array
    """
    elements_size = numpy_array.size

    r_horizontal_field = numpy_array[:, :].real.transpose().flatten().astype(numpy.float32)
    i_horizontal_field = numpy_array[:, :].imag.transpose().flatten().astype(numpy.float32)

    tmp = numpy.zeros(elements_size * 2, dtype=numpy.float32)
    for i in range(elements_size):
        tmp[2*i] = r_horizontal_field[i]
        tmp[2*i+1] = i_horizontal_field[i]

    return srw_array(type, tmp)

def numpyArraysToSRWArray(numpy_array_re, numpy_array_im, type='f'):
    """
    Converts a numpy.array to an array usable by SRW.
    :param numpy_array: a 2D numpy array
    :return: a 2D complex SRW array
    """
    elements_size = numpy_array_re.size

    r_horizontal_field = numpy_array_re[:, :].transpose().flatten().astype(numpy.float32)
    i_horizontal_field = numpy_array_im[:, :].transpose().flatten().astype(numpy.float32)

    tmp = numpy.zeros(elements_size * 2, dtype=numpy.float32)
    for i in range(elements_size):
        tmp[2*i]   = r_horizontal_field[i]
        tmp[2*i+1] = i_horizontal_field[i]

    return srw_array(type, tmp)

def __reshape(numpy_array, dim_x, dim_y, number_energies, polarized=True):
    if polarized: numpy_array = numpy_array.reshape((dim_y, dim_x, number_energies, 1))
    else:         numpy_array.reshape((dim_y, dim_x, number_energies))
    numpy_array = numpy_array.swapaxes(0, 2)

    return numpy_array.copy()

def SRWArrayToNumpyComplexArray(srw_array, dim_x, dim_y, number_energies, polarized=True):
    """
    Converts a SRW array to a numpy.array.
    :param srw_array: SRW array
    :param dim_x: size of horizontal dimension
    :param dim_y: size of vertical dimension
    :param number_energies: Size of energy dimension
    :return: 4D numpy array: [energy, horizontal, vertical, polarisation={0:horizontal, 1: vertical}]
    """
    re = numpy.array(srw_array[::2], dtype=numpy.float32)
    im = numpy.array(srw_array[1::2], dtype=numpy.float32)

    return __reshape(re + 1j * im, dim_x, dim_y, number_energies, polarized)

def SRWArrayToNumpyArrays(srw_array, dim_x, dim_y, number_energies, polarized=True):
    """
    Converts a SRW array to a numpy.array.
    :param srw_array: SRW array
    :param dim_x: size of horizontal dimension
    :param dim_y: size of vertical dimension
    :param number_energies: Size of energy dimension
    :return: 4D numpy array: [energy, horizontal, vertical, polarisation={0:horizontal, 1: vertical}]
    """
    re = numpy.array(srw_array[::2], dtype=numpy.float32)
    im = numpy.array(srw_array[1::2], dtype=numpy.float32)

    return __reshape(re, dim_x, dim_y, number_energies, polarized), \
           __reshape(im, dim_x, dim_y, number_energies, polarized)

