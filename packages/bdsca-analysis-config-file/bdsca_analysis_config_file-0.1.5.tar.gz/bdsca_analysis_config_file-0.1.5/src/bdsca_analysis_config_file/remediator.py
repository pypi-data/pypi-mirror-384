from __future__ import annotations

from .add_components_ops import AddComponentsOps
from .overwrite_ops import OverwriteOps
from .remediate_ops import RemediateOps


class BlackDuckRemediator(AddComponentsOps, RemediateOps, OverwriteOps):
    """Primary remediator class composed of feature-specific operations."""

    pass
