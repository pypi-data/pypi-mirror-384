# model/regression.py
import warnings
from typing import Tuple, Optional, Iterable

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from scipy import stats


class LinearRegression:
    """
    PyTorch-based Linear Regression (one variable)

    Model: y = w1 * x + w0
    Loss:  Mean Squared Error (MSE)
    Optimizer: SGD

    This class includes:
      - gradient-based training (fit) with optional test set and R^2 reporting
      - forward/predict helpers
      - training history of w0, w1, and loss for plotting
      - (optional) confidence intervals & regression band plot (kept from your code)
    """

    def __init__(self, learning_rate: float = 0.01, max_epochs: int = 1000,
                 tolerance: float = 1e-6):
        self.learning_rate = learning_rate
        self.max_epochs = int(max_epochs)
        self.tolerance = float(tolerance)

        # parameters (torch Parameters so autograd tracks them)
        self.w1 = nn.Parameter(torch.randn(1, requires_grad=True))  # slope
        self.w0 = nn.Parameter(torch.randn(1, requires_grad=True))  # intercept

        # optimizer + loss
        self.criterion = nn.MSELoss()
        self.optimizer = optim.SGD([self.w1, self.w0], lr=self.learning_rate)

        # buffers set during fit
        self.X_train: Optional[torch.Tensor] = None
        self.y_train: Optional[torch.Tensor] = None
        self.n_samples: Optional[int] = None

        # stats for CIs
        self.residual_sum_squares: Optional[float] = None
        self.X_mean: Optional[float] = None
        self.X_var: Optional[float] = None

        # training history
        self.w0_hist: list[float] = []
        self.w1_hist: list[float] = []
        self.loss_hist: list[float] = []

        self.fitted: bool = False

    # ---------- core model ----------
    def forward(self, X: torch.Tensor) -> torch.Tensor:
        """Compute ŷ = w1 * X + w0. X shape: (N,) or (N,1)"""
        if X.ndim == 2 and X.shape[1] == 1:
            X = X.squeeze(1)
        return self.w1 * X + self.w0

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: Optional[np.ndarray] = None,
        y_test: Optional[np.ndarray] = None,
        verbose: bool = False,
    ) -> Optional[float]:
        """
        Train on (X_train, y_train). If test data are provided,
        compute & print R^2 on the test set and return it.
        """
        # tensors
        self.X_train = torch.tensor(np.asarray(X_train), dtype=torch.float32).reshape(-1)
        self.y_train = torch.tensor(np.asarray(y_train), dtype=torch.float32).reshape(-1)
        self.n_samples = int(self.X_train.numel())

        # stats for CIs
        x_np = self.X_train.numpy()
        self.X_mean = float(np.mean(x_np))
        self.X_var = float(np.var(x_np, ddof=1)) if self.n_samples > 1 else 0.0

        prev_loss = float("inf")
        self.w0_hist.clear(); self.w1_hist.clear(); self.loss_hist.clear()

        for epoch in range(self.max_epochs):
            self.optimizer.zero_grad()
            y_pred = self.forward(self.X_train)
            loss = self.criterion(y_pred, self.y_train)
            loss.backward()
            self.optimizer.step()

            # record history
            self.loss_hist.append(float(loss.item()))
            self.w0_hist.append(float(self.w0.detach().item()))
            self.w1_hist.append(float(self.w1.detach().item()))

            if verbose and (epoch % max(1, self.max_epochs // 10) == 0 or epoch == self.max_epochs - 1):
                print(f"[{epoch+1:4d}/{self.max_epochs}] "
                      f"loss={self.loss_hist[-1]:.6f}  "
                      f"w0={self.w0_hist[-1]:.6f}  w1={self.w1_hist[-1]:.6f}")

            # early stopping
            if abs(prev_loss - self.loss_hist[-1]) < self.tolerance:
                if verbose:
                    print(f"Converged after {epoch+1} epochs")
                break
            prev_loss = self.loss_hist[-1]

        # RSS for CIs
        with torch.no_grad():
            residuals = self.y_train - self.forward(self.X_train)
            self.residual_sum_squares = float(torch.sum(residuals ** 2))

        self.fitted = True

        # R^2 on test (if provided)
        r2 = None
        if X_test is not None and y_test is not None:
            y_pred_test = self.predict(np.asarray(X_test))
            y_test_np = np.asarray(y_test).reshape(-1)
            ss_res = float(np.sum((y_test_np - y_pred_test) ** 2))
            ss_tot = float(np.sum((y_test_np - y_test_np.mean()) ** 2))
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
            print(f"R^2 (test) = {r2:.6f}")
        return r2

    @torch.no_grad()
    def predict(self, X: Iterable[float] | np.ndarray) -> np.ndarray:
        """Predict for new X. Returns shape (N,) numpy array."""
        if not self.fitted:
            raise ValueError("Model must be fitted before predicting.")
        X_t = torch.tensor(np.asarray(X), dtype=torch.float32).reshape(-1)
        y_hat = self.forward(X_t)
        return y_hat.cpu().numpy().reshape(-1)

    def get_parameters(self) -> Tuple[float, float]:
        """Return (w1, w0)."""
        if not self.fitted:
            raise ValueError("Model must be fitted before accessing parameters.")
        return float(self.w1.item()), float(self.w0.item())

    # ---------- analysis / plotting per HW spec ----------
    def analysis_plot(self, X_train: np.ndarray, y_train: np.ndarray,
                      title: str = "Training Summary"):
        """
        Create a figure with 3 subplots:
          (1) scatter of training data + fitted line
          (2) parameter traces (w0, w1)
          (3) loss curve
        """
        if not self.fitted:
            raise ValueError("Fit the model before calling analysis_plot().")

        X = np.asarray(X_train).reshape(-1)
        y = np.asarray(y_train).reshape(-1)

        # fitted line over range
        x_line = np.linspace(X.min(), X.max(), 300, dtype=np.float32)
        y_line = self.predict(x_line)

        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

        # (1) data + regression line
        axes[0].scatter(X, y, s=14, alpha=0.7, label="train data")
        axes[0].plot(x_line, y_line, lw=2.5, label="fitted line")
        axes[0].set_xlabel("BCR (x)")
        axes[0].set_ylabel("AnnualProduction (y)")
        axes[0].legend()
        axes[0].grid(True, ls="--", alpha=0.3)

        # (2) parameter traces
        axes[1].plot(self.w0_hist, label="w0 (intercept)")
        axes[1].plot(self.w1_hist, label="w1 (slope)")
        axes[1].set_xlabel("epoch")
        axes[1].set_ylabel("value")
        axes[1].legend()
        axes[1].grid(True, ls="--", alpha=0.3)

        # (3) loss curve
        axes[2].plot(self.loss_hist)
        axes[2].set_xlabel("epoch")
        axes[2].set_ylabel("MSE loss")
        axes[2].grid(True, ls="--", alpha=0.3)

        fig.suptitle(title, y=1.02, fontsize=12)
        fig.tight_layout()
        return fig

    # ---------- optional extras from your code ----------
    def parameter_confidence_intervals(self, confidence_level: float = 0.95) -> dict:
        """(Optional) CIs for w1 and w0 using classic formulas."""
        if not self.fitted:
            raise ValueError("Fit the model before computing confidence intervals.")

        if self.n_samples is None or self.n_samples < 3:
            raise ValueError("Not enough samples for CI computation.")

        df = self.n_samples - 2
        alpha = 1 - confidence_level
        t_crit = stats.t.ppf(1 - alpha/2, df)

        mse = (self.residual_sum_squares or 0.0) / df
        se_reg = np.sqrt(mse)

        if self.X_var == 0:
            warnings.warn("X variance is zero; CI for w1 is undefined.")
            se_w1 = np.inf
            se_w0 = np.inf
        else:
            se_w1 = se_reg / np.sqrt(self.n_samples * self.X_var)
            se_w0 = se_reg * np.sqrt(1/self.n_samples + (self.X_mean**2)/(self.n_samples * self.X_var))

        w1_val, w0_val = self.get_parameters()
        w1_ci = (w1_val - t_crit * se_w1, w1_val + t_crit * se_w1)
        w0_ci = (w0_val - t_crit * se_w0, w0_val + t_crit * se_w0)

        return {
            "w_1_confidence_interval": w1_ci,
            "w_0_confidence_interval": w0_ci,
            "confidence_level": confidence_level,
            "standard_errors": {
                "se_w1": se_w1,
                "se_w0": se_w0,
                "se_regression": se_reg,
            },
        }

    def plot_regression_with_confidence_band(
        self,
        confidence_level: float = 0.95,
        figsize: tuple[int, int] = (10, 6),
        title: Optional[str] = None,
    ):
        """(Optional) your original CI band plot."""
        if not self.fitted:
            raise ValueError("Fit the model before plotting.")

        fig, ax = plt.subplots(figsize=figsize)
        X_np = self.X_train.numpy()
        y_np = self.y_train.numpy()

        X_range = np.linspace(X_np.min(), X_np.max(), 200)
        y_pred = self.predict(X_range)

        df = self.n_samples - 2
        alpha = 1 - confidence_level
        t_crit = stats.t.ppf(1 - alpha/2, df)
        mse = (self.residual_sum_squares or 0.0) / df
        se_reg = np.sqrt(mse)

        X_center = X_range - (self.X_mean or 0.0)
        if self.X_var == 0:
            se_pred = np.full_like(X_range, np.inf, dtype=float)
        else:
            se_pred = se_reg * np.sqrt(1/self.n_samples + X_center**2 / (self.n_samples * self.X_var))

        margin = t_crit * se_pred
        ax.scatter(X_np, y_np, alpha=0.6, label="data")
        ax.plot(X_range, y_pred, "r-", lw=2, label="fitted line")
        ax.fill_between(X_range, y_pred - margin, y_pred + margin, alpha=0.25, color="red",
                        label=f"{int(confidence_level*100)}% band")

        w1_val, w0_val = self.get_parameters()
        ax.set_xlabel("X")
        ax.set_ylabel("y")
        ax.set_title(title or f"Linear Regression: y = {w1_val:.3f}x + {w0_val:.3f}")
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()
        return fig

