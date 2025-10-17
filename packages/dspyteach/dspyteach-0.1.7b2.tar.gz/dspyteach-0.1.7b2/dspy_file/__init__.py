"""DSPy file teaching analyzer package."""

from .file_analyzer import FileTeachingAnalyzer, TeachingConfig
from .refactor_analyzer import FileRefactorAnalyzer, RefactorTeachingConfig

__all__ = [
    "FileTeachingAnalyzer",
    "TeachingConfig",
    "FileRefactorAnalyzer",
    "RefactorTeachingConfig",
]
