# pkg_name/model/regression.py
from __future__ import annotations
import math
from typing import Optional, Tuple, Dict, Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt


class LinearRegression:
    """
    A minimal PyTorch-based Linear Regression for one variable.

    Model: y = w1 * x + w0
    Loss : Mean Squared Error (MSE)

    Assignment requirements covered:
      - __init__(learning_rate, n_epochs) sets optimizer=SGD and loss=MSE
      - forward(x) computes y
      - fit(train) trains; optionally accepts test set and computes R^2 on test
      - predict(x) predicts AnnualProduction given BCR
      - analysis() creates a single figure containing:
          (i) data + fitted line,
          (ii) loss vs. epoch,
          (iii) w1 history,
          (iv) w0 history
      - stores w0, w1, and loss histories during training
    """

    def __init__(
        self,
        learning_rate: float = 1e-2,
        n_epochs: int = 1000,
        tolerance: float = 1e-6,
        seed: Optional[int] = None,
    ):
        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed)

        self.learning_rate = float(learning_rate)
        self.n_epochs = int(n_epochs)
        self.tolerance = float(tolerance)

        # Parameters
        self.w1 = nn.Parameter(torch.randn(1, requires_grad=True))
        self.w0 = nn.Parameter(torch.randn(1, requires_grad=True))

        # Optimizer and loss
        self.criterion = nn.MSELoss()
        self.optimizer = optim.SGD([self.w1, self.w0], lr=self.learning_rate)

        # Training artifacts
        self.loss_history: list[float] = []
        self.w1_history: list[float] = []
        self.w0_history: list[float] = []

        # Bookkeeping
        self._fitted: bool = False
        self._train_r2: Optional[float] = None
        self._test_r2: Optional[float] = None

        # Cache of the last train data (for plotting)
        self._X_train: Optional[np.ndarray] = None
        self._y_train: Optional[np.ndarray] = None

    # (b) forward
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w1 * x + self.w0

    @staticmethod
    def _to_tensor_1d(x: np.ndarray | list | torch.Tensor) -> torch.Tensor:
        if isinstance(x, torch.Tensor):
            t = x
        else:
            t = torch.tensor(x, dtype=torch.float32)
        return t.view(-1)

    @staticmethod
    def _r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = y_true.reshape(-1)
        y_pred = y_pred.reshape(-1)
        ss_res = float(np.sum((y_true - y_pred) ** 2))
        ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
        return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    # (c) fit
    def fit(
        self,
        X_train: np.ndarray | list | torch.Tensor,
        y_train: np.ndarray | list | torch.Tensor,
        X_test: Optional[np.ndarray | list | torch.Tensor] = None,
        y_test: Optional[np.ndarray | list | torch.Tensor] = None,
        verbose: bool = False,
    ) -> "LinearRegression":
        x = self._to_tensor_1d(X_train)
        y = self._to_tensor_1d(y_train)

        self._X_train = x.detach().cpu().numpy()
        self._y_train = y.detach().cpu().numpy()

        prev_loss = math.inf
        for epoch in range(1, self.n_epochs + 1):
            self.optimizer.zero_grad()
            y_pred = self.forward(x)
            loss = self.criterion(y_pred, y)
            loss.backward()
            self.optimizer.step()

            # store histories
            L = loss.item()
            self.loss_history.append(L)
            self.w1_history.append(float(self.w1.detach().cpu().numpy()))
            self.w0_history.append(float(self.w0.detach().cpu().numpy()))

            if verbose and (epoch % max(1, self.n_epochs // 10) == 0 or epoch == 1):
                print(f"[{epoch:5d}/{self.n_epochs}] loss={L:.6f} w1={self.w1.item():.6f} w0={self.w0.item():.6f}")

            # simple early stopping on loss change
            if abs(prev_loss - L) < self.tolerance:
                if verbose:
                    print(f"Converged at epoch {epoch} (Δloss < {self.tolerance:g}).")
                break
            prev_loss = L

        # compute train R^2
        with torch.no_grad():
            yhat_tr = self.forward(x).detach().cpu().numpy()
        self._train_r2 = self._r2_score(self._y_train, yhat_tr)

        # optionally compute test R^2 (assignment calls for computing R^2 on test data)
        if X_test is not None and y_test is not None:
            xt = self._to_tensor_1d(X_test)
            yt = self._to_tensor_1d(y_test)
            with torch.no_grad():
                yhat_te = self.forward(xt).detach().cpu().numpy()
            self._test_r2 = self._r2_score(yt.detach().cpu().numpy(), yhat_te)

        self._fitted = True
        return self

    # (d) predict
    def predict(self, X: np.ndarray | list | torch.Tensor) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Call fit(...) before predict(...).")
        x = self._to_tensor_1d(X)
        with torch.no_grad():
            yhat = self.forward(x).detach().cpu().numpy()
        return yhat

    def summary(self) -> Dict[str, Any]:
        if not self._fitted:
            raise RuntimeError("Model not fitted.")
        return {
            "parameters": {"w1 (slope)": float(self.w1.item()), "w0 (intercept)": float(self.w0.item())},
            "training": {
                "epochs_run": len(self.loss_history),
                "final_loss": self.loss_history[-1] if self.loss_history else None,
                "train_R2": self._train_r2,
                "test_R2": self._test_r2,
            },
        }

    # (e) analysis plots on one figure
    def analysis(self, title: Optional[str] = None, figsize: Tuple[int, int] = (12, 9)) -> plt.Figure:
        """
        Creates ONE figure with 4 subplots:
          1) scatter of training data + fitted line
          2) loss vs. epoch
          3) w1 vs. epoch
          4) w0 vs. epoch
        """
        if not self._fitted:
            raise RuntimeError("Fit the model before calling analysis().")
        if self._X_train is None or self._y_train is None:
            raise RuntimeError("Training data cache is empty.")

        X = self._X_train
        y = self._y_train

        xx = np.linspace(X.min(), X.max(), 200)
        yy = self.predict(xx)

        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.25)

        ax1 = fig.add_subplot(gs[0, 0])
        ax1.scatter(X, y, alpha=0.7, label="Data")
        ax1.plot(xx, yy, linewidth=2, label=f"Fit: y = {self.w1.item():.3f}x + {self.w0.item():.3f}")
        ax1.set_xlabel("BCR (x)")
        ax1.set_ylabel("AnnualProduction (y)")
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_title("Data & Fitted Line")

        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(np.arange(1, len(self.loss_history) + 1), self.loss_history, linewidth=2)
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Loss (MSE)")
        ax2.grid(True, alpha=0.3)
        ax2.set_title("Loss vs. Epoch")

        ax3 = fig.add_subplot(gs[1, 0])
        ax3.plot(np.arange(1, len(self.w1_history) + 1), self.w1_history, linewidth=2)
        ax3.set_xlabel("Epoch")
        ax3.set_ylabel("w1 (slope)")
        ax3.grid(True, alpha=0.3)
        ax3.set_title("w1 during Training")

        ax4 = fig.add_subplot(gs[1, 1])
        ax4.plot(np.arange(1, len(self.w0_history) + 1), self.w0_history, linewidth=2)
        ax4.set_xlabel("Epoch")
        ax4.set_ylabel("w0 (intercept)")
        ax4.grid(True, alpha=0.3)
        ax4.set_title("w0 during Training")

        if title:
            fig.suptitle(title, y=1.02, fontsize=14)
        return fig

