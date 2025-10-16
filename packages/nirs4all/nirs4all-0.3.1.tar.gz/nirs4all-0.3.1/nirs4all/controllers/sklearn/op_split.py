from __future__ import annotations

import inspect
from typing import Any, Dict, Tuple, TYPE_CHECKING, List
import copy
from nirs4all.controllers.controller import OperatorController
from nirs4all.controllers.registry import register_controller

if TYPE_CHECKING:  # pragma: no cover
    from nirs4all.pipeline.runner import PipelineRunner
    from nirs4all.dataset.dataset import SpectroDataset


def _needs(splitter: Any) -> Tuple[bool, bool]:
    """Return booleans *(needs_y, needs_groups)* for the given splitter.

    Introspects the signature of ``split`` *plus* estimator tags (when
    available) so it works for *any* class respecting the sklearn contract.
    """
    split_fn = getattr(splitter, "split", None)
    if not callable(split_fn):
        # No split method → cannot be a valid splitter
        return False, False

    sig = inspect.signature(split_fn)
    params = sig.parameters

    needs_y = "y" in params # and params["y"].default is inspect._empty
    # Check if 'groups' parameter exists - sklearn group splitters have groups=None default
    # but still require the parameter to be provided for proper operation
    needs_g = "groups" in params

    # Honour estimator tags (sklearn >=1.3)
    if hasattr(splitter, "_get_tags"):
        tags = splitter._get_tags()
        needs_y = needs_y or tags.get("requires_y", False)

    return needs_y, needs_g


