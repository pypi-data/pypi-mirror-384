"""
Orbit files
===========

This module handles the storage, reading and writing of orbit files.

An orbit file holds the time series of various orbital quantities, as well as
metadata on the parameters used to generate it.

Following LISA Orbits and DDPC conventions, coordinate-dependent quantities are
expressed in the ICRS frame. Most quantities are regularly sampled in the TCB,
if not otherwise specified. The sampling grid properties (sampling period,
initial time, size) are common to all quantities.

Indexing conventions use LISA Constants definitions. For example, spacecraft
indices are given in the order defined by
:attr:`lisaconstants.indexing.SPACECRAFT`.

Content
-------

The content of an orbit file is represented in memory by an instance of
:class:`OrbitFile`. Its description below is the reference for the stored
quantities, their types, shapes, units, coordinate frames, time frames, etc.

.. autoclass:: OrbitFile
    :members:

Reading and writing
-------------------

To load the content of an orbit file into memory, use :func:`read_orbit_file`.
The function will return an instance of :class:`OrbitFile`.

.. code-block:: python

    from lisaorbits.file import read_orbit_file

    orbit_file = read_orbit_file("path/to/file.h5")
    type(orbit_file)  # OrbitFile

To write the an orbit file to disk, first create an instance of
:func:`read_orbit_file` with the data you wish to store, and then call
:func:`write_orbit_file`.

.. code-block:: python

    from lisaorbits.file import OrbitFile, write_orbit_file

    orbit_file = OrbitFile(t0=...)
    write_orbit_file(orbit_file, "path/to/file.h5")

.. autofunction:: read_orbit_file

.. autofunction:: write_orbit_file

"""

import logging
from typing import Any, Callable, Sequence

import numpy as np
from attrs import field, frozen
from attrs.validators import gt
from h5py import Dataset, File
from packaging.version import Version

logger = logging.getLogger(__name__)


def of_shape(
    shape: Sequence[int | str | None],
) -> Callable[[Any, Any, np.ndarray], None]:
    """Produce a validator that checks an array is of desired shape.

    Parameters
    ----------
    shape
        Excepted shape.

        If a dimension is an int, the dimension size must match exactly. If it
        is None, the dimension is not checked. If it is a string, the dimension
        size is checked against the instance attribute of the same name.

    Returns
    -------
        A validator.
    """

    def _validator(instance: Any, attribute: Any, value: np.ndarray) -> None:
        """Fails if ``value`` is not an array, or is of wrong shape."""
        # Check that we have an array
        if not isinstance(value, np.ndarray):
            raise TypeError(
                f"{attribute.name} must be a numpy.ndarray, got {type(value)}"
            )

        # Check number of dimensions
        actual_shape = value.shape
        if len(actual_shape) != len(shape):
            raise ValueError(
                f"{attribute.name} must have {len(shape)} dimensions, got {len(shape)}"
            )

        # Check dimension sizes
        for i, exp in enumerate(shape):
            if isinstance(exp, str):
                exp = getattr(instance, exp)  # checks against instance.exp
            if exp is not None and actual_shape[i] != exp:
                raise ValueError(
                    f"{attribute.name} has wrong shape at dim {i}: expected {exp}, got {shape[i]}"
                )

    return _validator


