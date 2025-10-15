# helpmehelp/matrix/elementary.py
import torch
from typing import Union

TensorLike = Union[torch.Tensor, list, tuple]

def _to_float_tensor(A: TensorLike) -> torch.Tensor:
    """
    Convert input to a *float* tensor so scaling works even if you pass ints.
    Returns a clone to avoid in-place modification of caller's data.
    """
    if isinstance(A, torch.Tensor):
        return A.clone().to(dtype=torch.get_default_dtype())
    return torch.tensor(A, dtype=torch.get_default_dtype()).clone()


def rowswap(A: TensorLike, i_src: int, i_tgt: int) -> torch.Tensor:
    """
    Swap two rows of A and return a *new* tensor.
    Indices are 0-based (i.e., first row is index 0).

    Args
    ----
    A : TensorLike (m x n)
    i_src : int (row to move)
    i_tgt : int (row to swap with)
    """
    M = _to_float_tensor(A)
    m, _ = M.shape
    if not (0 <= i_src < m and 0 <= i_tgt < m):
        raise IndexError("row indices out of range")
    if i_src == i_tgt:
        return M  # nothing to do
    # swap using a buffer
    buf = M[i_src, :].clone()
    M[i_src, :] = M[i_tgt, :]
    M[i_tgt, :] = buf
    return M


def rowscale(A: TensorLike, i_src: int, scale: float) -> torch.Tensor:
    """
    Scale a row R_i <- scale * R_i and return a *new* tensor.
    """
    M = _to_float_tensor(A)
    m, _ = M.shape
    if not (0 <= i_src < m):
        raise IndexError("row index out of range")
    M[i_src, :] = scale * M[i_src, :]
    return M


def rowreplacement(A: TensorLike, i: int, j: int, j_factor: float, k_factor: float) -> torch.Tensor:
    """
    Perform the elementary row operation:

        R_i <- j_factor * R_i + k_factor * R_j

    and return a *new* tensor. (This matches the spec "jR_i + kR_j".)
    """
    M = _to_float_tensor(A)
    m, _ = M.shape
    if not (0 <= i < m and 0 <= j < m):
        raise IndexError("row indices out of range")
    M[i, :] = j_factor * M[i, :] + k_factor * M[j, :]
    return M


def rref(A: TensorLike, tol: float = 1e-12) -> torch.Tensor:
    """
    Compute the Reduced Row Echelon Form (RREF) of A using Gauss–Jordan.

    - Each pivot is 1.
    - Zeros below *and* above each pivot.
    - Uses partial pivoting (max |entry| in column) for numerical stability.

    Returns a *new* float tensor.
    """
    M = _to_float_tensor(A)
    m, n = M.shape
    row = 0  # current pivot row

    for col in range(n):
        if row >= m:
            break

        # 1) Find pivot: index of max |M[r, col]| for r >= row
        pivot_row = torch.argmax(torch.abs(M[row:, col])) + row
        pivot_val = M[pivot_row, col].item()

        # if the column is effectively zero, move to next column
        if abs(pivot_val) <= tol:
            continue

        # 2) Move pivot row up if needed
        if pivot_row != row:
            M = rowswap(M, pivot_row, row)

        # 3) Normalize pivot row to make pivot = 1
        pivot_val = M[row, col].item()
        M = rowscale(M, row, 1.0 / pivot_val)

        # 4) Zero out all *other* rows in this column
        for r in range(m):
            if r == row:
                continue
            factor = M[r, col].item()
            if abs(factor) > tol:
                # R_r <- R_r - factor * R_row
                M[r, :] = M[r, :] - factor * M[row, :]

        # advance to next pivot row
        row += 1

    # Clean tiny numerical noise
    M[torch.abs(M) < tol] = 0.0
    return M

