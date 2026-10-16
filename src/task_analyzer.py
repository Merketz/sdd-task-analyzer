"""Módulo principal de análise e cálculo de métricas de tarefas (SDD).

Implementa o processamento em memória de lotes de tarefas em conformidade estrita
com as diretrizes de governança (CONTEXT_RULES.md) e com a especificação técnica
executável (specs/task_analyzer_spec.md).
"""

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from src.exceptions import (
    EmptyDatasetError,
    InconsistentDatesError,
    TaskAnalyzerError,
    TaskValidationError,
)

logger: logging.Logger = logging.getLogger(__name__)

VALID_PRIORITIES: tuple[str, ...] = ("BAIXA", "MEDIA", "ALTA")
VALID_STATUSES: tuple[str, ...] = (
    "PENDENTE",
    "EM_ANDAMENTO",
    "CONCLUIDA",
    "CANCELADA",
)
REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "titulo",
    "prioridade",
    "data_criacao",
    "data_limite",
    "status",
)


@dataclass(frozen=True)
class NormalizedTask:
    """Representação interna imutável e validada de uma tarefa.

    Attributes:
        task_id: Identificador único da tarefa.
        titulo: Título validado não vazio.
        prioridade: Prioridade validada ('BAIXA', 'MEDIA', 'ALTA').
        data_criacao: Timestamp de criação convertido para ``datetime``.
        data_limite: Timestamp limite convertido para ``datetime``.
        data_conclusao: Timestamp de conclusão ou ``None`` se não concluída.
        status: Status validado da tarefa.
    """

    task_id: str | int
    titulo: str
    prioridade: str
    data_criacao: datetime
    data_limite: datetime
    data_conclusao: datetime | None
    status: str


def _parse_datetime(
    raw_value: datetime | str | None,
    field_name: str,
    task_id: str | int,
    required: bool = True,
) -> datetime | None:
    """Converte de forma segura um valor ISO 8601 ou ``datetime`` em ``datetime``.

    Args:
        raw_value: Valor bruto da data (objeto ``datetime``, ``str`` ISO 8601 ou ``None``).
        field_name: Nome do campo avaliado para composição de mensagens de erro.
        task_id: Identificador da tarefa sob validação.
        required: Indica se o campo é de preenchimento obrigatório.

    Returns:
        Objeto ``datetime`` correspondente ou ``None`` quando opcional e ausente.

    Raises:
        TaskValidationError: Se o valor for nulo quando obrigatório, se o tipo for
            inválido ou se a string não estiver em formato ISO 8601 válido.
    """
    if raw_value is None:
        if required:
            msg = (
                f"Tarefa '{task_id}': o campo obrigatório '{field_name}' "
                "não pode ser nulo."
            )
            logger.error(msg)
            raise TaskValidationError(msg, task_id=task_id)
        return None

    if isinstance(raw_value, datetime):
        return raw_value

    if isinstance(raw_value, str):
        normalized_str = raw_value.strip()
        if normalized_str.endswith("Z"):
            normalized_str = f"{normalized_str[:-1]}+00:00"
        try:
            return datetime.fromisoformat(normalized_str)
        except ValueError as exc:
            msg = (
                f"Tarefa '{task_id}': formato ISO 8601 inválido no campo "
                f"'{field_name}' ('{raw_value}')."
            )
            logger.error(msg)
            raise TaskValidationError(msg, task_id=task_id) from exc

    msg = (
        f"Tarefa '{task_id}': tipo inválido para o campo '{field_name}'. "
        f"Esperado datetime ou str ISO 8601, recebido {type(raw_value).__name__}."
    )
    logger.error(msg)
    raise TaskValidationError(msg, task_id=task_id)