@frozen(kw_only=True)
class OrbitFile:
    """Holds in memory quantities stored in an orbit file."""

    t0: float
    """Initial time [s].

    The same value will be used for various time grids that are attached to
    different time scales.
    """

    dt: float
    """Time period [s].

    The same value will be used for various time grids that are attached to
    different time scales.
    """

    size: int = field(validator=gt(0))
    """Number of samples.

    The same value will be used for various time grids that are attached to
    different time scales.
    """

    @property
    def duration(self) -> float:
        """Duration of the orbits [s].

        This is computed as ``dt * size``.
        """
        return self.dt * self.size

    def t(self, *, relative: bool = False) -> np.ndarray:
        """Return the time array for the quantities stored in this orbit file.

        Parameters
        ----------
        relative
            Whether we should use absolute times (ie., starting by :attr:`t0`)
            or relative values for reduced dynamic range.

        Returns
        ------
        (size,) array
            Array of times [s].
        """
        t = np.arange(self.size) * self.dt
        if not relative:
            t += self.t0
        return t

    version: str
    """LISA Orbits version used to generate this file."""

    generator: str
    """Class used to generate this file."""

    # metadata: dict[str, Any]
    # """Parameters used to generate this file."""

    positions: np.ndarray = field(validator=of_shape(("size", 3, 3)))
    r"""Spacecraft position vectors in ICRS, functions of TCB [m].

    .. math::

            (\vb{x}, \vb{y}, \vb{z}).

    Its shape is (size, 3, 3) for (time, spacecraft, xyz).
    """

    velocities: np.ndarray = field(validator=of_shape(("size", 3, 3)))
    r"""Spacecraft velocity vectors in ICRS, functions of TCB [m].

    .. math::

            (\vb{v}_x, \vb{v}_y, \vb{v}_z).

    Its shape is (size, 3, 3) for (time, spacecraft, xyz).
    """

    accelerations: np.ndarray = field(validator=of_shape(("size", 3, 3)))
    r"""Spacecraft acceleration vectors in ICRS, functions of TCB [m].

    .. math::

            (\vb{a}_x, \vb{a}_y, \vb{a}_z).

    Its shape is (size, 3, 3) for (time, spacecraft, xyz).
    """

    tps_deviations: np.ndarray = field(validator=of_shape(("size", 3)))
    r"""Spacecraft proper time (TPS) deviations, functions of TCB [s].

    .. math::

            \delta\tau(t) = \tau(t) - t,

    where :math:`\tau` is the spacecraft TPS and :math:`t` the associated
    TCB, with the initial conditions :math:`\delta\tau(t_\text{init}) = 0`.

    Its shape is (size, 3) for (time, spacecraft).
    """

    unit_vectors: np.ndarray = field(validator=of_shape(("size", 6, 3)))
    r"""Link unit vectors, functions of TCB.

    The unit vector points from the emitter spacecraft to the receiver
    spacecraft,

    .. math::

        \vu{n}(t_\text{rec}) = \frac{\vb{x}_\text{rec}(t_\text{rec}) -
        \vb{x}_\text{emit}(t_\text{emit})} {\abs{\vb{x}_\text{rec}(t_\text{rec})
        - \vb{x}_\text{emit}(t_\text{emit})}}.

    Its shape is (size, 6, 3) for (time, link, xyz).
    """

    ltts: np.ndarray = field(validator=of_shape(("size", 6)))
    """Light travel times (LTTs) [s], functions of TCB.

    Light travel times (LTTs) are the differences between the TCB time of
    reception of a photon at one spacecraft, and the TCB time of emission of the
    same photon by another spacecraft.

    Its shape is (size, 6) for (time, link).
    """

    ltt_derivatives: np.ndarray = field(validator=of_shape(("size", 6)))
    """Light travel time (LTT) dericatives [s/s], functions of TCB.

    Its shape is (size, 6) for (time, link).
    """

    tcb_pprs: np.ndarray = field(validator=of_shape(("size", 6)))
    """Proper pseudoranges (PPR) [s], functions of TCB.

    Proper pseudoranges (PPRs) are the differences between the time of reception
    of a photon expressed in the TPS of the receiving spacecraft and the time of
    emission of the same photon expressed in the TPS of the emitting spacecraft.

    Note that they include information about LTTs, as well as the conversion
    between TPSs and TCB.

    Its shape is (size, 6) for (time, link).
    """

    tcb_ppr_derivatives: np.ndarray = field(validator=of_shape(("size", 6)))
    """Proper pseudorange (PPR) dericatives [s/s], functions of TCB.

    Its shape is (size, 6) for (time, link).
    """

    tcb_deviations: np.ndarray = field(validator=of_shape(("size", 3)))
    r"""Coordinate time (TCB) deviations [s], functions of TPS.

    .. math::

        \delta t(\tau) = t(\tau) - \tau.

    where :math:`\tau` is the TPS and :math:`t` the associated TCB, with the
    initial conditions :math:`\delta t(\tau = t_\text{init}) = 0`.

    Its shape is (size, 3) for (time, spacecraft).
    """

    tps_pprs: np.ndarray = field(validator=of_shape(("size", 6)))
    """Proper pseudoranges (PPR) [s], functions of respective TPS.

    These PPRs are computed from :attr:`tcb_pprs`, resampled to the receiver
    spacecraft TPS.

    Note that the time grids associated with each of the three quantities are
    not attached to the same time sclae (respective receiver spacecraft TPS).

    Its shape is (size, 6) for (time, link).
    """

    tps_ppr_derivatives: np.ndarray = field(validator=of_shape(("size", 6)))
    """Proper pseudorange (PPR) dericatives [s/s], functions of respective TPS.

    These PPR derivatives are computed from :attr:`tcb_ppr_derivatives`,
    resampled to the receiver spacecraft TPS.

    Note that the time grids associated with each of the three quantities are
    not attached to the same time sclae (respective receiver spacecraft TPS).

    Its shape is (size, 6) for (time, link).
    """


class OrbitFileVersionError(BaseException):
    """Exception raised when the orbit file version is not supported."""

    def __init__(self, message="Unsupported orbit file version") -> None:
        super().__init__(message)


