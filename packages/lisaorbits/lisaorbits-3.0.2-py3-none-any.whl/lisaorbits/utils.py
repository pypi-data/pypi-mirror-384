"""
Utility functions.

This module provides utility functions.

Authors:
    Jean-Baptiste Bayle <j2b.bayle@gmail.com>
"""

import numpy as np
from lisaconstants.indexing import mosa2sc


def dot(a, b):
    """Dot product on the last axis.

    Args:
        a (array-like): input array
        b (array-like): input array
    """
    return np.einsum("...j, ...j", a, b)


def norm(a):
    """Norm on the last axis.

    Args:
        a (array-like): input array
    """
    return np.linalg.norm(a, axis=-1)


def arrayindex(elements, a):
    """Return the array indices for ``a`` in ``elements``.

    >>> a = [1, 3, 5, 7]
    >>> indices = arrayindex(a, [3, 7, 1])

    Args:
        sc (array-like): spacecraft indices

    Returns:
        :obj:`ndarray`: List of array indices

    Raises:
        ValueError: if not all elements of ``a`` cannot be found in ``elements``.
    """
    if not np.all(np.isin(a, elements)):
        raise ValueError("cannot find elements")
    return np.searchsorted(elements, a)


def atleast_2d(a):
    """View inputs as arrays with at least two dimensions.

    Contrary to numpy's function, we here add the missing dimension
    on the last axis if needed.

    >>> np.atleast_2d(3.0)
    array([[3.]])
    >>> x = np.arange(3.0)
    >>> np.atleast_2d(x)
    array([[0., 1., 2.]])
    >>> np.atleast_2d(x).base is x
    True
    >>> np.atleast_2d(1, [1, 2], [[1, 2]])
    [array([[1]]), array([[1, 2]]), array([[1, 2]])]

    Args:
        a (array-like): input array

    Returns:
        :obj:`ndarray`: An array with ``ndim >= 2``.
        Copies are avoided where possible, and views with two or more
        dimensions are returned.
    """
    a = np.asanyarray(a)
    if a.ndim == 0:
        return a.reshape(1, 1)
    if a.ndim == 1:
        return a[:, np.newaxis]
    return a


@np.vectorize
def emitter(link: int) -> int:
    """Return emitter spacecraft index from link index.

    >>> emitter(12)
    array(2)
    >>> emitter([12, 31, 21])
    array([2, 1, 1])
    >>> emitter(np.array([23, 12]))
    array([3, 2])

    Parameters
    ----------
    link
        Link index.

    Returns
    -------
    Emitter spacecraft index.
    """
    return mosa2sc(link)[1]


@np.vectorize
def receiver(link: int) -> int:
    """Return receiver spacecraft index from a link index.

    >>> receiver(12)
    array(1)
    >>> receiver([12, 31, 21])
    array([1, 3, 2])
    >>> receiver(np.array([23, 12]))
    array([2, 1])

    Parameters
    ----------
    link
        Link index.

    Returns
    -------
    Receiver spacecraft index.
    """
    return mosa2sc(link)[0]
