"""
Embedding model compatibility checker for incremental indexing.

This module provides utilities to check if existing indexes can be reused
when switching embedding models, based on dimension compatibility.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class CompatibilityStatus(Enum):
    """Status of embedding model compatibility check."""

    EXACT_MATCH = "exact_match"  # Same model and dimensions
    DIMENSION_MATCH = "dimension_match"  # Different model, same dimensions
    INCOMPATIBLE = "incompatible"  # Different dimensions


@dataclass
class CompatibilityResult:
    """
    Result of a compatibility check.

    Attributes:
        status: Compatibility status
        can_reuse: Whether indexes can be reused
        reason: Explanation of the result
        warning: Optional warning message
        recommendation: Recommended action
    """

    status: CompatibilityStatus
    can_reuse: bool
    reason: str
    warning: Optional[str] = None
    recommendation: str = ""


class EmbeddingModelCompatibilityChecker:
    """
    Checker for embedding model compatibility.

    Determines if existing indexes can be reused when switching
    embedding models based on dimension compatibility.
    """

    def check_compatibility(
        self,
        stored_model: Optional[str],
        stored_dimensions: Optional[int],
        current_model: str,
        current_dimensions: int,
    ) -> CompatibilityResult:
        """
        Check compatibility between stored and current embedding models.

        Args:
            stored_model: Name of the stored embedding model (None if not stored)
            stored_dimensions: Dimensions of stored embeddings (None if not stored)
            current_model: Name of the current embedding model
            current_dimensions: Dimensions of current embeddings

        Returns:
            CompatibilityResult with status and recommendations
        """
        # Case 1: No stored metadata (new collection or old version)
        if stored_model is None and stored_dimensions is None:
            return CompatibilityResult(
                status=CompatibilityStatus.EXACT_MATCH,
                can_reuse=True,
                reason="No existing metadata found. This is a new collection.",
                recommendation="Proceed with indexing. Metadata will be stored for future compatibility checks.",
            )

        # Case 2: Exact match (same model and dimensions)
        if stored_model == current_model and stored_dimensions == current_dimensions:
            return CompatibilityResult(
                status=CompatibilityStatus.EXACT_MATCH,
                can_reuse=True,
                reason=f"Exact match: {current_model} ({current_dimensions} dimensions)",
                recommendation="Indexes can be reused safely. Proceed with incremental indexing.",
            )

        # Case 3: Different model, same dimensions
        if stored_dimensions == current_dimensions and stored_model != current_model:
            return CompatibilityResult(
                status=CompatibilityStatus.DIMENSION_MATCH,
                can_reuse=True,
                reason=(
                    f"Model changed: {stored_model} → {current_model}, "
                    f"but dimensions match ({current_dimensions})"
                ),
                warning=(
                    "⚠ WARNING: Embeddings from different models may not be directly comparable, "
                    "even with matching dimensions. Semantic search quality may be degraded."
                ),
                recommendation=(
                    "You can reuse indexes (dimensions match), but for best results, "
                    "consider full re-indexing with the new model."
                ),
            )

        # Case 4: Incompatible dimensions
        return CompatibilityResult(
            status=CompatibilityStatus.INCOMPATIBLE,
            can_reuse=False,
            reason=(
                f"Dimension mismatch: stored {stored_dimensions} dimensions ({stored_model}), "
                f"current {current_dimensions} dimensions ({current_model})"
            ),
            warning=(
                "❌ ERROR: Cannot mix embeddings with different dimensions in the same collection."
            ),
            recommendation=(
                "You must either:\n"
                f"  1. Switch back to {stored_model} ({stored_dimensions} dims), OR\n"
                f"  2. Create a new collection for {current_model} ({current_dimensions} dims), OR\n"
                "  3. Perform full re-indexing (clear existing data first)"
            ),
        )

    def get_recommendation(self, result: CompatibilityResult) -> str:
        """
        Get a detailed recommendation based on compatibility result.

        Args:
            result: CompatibilityResult from check_compatibility()

        Returns:
            Detailed recommendation string
        """
        if result.status == CompatibilityStatus.EXACT_MATCH:
            return (
                "✓ COMPATIBLE - Exact Match\n"
                f"  {result.reason}\n"
                f"  → {result.recommendation}"
            )

        elif result.status == CompatibilityStatus.DIMENSION_MATCH:
            return (
                "⚠ COMPATIBLE WITH WARNING - Dimension Match\n"
                f"  {result.reason}\n"
                f"  {result.warning}\n"
                f"  → {result.recommendation}"
            )

        else:  # INCOMPATIBLE
            return (
                "❌ INCOMPATIBLE - Dimension Mismatch\n"
                f"  {result.reason}\n"
                f"  {result.warning}\n"
                f"  → {result.recommendation}"
            )

    def check_and_log(
        self,
        stored_model: Optional[str],
        stored_dimensions: Optional[int],
        current_model: str,
        current_dimensions: int,
    ) -> CompatibilityResult:
        """
        Check compatibility and log the result.

        This is a convenience method that combines check_compatibility()
        with automatic logging.

        Args:
            stored_model: Name of the stored embedding model
            stored_dimensions: Dimensions of stored embeddings
            current_model: Name of the current embedding model
            current_dimensions: Dimensions of current embeddings

        Returns:
            CompatibilityResult with status and recommendations

        Raises:
            ValueError: If models are incompatible (different dimensions)
        """
        result = self.check_compatibility(
            stored_model, stored_dimensions, current_model, current_dimensions
        )

        # Log based on status
        if result.status == CompatibilityStatus.EXACT_MATCH:
            logger.info(f"Model compatibility: {result.reason}")

        elif result.status == CompatibilityStatus.DIMENSION_MATCH:
            logger.warning(f"Model compatibility: {result.reason}")
            if result.warning:
                logger.warning(result.warning)

        else:  # INCOMPATIBLE
            logger.error(f"Model compatibility: {result.reason}")
            if result.warning:
                logger.error(result.warning)
            # Raise error for incompatible models
            raise ValueError(
                f"{result.reason}\n{result.recommendation}"
            )

        return result

    def format_compatibility_report(
        self,
        stored_model: Optional[str],
        stored_dimensions: Optional[int],
        current_model: str,
        current_dimensions: int,
    ) -> str:
        """
        Generate a formatted compatibility report.

        Args:
            stored_model: Name of the stored embedding model
            stored_dimensions: Dimensions of stored embeddings
            current_model: Name of the current embedding model
            current_dimensions: Dimensions of current embeddings

        Returns:
            Formatted report string
        """
        result = self.check_compatibility(
            stored_model, stored_dimensions, current_model, current_dimensions
        )

        report = []
        report.append("=" * 80)
        report.append("EMBEDDING MODEL COMPATIBILITY REPORT")
        report.append("=" * 80)
        report.append("")
        report.append("Stored Model:")
        report.append(f"  Model: {stored_model or 'Not stored'}")
        report.append(f"  Dimensions: {stored_dimensions or 'Not stored'}")
        report.append("")
        report.append("Current Model:")
        report.append(f"  Model: {current_model}")
        report.append(f"  Dimensions: {current_dimensions}")
        report.append("")
        report.append("Compatibility:")
        report.append(f"  Status: {result.status.value}")
        report.append(f"  Can Reuse: {'Yes' if result.can_reuse else 'No'}")
        report.append(f"  Reason: {result.reason}")
        if result.warning:
            report.append(f"  Warning: {result.warning}")
        report.append("")
        report.append("Recommendation:")
        report.append(f"  {result.recommendation}")
        report.append("=" * 80)

        return "\n".join(report)

