# pylint: disable=C0302
"""
LISA Orbits

This module implements orbit classes.

Authors:
    Jean-Baptiste Bayle <j2b.bayle@gmail.com>
    Marc Lilley <marc.lilley@gmail.com>
    Aurelien Hees <aurelien.hees@obspm.fr>
"""

import abc
import logging
from typing import Any, Literal

import h5py
import importlib_metadata
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import CartesianRepresentation, SkyCoord
from lisaconstants import ASTRONOMICAL_UNIT, GM_SUN, SUN_SCHWARZSCHILD_RADIUS, c
from lisaconstants.indexing import LINKS
from lisaconstants.indexing import SPACECRAFT as SC
from numpy.typing import ArrayLike
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from scipy.interpolate import BSpline, make_interp_spline

from .utils import arrayindex, atleast_2d, dot, emitter, norm, receiver

logger = logging.getLogger(__name__)


def _bme2icrs(x: ArrayLike, y: ArrayLike, z: ArrayLike) -> np.ndarray:
    """Convert coordinates from BME J2000 to ICRS.

    Here, BME J200 stands for Barycentric Mean Ecliptic for J2000 equinox.

    Parameters
    ----------
    x : (...) array-like
        Coordinate along x in BME J2000 [m].
    y : (...) array-like
        Coordinate along y in BME J2000 [m].
    z : (...) array-like
        Coordinate along z in BME J2000 [m].

    Returns
    -------
    (3, ...) array
        Coordinate in ICRS [m].
    """
    # Define Astropy coordinates in BME J2000
    bme_coords = SkyCoord(
        x=x,
        y=y,
        z=z,
        representation_type="cartesian",
        frame="barycentricmeanecliptic",
    )

    # Convert to ICRS
    icrs_coords = bme_coords.icrs
    assert isinstance(icrs_coords, SkyCoord)

    # Get the Cartesian representation in meters
    icrs_cart = icrs_coords.cartesian
    assert isinstance(icrs_cart, CartesianRepresentation)

    # Get xyz coordinates
    icrs_xyz = icrs_cart.get_xyz()
    assert isinstance(icrs_xyz, u.Quantity)
    return icrs_xyz.value


