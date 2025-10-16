"""
Orbits from OEM files
=====================

Orbit Ephemeris Message (OEM) is a standard format for exchanging orbital
information. For example, ESA provides us with estimated LISA spacecraft orbits
using OEM files.

From custom OEM files
---------------------

You can initialize an :class:`lisaorbits.Orbits` instance from 3 OEM files (one
for each spacecraft). The OEM files will be parsed and the spacecraft positions
will be interpolated using splines. Those splines are then analytically
differentiated to produce the spacecraft velocities and accelerations

The start and end time of the orbits can be accessed with
:attr:`OEMOrbits.t_start` and :attr:`OEMOrbits.t_end` and are provided as
TCB time expressed in seconds after :attr:`lisaconstant.LISA_EPOCH_TCB`.

.. code:: python

    import numpy as np from lisaorbits import OEMOrbits

    oem_orbits = OEMOrbits(
        "path/to/first/oem/file.oem", "path/to/second/oem/file.oem",
        "path/to/third/oem/file.oem",
    )

    # You can now access orbital information as usual, # or write an orbit file
    to file oem_orbits.write("my_orbit_file.h5")

By default, the TCB time used for initial conditions
:attr:`lisaorbits.Orbits.t_init` (used for clock synchronization and expressed
in TCB seconds after :attr:`lisaconstant.LISA_EPOCH_TCB`) is set to
``t_start + 10``, which includes a 10-second margin for the computation of the
LTTs. Note that :attr:`lisaorbits.Orbits.t_init` is used as the default ``t0``
when generating an orbit file.

You can choose a different :attr:`lisaorbits.Orbits.t_init` when instantiating
your OEM orbits, or a different ``t0`` when generating your orbit file.

Note that the files generated using this class used a timestamping where the
reference epoch is given by :attr:`lisaconstant.LISA_EPOCH_TCB`. Say in other
words, the time is expressed as seconds elapsed since this epoch.

.. code:: python

    oem_orbits.write("my_orbit_file.h5", t0=my_t0)

From ESA files
--------------

LISA Orbits includes numerically-optimized orbits for 20-degree Earth-leading
("esa-leading") and Earth-trailing ("esa-trailing") orbits, kindly provided by
ESA :cite:`Martens:2021phh`.

To instantiate orbits from these included files, use
:meth:`OEMOrbits.from_included`. OEM files are automatically downloaded if
necessary.

.. code:: python

    from lisaorbits import OEMOrbits

    esa_trailing = OEMOrbits.from_included("esa-trailing")

By default, you will get the latest version of a specific standard orbit file.
You can chose a specific version using

.. code::python

    esa_trailing = OEMOrbits.from_included("esa-trailing", version="1.0")

.. admonition:: License

    ESA-provided orbit files are retreived from the official `ESA Github
    repository <https://github.com/esa/lisa-orbit-files>`__. They are
    distributed under the `Creative Commons Attribution 4.0 International
    license <https://github.com/esa/lisa-orbit-files/blob/main/LICENSE>`__,
    which permits almost any use subject to providing credit and license notice.

    Refer to the repository documentation for more information.


ESA Earth-trailing (v2.0)
~~~~~~~~~~~~~~~~~~~~~~~~~

In this orbit file, the constellation center of mass trails the Earth by 20
degrees.

The orbit file covers a period of 339253488.00076556 s (a bit more than 10
years), starting on December 9th 2036 at 00:58:50.816709 TCB (UNIX
2112393530.8167093).

.. image:: ../_build/img/esa-trailing-links.pdf
    :alt: Figure of light travel times and proper pseudoranges.
    :width: 23%

.. image:: ../_build/img/esa-trailing-sc1.pdf
    :alt: Figure of SC 1 position, velocity, acceleration and proper time.
    :width: 23%

.. image:: ../_build/img/esa-trailing-sc2.pdf
    :alt: Figure of SC 2 position, velocity, acceleration and proper time.
    :width: 23%

.. image:: ../_build/img/esa-trailing-sc3.pdf
    :alt: Figure of SC 3 position, velocity, acceleration and proper time.
    :width: 23%

ESA Earth-leading (v2.0)
~~~~~~~~~~~~~~~~~~~~~~~~

In this orbit file, the constellation center of mass leads the Earth by 20
degrees.

The orbit file covers a period of 338685113.47460556 s (a bit more than 10
years), starting on 2037 June, 11th at 01:58:50.815349 TCB (UNIX
2128291130.8153486).

.. image:: ../_build/img/esa-leading-links.pdf
    :alt: Figure of light travel times and proper pseudoranges.
    :width: 23%

.. image:: ../_build/img/esa-leading-sc1.pdf
    :alt: Figure of SC 1 position, velocity, acceleration and proper time.
    :width: 23%

.. image:: ../_build/img/esa-leading-sc2.pdf
    :alt: Figure of SC 2 position, velocity, acceleration and proper time.
    :width: 23%

.. image:: ../_build/img/esa-leading-sc3.pdf
    :alt: F../igure of SC 3 position, velocity, acceleration and proper time.
    :width: 23%

Reference
---------

.. autoclass:: OEMOrbits
    :members:

.. autoclass:: OEMValueError
    :members:

"""

