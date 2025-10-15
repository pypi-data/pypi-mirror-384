"""
Cryptographically secure random distributions using Python's `secrets`.

Design notes
------------
• IEEE-754 doubles have a 53-bit mantissa. We therefore draw 53 random bits and
  scale by 2**53 to obtain U ~ Uniform[0,1) with full double precision.

• Uniform(a,b):  a + (b - a) * U.

• Exponential(λ): inverse CDF method:
      F(x) = 1 - exp(-λx)  =>  X = F^{-1}(U) = -log(1 - U)/λ.
  We use math.log1p(-U) for numerical stability when U≈0.

• Poisson(λ): discrete inverse transform (CDF walk). Recurrence for PMF:
      p0 = exp(-λ),  p_{k+1} = p_k * λ / (k+1).
  Accumulate c += p_k until U <= c, then return k.
"""

from __future__ import annotations

import math
import secrets
from typing import List

# ---------- secure U(0,1) generator ----------

_TWO_POW_53 = 1 << 53  # 2**53


def _u01() -> float:
    """Return U ~ Uniform[0,1) using 53 cryptographically secure random bits."""
    # secrets.randbits(53) ∈ {0,1,...,2**53-1}; divide to map into [0,1).
    return secrets.randbits(53) / _TWO_POW_53


# ---------- Uniform(a,b) ----------

def uniform(a: float = 0.0, b: float = 1.0) -> float:
    """
    Draw one sample from Uniform(a, b) using a CSPRNG.

    Parameters
    ----------
    a, b : real numbers with b > a

    Returns
    -------
    float in [a, b)
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("a and b must be real numbers")
    if not (b > a):
        raise ValueError("require b > a")

    u = _u01()  # in [0,1)
    return a + (b - a) * u


def uniform_samples(n: int, a: float = 0.0, b: float = 1.0) -> List[float]:
    """Generate n IID Uniform(a,b) samples."""
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    return [uniform(a, b) for _ in range(n)]


# ---------- Exponential(λ) via inverse CDF ----------

def exponentialdist(lmbda: float) -> float:
    """
    Draw one sample from Exponential(λ) with λ > 0 via inverse transform:
        X = -log(1 - U) / λ,  U ~ U(0,1).
    Uses log1p(-U) for numerical stability.
    """
    if not isinstance(lmbda, (int, float)) or not (lmbda > 0.0):
        raise ValueError("lambda must be a positive real number")

    u = _u01()                     # ∈ [0,1)
    return -math.log1p(-u) / lmbda


def exponential_samples(n: int, lmbda: float) -> List[float]:
    """Generate n IID Exponential(λ) samples."""
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if not isinstance(lmbda, (int, float)) or not (lmbda > 0.0):
        raise ValueError("lambda must be a positive real number")
    return [-math.log1p(-_u01()) / lmbda for _ in range(n)]


# ---------- Poisson(λ) via discrete inverse transform ----------

def poissondist(lmbda: float) -> int:
    """
    Draw one sample from Poisson(λ) (λ > 0) using the discrete inverse CDF.

    Recurrence for PMF:
        p0 = exp(-λ)
        p_{k+1} = p_k * λ / (k+1)

    Algorithm:
        U ~ U(0,1); k = 0; p = p0; c = p
        while U > c:
            k += 1
            p *= λ / k
            c += p
        return k
    """
    if not isinstance(lmbda, (int, float)) or not (lmbda > 0.0):
        raise ValueError("lambda must be a positive real number")

    u = _u01()
    k = 0
    p = math.exp(-lmbda)  # p0
    c = p
    while u > c:
        k += 1
        p *= lmbda / k
        c += p
    return k


def poisson_samples(n: int, lmbda: float) -> List[int]:
    """Generate n IID Poisson(λ) samples."""
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if not isinstance(lmbda, (int, float)) or not (lmbda > 0.0):
        raise ValueError("lambda must be a positive real number")
    return [poissondist(lmbda) for _ in range(n)]


# Optional alias if your spec used the misspelling "poissiondist"
poissiondist = poissondist


# ---------- quick self-test when run directly ----------

if __name__ == "__main__":
    # Tiny smoke test: print a few samples and empirical means
    xs_u = uniform_samples(5)
    xs_e = exponential_samples(10_000, 1.7)
    xs_p = poisson_samples(10_000, 4.0)

    print("Uniform(0,1) 5 samples:", xs_u)
    print("Exp(1.7) mean ~ 1/1.7 =", sum(xs_e) / len(xs_e))
    print("Pois(4.0) mean ~ 4.0   =", sum(xs_p) / len(xs_p))

