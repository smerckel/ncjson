Glider profiles by example
==========================

Perhaps the easiest way to explain the use of the profiles module is
by going through an example.

Starting point is that we construct a dictionary with at least two
mandatory keys: `time` and `pressure`. The `time` key contains a a
time vector (numpy array) and the `pressure` key contains the
corresponding pressure vector (numpy array) in bar. Usually the
dictionary will contain further data arrays of other parameters that
are of interest.

Let's say we read in CTD data from a Slocum glider. So we start with
importing the required modules first.

.. code:: python

   import os

   import dbdreader
   from profiles import profiles


Using dbdreader to read the binary data files from a glider, we
extract the CTD data.

.. code ::

   path = dbdreader.EXAMPLE_DATA_PATH # new in version 0.5.6

   regex = os.path.join(path, "amadeus-2014-204-05-000.[de]bd")
   dbd=dbdreader.MultiDBD(regex)

   tctd,C,T,P = dbd.get_CTD_sync()

Then, the data can now be put in a dictionary. Note pressure is given
in bar. We can also add pressure as an additional variable (`P`), expressed in dbar.
   
.. code ::

   data=dict(time=tctd,
   pressure=P,
   T=T,
   C=C*10, # mS/cm
   P=P*10) # dbar


Now we can create a `ProfileSplitter` object. The
:class:`profiles.profiles.ProfileSplitter` takes five optional arguments:

       data: the data dictionary.

       window_size: a window size for a  moving average smoother of
       the raw pressure signal.

       threshold_bar_per_second: a threshold used to detect no
       vertical motion of the glider.
       
       remove_incomplete_tuples: a boolean, when True, discards if a
       down cast has no corresponding upcast, or vice versa.

       profile_factory: a class definition for a data container for a
       single profile. If not provided, the class
       :class:`profiles.SimpleProfile` is used. The user can supply a
       subclassed class with additional functionality.

.. code::
    
   ps=profiles.ProfileSplitter(data=data)


Note that in the line above, the data dictionary is supplied. If done,
the profiles are split immediately. The alternative is to call
:meth:`profiles.profiles.ProfileSplitter.split_profiles` explicitly,
whilst supplying the data dictionary.


Let's see how many profiles we got:

.. code::

   print("We have %d profiles"%(ps.nop))

The get the data for casts, we have three options. We can get

* up and down casts
  (:meth:`profiles.profiles.ProfileSplitter.get_casts`);
* down casts only
  (:meth:`profiles.profiles.ProfileSplitter.get_downcasts`);
* up casts only
  (:meth:`profiles.profiles.ProfileSplitter.get_upcasts`).

These three methods return a :class:`profiles.profiles.ProfileList`, which is a
container object holding single profiles.

Let's get all down casts:

.. code::
   
   casts = ps.get_downcasts()

Now we can loop through all the casts:

.. code ::

    for cast in casts:
        _T = cast.T
	_z = -cast.P
	...

Alternatively, we can get a tuple of arrays for a required parameter,
with an array for each cast.

.. code::

   T_all = casts.T
   Z_all = casts.P
   for _T, _Z in zip(T_all, Z_all):
       _Z*=-1

This allows also accessing a specfic cast:

.. code::

   T_2 = casts.T[2]


Implementing your own subclass of
:class:`profiles.profiles.SimpleProfile` allows to extend the
functionality of the SimpleProfile container. An example is
given in the class :class:`profiles.profiles.AdvancedProfile`,
which adds a despiking algorithm. To use this functionality, you would
need to pass the class as an argument to the ProfileSplitter.

.. code ::

    ps = profiles.ProfileSplitter(data=data,
                                  profile_factory=profiles.AdvancedProfile)

Repeating the steps above, then the temperature readings could be
despiked by

.. code ::

    T_2_despiked = casts[2].despike("T")


It is recommended to start with making a plot of the depth profiles,
where each profile is coloured differently, so that you reassure
yourself that the data are split into profiles correctly.    