def read_orbit_file(path: str) -> OrbitFile:
    """Read an orbit file in memory.

    Parameters
    ----------
    path
        Orbit file path.

    Returns
    -------
        Orbit file content.
    """
    logger.info("Reading orbit file '%s'", path)

    with File(path, mode="r") as f:

        logger.debug("Reading version")

        version = f.attrs["version"]
        assert isinstance(version, str)

        if Version(version) < Version("2.0.dev"):
            raise OrbitFileVersionError(f"Unsupported orbit file version {version}")

        logger.debug("Reading metadata")

        t0 = f.attrs["t0"]
        assert isinstance(t0, float)
        dt = f.attrs["dt"]
        assert isinstance(dt, float)
        size = f.attrs["size"]
        assert isinstance(size, np.number)
        size = int(size)

        generator = f.attrs["generator"]
        assert isinstance(generator, str)
        # metadata_json = f.attrs["metadata"]
        # assert isinstance(metadata_json, str)

        logger.debug("Reading TCB spacecraft quantities")

        positions = f["tcb/x"]
        assert isinstance(positions, Dataset)
        velocities = f["tcb/v"]
        assert isinstance(velocities, Dataset)
        accelerations = f["tcb/a"]
        assert isinstance(accelerations, Dataset)
        tps_deviations = f["tcb/delta_tau"]
        assert isinstance(tps_deviations, Dataset)

        logger.debug("Reading TCB link quantities")

        unit_vectors = f["tcb/n"]
        assert isinstance(unit_vectors, Dataset)
        ltts = f["tcb/ltt"]
        assert isinstance(ltts, Dataset)
        ltt_derivatives = f["tcb/d_ltt"]
        assert isinstance(ltt_derivatives, Dataset)
        tcb_pprs = f["tcb/ppr"]
        assert isinstance(tcb_pprs, Dataset)
        tcb_ppr_derivatives = f["tcb/d_ppr"]
        assert isinstance(tcb_ppr_derivatives, Dataset)

        logger.debug("Reading TPS spacecraft quantities")

        tcb_deviations = f["tps/delta_t"]
        assert isinstance(tcb_deviations, Dataset)

        logger.debug("Reading TPS link quantities")

        tps_pprs = f["tps/ppr"]
        assert isinstance(tps_pprs, Dataset)
        tps_ppr_derivatives = f["tps/d_ppr"]
        assert isinstance(tps_ppr_derivatives, Dataset)

        logger.debug("Creating OrbitFile instance")

        return OrbitFile(
            t0=t0,
            dt=dt,
            size=size,
            version=version,
            generator=generator,
            # metadata=json.loads(metadata_json),
            positions=positions[:],
            velocities=velocities[:],
            accelerations=accelerations[:],
            tps_deviations=tps_deviations[:],
            unit_vectors=unit_vectors[:],
            ltts=ltts[:],
            ltt_derivatives=ltt_derivatives[:],
            tcb_pprs=tcb_pprs[:],
            tcb_ppr_derivatives=tcb_ppr_derivatives[:],
            tcb_deviations=tcb_deviations[:],
            tps_pprs=tps_pprs[:],
            tps_ppr_derivatives=tps_ppr_derivatives[:],
        )


def write_orbit_file(content: OrbitFile, path: str, mode: str = "w-") -> None:
    """Write an orbit file to disk.

    Parameters
    ----------
    content
        Orbit file content.
    path
        Orbit file path.
    mode
        File mode.
    """
    logger.info("Creating orbit file '%s'", path)

    with File(path, mode) as f:

        logger.debug("Writing metadata")

        f.attrs["t0"] = content.t0
        f.attrs["dt"] = content.dt
        f.attrs["size"] = content.size

        f.attrs["version"] = content.version
        f.attrs["generator"] = content.generator
        # f.attrs["metadata"] = json.dumps(content.metadata)

        logger.debug("Writing TCB spacecraft quantities")

        f["tcb/x"] = content.positions
        f["tcb/v"] = content.velocities
        f["tcb/a"] = content.accelerations
        f["tcb/delta_tau"] = content.tps_deviations

        logger.debug("Writing TCB link quantities")

        f["tcb/n"] = content.unit_vectors
        f["tcb/ltt"] = content.ltts
        f["tcb/d_ltt"] = content.ltt_derivatives
        f["tcb/ppr"] = content.tcb_pprs
        f["tcb/d_ppr"] = content.tcb_ppr_derivatives

        logger.debug("Writing TPS spacecraft quantities")

        f["tps/delta_t"] = content.tcb_deviations

        logger.debug("Writing TPS link quantities")

        f["tps/ppr"] = content.tps_pprs
        f["tps/d_ppr"] = content.tps_ppr_derivatives

    logger.info("Closing orbit file '%s'", path)
