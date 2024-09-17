Introduction
============

Glider are ususally available as time series. For example, the
measured temperature can be extracted from the glider data as function
of time. In the post-processing of gliderdata, the user can reference
the measured time series to other coordinates, such as depth (or
pressure), latitude and longitude. Often it is desirable to treat a
glider time series on a per profile basis. When the daa are separated
into profiles, it becomes fairly straight forward to compare one file
to the next, interpolate a profile on a given grid and other
analysis. The python module :mod:`profiles` provide a class to
split glider data into profiles using the class definition :class:`profiles.profiles.ProfileSplitter`.
