"""Grey-Box Neural Ordinary Differential Equation (Neural ODE) for CSTR dynamics.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-09, and phase-08A:
- Preserves known macroscopic mass balance: dC_A/dt = (Q/V)*(C_A_in - C_A) - r_A(C_A)
- Constrains neural kinetics: r_A(C_A) >= 0 for C_A >= 0, and r_A(0) = 0.
- End-to-end differentiable RK4 integration in PyTorch.
- Seed control, early stopping, gradient clipping, checkpoint saving, and physical diagnostics.
"""

from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import Any, Optional, Sequence
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from backend.app.ml.evaluation import RegressionMetrics, compute_regression_metrics


class NeuralKineticNetwork(nn.Module):
    """Neural network parameterizing the unknown reaction rate r_A(C_A).

    Enforces physical kinetics:
    - r_A(C_A) = 0 when C_A <= 0 (no reaction in the absence of reactant).
    - r_A(C_A) >= 0 when C_A > 0 (strictly consumable reactant).
    """

    def __init__(self, hidden_dim: int = 32, num_layers: int = 2) -> None:
        super().__init__()
        layers: list[nn.Module] = [nn.Linear(1, hidden_dim), nn.Tanh()]
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 1))
        self.mlp = nn.Sequential(*layers)
        self.softplus = nn.Softplus()

    def forward(self, c_a: torch.Tensor) -> torch.Tensor:
        """Compute reaction rate r_A [mol/(L*min)] given C_A [mol/L]."""
        # Ensure c_a is shaped (..., 1)
        orig_shape = c_a.shape
        c_flat = c_a.reshape(-1, 1)

        # Base rate positive scaling
        raw = self.mlp(c_flat)
        rate_pos = self.softplus(raw)

        # Enforce r_A(0) = 0 and r_A >= 0 by scaling by ReLU(C_A)
        c_relu = torch.relu(c_flat)
        rate = c_relu * rate_pos

        return rate.reshape(orig_shape)


class GreyBoxNeuralODE(nn.Module):
    """Grey-box CSTR dynamic model combining macroscopic mass balance with neural kinetics."""

    def __init__(self, hidden_dim: int = 32, num_layers: int = 2) -> None:
        super().__init__()
        self.kinetics = NeuralKineticNetwork(hidden_dim=hidden_dim, num_layers=num_layers)

    def ode_rhs(
        self,
        c_a: torch.Tensor,
        V: float | torch.Tensor,
        Q: float | torch.Tensor,
        C_in: float | torch.Tensor,
    ) -> torch.Tensor:
        """Evaluate dC_A/dt = (Q/V)*(C_in - C_A) - r_A(C_A)."""
        conv = (Q / V) * (C_in - c_a)
        rxn = self.kinetics(c_a)
        return conv - rxn

    def forward_trajectory(
        self,
        t_span: torch.Tensor,
        C_0: float | torch.Tensor,
        V: float,
        Q: float,
        C_in: float,
    ) -> torch.Tensor:
        """Differentiable Runge-Kutta 4 (RK4) integration over 1D time grid."""
        n_steps = len(t_span)
        device = next(self.parameters()).device

        if not isinstance(C_0, torch.Tensor):
            c_current = torch.tensor(float(C_0), dtype=torch.float32, device=device)
        else:
            c_current = C_0.to(device=device, dtype=torch.float32)

        trajectory = [c_current]

        for i in range(n_steps - 1):
            dt = float(t_span[i + 1] - t_span[i])
            if dt <= 0:
                raise ValueError("Time grid must be strictly monotonically increasing.")

            k1 = self.ode_rhs(c_current, V, Q, C_in)
            k2 = self.ode_rhs(c_current + 0.5 * dt * k1, V, Q, C_in)
            k3 = self.ode_rhs(c_current + 0.5 * dt * k2, V, Q, C_in)
            k4 = self.ode_rhs(c_current + dt * k3, V, Q, C_in)

            c_next = c_current + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            # Physical projection: concentration cannot be negative
            c_current = torch.relu(c_next)
            trajectory.append(c_current)

        return torch.stack(trajectory)


