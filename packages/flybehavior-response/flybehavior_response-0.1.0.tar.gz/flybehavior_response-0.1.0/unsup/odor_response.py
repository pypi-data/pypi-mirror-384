"""Quantify odor-evoked responses using area-under-curve metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from .pca_core import PCAResults, compute_pca


@dataclass
class OdorResponseResults:
    """Container bundling per-trial odor response metrics."""

    metrics: pd.DataFrame
    cluster_summary: pd.DataFrame
    feature_matrix: np.ndarray | None
    feature_timepoints: np.ndarray | None
    trial_indices: np.ndarray
    trial_labels: np.ndarray
    trial_ids: np.ndarray
    auc_ratios: np.ndarray


def _match_metadata_columns(
    metadata: pd.DataFrame | None,
) -> Mapping[str, str | None]:
    """Identify canonical metadata columns for dataset context."""

    resolved: dict[str, str | None] = {
        "dataset": None,
        "fly": None,
        "trial_type": None,
        "trial_label": None,
    }

    if metadata is None or metadata.empty:
        return resolved

    lower_columns = {column.lower(): column for column in metadata.columns}

    candidates: Mapping[str, Tuple[str, ...]] = {
        "dataset": (
            "dataset",
            "dataset_name",
            "dataset_label",
            "dataset_full",
        ),
        "fly": (
            "fly",
            "fly_id",
            "fly_name",
            "fly_label",
        ),
        "trial_type": (
            "trial_type",
            "trial_type_name",
            "trialtype",
        ),
        "trial_label": (
            "trial_label",
            "trial_label_name",
            "trialname",
        ),
    }

    for key, options in candidates.items():
        for option in options:
            column = lower_columns.get(option.lower())
            if column is not None:
                resolved[key] = column
                break

    return resolved


def _extract_metadata_values(
    metadata: pd.DataFrame | None,
    column_map: Mapping[str, str | None],
    row_idx: int,
) -> Mapping[str, str]:
    """Return stringified metadata context for a given trial."""

    defaults = {
        "dataset": "",
        "fly": "",
        "trial_type": "",
        "trial_label": "",
    }

    if metadata is None or metadata.empty:
        return defaults

    values: dict[str, str] = {}
    row = metadata.iloc[row_idx]

    for key, column in column_map.items():
        if column is None:
            values[key] = ""
            continue
        raw_value = row.get(column, "")
        if pd.isna(raw_value):  # type: ignore[arg-type]
            values[key] = ""
        else:
            values[key] = str(raw_value)

    return {**defaults, **values}


def _validate_time_windows(
    time_points: np.ndarray,
    odor_on: float,
    odor_off: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return boolean masks for baseline and odor intervals."""

    baseline_mask = time_points < odor_on
    odor_mask = (time_points >= odor_on) & (time_points <= odor_off)

    if not baseline_mask.any():
        raise ValueError(
            "Baseline interval is empty; ensure odor_on exceeds earliest frame."
        )
    if not odor_mask.any():
        raise ValueError(
            "Odor interval is empty; check odor_on/odor_off against frame range."
        )

    return baseline_mask, odor_mask


def _compute_frame_durations(time_values: np.ndarray) -> np.ndarray:
    """Approximate dwell time for each sampled frame."""

    if time_values.size == 1:
        return np.ones_like(time_values, dtype=float)

    diffs = np.diff(time_values.astype(float))
    durations = np.empty_like(time_values, dtype=float)
    durations[:-1] = diffs
    durations[-1] = diffs[-1] if diffs.size else 1.0
    durations[durations <= 0] = 1.0
    return durations