import logging
from typing import Any, Literal

import h5py
import numpy as np
import pooch
from astropy.time import Time
from lisaconstants import LISA_EPOCH_TCB
from oem import OrbitEphemerisMessage
from packaging.version import Version

from .orbits import InterpolatedOrbits

logger = logging.getLogger(__name__)


#: ESA-owned repository on Github, hosting orbit files we provide access to
#:
#: We use this repository to save a list of "verified" files and associated
#: hashes for security.
# pylint: disable=line-too-long
_ESA_REPOSITORY = pooch.create(
    path=pooch.os_cache("lisaorbits"),
    base_url="https://github.com/esa/lisa-orbit-files/raw/",
    registry={
        "v1.0/crema_1p0/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss.oem1": "sha256:56452a2eb84aaf6c328e0931063cb6e62a3c2d01bbdb3dd25e2d6a063225b5e4",
        "v1.0/crema_1p0/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss.oem2": "sha256:9a43bed2239625786001c046c3dc49affff23891bf3fcfd58864390eb5399639",
        "v1.0/crema_1p0/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss.oem3": "sha256:f8166f2d7050782525634f1e7dd9e9155563ec485bf7bb0c9890e8d8433be46a",
        "v1.0/crema_1p0/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss.oem1": "sha256:eec0de47d4b6791aeb1b3caf2a3db3e89cb77e2011e0fed9d6622f3258ee8d78",
        "v1.0/crema_1p0/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss.oem2": "sha256:ac120521d8c9cefd3a943a8a0bedd0d56507ba1dcef881f8f88f5d360e068f53",
        "v1.0/crema_1p0/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss.oem3": "sha256:b36f2c95db5b524ef50b7ca7750f025b700dee8e4f2ee595c0b9c7d1cea2824c",
        "v2.0/crema_2p0/tcb_time_scale/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss_may_launch_lisa1.oem": "sha256:59a662a2a57fffdac10f339417b3d437d1f1c46a2af7cab75dffd699a28096cb",
        "v2.0/crema_2p0/tcb_time_scale/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss_may_launch_lisa2.oem": "sha256:3e3ddabe5b27e233095136846bd50ea9fcd5939855dc52ad6464654fa5bb21f0",
        "v2.0/crema_2p0/tcb_time_scale/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss_may_launch_lisa3.oem": "sha256:4be88fdd1ae5c00b22d1955a03a8b126ccb94979884a0c2bd09f72c00dbb4633",
        "v2.0/crema_2p0/tcb_time_scale/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss_nov_launch_lisa1.oem": "sha256:26c1a1b64718d44241605bbcd205f19767129126e487f755c9e9157c1bb066f5",
        "v2.0/crema_2p0/tcb_time_scale/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss_nov_launch_lisa2.oem": "sha256:a5a018b3351c8fe8f182659fb17928d928be174205161351d90bc0e0390a041b",
        "v2.0/crema_2p0/tcb_time_scale/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss_nov_launch_lisa3.oem": "sha256:b199402baa866450f7ad9d9a6f649155d8bc0ac7338b3a7b9e0ee35c5a3e672e",
    },
)
# pylint: enable=line-too-long