@dataclass
class TrajectorySample:
    """Preprocessed trajectory sample for Neural ODE training and validation."""

    trajectory_id: str
    t: np.ndarray
    C_true: np.ndarray
    V: float
    Q: float
    C_in: float
    C_0: float


@dataclass
class NeuralODETrainingResult:
    """Artifacts, curves, and evaluation metrics from Neural ODE training."""

    model: GreyBoxNeuralODE
    best_val_loss: float
    best_epoch: int
    train_history: list[float]
    val_history: list[float]
    train_metrics: RegressionMetrics
    val_metrics: RegressionMetrics
    test_metrics: RegressionMetrics
    training_duration_seconds: float
    checkpoint_path: Optional[str] = None


class GreyBoxODESimulator:
    """Inference wrapper for trained Grey-box Neural ODE."""

    def __init__(self, model: GreyBoxNeuralODE) -> None:
        self.model = model
        self.model.eval()

    def simulate(
        self,
        t_span: Sequence[float],
        C_0: float,
        V: float,
        Q: float,
        C_in: float,
    ) -> np.ndarray:
        """Simulate concentration trajectory using the trained neural ODE."""
        t_tensor = torch.tensor(t_span, dtype=torch.float32)
        with torch.no_grad():
            c_pred = self.model.forward_trajectory(t_tensor, C_0, V, Q, C_in)
        return c_pred.cpu().numpy()

    def predict_reaction_rate(self, c_a: float | np.ndarray) -> np.ndarray:
        """Query the learned reaction rate r_A(C_A)."""
        c_arr = np.asarray(c_a, dtype=np.float32)
        c_tensor = torch.from_numpy(c_arr)
        with torch.no_grad():
            rates = self.model.kinetics(c_tensor)
        return rates.cpu().numpy()


def parse_trajectories_from_df(
    df: Any,
    trajectory_ids: set[str],
    target_col: str = "C_A_clean_mol_L",
) -> list[TrajectorySample]:
    """Parse distinct trajectory samples from dataframe grouped by trajectory_id."""
    import pandas as pd
    samples: list[TrajectorySample] = []
    subset = df[df["trajectory_id"].isin(trajectory_ids)]

    for traj_id, group in subset.groupby("trajectory_id", sort=False):
        group_sorted = group.sort_values("time_min")
        t = group_sorted["time_min"].to_numpy(dtype=np.float64)
        c_vals = group_sorted[target_col].to_numpy(dtype=np.float64)
        v_val = float(group_sorted["V_L"].iloc[0])
        q_val = float(group_sorted["Q_L_min"].iloc[0])
        cin_val = float(group_sorted["C_A_in_mol_L"].iloc[0])
        c0_val = float(group_sorted["C_A_0_mol_L"].iloc[0])

        samples.append(
            TrajectorySample(
                trajectory_id=str(traj_id),
                t=t,
                C_true=c_vals,
                V=v_val,
                Q=q_val,
                C_in=cin_val,
                C_0=c0_val,
            )
        )
    return samples


