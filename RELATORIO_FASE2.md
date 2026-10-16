# RELATÓRIO TÉCNICO — ENTREGA INTERMEDIÁRIA (FASE 2)
## Desenvolvimento Orientado por Especificação (SDD) — `sdd-task-analyzer`

---

### 1. Identificação do Aluno
- **Nome:** Marco Antonio Rodrigues
- **Curso:** Engenharia de Software — UniCEUB
- **Polo:** Asa Norte
- **E-mail:** marco.rodrigues@sempreceub.com
- **Ambiente de Homologação:** Arch Linux | Python 3.14.8 | Pytest 9.x | Git & GitHub CLI (`gh`)

---

### 2. Links Oficiais da Entrega
- **Repositório GitHub Público:** `https://github.com/Merketz/sdd-task-analyzer`
- **Pull Request #1 (Especificação SDD & Context Rules):** `https://github.com/Merketz/sdd-task-analyzer/pull/1`
- **Pull Request #2 (Implementação TaskAnalyzer & Test Harness):** `https://github.com/Merketz/sdd-task-analyzer/pull/2`
- **Link do Vídeo de Apresentação (YouTube — Não Listado):**
  > `[INSERIR LINK DO VÍDEO DO YOUTUBE AQUI]`

---

### 3. Relato Técnico: Engenharia de Prompts, Guardrails (`CONTEXT_RULES.md`) e Test Harness

#### 3.1. Estratégia de Prompts Utilizados na Geração Orientada por Especificação
Durante a Fase 2, o desenvolvimento não foi conduzido por prompts abertos (*vibe coding*), mas sim por **engenharia de contexto determinística** ancorada nos artefatos da Fase 1 (`CONTEXT_RULES.md` e `specs/task_analyzer_spec.md`).

Os prompts fornecidos ao Agente de IA seguiram uma estrutura em três camadas:
1. **Ancoragem Normativa (Restrições de Sistema):** Instrução explícita obrigando a leitura prévia de `CONTEXT_RULES.md` antes de escrever qualquer linha em `src/`, impondo Python 3.14 nativo, Type Hints PEP 604 (`X | Y`, `list[...]`, `dict[...]`), Google Style Docstrings e proibição absoluta de bibliotecas externas de dados.
2. **Ancoragem Contratual (Especificação Executável):** Vinculação direta ao arquivo `specs/task_analyzer_spec.md`, exigindo o cumprimento simultâneo dos contratos de saída (`total_tarefas`, `tarefas_concluidas`, `total_concluidas`, `total_pendentes`, `tempo_medio_conclusao_horas`, `taxa_atraso_percentual` e `metricas_por_prioridade`) e da hierarquia de exceções (`TaskAnalyzerError -> TaskValidationError -> InconsistentDatesError / EmptyDatasetError`).
3. **Verificação Empírica via Test Harness (`tests/test_harness.py`):** Exigência de validação imediata com `pytest -v` cobrindo o Cenário 1 (4 tarefas com média `3.67h` e taxa de atraso `33.33%`), Cenário 2 (rejeição de datas inconsistentes citando o `id` da tarefa) e Cenário 3 / Casos de Borda (lotes vazios e lotes apenas com tarefas `PENDENTE`).

#### 3.2. Como o `CONTEXT_RULES.md` e o Test Harness Evitaram Alucinações da IA
A combinação entre regras de contexto declarativas e bateria de testes automatizados atuou como uma barreira dupla (*guardrails*) contra os desvios mais comuns de Modelos de Linguagem (LLMs):

1. **Bloqueio de Dependências Externas (`Pandas` / `NumPy` / `Pydantic`):**
   - *Risco de Alucinação:* Ao receber uma tarefa de agregação de métricas e cálculo de médias/percentuais por grupo (`prioridade`), LLMs frequentemente importam `pandas.DataFrame` ou `numpy.mean`.
   - *Ação do Guardrail:* A cláusula de Proibições Explícitas do `CONTEXT_RULES.md` restringiu as importações exclusivamente à biblioteca padrão (`datetime`, `logging`, `typing`, `dataclasses`). O código final realiza toda a normalização via `@dataclass(frozen=True)` e agregação nativa em memória com complexidade $O(N)$.
