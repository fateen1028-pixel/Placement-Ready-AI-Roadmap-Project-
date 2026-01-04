class ConcurrencyError(Exception):
    """Raised when an update fails due to a version mismatch."""
    pass

class TemplateResolutionError(Exception):
    """Raised when a task template cannot be resolved."""
    pass