def _validate_and_normalize_task(raw_task: dict[str, Any]) -> NormalizedTask:
    """Valida campos estruturais, domínios e invariantes temporais de uma tarefa.

    Args:
        raw_task: Dicionário bruto contendo os atributos da tarefa.

    Returns:
        Instância imutável de ``NormalizedTask`` pronta para agregação de métricas.

    Raises:
        TaskValidationError: Caso faltem chaves obrigatórias, tipos sejam inválidos
            ou domínios de status/prioridade sejam violados.
        InconsistentDatesError: Caso ``data_limite < data_criacao`` ou
            ``data_conclusao < data_criacao``.
    """
    if not isinstance(raw_task, dict):
        msg = "Cada item do lote deve ser um dicionário (dict[str, Any])."
        logger.error(msg)
        raise TaskValidationError(msg)

    raw_id: Any = raw_task.get("id")
    if raw_id is None or isinstance(raw_id, bool) or not isinstance(raw_id, (str, int)):
        msg = "Tarefa inválida: o campo 'id' é obrigatório e deve ser str ou int."
        logger.error(msg)
        raise TaskValidationError(msg)
    if isinstance(raw_id, str) and not raw_id.strip():
        msg = "Tarefa inválida: o campo 'id' não pode ser uma string vazia."
        logger.error(msg)
        raise TaskValidationError(msg)

    task_id: str | int = raw_id

    for field in REQUIRED_FIELDS:
        if field not in raw_task:
            msg = f"Tarefa '{task_id}': campo obrigatório '{field}' ausente."
            logger.error(msg)
            raise TaskValidationError(msg, task_id=task_id)

    titulo: Any = raw_task.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip():
        msg = f"Tarefa '{task_id}': o campo 'titulo' deve ser uma string não vazia."
        logger.error(msg)
        raise TaskValidationError(msg, task_id=task_id)

    prioridade: Any = raw_task.get("prioridade")
    if not isinstance(prioridade, str) or prioridade not in VALID_PRIORITIES:
        msg = (
            f"Tarefa '{task_id}': prioridade inválida '{prioridade}'. "
            f"Valores aceitos: {VALID_PRIORITIES}."
        )
        logger.error(msg)
        raise TaskValidationError(msg, task_id=task_id)

    status: Any = raw_task.get("status")
    if not isinstance(status, str) or status not in VALID_STATUSES:
        msg = (
            f"Tarefa '{task_id}': status inválido '{status}'. "
            f"Valores aceitos: {VALID_STATUSES}."
        )
        logger.error(msg)
        raise TaskValidationError(msg, task_id=task_id)

    data_criacao = _parse_datetime(
        raw_task.get("data_criacao"),
        field_name="data_criacao",
        task_id=task_id,
        required=True,
    )
    data_limite = _parse_datetime(
        raw_task.get("data_limite"),
        field_name="data_limite",
        task_id=task_id,
        required=True,
    )
    is_completed: bool = status == "CONCLUIDA"
    data_conclusao = _parse_datetime(
        raw_task.get("data_conclusao"),
        field_name="data_conclusao",
        task_id=task_id,
        required=is_completed,
    )

    assert data_criacao is not None
    assert data_limite is not None

    if data_limite < data_criacao:
        msg = (
            f"Inconsistência cronológica na tarefa '{task_id}': "
            f"data_limite ({data_limite.isoformat()}) é anterior à "
            f"data_criacao ({data_criacao.isoformat()})."
        )
        logger.error(msg)
        raise InconsistentDatesError(msg, task_id=task_id)

    if data_conclusao is not None and data_conclusao < data_criacao:
        msg = (
            f"Inconsistência cronológica na tarefa '{task_id}': "
            f"data_conclusao ({data_conclusao.isoformat()}) é anterior à "
            f"data_criacao ({data_criacao.isoformat()})."
        )
        logger.error(msg)
        raise InconsistentDatesError(msg, task_id=task_id)

    return NormalizedTask(
        task_id=task_id,
        titulo=titulo.strip(),
        prioridade=prioridade,
        data_criacao=data_criacao,
        data_limite=data_limite,
        data_conclusao=data_conclusao,
        status=status,
    )


def _compute_subset_metrics(
    tasks_subset: list[NormalizedTask],
) -> tuple[int, int, float, float]:
    """Calcula métricas agregadas para um subconjunto de tarefas normalizadas.

    Protege de maneira determinística contra ``ZeroDivisionError`` quando não
    existem tarefas concluídas no subconjunto analisado.

    Args:
        tasks_subset: Lista de objetos ``NormalizedTask`` a serem agregados.

    Returns:
        Tupla contendo ``(total, concluidas, tempo_medio_horas, taxa_atraso_percentual)``.
    """
    total: int = len(tasks_subset)
    completed_tasks: list[NormalizedTask] = [
        t for t in tasks_subset if t.status == "CONCLUIDA" and t.data_conclusao is not None
    ]
    concluidas: int = len(completed_tasks)

    if concluidas == 0:
        return total, 0, 0.0, 0.0

    total_hours: float = 0.0
    delayed_count: int = 0

    for task in completed_tasks:
        assert task.data_conclusao is not None
        duration_seconds: float = (
            task.data_conclusao - task.data_criacao
        ).total_seconds()
        total_hours += duration_seconds / 3600.0
        if task.data_conclusao > task.data_limite:
            delayed_count += 1

    tempo_medio_horas: float = round(total_hours / concluidas, 2)
    taxa_atraso_percentual: float = round((delayed_count / concluidas) * 100.0, 2)
    return total, concluidas, tempo_medio_horas, taxa_atraso_percentual


def _build_empty_metrics_response() -> dict[str, Any]:
    """Constrói a estrutura padrão de métricas zeradas para lotes vazios.

    Returns:
        Dicionário contratado em ``specs/task_analyzer_spec.md`` com valores
        numéricos inicializados em ``0`` e ``0.0``.
    """
    return {
        "total_tarefas": 0,
        "tarefas_concluidas": 0,
        "total_concluidas": 0,
        "total_pendentes": 0,
        "tempo_medio_conclusao_horas": 0.0,
        "taxa_atraso_percentual": 0.0,
        "metricas_por_prioridade": {
            priority: {
                "total": 0,
                "concluidas": 0,
                "tempo_medio_horas": 0.0,
                "taxa_atraso_percentual": 0.0,
            }
            for priority in VALID_PRIORITIES
        },
    }


