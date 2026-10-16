# Especificação Técnica Executável (SDD) — `sdd-task-analyzer`

**Autor:** Marco Antonio Rodrigues  
**Curso:** Engenharia de Software — Polo Asa Norte (UniCEUB)  
**E-mail:** marco.rodrigues@sempreceub.com  
**Versão:** 2.0 (Homologada para Python 3.11+ / Python 3.14)

---

## 1. Objetivo do Componente
O módulo `src/task_analyzer.py` é responsável por processar lotes de tarefas em memória, validar rigorosamente seus contratos de dados e invariantes temporais, e calcular indicadores gerenciais de desempenho (KPIs globais e segmentados por nível de prioridade), seguindo a metodologia de **Desenvolvimento Orientado por Especificação (Specification-Driven Development — SDD)**.

---

## 2. Contrato de Interface Pública

### 2.1 Assinaturas Contratadas
- `TaskAnalyzer.analyze(tasks: list[dict[str, Any]], raise_on_empty: bool = True) -> dict[str, Any]`
- `analyze_tasks(tasks: list[dict[str, Any]], raise_on_empty: bool = False) -> dict[str, Any]`

### 2.2 Contrato de Entrada (`tasks: list[dict[str, Any]]`)
Cada elemento da lista `tasks` deve ser um dicionário contendo os seguintes atributos:

| Campo | Tipo Aceito | Obrigatório | Regras de Domínio e Invariantes |
| :--- | :--- | :---: | :--- |
| `id` | `str \| int` | Sim | Identificador único da tarefa (não nulo e não vazio se `str`). |
| `titulo` | `str` | Sim | Descrição curta da tarefa. Não pode ser `None` nem string vazia/apenas espaços. |
| `prioridade` | `str` | Sim | Valores permitidos estritamente em `{'BAIXA', 'MEDIA', 'ALTA'}`. |
| `data_criacao` | `datetime \| str` (ISO 8601) | Sim | Timestamp de abertura da tarefa. |
| `data_limite` | `datetime \| str` (ISO 8601) | Sim | Prazo máximo planejado. Invariante: **`data_limite >= data_criacao`**. |
| `data_conclusao` | `datetime \| str \| None` | Condicional | Obrigatório quando `status == 'CONCLUIDA'`. Invariante: **`data_conclusao >= data_criacao`**. |
| `status` | `str` | Sim | Valores permitidos estritamente em `{'PENDENTE', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA'}`. |

### 2.3 Contrato de Saída (`dict[str, Any]`)
O dicionário retornado pela análise contém obrigatoriamente as chaves abaixo:

- `total_tarefas` (`int`): Contagem bruta de itens recebidos no lote.
- `tarefas_concluidas` (`int`): Contagem de itens com `status == 'CONCLUIDA'`.
- `total_concluidas` (`int`): Alias exato com o mesmo valor de `tarefas_concluidas` (garantindo compatibilidade simultânea entre os contratos da Fase 1 e da Fase 2).
- `total_pendentes` (`int`): Contagem de itens não concluídos (`status != 'CONCLUIDA'`, englobando `'PENDENTE'`, `'EM_ANDAMENTO'`, `'CANCELADA'`).
- `tempo_medio_conclusao_horas` (`float`): Média aritmética em horas (arredondada em 2 casas decimais via `round(val, 2)`) da diferença `(data_conclusao - data_criacao)` considerando exclusivamente as tarefas concluídas. Caso não existam tarefas concluídas, retorna `0.0`.
- `taxa_atraso_percentual` (`float`): Percentual (arredondado em 2 casas decimais via `round(val, 2)`) de tarefas concluídas em que `data_conclusao > data_limite`, calculado pela fórmula `((atrasadas / concluidas) * 100)`. Caso não existam tarefas concluídas, retorna `0.0`.
- `metricas_por_prioridade` (`dict[str, dict[str, int | float]]`): Dicionário indexado pelas chaves `'BAIXA'`, `'MEDIA'` e `'ALTA'`, contendo para cada nível:
  - `total` (`int`): Total de tarefas daquela prioridade.
  - `concluidas` (`int`): Total de tarefas concluídas daquela prioridade.
  - `tempo_medio_horas` (`float`): Tempo médio de conclusão em horas (2 casas decimais) daquela prioridade (`0.0` se `concluidas == 0`).
  - `taxa_atraso_percentual` (`float`): Percentual de atraso dentre as tarefas concluídas daquela prioridade (`0.0` se `concluidas == 0`).

---

## 3. Hierarquia de Exceções (`src/exceptions.py`)
- `TaskAnalyzerError(Exception)`: Exceção base do módulo.
- `TaskValidationError(TaskAnalyzerError)`: Lançada para erros de estrutura, tipos inválidos, campos obrigatórios ausentes ou domínios violados (`prioridade` ou `status` inválidos).
- `InconsistentDatesError(TaskValidationError)`: Subclasse de `TaskValidationError` lançada quando `data_conclusao < data_criacao` ou `data_limite < data_criacao`. A mensagem deve conter explicitamente o `id` da tarefa violadora.
- `EmptyDatasetError(TaskValidationError)`: Subclasse de `TaskValidationError` lançada por `TaskAnalyzer.analyze([])` quando `raise_on_empty=True`.