@register_controller
class CrossValidatorController(OperatorController):
    """Controller for **any** sklearn‑compatible splitter (native or custom)."""

    priority = 10  # processed early but after mandatory pre‑processing steps

    @classmethod
    def matches(cls, step: Any, operator: Any, keyword: str) -> bool:  # noqa: D401
        """Return *True* if *operator* behaves like a splitter.

        **Criteria** – must expose a callable ``split`` whose first positional
        argument is named *X*.  Optional presence of ``get_n_splits`` is a plus
        but not mandatory, so user‑defined simple splitters are still accepted.

        Also matches on the 'split' keyword for group-aware splitting syntax.
        """
        # Priority 1: Match on 'split' keyword (explicit workflow operator)
        if keyword == "split":
            return True

        # Priority 2: Match dict with 'split' key
        if isinstance(step, dict) and "split" in step:
            return True

        # Priority 3: Match objects with split() method (existing behavior)
        if operator is None:
            return False

        split_fn = getattr(operator, "split", None)
        if not callable(split_fn):
            return False
        try:
            sig = inspect.signature(split_fn)
        except (TypeError, ValueError):  # edge‑cases: C‑extensions or cythonised
            return True  # accept – we can still attempt runtime call
        params: List[inspect.Parameter] = [
            p for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        return bool(params) and params[0].name == "X"

    @classmethod
    def use_multi_source(cls) -> bool:  # noqa: D401
        """Cross‑validators themselves are single‑source operators."""
        return False

    @classmethod
    def supports_prediction_mode(cls) -> bool:
        """Cross-validators should not execute during prediction mode."""
        return True

    def execute(  # type: ignore[override]
        self,
        step: Any,
        operator: Any,
        dataset: "SpectroDataset",
        context: Dict[str, Any],
        runner: "PipelineRunner",
        source: int = -1,
        mode: str = "train",
        loaded_binaries: Any = None,
        prediction_store: Any = None
    ):
        """Run ``operator.split`` and store the resulting folds on *dataset*.

        * Smartly supplies ``y`` / ``groups`` only if required.
        * Extracts groups from metadata if specified.
        * Maps local indices back to the global index space.
        * Stores the list of folds into the dataset for subsequent steps.
        """
        # Extract group column specification from step dict
        group_column = None
        if isinstance(step, dict) and "group" in step:
            group_column = step["group"]
            if not isinstance(group_column, str):
                raise TypeError(
                    f"Group column must be a string, got {type(group_column).__name__}"
                )

        local_context = copy.deepcopy(context)
        local_context["partition"] = "train"
        needs_y, needs_g = _needs(operator)
        X = dataset.x(local_context, layout="2d", concat_source=True)
        y = dataset.y(local_context) if needs_y else None

        # Get groups from metadata if available
        groups = None
        if needs_g:
            # Only extract groups if:
            # 1. Explicit group column specified, OR
            # 2. Dataset has metadata (use first column as default)
            if group_column is not None:
                # Explicit group column specified - validate and extract
                if not hasattr(dataset, 'metadata_columns') or not dataset.metadata_columns:
                    raise ValueError(
                        f"Group column '{group_column}' specified but dataset has no metadata columns."
                    )
                if group_column not in dataset.metadata_columns:
                    raise ValueError(
                        f"Group column '{group_column}' not found in metadata.\n"
                        f"Available columns: {dataset.metadata_columns}"
                    )
                # Extract groups from specified column
                try:
                    groups = dataset.metadata_column(group_column, local_context)
                    if len(groups) != X.shape[0]:
                        raise ValueError(
                            f"Group array length ({len(groups)}) doesn't match X rows ({X.shape[0]})"
                        )
                except Exception as e:
                    raise ValueError(
                        f"Failed to extract groups from metadata column '{group_column}': {e}"
                    ) from e
            elif hasattr(dataset, 'metadata_columns') and dataset.metadata_columns:
                # No explicit group column, but metadata available - use first column as default
                group_column = dataset.metadata_columns[0]
                print(
                    f"⚠️ {operator.__class__.__name__} has 'groups' parameter but no 'group' specified. "
                    f"Using default: '{group_column}'"
                )
                try:
                    groups = dataset.metadata_column(group_column, local_context)
                    if len(groups) != X.shape[0]:
                        raise ValueError(
                            f"Group array length ({len(groups)}) doesn't match X rows ({X.shape[0]})"
                        )
                except Exception as e:
                    raise ValueError(
                        f"Failed to extract groups from metadata column '{group_column}': {e}"
                    ) from e
            # else: No group column specified and no metadata available
            # Leave groups=None and let the splitter handle it
            # (will work for splitters that don't require groups, will fail for those that do)

        n_samples = X.shape[0]

        # Build kwargs for split()
        kwargs: Dict[str, Any] = {}
        if needs_y:
            if y is None:
                raise ValueError(
                    f"{operator.__class__.__name__} requires y but dataset.y returned None"
                )
            kwargs["y"] = y
        if needs_g and groups is not None:
            # Only provide groups if we actually extracted them
            # (non-group splitters like KFold, ShuffleSplit ignore groups anyway)
            kwargs["groups"] = groups

        if mode != "predict" and mode != "explain":
            folds = list(operator.split(X, **kwargs))  # Convert to list to avoid iterator consumption

            # Store the folds in the dataset
            dataset.set_folds(folds)

            # If no test partition exists, use first fold as test
            if dataset.x({"partition": "test"}).shape[0] == 0:
                print("⚠️ No test partition found; using first fold as test set.")
                fold_1 = folds[0]
                dataset._indexer.update_by_indices(
                    fold_1[1], {"partition": "test"}
                )

            # Generate binary output with fold information
            headers = [f"fold_{i}" for i in range(len(folds))]
            binary = ",".join(headers).encode("utf-8") + b"\n"
            max_train_samples = max(len(train_idx) for train_idx, _ in folds)

            for row_idx in range(max_train_samples):
                row_values = []
                for fold_idx, (train_idx, val_idx) in enumerate(folds):
                    if row_idx < len(train_idx):
                        row_values.append(str(train_idx[row_idx]))
                    else:
                        row_values.append("")  # Empty cell if this fold has fewer samples
                binary += ",".join(row_values).encode("utf-8") + b"\n"

            # Filename includes group column if used
            folds_name = f"folds_{operator.__class__.__name__}"
            if group_column:
                folds_name += f"_group-{group_column}"
            if hasattr(operator, "random_state"):
                seed = getattr(operator, "random_state")
                if seed is not None:
                    folds_name += f"_seed{seed}"
            folds_name += ".csv"

            return context, [(folds_name, binary)]
        else:
            n_folds = operator.get_n_splits(**kwargs) if hasattr(operator, "get_n_splits") else 1
            dataset.set_folds([(list(range(n_samples)), [])] * n_folds)
            return context, []