class TaskAnalyzer:
    """Analisador de tarefas em memória orientado por especificação (SDD).

    Fornece validação estrita de contratos e cálculo de indicadores de
    produtividade e pontualidade sem dependências externas.
    """

    @classmethod
    def analyze(
        cls,
        tasks: list[dict[str, Any]],
        raise_on_empty: bool = True,
    ) -> dict[str, Any]:
        """Analisa um lote de tarefas e retorna os indicadores de desempenho.

        Args:
            tasks: Lista de dicionários representando as tarefas do lote.
            raise_on_empty: Se ``True`` (padrão da classe), lança
                ``EmptyDatasetError`` quando ``tasks`` for vazio. Se ``False``,
                retorna o dicionário de métricas zeradas.

        Returns:
            Dicionário contendo ``total_tarefas``, ``tarefas_concluidas``,
            ``total_concluidas``, ``total_pendentes``,
            ``tempo_medio_conclusao_horas``, ``taxa_atraso_percentual`` e
            ``metricas_por_prioridade``.

        Raises:
            EmptyDatasetError: Se ``tasks`` estiver vazio e ``raise_on_empty=True``.
            InconsistentDatesError: Se houver datas inconsistentes em qualquer tarefa.
            TaskValidationError: Se o payload não for uma lista ou contiver
                tarefas com dados inválidos.
        """
        if not isinstance(tasks, list):
            msg = "O parâmetro 'tasks' deve ser uma lista de dicionários."
            logger.error(msg)
            raise TaskValidationError(msg)

        logger.info("Iniciando análise de lote com %d tarefa(s).", len(tasks))

        if len(tasks) == 0:
            if raise_on_empty:
                msg = "Não é possível analisar um lote vazio de tarefas (tasks=[])."
                logger.warning(msg)
                raise EmptyDatasetError(msg)
            logger.warning(
                "Lote de tarefas vazio recebido com raise_on_empty=False. "
                "Retornando métricas zeradas."
            )
            return _build_empty_metrics_response()

        normalized_tasks: list[NormalizedTask] = [
            _validate_and_normalize_task(raw_task) for raw_task in tasks
        ]

        (
            total_tarefas,
            tarefas_concluidas,
            tempo_medio_conclusao_horas,
            taxa_atraso_percentual,
        ) = _compute_subset_metrics(normalized_tasks)

        total_pendentes: int = total_tarefas - tarefas_concluidas

        metricas_por_prioridade: dict[str, dict[str, int | float]] = {}
        for priority in VALID_PRIORITIES:
            subset: list[NormalizedTask] = [
                t for t in normalized_tasks if t.prioridade == priority
            ]
            p_total, p_concluidas, p_tempo_medio, p_taxa_atraso = (
                _compute_subset_metrics(subset)
            )
            metricas_por_prioridade[priority] = {
                "total": p_total,
                "concluidas": p_concluidas,
                "tempo_medio_horas": p_tempo_medio,
                "taxa_atraso_percentual": p_taxa_atraso,
            }

        result: dict[str, Any] = {
            "total_tarefas": total_tarefas,
            "tarefas_concluidas": tarefas_concluidas,
            "total_concluidas": tarefas_concluidas,
            "total_pendentes": total_pendentes,
            "tempo_medio_conclusao_horas": tempo_medio_conclusao_horas,
            "taxa_atraso_percentual": taxa_atraso_percentual,
            "metricas_por_prioridade": metricas_por_prioridade,
        }

        logger.info(
            "Análise concluída com sucesso: total=%d, concluidas=%d, pendentes=%d.",
            total_tarefas,
            tarefas_concluidas,
            total_pendentes,
        )
        return result


def analyze_tasks(
    tasks: list[dict[str, Any]],
    raise_on_empty: bool = False,
) -> dict[str, Any]:
    """Função utilitária de módulo para análise de tarefas (contrato Fase 2).

    Delega a execução para ``TaskAnalyzer.analyze`` utilizando por padrão
    ``raise_on_empty=False``, retornando métricas zeradas (`0.0`) para listas
    vazias sem lançar exceção não tratada.

    Args:
        tasks: Lista de dicionários com os dados das tarefas.
        raise_on_empty: Define se uma lista vazia deve lançar ``EmptyDatasetError``
            (``True``) ou retornar métricas zeradas (``False``, padrão).

    Returns:
        Dicionário estruturado com todas as métricas globais e por prioridade.

    Raises:
        EmptyDatasetError: Quando ``tasks`` for vazio e ``raise_on_empty=True``.
        InconsistentDatesError: Quando ``data_conclusao < data_criacao`` ou
            ``data_limite < data_criacao``.
        TaskValidationError: Quando ocorrer erro de validação de domínio/estrutura.
    """
    return TaskAnalyzer.analyze(tasks=tasks, raise_on_empty=raise_on_empty)


__all__: list[str] = [
    "EmptyDatasetError",
    "InconsistentDatesError",
    "TaskAnalyzer",
    "TaskAnalyzerError",
    "TaskValidationError",
    "analyze_tasks",
]
