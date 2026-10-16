"""Suíte de Testes Automatizados (Test Harness) para o módulo TaskAnalyzer.

Valida a conformidade estrita do código gerado contra a Especificação Técnica
Executável (specs/task_analyzer_spec.md) e as regras de governança (CONTEXT_RULES.md).
"""

from datetime import datetime
from typing import Any

import pytest

from src.exceptions import (
    EmptyDatasetError,
    InconsistentDatesError,
    TaskValidationError,
)
from src.task_analyzer import TaskAnalyzer, analyze_tasks


def test_analyze_valid_tasks_returns_correct_metrics() -> None:
    """Testa o Cenário 1 exato da especificação SDD com 4 tarefas válidas.

    Verifica se tanto ``TaskAnalyzer.analyze`` quanto ``analyze_tasks`` calculam
    corretamente ``total_tarefas``, ``tarefas_concluidas``, ``total_concluidas``,
    ``total_pendentes``, ``tempo_medio_conclusao_horas`` (3.67),
    ``taxa_atraso_percentual`` (33.33) e ``metricas_por_prioridade``.
    """
    tasks: list[dict[str, Any]] = [
        {
            "id": 1,
            "titulo": "Implementar parser ISO 8601",
            "prioridade": "ALTA",
            "data_criacao": "2026-10-16T08:00:00",
            "data_limite": "2026-10-16T12:00:00",
            "data_conclusao": "2026-10-16T10:00:00",
            "status": "CONCLUIDA",
        },
        {
            "id": 2,
            "titulo": "Configurar pipeline de validação",
            "prioridade": "ALTA",
            "data_criacao": "2026-10-16T08:00:00",
            "data_limite": "2026-10-16T10:00:00",
            "data_conclusao": "2026-10-16T11:00:00",
            "status": "CONCLUIDA",
        },
        {
            "id": 3,
            "titulo": "Revisar documentação SDD",
            "prioridade": "BAIXA",
            "data_criacao": "2026-10-16T09:00:00",
            "data_limite": "2026-10-16T18:00:00",
            "data_conclusao": "2026-10-16T15:00:00",
            "status": "CONCLUIDA",
        },
        {
            "id": 4,
            "titulo": "Homologar relatório final",
            "prioridade": "MEDIA",
            "data_criacao": "2026-10-16T10:00:00",
            "data_limite": "2026-10-16T18:00:00",
            "data_conclusao": None,
            "status": "PENDENTE",
        },
    ]

    for analyzer_fn in (TaskAnalyzer.analyze, analyze_tasks):
        result: dict[str, Any] = analyzer_fn(tasks)

        assert result["total_tarefas"] == 4
        assert result["tarefas_concluidas"] == 3
        assert result["total_concluidas"] == 3
        assert result["total_pendentes"] == 1
        assert result["tempo_medio_conclusao_horas"] == 3.67
        assert result["taxa_atraso_percentual"] == 33.33

        prioridades: dict[str, dict[str, int | float]] = result[
            "metricas_por_prioridade"
        ]
        assert prioridades["ALTA"] == {
            "total": 2,
            "concluidas": 2,
            "tempo_medio_horas": 2.5,
            "taxa_atraso_percentual": 50.0,
        }
        assert prioridades["BAIXA"] == {
            "total": 1,
            "concluidas": 1,
            "tempo_medio_horas": 6.0,
            "taxa_atraso_percentual": 0.0,
        }
        assert prioridades["MEDIA"] == {
            "total": 1,
            "concluidas": 0,
            "tempo_medio_horas": 0.0,
            "taxa_atraso_percentual": 0.0,
        }


def test_analyze_inconsistent_dates_raises_exception() -> None:
    """Testa o Cenário 2 de inconsistência cronológica nas datas da tarefa.

    Verifica se ``data_conclusao < data_criacao`` e ``data_limite < data_criacao``
    disparam tanto ``InconsistentDatesError`` quanto ``TaskValidationError`` e
    incluem o ``id`` da tarefa violadora na mensagem da exceção.
    """
    invalid_conclusion_tasks: list[dict[str, Any]] = [
        {
            "id": "TASK-ERR-01",
            "titulo": "Tarefa com conclusão anterior à criação",
            "prioridade": "ALTA",
            "data_criacao": "2026-10-16T14:00:00",
            "data_limite": "2026-10-16T18:00:00",
            "data_conclusao": "2026-10-16T10:00:00",
            "status": "CONCLUIDA",
        }
    ]

    with pytest.raises(InconsistentDatesError) as exc_info_conclusao:
        TaskAnalyzer.analyze(invalid_conclusion_tasks)
    assert "TASK-ERR-01" in str(exc_info_conclusao.value)
    assert isinstance(exc_info_conclusao.value, TaskValidationError)

    invalid_deadline_tasks: list[dict[str, Any]] = [
        {
            "id": "TASK-ERR-02",
            "titulo": "Tarefa com data limite anterior à criação",
            "prioridade": "MEDIA",
            "data_criacao": "2026-10-16T14:00:00",
            "data_limite": "2026-10-16T12:00:00",
            "data_conclusao": None,
            "status": "PENDENTE",
        }
    ]

    with pytest.raises(TaskValidationError) as exc_info_limite:
        analyze_tasks(invalid_deadline_tasks)
    assert "TASK-ERR-02" in str(exc_info_limite.value)
    assert isinstance(exc_info_limite.value, InconsistentDatesError)