---

## 4. Cenários de Comportamento (BDD — Dado / Quando / Então)

### Cenário 1: Processamento de Lote Válido com Cálculo Preciso de Métricas (Sucesso)
- **Dado** um lote contendo 4 tarefas válidas na mesma data base (`2026-10-16`):
  1. **Tarefa 1 (`id=1`):** Prioridade `'ALTA'`, criada às `08:00`, limite às `12:00`, concluída às `10:00`, status `'CONCLUIDA'` (duração: `2.0h`, pontual).
  2. **Tarefa 2 (`id=2`):** Prioridade `'ALTA'`, criada às `08:00`, limite às `10:00`, concluída às `11:00`, status `'CONCLUIDA'` (duração: `3.0h`, atrasada pois `11:00 > 10:00`).
  3. **Tarefa 3 (`id=3`):** Prioridade `'BAIXA'`, criada às `09:00`, limite às `18:00`, concluída às `15:00`, status `'CONCLUIDA'` (duração: `6.0h`, pontual).
  4. **Tarefa 4 (`id=4`):** Prioridade `'MEDIA'`, criada às `10:00`, limite às `18:00`, `data_conclusao=None`, status `'PENDENTE'`.
- **Quando** o analisador (`TaskAnalyzer.analyze` ou `analyze_tasks`) processar o lote,
- **Então** o resultado deve conter exatamente:
  - `total_tarefas == 4`
  - `tarefas_concluidas == 3` e `total_concluidas == 3`
  - `total_pendentes == 1`
  - `tempo_medio_conclusao_horas == 3.67` (`(2 + 3 + 6) / 3 = 3.666... -> 3.67`)
  - `taxa_atraso_percentual == 33.33` (`(1 / 3) * 100 = 33.333... -> 33.33`)
  - `metricas_por_prioridade['ALTA'] == {'total': 2, 'concluidas': 2, 'tempo_medio_horas': 2.5, 'taxa_atraso_percentual': 50.0}`
  - `metricas_por_prioridade['BAIXA'] == {'total': 1, 'concluidas': 1, 'tempo_medio_horas': 6.0, 'taxa_atraso_percentual': 0.0}`
  - `metricas_por_prioridade['MEDIA'] == {'total': 1, 'concluidas': 0, 'tempo_medio_horas': 0.0, 'taxa_atraso_percentual': 0.0}`

### Cenário 2: Rejeição de Inconsistência Cronológica
- **Dado** um lote contendo uma tarefa onde `data_conclusao < data_criacao` (ex.: `id="TASK-99"`, criada às `14:00` e concluída às `10:00`) ou onde `data_limite < data_criacao` (ex.: `id="TASK-100"`, criada às `14:00` e limite às `12:00`),
- **Quando** o analisador executar a validação,
- **Então** deve interromper imediatamente o processamento, registrar um log de nível `ERROR` e lançar a exceção `InconsistentDatesError` (que também é instância de `TaskValidationError`), mencionando explicitamente o `id` da tarefa violadora na mensagem.

### Cenário 3 e Casos de Borda: Lote Vazio e Lote Apenas com Tarefas Pendentes (Prevenção de `ZeroDivisionError`)
- **Dado** um lote vazio `[]`:
  - **Quando** invocado via `TaskAnalyzer.analyze([])` (`raise_on_empty=True`), **Então** deve lançar `EmptyDatasetError`.
  - **Quando** invocado via `analyze_tasks([])` (`raise_on_empty=False`), **Então** deve retornar todas as contagens em `0` e médias/percentuais em `0.0` sem lançar exceção.
- **Dado** um lote contendo apenas tarefas com status `'PENDENTE'` (zero tarefas concluídas):
  - **Quando** invocado via `TaskAnalyzer.analyze` ou `analyze_tasks`,
  - **Então** deve retornar `tarefas_concluidas == 0`, `total_concluidas == 0`, `tempo_medio_conclusao_horas == 0.0` e `taxa_atraso_percentual == 0.0`, prevenindo `ZeroDivisionError`.

---

## 5. Plano de Homologação Humana (5 Etapas)
1. **Execução Automatizada do Test Harness:** Execução de `./.venv/bin/pytest -v` com 100% de aprovação nos cenários nominais, exceções e casos de borda.
2. **Auditoria de Conformidade Contratual (SDD):** Conferência estrita das assinaturas públicas e chaves de saída contra esta especificação.
3. **Inspeção Estática de Qualidade (PEP 8, Type Hints e Docstrings):** Verificação de Type Hints PEP 604 (`X | Y`), Google Style Docstrings e ausência de bibliotecas externas proibidas (`pandas`, `numpy`).
4. **Validação de Casos de Borda e Logs:** Confirmação da proteção contra `ZeroDivisionError` e emissão de logs estruturados.
5. **Aprovação Final em Pull Request:** Revisão humana do código gerado por IA antes do merge na branch principal `main`.
