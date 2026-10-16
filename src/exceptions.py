"""Hierarquia de exceções customizadas do domínio TaskAnalyzer (SDD).

Define exceções específicas para tratamento estruturado de erros de validação,
inconsistências cronológicas e lotes de dados vazios.
"""


class TaskAnalyzerError(Exception):
    """Exceção base para todos os erros de domínio do TaskAnalyzer.

    Attributes:
        message: Mensagem descritiva do erro ocorrido.
        task_id: Identificador opcional da tarefa associada ao erro.
    """

    def __init__(self, message: str, task_id: str | int | None = None) -> None:
        """Inicializa a exceção base do analisador de tarefas.

        Args:
            message: Descrição detalhada do erro.
            task_id: Identificador da tarefa que originou a falha, se aplicável.
        """
        self.message: str = message
        self.task_id: str | int | None = task_id
        super().__init__(message)


class TaskValidationError(TaskAnalyzerError):
    """Exceção lançada quando uma tarefa viola regras estruturais ou de domínio.

    Usada para campos obrigatórios ausentes, tipos incompatíveis, títulos vazios
    ou valores fora dos domínios permitidos de prioridade e status.
    """

    def __init__(self, message: str, task_id: str | int | None = None) -> None:
        """Inicializa a exceção de validação de tarefa.

        Args:
            message: Descrição detalhada da violação de validação.
            task_id: Identificador da tarefa inválida, se disponível.
        """
        super().__init__(message=message, task_id=task_id)


class InconsistentDatesError(TaskValidationError):
    """Exceção lançada quando há inconsistência cronológica nas datas da tarefa.

    Herdada de ``TaskValidationError`` para garantir compatibilidade polimórfica
    tanto em capturas específicas (``InconsistentDatesError``) quanto genéricas
    de validação (``TaskValidationError``).
    """

    def __init__(self, message: str, task_id: str | int | None = None) -> None:
        """Inicializa a exceção de inconsistência cronológica.

        Args:
            message: Explicação da violação temporal contendo o ID da tarefa.
            task_id: Identificador da tarefa com datas inconsistentes.
        """
        super().__init__(message=message, task_id=task_id)


class EmptyDatasetError(TaskValidationError):
    """Exceção lançada quando o lote de tarefas está vazio no modo estrito.

    Disparada por ``TaskAnalyzer.analyze([])`` quando o parâmetro
    ``raise_on_empty`` está configurado como ``True``.
    """

    def __init__(
        self,
        message: str = "O lote de tarefas enviado para análise está vazio.",
    ) -> None:
        """Inicializa a exceção de lote vazio.

        Args:
            message: Mensagem informando que a coleção de entrada está vazia.
        """
        super().__init__(message=message, task_id=None)
