"""Principal nested spheres analysis."""

from sklearn.base import BaseEstimator, TransformerMixin

from .pns import from_unit_sphere, pns, proj, to_unit_sphere

__all__ = [
    "PNS",
]


class PNS(TransformerMixin, BaseEstimator):
    """Principal nested spheres (PNS) analysis [1]_.

    Parameters
    ----------
    n_components : int, default=2
        Number of components to keep.
        Data are transformed onto unit hypersphere embedded in this dimension.
    tol : float, default=1e-3
        Optimization tolerance.

    Attributes
    ----------
    embedding_ : ndarray of shape (n_samples, n_components)
        Stores the embedding vectors.
    v_ : list of (n_features - 1) arrays
        Principal directions of nested spheres.
    r_ : ndarray of shape (n_features - 1,)
        Principal radii of nested spheres.

    References
    ----------
    .. [1] Jung, Sungkyu, Ian L. Dryden, and James Stephen Marron.
       "Analysis of principal nested spheres." Biometrika 99.3 (2012): 551-568.

    Examples
    --------
    >>> from skpns import PNS
    >>> from skpns.util import circular_data
    >>> X = PNS(n_components=2).fit_transform(circular_data())
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(*X.T, "x")
    ... plt.gca().set_aspect("equal")
    """

    def __init__(self, n_components=2, tol=1e-3):
        self.n_components = n_components
        self.tol = tol

    def _fit_transform(self, X):
        self._n_features = X.shape[1]
        self.v_ = []
        self.r_ = []

        D = X.shape[1]
        pns_ = pns(X, self.tol)
        for _ in range(D - self.n_components):
            v, r, X = next(pns_)
            self.v_.append(v)
            self.r_.append(r)
        self.embedding_ = X

    def fit(self, X, y=None):
        """Find principal nested spheres for data X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data on (n_features - 1)-dimensional hypersphere.
        y : Ignored
            Not used, present for API consistency by convention.

        Returns
        -------
        self : object
            Returns a fitted instance of self.
        """
        self._fit_transform(X)
        return self

    def fit_transform(self, X, y=None):
        """Fit the model from data in X and transform X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data on (n_features - 1)-dimensional hypersphere.
        y : Ignored
            Not used, present for API consistency by convention.

        Returns
        -------
        X_new : array-like, shape (n_samples, n_components)
            X transformed in the new space.
        """
        self._fit_transform(X)
        return self.embedding_

    def transform(self, X):
        """Transform X onto the fitted subsphere.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data on (n_features - 1)-dimensional hypersphere.

        Returns
        -------
        X_new : array-like, shape (n_samples, n_components)
            X transformed in the new space.
        """
        if X.shape[1] != self._n_features:
            raise ValueError(
                f"Input dimension {X.shape[1]} does not match "
                f"fitted dimension {self._n_features}."
            )

        for v, r in zip(self.v_, self.r_):
            A = proj(X, v, r)
            X = to_unit_sphere(A, v, r)
        return X

    def to_hypersphere(self, X):
        """Transform the low-dimensional data into the original hypersphere.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_components)

        Returns
        -------
        X_new : array-like of shape (n_samples, n_features)
        """
        for v, r in zip(reversed(self.v_), reversed(self.r_)):
            X = from_unit_sphere(X, v, r)
        return X


try:
    from skl2onnx import update_registered_converter

    from .onnx import pns_converter, pns_shape_calculator

    update_registered_converter(PNS, "SkpnsPNS", pns_shape_calculator, pns_converter)

except ModuleNotFoundError:
    pass