def evaluate_odor_response(
    traces: np.ndarray,
    labels: Sequence[int],
    metadata: pd.DataFrame | None,
    time_points: Sequence[float],
    *,
    odor_on: float,
    odor_off: float,
    target_clusters: Sequence[int] = (0, 1),
) -> OdorResponseResults:
    """Compute odor-evoked AUC metrics for select clusters."""

    if traces.ndim != 2:
        raise ValueError("traces must be two-dimensional")

    labels_array = np.asarray(labels)
    time_array = np.asarray(time_points, dtype=float)
    baseline_mask, odor_mask = _validate_time_windows(time_array, odor_on, odor_off)

    baseline = traces[:, baseline_mask]
    odor_response = traces[:, odor_mask]
    frame_durations = _compute_frame_durations(time_array[odor_mask])

    baseline_mean = baseline.mean(axis=1)
    baseline_std = baseline.std(axis=1, ddof=0)
    threshold = baseline_mean + 4.0 * baseline_std

    positive_response = odor_response - threshold[:, None]
    positive_response[positive_response < 0] = 0.0

    weighted_response = positive_response * frame_durations
    auc_values = weighted_response.sum(axis=1)
    total_duration = frame_durations.sum()
    threshold_area = np.clip(np.abs(threshold) * total_duration, a_min=1e-8, a_max=None)
    auc_ratio = auc_values / threshold_area

    records: list[dict[str, object]] = []
    selected_rows: list[int] = []
    selected_labels: list[int] = []
    selected_ids: list[object] = []
    selected_auc_ratios: list[float] = []
    metadata = metadata if metadata is not None else pd.DataFrame()
    index_list = list(metadata.index)
    column_map = _match_metadata_columns(metadata)

    target_set = {int(label) for label in target_clusters}

    for row_idx, cluster_label in enumerate(labels_array):
        if int(cluster_label) not in target_set:
            continue
        context = _extract_metadata_values(metadata, column_map, row_idx)
        record = {
            "cluster_label": int(cluster_label),
            "baseline_mean": float(baseline_mean[row_idx]),
            "baseline_std": float(baseline_std[row_idx]),
            "threshold": float(threshold[row_idx]),
            "auc_above_threshold": float(auc_values[row_idx]),
            "auc_ratio": float(auc_ratio[row_idx]),
        }
        record.update(context)
        records.append(record)
        selected_rows.append(row_idx)
        selected_labels.append(int(cluster_label))
        descriptor_parts = [
            context.get("dataset", ""),
            context.get("fly", ""),
            context.get("trial_type", ""),
            context.get("trial_label", ""),
        ]
        descriptor = " | ".join(part for part in descriptor_parts if part)
        fallback_identifier = (
            index_list[row_idx] if row_idx < len(index_list) else row_idx
        )
        if not descriptor:
            descriptor = str(fallback_identifier)
        selected_ids.append(descriptor)
        selected_auc_ratios.append(float(auc_ratio[row_idx]))

    metrics_df = pd.DataFrame(records)
    if metrics_df.empty:
        metrics_df = pd.DataFrame(
            columns=[
                "rank",
                "dataset",
                "fly",
                "trial_type",
                "trial_label",
                "cluster_label",
                "baseline_mean",
                "baseline_std",
                "threshold",
                "auc_above_threshold",
                "auc_ratio",
            ]
        )
    else:
        metrics_df.sort_values("auc_ratio", ascending=False, inplace=True)
        metrics_df.insert(0, "rank", np.arange(1, len(metrics_df) + 1))
        desired_order = [
            "rank",
            "dataset",
            "fly",
            "trial_type",
            "trial_label",
            "cluster_label",
            "baseline_mean",
            "baseline_std",
            "threshold",
            "auc_above_threshold",
            "auc_ratio",
        ]
        existing_order = [
            column
            for column in desired_order
            if column in metrics_df.columns
        ]
        remaining = [
            column
            for column in metrics_df.columns
            if column not in existing_order
        ]
        metrics_df = metrics_df[existing_order + remaining]

    summary_columns = [
        "cluster_label",
        "n_trials",
        "mean_auc_ratio",
        "median_auc_ratio",
        "max_auc_ratio",
    ]
    summary_df = pd.DataFrame(columns=summary_columns)
    if not metrics_df.empty:
        summary_df = (
            metrics_df.groupby("cluster_label")
            .agg(
                n_trials=("auc_ratio", "size"),
                mean_auc_ratio=("auc_ratio", "mean"),
                median_auc_ratio=("auc_ratio", "median"),
                max_auc_ratio=("auc_ratio", "max"),
            )
            .reset_index()
            .sort_values("mean_auc_ratio", ascending=False)
        )
        summary_df = summary_df[summary_columns]

    feature_matrix: np.ndarray | None = None
    feature_time: np.ndarray | None = None
    if selected_rows:
        feature_matrix = positive_response[selected_rows]
        feature_time = time_array[odor_mask]

    return OdorResponseResults(
        metrics=metrics_df,
        cluster_summary=summary_df,
        feature_matrix=feature_matrix,
        feature_timepoints=feature_time,
        trial_indices=np.asarray(selected_rows, dtype=int),
        trial_labels=np.asarray(selected_labels, dtype=int),
        trial_ids=np.asarray(selected_ids, dtype=object),
        auc_ratios=np.asarray(selected_auc_ratios, dtype=float),
    )


def run_response_pca(
    feature_matrix: np.ndarray | None,
    *,
    max_pcs: int,
    random_state: int | None = None,
) -> PCAResults | None:
    """Fit PCA on odor-response features when sufficient variance exists."""

    if feature_matrix is None:
        return None
    if feature_matrix.shape[0] < 2 or feature_matrix.shape[1] < 2:
        return None

    col_std = feature_matrix.std(axis=0)
    if np.allclose(col_std, 0):
        return None

    capped_pcs = min(max_pcs, feature_matrix.shape[1])
    return compute_pca(feature_matrix, max_pcs=capped_pcs, random_state=random_state)


__all__ = ["OdorResponseResults", "evaluate_odor_response", "run_response_pca"]
