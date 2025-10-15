"""Dataset result sizes."""

from enum import Enum


class DatasetResultSize(Enum):
    """
    Enumeration of dataset result size categories.

    This enum defines the different size categories for dataset results,
    which can be used for performance optimization and resource allocation.

    Attributes:
        SMALL: Small dataset size category
        MEDIUM: Medium dataset size category
        LARGE: Large dataset size category

    """

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
