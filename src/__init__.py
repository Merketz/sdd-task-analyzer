"""Pacote principal do analisador de tarefas orientado por especificação (SDD)."""

from src.exceptions import (
    EmptyDatasetError,
    InconsistentDatesError,
    TaskAnalyzerError,
    TaskValidationError,
)
from src.task_analyzer import TaskAnalyzer, analyze_tasks

__all__: list[str] = [
    "EmptyDatasetError",
    "InconsistentDatesError",
    "TaskAnalyzer",
    "TaskAnalyzerError",
    "TaskValidationError",
    "analyze_tasks",
]
