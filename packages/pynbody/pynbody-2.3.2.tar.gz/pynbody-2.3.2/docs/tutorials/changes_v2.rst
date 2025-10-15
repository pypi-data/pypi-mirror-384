.. _changes::

Changes in version 2
====================


Version 2 of *pynbody* is the first ever release to break full backwards compatibility. Most code for
pynbody 1.6 will also work with pynbody 2.0, but there are some changes that may require you to
modify code. This document summarises the most important changes.

Rationale
---------

The changes in pynbody 2.0 are designed to make the codebase more maintainable. The essential principle
was to remove rarely-used code that was adding complication -- to do less, but do it better.
Breaking changes are never pleasant, but in its 15-year history, pynbody has never had a major version
increment like this. We hope that the changes will make the codebase more sustainable in the long term.

Key changes
-----------

- By far the biggest improvement is the documentation, including tutorials; these have been completely
  overhauled and updated.
- The :mod:`~pynbody.halo` subpackage has been completely re-implemented, for greater consistency across
  formats. For many simple uses, old code will continue to work. However, please read the change notice
  in :mod:`~pynbody.halo` for important changes. This especially affects certain AHF catalogues which used
  to be given an inconsistent halo numbering scheme. Backwards compatibility can be achieved there by
  passing the correct flag. There is also now a format-independent way to describe parent/child relationships
  in catalogs, which is described in the :ref:`halo_tutorial` tutorial.
- The :mod:`~pynbody.plot` subpackage has been streamlined, with a number of trivial routines removed, and
  options to save files etc removed. These are much better handled by matplotlib directly.
  See the :mod:`~pynbody.plot` documentation for details.
- The :mod:`~pynbody.analysis` package has been rationalised, with unnecessary routines removed (including the
  ``pkdgrav_cosmo`` module). Major improvements have been made to :mod:`~pynbody.analysis.luminosity` and
  :mod:`~pynbody.analysis.ionfrac` to bring their estimates up to date and explain more clearly how to
  introduce new tables for interpolation. The :mod:`~pynbody.analysis.profile` module has been improved. The
  ``decomp`` module has been renamed to :mod:`~pynbody.analysis.morphology`.
- The :mod:`~pynbody.sph` subpackage has been overhauled to improve efficiency and robustness of SPH
  operations. The implementation of healpix rendering has been improved, by using our own healpix pixelization
  implementation that enables faster, parallel rendering.  KD-tree operations are now found in :mod:`~pynbody.kdtree`
  and KD-tree information can be accessed directly from python as a numpy record array (e.g. for saving or
  manipulating KD-trees directly).
- The :mod:`~pynbody.array` subpackage now publishes a number of functions that were previously hidden,
  specifically enabling the use of shared memory in complex analysis pipelines across multiple processors. For
  more information see :ref:`using_shared_arrays`.
- The implementation of bridges, and particularly halo matching, has been improved. Methods
  :meth:`~pynbody.bridge.Bridge.match_catalog` and :meth:`~pynbody.bridge.Bridge.fuzzy_match_catalog`
  have been deprecated in favour of more robust alternatives
  :meth:`~pynbody.bridge.Bridge.match_halos` and :meth:`~pynbody.bridge.Bridge.fuzzy_match_halos`.
- There is improved support for various flavours of GadgetHDF files, including Swift, Arepo and TNG.
- The :mod:`~pynbody.transformation` subpackage has been overhauled, with improved consistency e.g.
  if one loads data after a transformation has been applied (it will now be correctly transformed).
- Test data is now stored as a series of separate tars on Zenodo, rather than as a single large tarball.
  Accessing test data can be accomplished automatically via the :mod:`pynbody.test_utils` function. When
  running tests, the required data will be downloaded automatically if needed.
- A number of external dependencies have changed; this should be taken care of automatically by pip. Numpy
  2.0 is now supported.