def test_analyze_empty_payload_raises_error() -> None:
    """Testa o Cenário 3 da Fase 1 em que lote vazio levanta ``EmptyDatasetError``.

    Garante que ``TaskAnalyzer.analyze([])`` (com ``raise_on_empty=True`` por
    padrão) dispare ``EmptyDatasetError``.
    """
    with pytest.raises(EmptyDatasetError) as exc_info:
        TaskAnalyzer.analyze([])
    assert isinstance(exc_info.value, TaskValidationError)


def test_analyze_empty_and_only_pending_tasks_returns_zero_metrics() -> None:
    """Testa o Caso de Borda da Fase 2 prevenindo ``ZeroDivisionError``.

    Verifica que ``analyze_tasks([])`` e lotes contendo apenas tarefas com
    status ``PENDENTE`` retornam ``0.0`` para ``tempo_medio_conclusao_horas`` e
    ``taxa_atraso_percentual`` sem lançar ``ZeroDivisionError``.
    """
    empty_result: dict[str, Any] = analyze_tasks([])
    assert empty_result["total_tarefas"] == 0
    assert empty_result["tarefas_concluidas"] == 0
    assert empty_result["total_concluidas"] == 0
    assert empty_result["total_pendentes"] == 0
    assert empty_result["tempo_medio_conclusao_horas"] == 0.0
    assert empty_result["taxa_atraso_percentual"] == 0.0

    only_pending_tasks: list[dict[str, Any]] = [
        {
            "id": 101,
            "titulo": "Modelar banco em memória",
            "prioridade": "ALTA",
            "data_criacao": "2026-10-16T08:00:00",
            "data_limite": "2026-10-16T12:00:00",
            "data_conclusao": None,
            "status": "PENDENTE",
        },
        {
            "id": 102,
            "titulo": "Escrever casos de teste adicionais",
            "prioridade": "MEDIA",
            "data_criacao": "2026-10-16T09:00:00",
            "data_limite": "2026-10-16T15:00:00",
            "data_conclusao": None,
            "status": "PENDENTE",
        },
    ]

    pending_result: dict[str, Any] = TaskAnalyzer.analyze(only_pending_tasks)
    assert pending_result["total_tarefas"] == 2
    assert pending_result["tarefas_concluidas"] == 0
    assert pending_result["total_concluidas"] == 0
    assert pending_result["total_pendentes"] == 2
    assert pending_result["tempo_medio_conclusao_horas"] == 0.0
    assert pending_result["taxa_atraso_percentual"] == 0.0
    assert pending_result["metricas_por_prioridade"]["ALTA"][
        "tempo_medio_horas"
    ] == 0.0
    assert pending_result["metricas_por_prioridade"]["ALTA"][
        "taxa_atraso_percentual"
    ] == 0.0


def test_analyze_supports_iso_strings_and_datetime_objects() -> None:
    """Testa suporte híbrido a strings ISO 8601 e objetos ``datetime`` nativos.

    Garante que o analisador processe perfeitamente um lote misto contendo tanto
    objetos ``datetime`` quanto strings ISO 8601.
    """
    mixed_tasks: list[dict[str, Any]] = [
        {
            "id": "MIX-1",
            "titulo": "Tarefa com objetos datetime nativos",
            "prioridade": "ALTA",
            "data_criacao": datetime(2026, 10, 16, 8, 0, 0),
            "data_limite": datetime(2026, 10, 16, 12, 0, 0),
            "data_conclusao": datetime(2026, 10, 16, 10, 0, 0),
            "status": "CONCLUIDA",
        },
        {
            "id": "MIX-2",
            "titulo": "Tarefa com strings ISO 8601",
            "prioridade": "BAIXA",
            "data_criacao": "2026-10-16T08:00:00",
            "data_limite": "2026-10-16T09:00:00",
            "data_conclusao": "2026-10-16T12:00:00",
            "status": "CONCLUIDA",
        },
    ]

    result: dict[str, Any] = analyze_tasks(mixed_tasks)
    assert result["total_tarefas"] == 2
    assert result["tarefas_concluidas"] == 2
    assert result["total_concluidas"] == 2
    assert result["total_pendentes"] == 0
    assert result["tempo_medio_conclusao_horas"] == 3.0
    assert result["taxa_atraso_percentual"] == 50.0