2. **Prevenção Determinística contra `ZeroDivisionError`:**
   - *Risco de Alucinação:* Implementações ingênuas dividem a soma das durações ou a contagem de atrasos por `len(tasks)` ou por `concluidas` sem verificar se o denominador é zero (ex.: quando todas as tarefas estão com status `PENDENTE` ou quando uma prioridade específica, como `'MEDIA'` no Cenário 1, possui `total=1` e `concluidas=0`).
   - *Ação do Guardrail:* A função `_compute_subset_metrics` verifica explicitamente `if concluidas == 0: return total, 0, 0.0, 0.0`, garantindo segurança matemática tanto no escopo global quanto dentro de cada faixa de `metricas_por_prioridade`. O teste `test_analyze_empty_and_only_pending_tasks_returns_zero_metrics` comprova empiricamente esse comportamento.
3. **Validação Estrita de Datas e Rastreabilidade de Erros:**
   - *Risco de Alucinação:* Permitir cálculos de duração negativos quando `data_conclusao < data_criacao` ou aceitar `data_limite < data_criacao`, gerando métricas corrompidas silenciosamente.
   - *Ação do Guardrail:* A função `_validate_and_normalize_task` converte tanto objetos `datetime` quanto strings ISO 8601 e valida imediatamente as invariantes temporais, registrando log de nível `ERROR` e disparando `InconsistentDatesError(TaskValidationError)` com o `id` exato da tarefa violadora na mensagem, validado por `test_analyze_inconsistent_dates_raises_exception`.
4. **Tipagem Estática Moderna no Python 3.14 e Compatibilidade Contratual:**
   - *Risco de Alucinação:* Uso de anotações obsoletas (`Optional[...]`, `Union[...]`, `List[...]`) ou divergência nos nomes das chaves de saída entre especificações.
   - *Ação do Guardrail:* O código utiliza 100% de sintaxe PEP 604 (`datetime | str | None`, `str | int`) homologada no Python 3.14 e expõe tanto `TaskAnalyzer.analyze` quanto `analyze_tasks`, mantendo as chaves `tarefas_concluidas` e `total_concluidas` sincronizadas.

---

### 4. Evidências Visuais (Prints para Exportação em PDF)

#### 4.1. Print 1 — Interação com o Assistente de IA e Geração Orientada por Especificação
> **[COLE AQUI O PRINT DA CONVERSA / EXECUÇÃO DO AGENTE DE IA GERANDO O CÓDIGO E OS TESTES]**

---

#### 4.2. Print 2 — Execução do Test Harness (`./.venv/bin/pytest -v`) no Terminal
> **[COLE AQUI O PRINT DO TERMINAL MOSTRANDO 100% DOS TESTES APROVADOS NO PYTHON 3.14]**

```text
========================= test session starts ==========================
platform linux -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0
collected 5 items

tests/test_harness.py::test_analyze_valid_tasks_returns_correct_metrics PASSED [ 20%]
tests/test_harness.py::test_analyze_inconsistent_dates_raises_exception PASSED [ 40%]
tests/test_harness.py::test_analyze_empty_payload_raises_error PASSED          [ 60%]
tests/test_harness.py::test_analyze_empty_and_only_pending_tasks_returns_zero_metrics PASSED [ 80%]
tests/test_harness.py::test_analyze_supports_iso_strings_and_datetime_objects PASSED [100%]

========================== 5 passed in 0.02s ===========================
```

---

#### 4.3. Print 3 — Repositório GitHub, Branches e Pull Requests com Plano de Homologação Humana
> **[COLE AQUI O PRINT DO GITHUB MOSTRANDO OS PULL REQUESTS E O CHECKLIST DE HOMOLOGAÇÃO]**