class Orbits(abc.ABC):
    r"""Abstract base class for orbit classes.

    Note that :attr:`t_init` is used to define all initial conditions, including
    the synchronization of the spacecraft proper times (TPS) w.r.t. TCB (used as
    the global time frame),

    .. math::

        \delta \tau(t_\text{init}) = 0.

    This class provides default implementation for the calculation of the TCB
    deviations (from the TPS deviations), the unit vectors (from the spacecraft
    positions), the LTTs (from the spacecraft positions, velocities and
    accelerations; either from an analytical expansion or using an iterative
    method), their time derivatives, the PPR and their derivatives (from the TPS
    deviations).

    Parameters
    ----------
    t_init
        TCB time for initial conditions [s], as the number of seconds elapsed
        since the LISA epoch.
    tt_method
        Light travel time computation method. Chose ``"analytic"`` for an
        analytic series expansion of the light travel times, or ``"iterative"``
        for an iterative resolution procedure.
    tt_order
        Light travel time series expansion order (0, 1 or 2). This is only used
        when the analytic LTT computation method is chosen.
    tt_niter
        Number of iterations for light travel times iterative procedure. This is
        only used when the iterative LTT computation method is chosen.
    ignore_shapiro
        Whether Shapiro delay should be included when computing light travel
        times.
    """

    def __init__(
        self,
        *,
        t_init: float = 0.0,
        tt_method: Literal["analytic", "iterative"] = "analytic",
        tt_order: Literal[0, 1, 2] = 2,
        tt_niter: int = 4,
        ignore_shapiro: bool = False,
    ) -> None:

        # Retreive some metadata
        self.version = importlib_metadata.version("lisaorbits")
        self.generator = self.__class__.__name__

        logger.info("Initializing orbits (lisaorbit verion %s)", self.version)

        #: Light travel time computation method.
        self.tt_method = tt_method
        #: Maximum relativistic order for light travel time analytical
        #: expansion (use twice the half-integer order to make it an integer).
        self.tt_order = int(tt_order)
        #: Number of iterations for the light travel time iterative method.
        self.tt_niter = int(tt_niter)
        #: Whether Shapiro delay is included in the computation
        #: of light travel times.
        self.ignore_shapiro = ignore_shapiro
        #: TCB time for initial conditions [s].
        self.t_init = float(t_init)

    def _since_init(self, t: ArrayLike) -> np.ndarray:
        """Compute time since :attr:`t_init`.

        Parameters
        ----------
        t : (...) array-like
            TCB time [s].

        Returns
        -------
        (...) ndarray
            Time since :attr:`t_init` [s].
        """
        return np.asarray(t) - self.t_init

    @abc.abstractmethod
    def compute_position(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        r"""Compute spacecraft position vector.

        .. math::

            (\vb{x}, \vb{y}, \vb{z}).

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        sc : (M,) array-like
            Spacecraft index.

        Returns
        -------
        (N, M, 3) ndarray
            Spacecraft position vector in ICRS [m].
        """
        raise NotImplementedError

    @abc.abstractmethod
    def compute_velocity(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        r"""Compute spacecraft velocity vector.

        .. math::

            (\vb{v}_x, \vb{v}_y, \vb{v}_z).

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        sc : (M,) array-like
            Spacecraft index.

        Returns
        -------
        (N, M, 3) ndarray
            Spacecraft velocity vector in ICRS [m/s].
        """
        raise NotImplementedError

    @abc.abstractmethod
    def compute_acceleration(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        r"""Compute spacecraft acceleration vector.

        .. math::

            (\vb{a}_x, \vb{a}_y, \vb{a}_z).

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        sc : (M,) array-like
            Spacecraft index.

        Returns
        -------
        (N, M, 3) ndarray
            Spacecraft acceleration vector in ICRS [m/s^2].
        """
        raise NotImplementedError

    @abc.abstractmethod
    def compute_tps_deviation(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        r"""Compute TPS deviations as function of TCB.

        We compute the spacecraft proper time (TPS) deviations, defined by

        .. math::

            \delta\tau(t) = \tau(t) - t,

        where :math:`\tau` is the spacecraft TPS and :math:`t` the associated
        TCB, with the initial conditions :math:`\delta\tau(t_\text{init}) = 0`.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        sc : (M,) array-like
            Spacecraft index.

        Returns
        -------
        (N, M) ndarray
            Spacecraft proper time deviation [s].
        """
        raise NotImplementedError

    @abc.abstractmethod
    def compute_tps_deviation_derivative(
        self, t: ArrayLike, sc: ArrayLike = SC
    ) -> np.ndarray:
        r"""Compute TPS deviation derivatives as function of TCB.

        We compute the time derivatives of the spacecraft proper time (TPS)
        deviations, defined by

        .. math::

            \dv{(\delta\tau)}{t} = \dv{(\tau - t)}{t} = \dv{\tau}{t} - 1,

        where :math:`\tau` is the TPS and :math:`t` the associated TCB.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        sc : (M,) array-like
            Spacecraft index.

        Returns
        -------
        (N, M) ndarray
            Spacecraft proper time deviation derivative [s/s].
        """
        raise NotImplementedError

    def compute_tcb_deviation(
        self, tau: ArrayLike, sc: ArrayLike = SC, order: int = 1
    ) -> np.ndarray:
        r"""Compute TCB deviations as function of TPS.

        We compute iteratively, to a given order, the barycentric coordinate
        time (TCB),

        .. math::

            \delta t(\tau) = t(\tau) - \tau.

        where :math:`\tau` is the TPS and :math:`t` the associated TCB, with the
        initial conditions :math:`\delta t(\tau = t_\text{init}) = 0`.

        Parameters
        ----------
        tau : (N,) or (N, M) array-like
            TPS time [s].
        sc : (M,) array-like
            Spacecraft index.
        order
            Number of iterations.

        Returns
        -------
        (N, M) ndarray
            Barycentric coordinate time deviation [s].
        """
        tau = np.asarray(tau)
        # At zeroth order, there is no deviations
        tcb_deviation = np.array(0)
        for _ in range(order):
            tcb_deviation = -self.compute_tps_deviation(
                tcb_deviation + tau, sc
            )  # (N, M)
        return tcb_deviation

    def compute_unit_vector(self, t: ArrayLike, link: ArrayLike = LINKS) -> np.ndarray:
        r"""Compute link unit vectors.

        The unit vector points from the emitter spacecraft to the receiver
        spacecraft.

        We compute

        .. math::

           \vu{n}(t_\text{rec}) = \frac{\vb{x}_\text{rec}(t_\text{rec}) -
           \vb{x}_\text{emit}(t_\text{emit})}
           {\abs{\vb{x}_\text{rec}(t_\text{rec}) -
           \vb{x}_\text{emit}(t_\text{emit})}}.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        link : (M,) array-like
            Link index.

        Returns
        -------
        (N, M, 3) ndarray
            Link unit vector.
        """
        tt = self.compute_ltt(t, link)  # (N, M)
        pos_rec = self.compute_position(t, receiver(link))  # (N, M, 3)
        t_em = atleast_2d(t) - tt  # (N, M)
        pos_em = self.compute_position(t_em, emitter(link))  # (N, M, 3)
        return (pos_rec - pos_em) / norm(pos_rec - pos_em)[
            :, :, np.newaxis
        ]  # (N, M, 3)

    def compute_ltt(self, t: ArrayLike, link: ArrayLike = LINKS) -> np.ndarray:
        """Compute light travel times.

        Light travel times (LTTs) are the differences between the TCB time of
        reception of a photon at one spacecraft, and the TCB time of emission of
        the same photon by another spacecraft.

        The default implementation calls :meth:`Orbits._compute_ltt_analytic` or
        :meth:`Orbits._compute_ltt_iterative` depending on the value of
        :attr:`Orbits.tt_method`.

        Note that Shapiro delay can only be included if ``tt_order`` or
        ``tt_niter`` is greater than 2 (depending on the method chosen).

        Subclasses can override this method with custom implementations.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        link : (M,) array-like
            Link index.

        Returns
        -------
        (N, M) ndarray
            Light travel time [s].

        Raises
        ------
        ValueError
            If the computation method is invalid.
        ValueError
            If Shapiro delay is enabled with ``tt_order`` or ``tt_niter`` less
            than 2.
        """
        if self.tt_method == "analytic":
            return self._compute_ltt_analytic(t, link)  # (N, M)
        if self.tt_method == "iterative":
            return self._compute_ltt_iterative(t, link)  # (N, M)
        raise ValueError(f"Invalid LTT computation method (got '{self.tt_method}')")

    def _compute_ltt_analytic(self, t: ArrayLike, link: ArrayLike) -> np.ndarray:
        """Compute LTTs from a series expansion of the emitter trajectory.

        Refer to the model for more information.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        link : (M,) array-like
            Link index.

        Returns
        -------
        (N, M) ndarray
            Light travel time [s].

        Raises
        ------
        ValueError
            If expansion order is invalid.
        ValueError
            If Shapiro delay is enabled, but expansion order is less than 2.
        """
        # Checks parameters
        if self.tt_order < 0 or self.tt_order > 2:
            raise ValueError(
                f"Invalid light travel time computation order '{self.tt_order}', "
                "should be one of 0, 1, or 2 when computed with analytical expansion"
            )

        if self.tt_order < 2 and not self.ignore_shapiro:
            raise ValueError(
                "Cannot include Shapiro delay for light travel times using an analytic "
                f"expansion of order '{self.tt_order}' (must be greater than 2)"
            )

        pos_em = self.compute_position(t, emitter(link))  # (N, M, 3)
        pos_rec = self.compute_position(t, receiver(link))  # (N, M, 3)

        # Order 0
        d_er = norm(pos_rec - pos_em)  # (N, M)
        tt = d_er  # (N, M)

        if self.tt_order == 0:
            return tt / c  # (N, M)

        # Order 1
        vel_em = self.compute_velocity(t, emitter(link))  # (N, M, 3)
        r_er = pos_rec - pos_em  # from emitter to receiver (N, M, 3)
        velem_rer = dot(vel_em, r_er)  # (N, M)
        tt += velem_rer / c  # (N, M)

        if self.tt_order == 1:
            return tt / c  # (N, M)

        # Order 2
        acc_em = self.compute_acceleration(t, emitter(link))  # (N, M, 3)
        # This part is a correction arising from emitter motion
        tt += (
            0.5
            * (dot(vel_em, vel_em) + (velem_rer / d_er) ** 2 - dot(acc_em, r_er))
            * d_er
            / c**2
        )  # (N, M)
        # The following part is the Shapiro delay
        if not self.ignore_shapiro:
            r_em, r_rec = norm(pos_em), norm(pos_rec)  # (N, M)
            tt += SUN_SCHWARZSCHILD_RADIUS * np.log(
                (r_em + r_rec + d_er) / (r_em + r_rec - d_er)
            )  # (N, M)

        return tt / c  # (N, M)

    def _compute_ltt_iterative(self, t: ArrayLike, link: ArrayLike) -> np.ndarray:
        """Compute LTTs using an iterative procedure.

        Refer to the model for more information.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        link : (M,) array-like
            Link index.

        Returns
        -------
        (N, M) ndarray
            Light travel time [s].

        Raises
        ------
        ValueError
            If the number of iterations is invalid.
        ValueError
            If Shapiro delay is enabled, but expansion order is less than 2.
        """
        # Checks parameters
        if self.tt_niter < 0:
            raise ValueError(
                f"Invalid number of iterations '{self.tt_niter}' for iterative procedure when "
                "computing the light travel times."
            )

        if self.tt_niter < 2 and not self.ignore_shapiro:
            raise ValueError(
                "Cannot include Shapiro delay for light travel times using an iterative"
                f"procedure with number of iterations '{self.tt_niter}' (must be greater than 2)"
            )

        pos_em = self.compute_position(t, emitter(link))  # (N, M, 3)
        pos_rec = self.compute_position(t, receiver(link))  # (N, M, 3)

        # First the iteration to find the flat spacetime travel time
        tt = norm(pos_rec - pos_em) / c  # (N, M)
        for _ in range(self.tt_niter):
            t_em = atleast_2d(t) - tt  # (N, M)
            pos_em = self.compute_position(t_em, emitter(link))  # (N, M, 3)
            tt = norm(pos_rec - pos_em) / c  # (N, M)

        # And the Shapiro time delay
        if not self.ignore_shapiro:
            r_em, r_rec = norm(pos_em), norm(pos_rec)  # (N, M)
            d_er = c * tt  # (N, M)
            tt += (
                SUN_SCHWARZSCHILD_RADIUS
                * np.log((r_em + r_rec + d_er) / (r_em + r_rec - d_er))
                / c
            )  # (N, M)

        return tt  # (N, M)

    def compute_ltt_derivative(
        self, t: ArrayLike, link: ArrayLike = LINKS
    ) -> np.ndarray:
        """Compute LTT derivatives.

        The default implementation uses a series expansion of the emitting
        spacecraft trajectory. Subclasses can override this method with custom
        implementations.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        link : (M,) array-like
            Link index.

        Returns
        -------
        (N, M) ndarray
            Light travel time derivative [s/s].
        """
        pos_rec = self.compute_position(t, receiver(link))  # (N, M, 3)
        vel_rec = self.compute_velocity(t, receiver(link))  # (N, M, 3)
        ltt = self.compute_ltt(t, link)  # (N, M)

        # Note that the position and velocity of the emitter are evaluated
        # at receiver time for order 0 and 1, but at emitter time for order 2
        if self.tt_order < 2 and self.tt_method == "analytic":
            pos_em = self.compute_position(t, emitter(link))  # (N, M, 3)
            vel_em = self.compute_velocity(t, emitter(link))  # (N, M, 3)
        else:
            t_em = atleast_2d(t) - ltt  # (N, M)
            pos_em = self.compute_position(t_em, emitter(link))  # (N, M, 3)
            vel_em = self.compute_velocity(t_em, emitter(link))  # (N, M, 3)

        r_er = pos_rec - pos_em  # from emitter to receiver (N, M, 3)
        d_er = norm(pos_rec - pos_em)  # (N, M)
        n_er = (
            r_er / d_er[:, :, np.newaxis]
        )  # unit vector from emitter to receiver (N, M, 3)
        ner_vr = dot(n_er, vel_rec)  # (N, M)
        ner_ve = dot(n_er, vel_em)  # (N, M)

        if self.tt_order < 2 and self.tt_method == "analytic":
            # This is the zeroth order term which contributes only
            # for order 0 or order 1
            # all quantities being evaluated at the receiver time
            d_tt = (ner_vr - ner_ve) / c  # (N, M)
        else:
            # The derivation is different if one goes to 2nd order.
            # See Eq. 27 in Hees et al CQG 29(23):235027 (2012).
            r_em = norm(pos_em)  # (N, M)
            r_rec = norm(pos_rec)  # (N, M)
            den = (r_em + r_rec) ** 2 - d_er**2  # (N, M)
            dq_rec = (
                ner_vr
                + 2
                * SUN_SCHWARZSCHILD_RADIUS
                * ((r_em + r_rec) * ner_vr - d_er * dot(pos_rec, vel_rec) / r_rec)
                / den
            )  # (N, M)
            dq_em = (
                ner_ve
                + 2
                * SUN_SCHWARZSCHILD_RADIUS
                * ((r_em + r_rec) * ner_ve + d_er * dot(pos_em, vel_em) / r_em)
                / den
            )  # (N, M)
            d_tt = (dq_rec - dq_em) / (c - dq_em)  # (N, M)

        if self.tt_order == 1 and self.tt_method == "analytic":
            # This is the first order contribution, to be included only if
            # the order is strictly less than 2
            acc_em = self.compute_acceleration(t, emitter(link))  # (N, M, 3)
            d_tt += (
                dot(vel_rec - vel_em, vel_em) + dot(pos_rec - pos_em, acc_em)
            ) / c**2  # (N, M)

        return d_tt  # (N, M)

    def compute_ppr(self, t: ArrayLike, link: ArrayLike = LINKS) -> np.ndarray:
        """Compute proper pseudoranges.

        Proper pseudoranges (PPRs) are the differences between the time of
        reception of a photon expressed in the TPS of the receiving spacecraft
        and the time of emission of the same photon expressed in the TPS of the
        emitting spacecraft.

        Note that they include information about LTTs, as well as the conversion
        between TPSs and TCB.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        link : (M,) array-like
            Link index.

        Returns
        -------
        (N, M) ndarray
            Proper pseudorange [s].
        """
        tau_receiver = self.compute_tps_deviation(t, receiver(link))  # (N, M)
        ltt = self.compute_ltt(t, link)  # (N, M)
        t_em = atleast_2d(t) - ltt  # (N, M)
        tau_emitter = self.compute_tps_deviation(t_em, emitter(link))  # (N, M)
        return ltt + tau_receiver - tau_emitter  # (N, M)

    def compute_ppr_derivative(
        self, t: ArrayLike, link: ArrayLike = LINKS
    ) -> np.ndarray:
        """Compute PPR derivatives.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        link : (M,) array-like
            Link index.

        Returns
        -------
        (N, M) ndarray
            Proper pseudorange derivative [s/s].
        """
        dtau_receiver = self.compute_tps_deviation_derivative(
            t, receiver(link)
        )  # (N, M)
        d_tt = self.compute_ltt_derivative(t, link)  # (N, M)
        ltt = self.compute_ltt(t, link)  # (N, M)
        t_em = atleast_2d(t) - ltt  # (N, M)
        dtau_emitter = self.compute_tps_deviation_derivative(
            t_em, emitter(link)
        )  # (N, M)
        return (dtau_receiver - dtau_emitter + d_tt * (1 + dtau_emitter)) / (
            1 + dtau_receiver
        )  # (N, M)

    def plot_spacecraft(self, t: ArrayLike, sc: int, output: str | None = None) -> None:
        """Plot quantities associated with one spacecraft.

        Parameters
        ----------
        t : (N,) array-like
            TCB time [s].
        sc
            Spacecraft index.
        output
            Filename to save the plot, or ``None`` to show the plots.
        """
        # Initialize the plot
        _, axes = plt.subplots(5, 1, figsize=(12, 20))
        axes[0].set_title(f"Spacecraft {sc}")
        axes[4].set_xlabel("Barycentric time (TCB) [s]")
        # Plot positions
        logger.info("Plotting positions for spacecraft %d", sc)
        axes[0].set_ylabel("Position (ICRS) [m]")
        positions = self.compute_position(t, [sc])[:, 0]  # (N, 3)
        axes[0].plot(t, positions[:, 0], label=r"$x$")
        axes[0].plot(t, positions[:, 1], label=r"$y$")
        axes[0].plot(t, positions[:, 2], label=r"$z$")
        # Plot velocities
        logger.info("Plotting velocities for spacecraft %d", sc)
        axes[1].set_ylabel("Velocity (ICRS) [m/s]")
        velocities = self.compute_velocity(t, [sc])[:, 0]  # (N, 3)
        axes[1].plot(t, velocities[:, 0], label=r"$v_x$")
        axes[1].plot(t, velocities[:, 1], label=r"$v_y$")
        axes[1].plot(t, velocities[:, 2], label=r"$v_z$")
        # Plot accelerations
        logger.info("Plotting accelerations for spacecraft %d", sc)
        axes[2].set_ylabel("Acceleration (ICRS) [m/s^2]")
        accelerations = self.compute_acceleration(t, [sc])[:, 0]  # (N, 3)
        axes[2].plot(t, accelerations[:, 0], label=r"$a_x$")
        axes[2].plot(t, accelerations[:, 1], label=r"$a_y$")
        axes[2].plot(t, accelerations[:, 2], label=r"$a_z$")
        # Plot proper times
        logger.info("Plotting proper times for spacecraft %d", sc)
        axes[3].set_ylabel("Proper time deviation [s]")
        tps_deviations = self.compute_tps_deviation(t, [sc])[:, 0]  # (N,)
        axes[3].plot(t, tps_deviations, label=r"$\delta \tau$")
        # Plot proper time derivatives
        logger.info("Plotting proper time derivatives for spacecraft %d", sc)
        axes[4].set_ylabel("Proper time deviation derivative [s/s]")
        tps_deviations_derivatives = self.compute_tps_deviation_derivative(t, [sc])[
            :, 0
        ]  # (N,)
        axes[4].plot(t, tps_deviations_derivatives, label=r"$\dot \delta \tau$")
        # Add legend and grid
        for axis in axes:
            axis.legend()
            axis.grid()
        # Show or save figure
        if output is not None:
            logger.info("Saving plots to %s", output)
            plt.savefig(output, bbox_inches="tight")
        else:
            logger.info("Showing plots")
            plt.show()

    def plot_links(self, t: ArrayLike, output: str | None = None) -> None:
        """Plot quantities associated with the 6 links.

        Parameters
        ----------
        t : (N,) array-like
            TCB time [s].
        output
            Filename to save the plot, or ``None`` to show the plots.
        """
        t = np.asarray(t)
        # Initialize the plot
        _, axes = plt.subplots(4, 1, figsize=(12, 16))
        axes[0].set_title("Light travel times, proper pseudorange and derivatives")
        axes[3].set_xlabel("Barycentric time (TCB) [s]")
        # Plot light travel times
        logger.info("Plotting light travel times")
        axes[0].set_ylabel("Light travel time [s]")
        ltts = self.compute_ltt(t, LINKS)  # (N, M)
        for index, link in enumerate(LINKS):
            axes[0].plot(t, ltts[:, index], label=link)
        # Plot proper pseudoranges
        logger.info("Plotting proper pseudoranges")
        axes[1].set_ylabel("Proper pseudorange [s]")
        pprs = self.compute_ppr(t, LINKS)  # (N, M)
        for index, link in enumerate(LINKS):
            axes[1].plot(t, pprs[:, index], label=link)
        # Plot light travel time derivatives
        logger.info("Plotting light travel time derivatives")
        axes[2].set_ylabel("Light travel time derivative [s/s]")
        ltt_derivatives = self.compute_ltt_derivative(t, LINKS)  # (N, M)
        for index, link in enumerate(LINKS):
            axes[2].plot(t, ltt_derivatives[:, index], label=link)
        # Plot proper pseudorange derivatives
        logger.info("Plotting proper pseudorange derivatives")
        axes[3].set_ylabel("Proper pseudorange derivative [s/s]")
        ppr_derivatives = self.compute_ppr_derivative(t, LINKS)  # (N, M)
        for index, link in enumerate(LINKS):
            axes[3].plot(t, ppr_derivatives[:, index], label=link)
        # Add legend and grid
        for axis in axes:
            axis.legend()
            axis.grid()
        # Show or save figure
        if output is not None:
            logger.info("Saving plots to %s", output)
            plt.savefig(output, bbox_inches="tight")
        else:
            logger.info("Showing plots")
            plt.show()

    def _write_attr(self, hdf5: h5py.Group, *names: str) -> None:
        """Write a single object attribute as metadata on an HDF5 group.

        This method is used in :meth:`Orbits._write_metadata` to write Python
        self's attributes as HDF5 attributes.

        Parameters
        ----------
        hdf5
            An HDF5 group or file.
        names
            Attribute names; values will be fetched on self.
        """
        for name in names:
            hdf5.attrs[name] = getattr(self, name)

    def _write_metadata(self, hdf5: h5py.Group) -> None:
        """Write relevant object's attributes as metadata on an HDF5 group.

        This is for tracability and reproducibility. All parameters necessary to
        re-instantiate the orbits object and reproduce the exact same simulation
        should be written to file.

        .. admonition:: Suclassing notes

            This class is intended to be overloaded by subclasses to write
            additional attributes. You MUST call super implementation in
            subclasses.

        Parameters
        ----------
        hdf5
            An HDF5 group or file.
        """
        self._write_attr(
            hdf5,
            "version",
            "generator",
            "t_init",
            "tt_method",
            "tt_order",
            "tt_niter",
            "ignore_shapiro",
        )

    def write(
        self,
        path: str,
        t0: float | Literal["init"] = "init",
        dt: float = 100000.0,
        size: int = 316,
        *,
        mode: str = "x",
    ) -> None:
        """Write an orbit file to disk.

        An orbit file contains necessary information about LISA orbits,
        including but not limited to the spacecraft positions and velocities,
        LTTs, and PPRs.

        Parameters
        ----------
        path
            Filename for the orbit file.
        t0
            Initial time [s], or ``"init"`` to use :attr:`t_init` as the initial
            time. When interpreted as a TCB time, this is the number of seconds
            elapsed since the LISA epoch.
        dt
            Time period [s].

            The same time period will be used for various time grids that are
            attached to different time scales.
        size
            Number of samples.
        mode
            File mode. By default, create file but fail if it already exists.
        """
        # Adjust t0 on t_init if requested
        if t0 == "init":
            t0 = self.t_init

        # Make sure we get the correct types
        dt = float(dt)
        size = int(size)
        t0 = float(t0)

        # Open orbit file
        logger.info("Creating orbit file %s", path)
        with h5py.File(path, mode) as hdf5:

            logger.debug("Writing metadata")
            self._write_metadata(hdf5)
            hdf5.attrs["dt"] = dt
            hdf5.attrs["size"] = size
            hdf5.attrs["t0"] = t0

            logger.debug("Writing TCB spacecraft quantities")
            t = t0 + np.arange(size) * dt
            hdf5["tcb/x"] = self.compute_position(t, SC)
            hdf5["tcb/v"] = self.compute_velocity(t, SC)
            hdf5["tcb/a"] = self.compute_acceleration(t, SC)
            hdf5["tcb/delta_tau"] = self.compute_tps_deviation(t, SC)

            logger.debug("Writing TCB link quantities")
            hdf5["tcb/n"] = self.compute_unit_vector(t, LINKS)
            hdf5["tcb/ltt"] = self.compute_ltt(t, LINKS)
            hdf5["tcb/ppr"] = self.compute_ppr(t, LINKS)
            hdf5["tcb/d_ltt"] = self.compute_ltt_derivative(t, LINKS)
            hdf5["tcb/d_ppr"] = self.compute_ppr_derivative(t, LINKS)

            logger.debug("Writing TPS spacecraft quantities")
            delta_t = self.compute_tcb_deviation(t, SC)
            hdf5["tps/delta_t"] = delta_t

            logger.debug("Writing TPS link quantities")
            t = t[:, np.newaxis] + delta_t[:, arrayindex(SC, receiver(LINKS))]
            hdf5["tps/ppr"] = self.compute_ppr(t, LINKS)
            hdf5["tps/d_ppr"] = self.compute_ppr_derivative(t, LINKS)

            logger.info("Closing orbit file %s", path)


class StaticConstellation(Orbits):
    """Static constellation (fixed positions and constant armlengths).

    You can either initialize the orbits from a set of spacecraft positions,
    another instance of :class:`Orbits`, or a set of armlengths.

    We assume that TPS deviations and derivatives thereof are vanishing.
    Similarly, velocities and accelerations are set to zero.

    Parameters
    ----------
    r_1 : (3,) array-like)
        Position vector of spacecraft 1 in ICRS [m].
    r_2 : (3,) array-like)
        Position vector of spacecraft 2 in ICRS [m].
    r_3 : (3,) array-like)
        Position vector of spacecraft 3 in ICRS [m].
    **kwargs
        Other kwargs from :class:`Orbits`.
    """

    def __init__(
        self,
        r_1: ArrayLike,
        r_2: ArrayLike,
        r_3: ArrayLike,
        **kwargs: Any,
    ) -> None:

        # Disable the use of tt_order, tt_niter, and ignore_shapiro
        # as higher orders in LTT computation are meaningless here
        if "tt_order" in kwargs:
            raise ValueError(
                "Cannot set 'tt_order' when using StaticConstellation, as "
                "there are no higher orders when computing LTTs"
            )
        if "tt_niter" in kwargs:
            raise ValueError(
                "Cannot set 'tt_niter' when using StaticConstellation, as "
                "there are no higher orders when computing LTTs"
            )
        if "ignore_shapiro" in kwargs:
            raise ValueError(
                "Cannot set 'ignore_shapiro' when using StaticConstellation, as "
                "there are no higher orders when computing LTTs"
            )

        # Update default args because we have a static constellation
        super().__init__(
            tt_order=0,
            tt_niter=0,
            ignore_shapiro=True,
            **kwargs,
        )

        #: Spacecraft position vectors in BCRS [m].
        self.sc_positions = np.stack([r_1, r_2, r_3], axis=0)  # (3 SC, 3 COORD)
        if self.sc_positions.shape != (3, 3):
            raise TypeError(
                "Invalid shape '{self.sc_positions.shape}' for spacecraft positions"
            )

    @classmethod
    def from_orbits(
        cls, orbits: Orbits, t_freeze: float, **kwargs: Any
    ) -> "StaticConstellation":
        """Freeze orbits at a certain time to produce a static constellation.

        We compute spacecraft positions from ``orbits`` at ``t_freeze``, and
        use them as constant spacecraft positions for our static constellation.

        Parameters
        ----------
        orbits
            Orbit instance.
        t_freeze
            TCB time at which spacecraft positions are computed [s].
        **kwargs
            Other kwargs from :class:`StaticConstellation`.
        """
        # Freeze positions
        pos = orbits.compute_position([t_freeze], [1, 2, 3])[0]  # (3 SC, 3 COORD)
        return cls(pos[0], pos[1], pos[2], **kwargs)

    @classmethod
    def from_armlengths(
        cls,
        l_12: float,
        l_23: float,
        l_31: float,
        *,
        barycenter: ArrayLike = (0, 0, 0),
        **kwargs: Any,
    ) -> "StaticConstellation":
        r"""Initialize a static constellation with constant armlengths.

        The spacecraft are positioned such that spacecraft 1 lies on the x-axis
        of the ICRS, and the constellation is contained in the xy-plane.

        Parameters
        ----------
        l_12
            Constant armlength between spacecraft 1 and 2 [m].
        l_23
            Constant armlength between spacecraft 2 and 3 [m].
        l_31
            Constant armlength between spacecraft 3 and 1 [m].
        barycenter : (3,) array-like
            Cconstellation's barycenter position in ICRS [m].
        **kwargs
            Other kwargs from :class:`StaticConstellation`.
        """
        x_1 = np.sqrt(2 * l_12**2 - l_23**2 + 2 * l_31**2) / 3
        x_2 = (l_23**2 + l_31**2 - 5 * l_12**2) / (18 * x_1)
        x_3 = (l_12**2 + l_23**2 - 5 * l_31**2) / (18 * x_1)

        y_2 = -np.sqrt(
            -(l_12 - l_23 - l_31)
            * (l_12 + l_23 - l_31)
            * (l_12 - l_23 + l_31)
            * (l_12 + l_23 + l_31)
        ) / (6 * x_1)

        # Convert barycenter coordinates to array
        barycenter = np.asarray(barycenter)

        return cls(
            r_1=[x_1 + barycenter[0], barycenter[1], barycenter[2]],
            r_2=[x_2 + barycenter[0], y_2 + barycenter[1], barycenter[2]],
            r_3=[x_3 + barycenter[0], -y_2 + barycenter[1], barycenter[2]],
            **kwargs,
        )

    def _write_metadata(self, hdf5: h5py.Group) -> None:
        super()._write_metadata(hdf5)
        self._write_attr(hdf5, "sc_positions")

    def compute_position(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        t = np.asarray(t)
        sc_indices = arrayindex(SC, sc)  # (M,)
        positions = self.sc_positions[sc_indices][np.newaxis]  # (1, M, 3)
        return np.repeat(positions, len(t), axis=0)  # (N, M, 3)

    def compute_velocity(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        t = np.asarray(t)
        sc = np.array(sc)
        return np.zeros((len(t), len(sc), 3))  # (N, M, 3)

    def compute_acceleration(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        t = np.asarray(t)
        sc = np.array(sc)
        return np.zeros((len(t), len(sc), 3))  # (N, M, 3)

    def compute_tps_deviation(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        t = np.asarray(t)
        sc = np.array(sc)
        return np.zeros((len(t), len(sc)))  # (N, M)

    def compute_tps_deviation_derivative(
        self, t: ArrayLike, sc: ArrayLike = SC
    ) -> np.ndarray:
        t = np.asarray(t)
        sc = np.array(sc)
        return np.zeros((len(t), len(sc)))  # (N, M)


class EqualArmlengthOrbits(Orbits):
    r"""Keplerian orbits that minimize flexing to leading order in eccentricity.

    These orbits are the solution to the two-body problem in Newtonian gravity,
    optimized to leave inter-spacecraft distances constant to leading order in
    eccentricity.

    Parameters
    ----------
    L
        Mean inter-spacecraft distance [m].
    a
        Semi-major axis for an orbital period of 1 yr [m].
    lambda1
        Spacecraft 1's longitude of periastron in Barycentric Mean Ecliptic
        (BME) J200 [rad].
    m_init1
        Spacecraft 1's mean anomaly at initial time :math:`t_init` [rad].
    **kwargs
        All other kwargs from :class:`Orbits`.
    """

    def __init__(
        self,
        L: float = 2.5e9,
        a: float = ASTRONOMICAL_UNIT,
        lambda1: float = 0,
        m_init1: float = 0,
        **kwargs: Any,
    ) -> None:

        super().__init__(**kwargs)

        #: Semi-major axis for an orbital period of 1 yr [m].
        self.a = float(a)
        #: Mean inter-spacecraft distance [m].
        self.L = float(L)
        #: Spacecraft 1's mean anomaly at :attr:`t_init` [rad].
        self.m_init1 = float(m_init1)
        #: Spacecraft 1's longitude of periastron in Barycentric Mean Ecliptic
        #: (BME) J200 [rad].
        self.lambda1 = float(lambda1)
        #: Orbits eccentricity.
        self.e = self.L / (2 * self.a) / np.sqrt(3)

        self.n = np.sqrt(GM_SUN / self.a**3)
        self.theta = (SC - 1) * 2 * np.pi / 3  # (M,)
        self.beta = self.theta + self.lambda1  # (M,)
        self.cos_beta = np.cos(self.beta)  # (M,)
        self.sin_beta = np.sin(self.beta)  # (M,)

        self.gr_const = (self.n * self.a / c) ** 2

    def _write_metadata(self, hdf5: h5py.Group) -> None:
        super()._write_metadata(hdf5)
        self._write_attr(hdf5, "a", "L", "m_init1", "lambda1")

    def _compute_mbar(self, t: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Computes the angle of the constellation center of mass.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].

        Returns
        -------
        The 3-tuple ``(m_bar, cos(mbar), sin(mbar))`` of ndarrays, each with
        shape (N, 1) or (N, M) for each element.
        """
        t = atleast_2d(t)  # (N, 1) or (N, M)
        mbar = (
            self.n * self._since_init(t) + self.m_init1 + self.lambda1
        )  # (N, 1) or (N, M)
        return (mbar, np.cos(mbar), np.sin(mbar))  # each (N, 1) or (N, M)

    def compute_position(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc_indices = arrayindex(SC, sc)  # (M,)
        # Compute constellation angle
        mbar, cos_mbar, sin_mbar = self._compute_mbar(t)  # (N, 1) or (N, M)
        # Compute positions
        sc_x = self.a * cos_mbar + self.a * self.e * (
            sin_mbar * cos_mbar * self.sin_beta[np.newaxis, sc_indices]
            - (1 + sin_mbar**2) * self.cos_beta[np.newaxis, sc_indices]
        )  # (N, M)
        sc_y = self.a * sin_mbar + self.a * self.e * (
            sin_mbar * cos_mbar * self.cos_beta[np.newaxis, sc_indices]
            - (1 + cos_mbar**2) * self.sin_beta[np.newaxis, sc_indices]
        )  # (N, M)
        sc_z = (
            -self.a
            * self.e
            * np.sqrt(3)
            * np.cos(mbar - self.beta[np.newaxis, sc_indices])
        )  # (N, M)
        # Transform coordinates to ICRS
        icrs_xyz = _bme2icrs(sc_x, sc_y, sc_z)  # (3, N, M)
        return np.transpose(icrs_xyz, axes=(1, 2, 0))  # (N, M, 3)

    def compute_velocity(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc_indices = arrayindex(SC, sc)  # (M,)
        # Compute constellation angle
        mbar, cos_mbar, sin_mbar = self._compute_mbar(t)  # (N, 1) or (N, M)
        # Compute velocities
        sc_vx = -self.a * self.n * sin_mbar + self.a * self.e * self.n * (
            (cos_mbar**2 - sin_mbar**2) * self.sin_beta[np.newaxis, sc_indices]
            - 2 * sin_mbar * cos_mbar * self.cos_beta[np.newaxis, sc_indices]
        )  # (N, M)
        sc_vy = self.a * self.n * cos_mbar + self.a * self.e * self.n * (
            (cos_mbar**2 - sin_mbar**2) * self.cos_beta[np.newaxis, sc_indices]
            + 2 * sin_mbar * cos_mbar * self.sin_beta[np.newaxis, sc_indices]
        )  # (N, M)
        sc_vz = (
            self.a
            * self.e
            * self.n
            * np.sqrt(3)
            * np.sin(mbar - self.beta[np.newaxis, sc_indices])
        )  # (N, M)
        # Transform coordinates to ICRS
        icrs_xyz = _bme2icrs(sc_vx, sc_vy, sc_vz)  # (3, N, M)
        return np.transpose(icrs_xyz, axes=(1, 2, 0))  # (N, M, 3)

    def compute_acceleration(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc_indices = arrayindex(SC, sc)  # (M,)
        # Compute constellation angle
        mbar, cos_mbar, sin_mbar = self._compute_mbar(t)  # (N, 1) or (N, M)
        # Compute velocities
        sc_ax = -self.a * self.n**2 * cos_mbar - 4 * self.a * self.e * self.n**2 * (
            sin_mbar * cos_mbar * self.sin_beta[np.newaxis, sc_indices]
            + (0.5 - sin_mbar**2) * self.cos_beta[np.newaxis, sc_indices]
        )  # (N, M)
        sc_ay = -self.a * self.n**2 * sin_mbar - 4 * self.a * self.e * self.n**2 * (
            sin_mbar * cos_mbar * self.cos_beta[np.newaxis, sc_indices]
            + (0.5 - cos_mbar**2) * self.sin_beta[np.newaxis, sc_indices]
        )  # (N, M)
        sc_az = (
            self.a
            * self.e
            * self.n**2
            * np.sqrt(3)
            * np.cos(mbar - self.beta[np.newaxis, sc_indices])
        )  # (N, M)
        # Transform coordinates to ICRS
        icrs_xyz = _bme2icrs(sc_ax, sc_ay, sc_az)  # (3, N, M)
        return np.transpose(icrs_xyz, axes=(1, 2, 0))  # (N, M, 3)

    def compute_tps_deviation(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc_indices = arrayindex(SC, sc)  # (M,)
        # Compute constellation angle
        t = atleast_2d(t)  # (N, 1) or (N, M)
        mbar, _, _ = self._compute_mbar(t)  # (N, 1) or (N, M)
        # Compute proper time deviation
        return -self.gr_const * (
            1.5 * self._since_init(t)
            + 2
            * self.e
            / self.n
            * (
                np.sin(mbar - self.beta[np.newaxis, sc_indices])
                - np.sin(self.m_init1 - self.theta[np.newaxis, sc_indices])
            )
        )  # (N, M)

    def compute_tps_deviation_derivative(
        self, t: ArrayLike, sc: ArrayLike = SC
    ) -> np.ndarray:
        sc_indices = arrayindex(SC, sc)  # (M,)
        # Compute constellation angle
        mbar, _, _ = self._compute_mbar(t)  # (N, 1) or (N, M)
        # Compute proper time deviation
        return -self.gr_const * (
            1.5 + 2 * self.e * np.cos(mbar - self.beta[np.newaxis, sc_indices])
        )  # (N, M)


class KeplerianOrbits(Orbits):
    """Keplerian orbits that minimize flexing to second order in eccentricity.

    These orbits are the solution to the two-body problem in Newtonian gravity,
    optimized to leave inter-spacecraft distances constant to second order in
    eccentricity.

    Parameters
    ----------
    L
        Mean inter-spacecraft distance [m].
    a
        Semi-major axis for an orbital period of 1 yr [m].
    lambda1
        Spacecraft 1's longitude of periastron in Barycentric Mean Ecliptic
        (BME) J200 [rad].
    m_init1
        Spacecraft 1's mean anomaly at initial time :math:`t_init` [rad].
    kepler_order
        Number of iterations in the Newton-Raphson procedure.
    **kwargs
        All other kwargs from :class:`Orbits`.
    """

    def __init__(
        self,
        L: float = 2.5e9,
        a: float = ASTRONOMICAL_UNIT,
        lambda1: float = 0,
        m_init1: float = 0,
        kepler_order: int = 2,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        #: Semi-major axis for an orbital period of 1 yr [m].
        self.a = float(a)
        #: Mean inter-spacecraft distance [m].
        self.L = float(L)
        #: int: Number of iterations in the Newton-Raphson procedure.
        self.kepler_order = int(kepler_order)
        #: Spacecraft 1's mean anomaly at initial time [rad].
        self.m_init1 = float(m_init1)
        #: Spacecraft 1's longitude of periastron in Barycentric Mean Ecliptic
        #: (BME) J200 [rad].
        self.lambda1 = float(lambda1)

        #: Perturbation :math:`\delta` to tilt angle :math:`\nu`.
        self.delta = 5.0 / 8.0
        #: Orbital parameter (used for series expansions).
        self.alpha = self.L / (2 * self.a)
        #: Orbits tilt angle [rad].
        self.nu = np.pi / 3 + self.delta * self.alpha
        #: Orbits eccentricity.
        self.e = (
            np.sqrt(
                1
                + 4 * self.alpha * np.cos(self.nu) / np.sqrt(3)
                + 4 * self.alpha**2 / 3
            )
            - 1
        )

        self.tan_i = (
            self.alpha
            * np.sin(self.nu)
            / ((np.sqrt(3) / 2) + self.alpha * np.cos(self.nu))
        )
        self.cos_i = 1 / np.sqrt(1 + self.tan_i**2)
        self.sin_i = self.tan_i * self.cos_i

        self.n = np.sqrt(GM_SUN / self.a**3)
        self.theta = (SC - 1) * 2 * np.pi / 3  # (3,)
        self.m_init = self.m_init1 - self.theta  # (3,)
        self.lambda_k = self.lambda1 + self.theta  # (3,)
        self.sin_lambda = np.sin(self.lambda_k)  # (3,)
        self.cos_lambda = np.cos(self.lambda_k)  # (3,)

        self.gr_const = (self.n * self.a / c) ** 2

    def _write_metadata(self, hdf5: h5py.Group) -> None:
        super()._write_metadata(hdf5)
        self._write_attr(hdf5, "a", "L", "kepler_order", "m_init1", "lambda1")

    def compute_eccentric_anomaly(self, t: ArrayLike, sc: ArrayLike) -> np.ndarray:
        r"""Estimate the eccentric anomaly.

        This uses an iterative Newton-Raphson method to solve the Kepler
        equation, starting from a low eccentricity expansion of the solution.

        .. math::

            \psi_k - e \sin \psi_k = m_k(t),

        with :math:`m_k(t)` the mean anomaly.

        We use ``kepler_order`` iterations. For low eccentricity, the
        convergence rate of this iterative scheme is of the order of
        :math:`e^2`. Typically for LISA spacecraft (characterized by a small
        eccentricity 0.005), the iterative procedure converges in one iteration
        using double precision.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        sc : (M,) array-like
            Spacecraft index.

        Returns
        -------
        (N, M) ndarray
            Eccentric anomaly [rad].
        """
        # Compute the mean anomaly
        logger.debug(
            "Computing eccentric anomaly for spacecraft %s at time %s s", sc, t
        )
        sc_index = arrayindex(SC, sc)  # (M,)
        m_init = self.m_init[sc_index]  # (M,)
        m = m_init[np.newaxis] + self.n * atleast_2d(self._since_init(t))  # (N, M)
        # The following expression is valid up to e**4
        ecc_anomaly = (
            m
            + (self.e - self.e**3 / 8) * np.sin(m)
            + 0.5 * self.e**2 * np.sin(2 * m)
            + 3 / 8 * self.e**3 * np.sin(3 * m)
        )  # (N, M)
        # Standard Newton-Raphson iterative procedure
        for _ in range(self.kepler_order):
            error = ecc_anomaly - self.e * np.sin(ecc_anomaly) - m  # (N, M)
            ecc_anomaly -= error / (1 - self.e * np.cos(ecc_anomaly))  # (N, M)
        return ecc_anomaly  # (N, M)

    def compute_position(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc_index = arrayindex(SC, sc)
        # Compute eccentric anomaly
        psi = self.compute_eccentric_anomaly(t, sc)  # (N, M)
        cos_psi = np.cos(psi)  # (N, M)
        sin_psi = np.sin(psi)  # (N, M)
        # Reference position
        ref_x = self.a * self.cos_i * (cos_psi - self.e)  # (N, M)
        ref_y = self.a * np.sqrt(1 - self.e**2) * sin_psi  # (N, M)
        ref_z = -self.a * self.sin_i * (cos_psi - self.e)  # (N, M)
        # Spacecraft position
        sc_x = (
            self.cos_lambda[np.newaxis, sc_index] * ref_x
            - self.sin_lambda[np.newaxis, sc_index] * ref_y
        )  # (N, M)
        sc_y = (
            self.sin_lambda[np.newaxis, sc_index] * ref_x
            + self.cos_lambda[np.newaxis, sc_index] * ref_y
        )  # (N, M)
        sc_z = ref_z  # (N, M)
        # Transform coordinates to ICRS
        icrs_xyz = _bme2icrs(sc_x, sc_y, sc_z)  # (3, N, M)
        return np.transpose(icrs_xyz, axes=(1, 2, 0))  # (N, M, 3)

    def compute_velocity(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc_index = arrayindex(SC, sc)
        # Compute eccentric anomaly
        psi = self.compute_eccentric_anomaly(t, sc)  # (N, M)
        cos_psi = np.cos(psi)  # (N, M)
        sin_psi = np.sin(psi)  # (N, M)
        dpsi = self.n / (1 - self.e * cos_psi)  # (N, M)
        # Reference velocity
        ref_vx = -self.a * dpsi * self.cos_i * sin_psi  # (N, M)
        ref_vy = self.a * dpsi * np.sqrt(1 - self.e**2) * cos_psi  # (N, M)
        ref_vz = self.a * self.sin_i * dpsi * sin_psi  # (N, M)
        # Spacecraft velocity
        sc_vx = (
            self.cos_lambda[np.newaxis, sc_index] * ref_vx
            - self.sin_lambda[np.newaxis, sc_index] * ref_vy
        )  # (N, M)
        sc_vy = (
            self.sin_lambda[np.newaxis, sc_index] * ref_vx
            + self.cos_lambda[np.newaxis, sc_index] * ref_vy
        )  # (N, M)
        sc_vz = ref_vz  # (N, M)
        # Transform coordinates to ICRS
        icrs_xyz = _bme2icrs(sc_vx, sc_vy, sc_vz)  # (3, N, M)
        return np.transpose(icrs_xyz, axes=(1, 2, 0))  # (N, M, 3)

    def compute_acceleration(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        pos = self.compute_position(t, sc)  # (N, M, 3)
        # Spacecraft acceleration
        a3_dist3 = float(self.a**3) / norm(pos) ** 3  # (N, M)
        return -self.n**2 * pos * a3_dist3[:, :, np.newaxis]  # (N, M, 3)

    def compute_tps_deviation(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        # Compute eccentric anomaly
        t = atleast_2d(t)  # (N, 1) or (N, M)
        sin_psi = np.sin(self.compute_eccentric_anomaly(t, sc))  # (N, M)
        sin_psi_init = np.sin(self.compute_eccentric_anomaly(self.t_init, sc))  # (1, M)
        # Proper time deviation
        return -1.5 * self.gr_const * self._since_init(t) - 2 * self.gr_const * (
            self.e / self.n
        ) * (
            sin_psi - sin_psi_init
        )  # (N, M)

    def compute_tps_deviation_derivative(
        self, t: ArrayLike, sc: ArrayLike = SC
    ) -> np.ndarray:
        # Compute eccentric anomaly
        psi = self.compute_eccentric_anomaly(t, sc)  # (N, M)
        cos_psi = np.cos(psi)  # (N, M)
        dpsi = self.n / (1 - self.e * cos_psi)  # (N, M)
        # Compute proper time deviation
        return -(3 + self.e * cos_psi) / (2 * self.n) * self.gr_const * dpsi  # (N, M)


class InterpolatedOrbits(Orbits):
    """Interpolate an array of spacecraft positions.

    Splines are used to interpolate the spacecraft positions. If the velocities
    are also provided, they are interpolated with the same splines. Analytic
    derivatives of the splines are used to compute spacecraft velocities and
    accelerations if they are not provided.

    TPS deviations are numerically integrated.

    Parameters
    ----------
    t_interp : (N,) array-like
        Interpolating TCB times (needs to be ordered) [s].
    spacecraft_positions : (N, 3, 3) array-like
        Spacecraft positions with dimension ``(t, sc, coordinate)`` [m].
    spacecraft_velocities : (N, 3, 3) array-like or None
        Spacecraft velocities with dimension ``(t, sc, coordinate)`` [m/s], or
        None to compute velocities as the derivatives of the interpolated
        positions.
    interp_order
        Spline interpolation order (at least 3).
    extrapolate
        Whether to extrapolate beyond the base interval, or to return NaNs.
    **kwargs
        All other kwargs from :class:`Orbits`.

    Raises
    ------
    ValueError
        If the interpolation order is less than 3.
    """

    def __init__(
        self,
        t_interp: ArrayLike,
        spacecraft_positions: ArrayLike,
        spacecraft_velocities: ArrayLike | None = None,
        interp_order: Literal[3, 4, 5] = 5,
        extrapolate: bool = False,
        **kwargs: Any,
    ) -> None:

        super().__init__(**kwargs)

        #: Interpolating TCB times [s].
        self.t_interp = np.asarray(t_interp)
        #: Spacecraft positions [m].
        self.spacecraft_positions = np.asarray(spacecraft_positions)
        #: Spacecraft velocities [m/s].
        self.spacecraft_velocities = (
            np.asarray(spacecraft_velocities)
            if spacecraft_velocities is not None
            else None
        )
        #: Spline interpolation order (at least 3).
        self.interp_order = interp_order
        if self.interp_order < 3:
            raise ValueError(
                f"Spline interpolation order must be at least 3 (get {interp_order})"
            )
        #: Whether to extrapolate beyond the base interval, or to return NaNs.
        self.extrapolate = extrapolate

        # Check t_interp, spacecraft_positions and spacecraft_velocities' shapes
        self._check_shapes()

        # Define interpolation method
        def interpolate(x: np.ndarray) -> BSpline:
            spline = make_interp_spline(x=self.t_interp, y=x, k=self.interp_order)
            spline.extrapolate = extrapolate
            return spline

        # Compute spline interpolation for positions
        logger.debug("Computing spline interpolation for spacecraft positions")
        self.interp_x = {
            sc: interpolate(self.spacecraft_positions[:, sc - 1, 0]) for sc in SC
        }
        self.interp_y = {
            sc: interpolate(self.spacecraft_positions[:, sc - 1, 1]) for sc in SC
        }
        self.interp_z = {
            sc: interpolate(self.spacecraft_positions[:, sc - 1, 2]) for sc in SC
        }

        if spacecraft_velocities is None:
            logger.debug("Computing spline derivatives for spacecraft velocities")
            # Compute derivatives of spline objects for spacecraft velocities
            self.interp_vx = {sc: self.interp_x[sc].derivative() for sc in SC}
            self.interp_vy = {sc: self.interp_y[sc].derivative() for sc in SC}
            self.interp_vz = {sc: self.interp_z[sc].derivative() for sc in SC}
        else:
            # Compute spline interpolation for velocities
            logger.debug("Computing spline interpolation for spacecraft velocities")
            spacecraft_velocities = np.asarray(spacecraft_velocities)
            self.interp_vx = {
                sc: interpolate(spacecraft_velocities[:, sc - 1, 0]) for sc in SC
            }
            self.interp_vy = {
                sc: interpolate(spacecraft_velocities[:, sc - 1, 1]) for sc in SC
            }
            self.interp_vz = {
                sc: interpolate(spacecraft_velocities[:, sc - 1, 2]) for sc in SC
            }

        # Compute derivatives of spline objects for spacecraft accelerations
        logger.debug("Computing spline derivatives for spacecraft accelerations")
        self.interp_ax = {sc: self.interp_vx[sc].derivative() for sc in SC}
        self.interp_ay = {sc: self.interp_vy[sc].derivative() for sc in SC}
        self.interp_az = {sc: self.interp_vz[sc].derivative() for sc in SC}

        logger.debug("Computing spline interpolation for spacecraft proper times")
        self.interp_dtau = {}
        self.interp_tau = {}
        self.tau_init = {}
        self.tau_t = {}
        for sc in SC:
            pos_norm = norm(self.spacecraft_positions[:, sc - 1])
            v_squared = (
                self.interp_vx[sc](self.t_interp) ** 2
                + self.interp_vy[sc](self.t_interp) ** 2
                + self.interp_vz[sc](self.t_interp) ** 2
            )
            dtau = -0.5 * (SUN_SCHWARZSCHILD_RADIUS / pos_norm + v_squared / c**2)
            self.interp_dtau[sc] = interpolate(dtau)
            # Antiderivative of dtau is integral from t_interp_0 to t, so tau(t) - tau(t_interp_0)
            # To use initial condition, we compute integral from t_init to t, which
            # is tau(t) - tau(t_init) = tau(t), but also int_{t_init}^{t_interp_0} + int_{t_interp_0}^t
            self.tau_t[sc] = self.interp_dtau[
                sc
            ].antiderivative()  # int_{t_interp_0}^t dtau
            self.tau_init[sc] = self.tau_t[sc](
                self.t_init
            )  # int_{t_interp_0}^{t_init} dtau
            self.interp_tau[sc] = lambda t, sc=sc: self.tau_t[sc](t) - self.tau_init[sc]

    def _write_metadata(self, hdf5: h5py.Group) -> None:
        super()._write_metadata(hdf5)
        self._write_attr(hdf5, "interp_order", "extrapolate")

    def _check_shapes(self) -> None:
        """Check array shapes.

        We check that

        * ``t_interp`` is of shape (N,), and
        * ``spacecraft_positions`` is of shape (N, 3, 3), and
        * ``spacecraft_velocities`` (if not None) is of shape (N, 3, 3).

        Raises
        ------
        ValueError
            If one of the shapes is invalid.
        """
        if len(self.t_interp.shape) != 1:
            raise ValueError(
                f"time array has shape {self.t_interp.shape}, must be (N)."
            )

        size = self.t_interp.shape[0]
        if (
            len(self.spacecraft_positions.shape) != 3
            or self.spacecraft_positions.shape[0] != size
            or self.spacecraft_positions.shape[1] != 3
            or self.spacecraft_positions.shape[2] != 3
        ):
            raise ValueError(
                f"spacecraft position array has shape "
                f"{self.spacecraft_positions.shape}, expected ({size}, 3, 3)."
            )
        if self.spacecraft_velocities is not None and (
            len(self.spacecraft_velocities.shape) != 3
            or self.spacecraft_velocities.shape[0] != size
            or self.spacecraft_velocities.shape[1] != 3
            or self.spacecraft_velocities.shape[2] != 3
        ):
            raise ValueError(
                f"spacecraft velocity array has shape "
                f"{self.spacecraft_velocities.shape}, expected ({size}, 3, 3)."
            )

    @staticmethod
    def _broadcast(t: ArrayLike, sc: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
        """Broadcast ``t`` to have compatible shape with ``sc``.

        Add a second axis to ``t`` if necessary, and broadcast to ``sc`` shape.

        Parameters
        ----------
        t : (N,) or (N, M) array-like
            TCB time [s].
        sc : (M,) array-like
            Spacecraft index.

        Returns
        -------
        tuple (t, n)
            Broadcasted time array and length of second axis.
        """
        t = atleast_2d(t)
        broad_t, _ = np.broadcast_arrays(t, sc)
        return broad_t, broad_t.shape[1]

    def compute_position(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc = np.asarray(sc)
        t, n = self._broadcast(t, sc)
        sc_x = np.stack(
            [self.interp_x[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)
        sc_y = np.stack(
            [self.interp_y[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)
        sc_z = np.stack(
            [self.interp_z[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)

        return np.stack([sc_x, sc_y, sc_z], axis=-1)  # (N, M, 3)

    def compute_velocity(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc = np.asarray(sc)
        t, n = self._broadcast(t, sc)
        sc_vx = np.stack(
            [self.interp_vx[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)
        sc_vy = np.stack(
            [self.interp_vy[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)
        sc_vz = np.stack(
            [self.interp_vz[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)

        return np.stack([sc_vx, sc_vy, sc_vz], axis=-1)  # (N, M, 3)

    def compute_acceleration(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc = np.asarray(sc)
        t, n = self._broadcast(t, sc)
        sc_ax = np.stack(
            [self.interp_ax[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)
        sc_ay = np.stack(
            [self.interp_ay[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)
        sc_az = np.stack(
            [self.interp_az[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)

        return np.stack([sc_ax, sc_ay, sc_az], axis=-1)  # (N, M, 3)

    def compute_tps_deviation(self, t: ArrayLike, sc: ArrayLike = SC) -> np.ndarray:
        sc = np.asarray(sc)
        t, n = self._broadcast(t, sc)
        return np.stack(
            [self.interp_tau[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)

    def compute_tps_deviation_derivative(
        self, t: ArrayLike, sc: ArrayLike = SC
    ) -> np.ndarray:
        sc = np.asarray(sc)
        t, n = self._broadcast(t, sc)
        return np.stack(
            [self.interp_dtau[sc[i]](t[:, i]) for i in range(n)], axis=-1
        )  # (N, M)


class ResampledOrbits(InterpolatedOrbits):
    """Resamples a orbit file (created with LISA Orbits) to a new time grid.

    Splines are used to resample the spacecraft positions. All other quantities
    are deduced, as described in :class:`InterpolatedOrbits`.

    Parameters
    ----------
    orbits
        Path to an existing orbit file.
    **kwargs
        All other kwargs from :class:`InterpolatedOrbits`.
    """

    def __init__(
        self,
        orbits: str,
        **kwargs: Any,
    ) -> None:

        #: Path to the original orbit file.
        self.orbits_path = orbits

        # Load orbit file
        logger.info("Reading orbit file '%s'", self.orbits_path)
        t, spacecraft_positions = self._read_orbit_file()

        # Read original attributes
        with h5py.File(self.orbits_path, "r") as orbitf:
            self.original_attrs = dict(orbitf.attrs)

        # Read t_init
        t_init = self.original_attrs["t_init"]

        super().__init__(t, spacecraft_positions, t_init=t_init, **kwargs)

    def _write_metadata(self, hdf5: h5py.Group) -> None:
        super()._write_metadata(hdf5)
        self._write_attr(hdf5, "original_attrs")

    def _read_orbit_file(self) -> tuple[np.ndarray, np.ndarray]:
        """Read the original orbit file.

        Returns
        -------
        tuple (t, positions)
            TCB time [s] and spacecraft positions in ICRS [m] with dimension
            ``(t, sc, coordinate)``.

        Raises
        ------
        ValueError
            If the orbit file's version is not supported.
        """
        with h5py.File(self.orbits_path, "r") as orbitf:

            version_attr = orbitf.attrs["version"]
            assert isinstance(version_attr, str)
            version = Version(version_attr)
            logger.debug("Using orbit file version %s", version)

            # Warn for orbit file development version
            if version.is_devrelease:
                logger.warning("You are using an orbit file in a development version")
            current_version = importlib_metadata.version("lisaorbits")
            if version > Version(current_version):
                logger.warning(
                    "You are using an orbit file in a version that might not be "
                    "fully supported (version %s)",
                    version,
                )

            if version in SpecifierSet("== 1.*", True):

                times_ds = orbitf["tcb/t"]
                assert isinstance(times_ds, h5py.Dataset)
                times = times_ds[:]

                sc1_ds = orbitf["tcb/sc_1"]
                sc2_ds = orbitf["tcb/sc_1"]
                sc3_ds = orbitf["tcb/sc_1"]
                assert isinstance(sc1_ds, h5py.Dataset)
                assert isinstance(sc2_ds, h5py.Dataset)
                assert isinstance(sc3_ds, h5py.Dataset)
                sc_1 = np.stack([sc1_ds[coord] for coord in "xyz"], axis=-1)
                sc_2 = np.stack([sc2_ds[coord] for coord in "xyz"], axis=-1)
                sc_3 = np.stack([sc3_ds[coord] for coord in "xyz"], axis=-1)
                sc_positions = np.stack([sc_1, sc_2, sc_3], axis=1)
                return times, sc_positions

            if version in SpecifierSet(">= 2.0", True):

                t0_attr = orbitf.attrs["t0"]
                assert isinstance(t0_attr, np.floating)
                size_attr = orbitf.attrs["size"]
                assert isinstance(size_attr, np.integer)
                dt_attr = orbitf.attrs["dt"]
                assert isinstance(dt_attr, np.floating)
                times = t0_attr + np.arange(size_attr) * dt_attr

                sc_position_ds = orbitf["tcb/x"]
                assert isinstance(sc_position_ds, h5py.Dataset)
                sc_positions = sc_position_ds[:]

                return times, sc_positions

            raise ValueError(f"Unsupported orbit file version '{version}'")
