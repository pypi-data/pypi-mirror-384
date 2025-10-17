import numpy
def as_of(lat, lon):
    return numpy.array([lat, lon])

radius=6371000 # of earth, in meter
def xyz_of(lat, lon):
    lat = numpy.radians(lat)
    lon = numpy.radians(lon)
    x = radius * numpy.cos(lat) * numpy.cos(lon)
    y = radius * numpy.cos(lat) * numpy.sin(lon)
    z = radius * numpy.sin(lat)
    return numpy.array([x, y, z])