#: Included OEM orbits
#:
#: This is a dictionary, with keys corresponding to a tuple (name, version), and
#: the values a 3-tuple of paths to the files for SC 1, 2 and 3, respectively.
# pylint: disable=line-too-long
_INCLUDED_OEM_ORBITS = {
    ("esa-trailing", "1.0.0"): (
        "v1.0/crema_1p0/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss.oem1",
        "v1.0/crema_1p0/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss.oem2",
        "v1.0/crema_1p0/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss.oem3",
    ),
    ("esa-leading", "1.0.0"): (
        "v1.0/crema_1p0/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss.oem1",
        "v1.0/crema_1p0/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss.oem2",
        "v1.0/crema_1p0/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss.oem3",
    ),
    ("esa-trailing", "2.0.0"): (
        "v2.0/crema_2p0/tcb_time_scale/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss_may_launch_lisa1.oem",
        "v2.0/crema_2p0/tcb_time_scale/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss_may_launch_lisa2.oem",
        "v2.0/crema_2p0/tcb_time_scale/mida-20deg/trajectory_out_mida-20deg_cw_sg-2nmss_may_launch_lisa3.oem",
    ),
    ("esa-leading", "2.0.0"): (
        "v2.0/crema_2p0/tcb_time_scale/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss_nov_launch_lisa1.oem",
        "v2.0/crema_2p0/tcb_time_scale/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss_nov_launch_lisa2.oem",
        "v2.0/crema_2p0/tcb_time_scale/mida+20deg/trajectory_out_mida+20deg_cw_sg-2nmss_nov_launch_lisa3.oem",
    ),
}
# pylint: enable=line-too-long


class OEMValueError(Exception):
    """Unexpected value in OEM file."""

    def __init__(self, message="Unexpected value while parsing OEM file") -> None:
        super().__init__(message)
        self.message = message