def train_grey_box_neural_ode(
    train_samples: list[TrajectorySample],
    val_samples: list[TrajectorySample],
    test_samples: list[TrajectorySample],
    hidden_dim: int = 32,
    num_layers: int = 2,
    lr: float = 0.01,
    epochs: int = 60,
    patience: int = 15,
    seed: int = 42,
    checkpoint_dir: Optional[Path] = None,
) -> NeuralODETrainingResult:
    """Train Grey-Box Neural ODE with strict validation early stopping and checkpointing."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    start_time = time.time()
    model = GreyBoxNeuralODE(hidden_dim=hidden_dim, num_layers=num_layers)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    loss_fn = nn.MSELoss()

    best_val_loss = float("inf")
    best_epoch = 0
    best_state_dict: Optional[dict[str, Any]] = None
    patience_counter = 0

    train_loss_history: list[float] = []
    val_loss_history: list[float] = []

    for epoch in range(1, epochs + 1):
        model.train()
        train_losses: list[float] = []

        # Process training trajectories
        for sample in train_samples:
            optimizer.zero_grad()
            t_span = torch.tensor(sample.t, dtype=torch.float32)
            c_target = torch.tensor(sample.C_true, dtype=torch.float32)

            c_pred = model.forward_trajectory(
                t_span, sample.C_0, sample.V, sample.Q, sample.C_in
            )
            loss = loss_fn(c_pred, c_target)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_losses.append(loss.item())

        mean_train_loss = float(np.mean(train_losses))
        train_loss_history.append(mean_train_loss)

        # Validation evaluation
        model.eval()
        val_losses: list[float] = []
        with torch.no_grad():
            for sample in val_samples:
                t_span = torch.tensor(sample.t, dtype=torch.float32)
                c_target = torch.tensor(sample.C_true, dtype=torch.float32)
                c_pred = model.forward_trajectory(
                    t_span, sample.C_0, sample.V, sample.Q, sample.C_in
                )
                v_loss = loss_fn(c_pred, c_target)
                val_losses.append(v_loss.item())

        mean_val_loss = float(np.mean(val_losses))
        val_loss_history.append(mean_val_loss)

        # Early stopping logic
        if mean_val_loss < best_val_loss:
            best_val_loss = mean_val_loss
            best_epoch = epoch
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    # Restore best checkpoint
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)

    # Save checkpoint file if requested
    checkpoint_file: Optional[str] = None
    if checkpoint_dir is not None:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        ckpt_path = checkpoint_dir / f"grey_box_neural_ode_seed{seed}.pt"
        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "best_epoch": best_epoch,
                "best_val_loss": best_val_loss,
                "hidden_dim": hidden_dim,
                "num_layers": num_layers,
                "seed": seed,
            },
            ckpt_path,
        )
        checkpoint_file = str(ckpt_path)

    # Evaluate across train, val, and locked test partitions
    def eval_dataset(samples: list[TrajectorySample]) -> RegressionMetrics:
        all_true: list[float] = []
        all_pred: list[float] = []
        all_res: list[float] = []

        simulator = GreyBoxODESimulator(model)
        for s in samples:
            pred = simulator.simulate(s.t, s.C_0, s.V, s.Q, s.C_in)
            all_true.extend(s.C_true)
            all_pred.extend(pred)

            # Mass balance residual: dC/dt - (Q/V*(Cin - C) - r_A)
            # RK4 internally satisfies this, but let's check finite differences
            dt = np.diff(s.t)
            dC_dt = np.diff(pred) / np.where(dt == 0, 1e-6, dt)
            c_mid = 0.5 * (pred[:-1] + pred[1:])
            rxn_mid = simulator.predict_reaction_rate(c_mid)
            rhs_mid = (s.Q / s.V) * (s.C_in - c_mid) - rxn_mid
            res = np.abs(dC_dt - rhs_mid)
            all_res.extend(res)

        return compute_regression_metrics(
            y_true=all_true,
            y_pred=all_pred,
            residuals=all_res,
        )

    tr_metrics = eval_dataset(train_samples)
    val_metrics = eval_dataset(val_samples)
    te_metrics = eval_dataset(test_samples)

    duration = time.time() - start_time

    return NeuralODETrainingResult(
        model=model,
        best_val_loss=best_val_loss,
        best_epoch=best_epoch,
        train_history=train_loss_history,
        val_history=val_loss_history,
        train_metrics=tr_metrics,
        val_metrics=val_metrics,
        test_metrics=te_metrics,
        training_duration_seconds=duration,
        checkpoint_path=checkpoint_file,
    )
