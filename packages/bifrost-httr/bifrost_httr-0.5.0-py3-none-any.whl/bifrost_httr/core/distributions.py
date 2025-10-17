# Bifrost-HTTr- transcriptomics based dose response analysis
# Copyright (C) 2025 as Unilever Global IP Limited
# Bifrost-HTTr is free software: you can redistribute it and/or modify it under the terms
# of the GNU Lesser General Public License as published by the Free Software Foundation,
# either version 3 of the License. Bifrost-HTTr is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with Bifrost-HTTr.
# If not, see https://www.gnu.org/licenses/ . It is the responsibility of Bifrost-HTTr users to
# familiarise themselves with all dependencies and their associated licenses.

"""Distribution classes for BIFROST analysis."""

import numpy as np
from scipy.optimize import brentq
from scipy.special import beta, betainc, digamma, expit, polygamma


class BetaLogistic:
    """A class representing a 4-parameter Beta-Logistic distribution.

    This class provides methods for calculating the PDF, CDF, and quantiles
    of a Beta-Logistic distribution.
    """

    def __init__(self, mu: float, sigma: float, a: float, b: float) -> None:
        """Initialize a BetaLogistic instance.

        Args:
            mu: Mean of the distribution
            sigma: Standard deviation of the distribution
            a: Shape parameter for the left tail
            b: Shape parameter for the right tail

        """
        self.mu, self.sigma, self.a, self.b = mu, sigma, a, b
        self.m = digamma(a) - digamma(b)
        self.s = np.sqrt(polygamma(1, a) + polygamma(1, b))

    def cdf(self, x: float | np.ndarray) -> float | np.ndarray:
        """Calculate the cumulative distribution function (CDF).

        Args:
            x: Value(s) at which to evaluate the CDF

        Returns:
            CDF evaluated at x

        """
        y = self.m + self.s * (x - self.mu) / self.sigma

        if isinstance(y, (list | np.ndarray)):
            cdf = np.zeros(len(y))
            index = np.where(y <= 0)[0]
            cdf[index] = betainc(self.a, self.b, expit(y[index]))
            index = np.where(y > 0)[0]
            cdf[index] = 1 - betainc(self.b, self.a, expit(-y[index]))
        else:
            cdf = (
                betainc(self.a, self.b, expit(y))
                if y <= 0
                else 1 - betainc(self.b, self.a, expit(-y))
            )

        return cdf

    def ppf(self, q: float) -> float:
        """Calculate the percent point function (inverse of CDF).

        Args:
            q: Quantile at which to evaluate the PPF

        Returns:
            Value x such that P(X <= x) = q

        """

        def func(x: float, q_val: float) -> float:
            return self.cdf(x) - q_val

        # Find a value of x with func < 0
        lower_bracket = -5
        while True:
            if func(lower_bracket, q) < 0:
                break
            lower_bracket -= 5

        # Find a value of x with func > 0
        upper_bracket = 5
        while True:
            if func(upper_bracket, q) > 0:
                break
            upper_bracket += 5

        return brentq(func, a=lower_bracket, b=upper_bracket, args=(q,))

    def pdf(self, x: float | np.ndarray) -> float | np.ndarray:
        """Calculate the probability density function (PDF).

        Args:
            x: Value(s) at which to evaluate the PDF

        Returns:
            PDF evaluated at x

        """
        y = self.m + self.s * (x - self.mu) / self.sigma
        return (
            expit(y) ** self.a
            * expit(-y) ** self.b
            / beta(self.a, self.b)
            * self.s
            / self.sigma
        )

    def logpdf(self, x: float | np.ndarray) -> float | np.ndarray:
        """Calculate the log probability density function.

        Args:
            x: Value(s) at which to evaluate the log PDF

        Returns:
            Log PDF evaluated at x

        """
        y = self.m + self.s * (x - self.mu) / self.sigma
        return (
            -self.a * np.logaddexp(0, -y)
            - self.b * np.logaddexp(0, y)
            - np.log(beta(self.a, self.b))
            + np.log(self.s)
            - np.log(self.sigma)
        )