class OEMOrbits(InterpolatedOrbits):
    """Interpolate orbits from three Orbit Ephemeris Message (OEM) files.

    Each OEM file describes the orbit of one spacecraft.

    Parameters
    ----------
    oem_1
        Path to OEM file for spacecraft 1.
    oem_2
        Path to OEM file for spacecraft 2.
    oem_3
        Path to OEM file for spacecraft 3.
    t_init
        TCB time for initial conditions expressed as seconds after
        :attr:`lisaconstant.LISA_EPOCH_TCB` [s], or ``"start"`` to use the start
        time of the OEM orbits ``t_start + 10``, which includes a 10-second
        margin that allows to compute all quantities without errors
    **kwargs
        All other kwargs from :class:`InterpolatedOrbits`.
    """

    def __init__(
        self,
        oem_1: str,
        oem_2: str,
        oem_3: str,
        *,
        t_init: float | Literal["start"] = "start",
        **kwargs: Any,
    ) -> None:

        # Save file paths
        #: Path to OEM file for spacecraft 1.
        self.filename_1 = oem_1
        #: Path to OEM file for spacecraft 2.
        self.filename_2 = oem_2
        #: Path to OEM file for spacecraft 3.
        self.filename_3 = oem_3

        # Read files
        epochs_1, positions_1 = self._read_oem(oem_1, 1)
        epochs_2, positions_2 = self._read_oem(oem_2, 2)
        epochs_3, positions_3 = self._read_oem(oem_3, 3)

        # Check time scales are identical
        if not np.all(epochs_1 == epochs_2) or not np.all(epochs_2 == epochs_3):
            raise ValueError("input files have different sampling")
        epochs = epochs_1

        oem_positions = np.stack(
            [positions_1, positions_2, positions_3], axis=1
        )  # (t, sc, coord)

        # Save first and last time
        #: Start time of the orbits [s].
        self.t_start = epochs[0]
        #: End time of the orbits [s].
        self.t_end = epochs[-1]

        # Adjust t_init to start time if requested
        if t_init == "start":
            t_init = self.t_start + 10  # includes a 10-s margin to avoid extrapolation

        # Assume positions are in km and in EME2000 frame
        # In astropy, the EME2000 frame is referred to as ICRS (International
        # Celestial Reference System), which is very close to EME2000, with
        # differences typically below a few milliarcseconds.
        km2m = 1e3  # conversion between km and m
        positions = np.stack(
            [
                oem_positions[:, :, 0] * km2m,
                oem_positions[:, :, 1] * km2m,
                oem_positions[:, :, 2] * km2m,
            ],
            axis=-1,
        )  # (t, sc, coord)

        logger.warning(
            "OEM preferred interpolation method ignored, using spline "
            "interpolation (see InterpolatedOrbits for details)"
        )
        super().__init__(epochs, positions, t_init=t_init, **kwargs)

    @classmethod
    def from_included(
        cls, name: str, *, version: str | Literal["latest"] = "latest", **kwargs: Any
    ) -> "OEMOrbits":
        """Initialize an instance from OEM files included in the package.

        Parameters
        ----------
        name
            Name of the included orbits (currently supporting "esa-leading" or
            "esa-trailing").
        version
            Version of the orbits, or "latest" for the latest version.
        **kwargs
            All other kwargs from :class:`OEMOrbits`.

        Returns
        -------
        An instance of :class:`OEMOrbits`.
        """
        logger.info("Fetching OEM files from ESA repository")

        # Retreive paths to orbit files
        path_1, path_2, path_3 = OEMOrbits._get_included_paths(name, version=version)

        # Fetch the files
        oem_1 = _ESA_REPOSITORY.fetch(path_1, progressbar=True)
        oem_2 = _ESA_REPOSITORY.fetch(path_2, progressbar=True)
        oem_3 = _ESA_REPOSITORY.fetch(path_3, progressbar=True)

        # Print file hashes of files fetched from ESA repository
        logger.debug("SHA256 hash for '%s' is '%s'", oem_1, pooch.file_hash(oem_1))
        logger.debug("SHA256 hash for '%s' is '%s'", oem_2, pooch.file_hash(oem_2))
        logger.debug("SHA256 hash for '%s' is '%s'", oem_3, pooch.file_hash(oem_3))

        return cls(oem_1, oem_2, oem_3, **kwargs)

    @staticmethod
    def _get_included_paths(
        name: str, *, version: str | Literal["latest"]
    ) -> tuple[str, str, str]:
        """Return path to included EOM files.

        Parameters
        ----------
        name
            Name of the included orbits (currently supporting "esa-leading" or
            "esa-trailing").
        version
            Version of the orbits, or "latest" for the latest version.
        **kwargs
            All other kwargs from :class:`OEMOrbits`.

        Returns
        -------
        tuple (oem_1, oem_2, oem_3)
            A tuple of paths for the OEM files associated with spacecraft 1, 2,
            and 3, respectively.
        """
        # Store versions that match the desired name in case we want to find the
        # latest version
        versions = []

        for (_name, _version), paths in _INCLUDED_OEM_ORBITS.items():
            # If the names do not match, we skip this element
            if name != _name:
                continue
            # If the version match, we return the paths
            if version != "latest" and Version(version) == Version(_version):
                logger.info("Found matching OEM orbits from ESA (version %s)", version)
                return paths
            # If the names match but the versions do not, we store the version
            # in case we want to find the latest version
            versions.append(Version(_version))

        # If we haven't found the correct version, it's either that we've asked
        # for the latest version, or that the files do not exist
        if version == "latest" and versions:
            latest_version = max(versions)
            logger.info(
                "Found matching OEM orbits from ESA (version %s)", latest_version
            )
            return _INCLUDED_OEM_ORBITS[(name, str(latest_version))]

        raise ValueError(f"cannot find included orbits '{name}' version {version}")

    def _write_metadata(self, hdf5: h5py.Group) -> None:
        super()._write_metadata(hdf5)
        self._write_attr(
            hdf5, "filename_1", "filename_2", "filename_3", "t_start", "t_end"
        )

    def _read_oem(self, path: str, index: int) -> tuple[np.ndarray, np.ndarray]:
        """Parse OEM file.

        We check structure and metadata, and return epochs and positions.

        Parameters
        ----------
        path
            Path to OEM file.
        index
            Spacecraft index.

        Returns
        -------
        tuple (epochs, positions)
            UNIX timestamps of shape (N,), and spacecraft positions of shape (N,
            3).
        """
        # pylint: disable=protected-access
        logger.info("Reading OEM file '%s'", path)
        ephemeris = OrbitEphemerisMessage.open(path)

        if ephemeris.version.strip() != "2.0":
            raise OEMValueError("unsupported OEM version")
        if len(ephemeris._segments) != 1:
            logger.warning(
                "OEM file contains more than one segment, using the first one"
            )

        header = {key: ephemeris.header[key] for key in ephemeris.header}
        setattr(self, f"header_{index}", header)

        segment = ephemeris._segments[0]
        metadata = segment.metadata

        # We only support EME2000 coordinates
        if metadata["REF_FRAME"] != "EME2000":
            raise OEMValueError(
                f"Unsupported reference frame in OEM '{path}' "
                f"(expected EMEJ2000, got {metadata['REF_FRAME']}'"
            )

        # Issue a warning of the file is not given in TCB
        # We still go on, assuming times are actually TCB (but no conversion)
        if metadata["TIME_SYSTEM"] != "TCB":
            logger.warning(
                "Unsupported time system '%s' in OEM '%s', "
                "will be interpreted as TCB without conversion",
                metadata["TIME_SYSTEM"],
                path,
            )

        metadata_dict = {key: metadata[key] for key in metadata}
        setattr(self, f"metadata_{index}", metadata_dict)

        t0 = Time(LISA_EPOCH_TCB, format="isot", scale="tcb")
        epochs = np.array([(state.epoch - t0).sec for state in segment])

        positions = np.stack([state.position for state in segment], axis=0)
        return (epochs, positions)
