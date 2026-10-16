# sdd-task-analyzer — Analisador de Tarefas Orientado por Especificação (SDD)

![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.14-blue)
![Tests](https://img.shields.io/badge/pytest-5%20passed%20(100%25)-brightgreen)
![Methodology](https://img.shields.io/badge/Methodology-SDD-purple)

Repositório oficial da **Entrega Intermediária (Fase 2)** da disciplina de **Engenharia de Software (UniCEUB)**, aplicando a metodologia **Specification-Driven Development (SDD)** para construção, validação e homologação de um motor em memória de análise de métricas de tarefas (`TaskAnalyzer`).

---

## Identificação Acadêmica
- **Aluno:** Marco Antonio Rodrigues
- **Curso:** Engenharia de Software
- **Polo:** Asa Norte — UniCEUB
- **E-mail:** marco.rodrigues@sempreceub.com

---

## 1. Visão Geral da Arquitetura SDD
No paradigma **Desenvolvimento Orientado por Especificação (SDD)**, a especificação técnica e as regras de contexto atuam como a fonte única de verdade (*Single Source of Truth*) antes de qualquer geração de código por Assistentes de IA:

1. **Governança e Guardrails (`CONTEXT_RULES.md`):** Define restrições arquiteturais estritas, como uso exclusivo da biblioteca padrão do Python (proibindo `Pandas`/`NumPy`), tipagem estática moderna PEP 604 (`X | Y`, `list[...]`, `dict[...]`), Google Style Docstrings, módulo nativo `logging` e hierarquia própria de exceções.
2. **Especificação Técnica Executável (`specs/task_analyzer_spec.md`):** Formaliza os contratos de entrada/saída, invariantes cronológicas e cenários BDD (*Dado-Quando-Então*).
3. **Implementação (`src/`):** Código limpo, modular e aderente ao Princípio de Responsabilidade Única (SRP).
4. **Test Harness (`tests/test_harness.py`):** Suíte automatizada em `pytest` que valida o comportamento nominal, a rejeição de inconsistências temporais e os casos de borda (`ZeroDivisionError`).

---

## 2. Estrutura do Repositório

```text
sdd-task-analyzer/
├── README.md
├── CONTEXT_RULES.md
├── .gitignore
├── requirements.txt
├── RELATORIO_FASE2.md
├── specs/
│   └── task_analyzer_spec.md
├── src/
│   ├── __init__.py
│   ├── exceptions.py
│   └── task_analyzer.py
└── tests/
    ├── __init__.py
    └── test_harness.py
```

---

## 3. Regras de Negócio e Contratos

### Entradas (`list[dict[str, Any]]`)
Cada tarefa possui:
- `id` (`str | int`, obrigatório): Identificador único.
- `titulo` (`str`, obrigatório): Não nulo e não vazio.
- `prioridade` (`str`, obrigatório): `'BAIXA'`, `'MEDIA'` ou `'ALTA'`.
- `data_criacao` (`datetime | str` ISO 8601, obrigatório).
- `data_limite` (`datetime | str` ISO 8601, obrigatório): Deve ser `>= data_criacao`.
- `data_conclusao` (`datetime | str` ISO 8601 `| None`, opcional): Obrigatório quando `status == 'CONCLUIDA'`. Deve ser `>= data_criacao`.
- `status` (`str`, obrigatório): `'PENDENTE'`, `'EM_ANDAMENTO'`, `'CONCLUIDA'` ou `'CANCELADA'`.

### Saídas (`dict[str, Any]`)
- `total_tarefas` (`int`): Total de tarefas recebidas no lote.
- `tarefas_concluidas` (`int`) e `total_concluidas` (`int`): Total de tarefas com `status == 'CONCLUIDA'`.
- `total_pendentes` (`int`): Total de tarefas não concluídas.
- `tempo_medio_conclusao_horas` (`float`): Média em horas (arredondada em 2 casas decimais) entre `data_criacao` e `data_conclusao` das tarefas concluídas (`0.0` quando não há concluídas).
- `taxa_atraso_percentual` (`float`): Percentual (arredondado em 2 casas decimais) de tarefas concluídas com `data_conclusao > data_limite` (`0.0` quando não há concluídas).
- `metricas_por_prioridade` (`dict[str, dict[str, int | float]]`): Métricas segmentadas para `'BAIXA'`, `'MEDIA'` e `'ALTA'`.

---

## 4. Instalação e Execução (Python 3.14 + Pytest)

### 4.1 Criação do Ambiente Virtual e Instalação de Dependências
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.2 Execução da Suíte de Testes (Test Harness)
```bash
./.venv/bin/pytest -v
```

### 4.3 Status dos Testes
| Caso de Teste (`tests/test_harness.py`) | Cenário SDD | Status |
| :--- | :--- | :---: |
| `test_analyze_valid_tasks_returns_correct_metrics` | Cenário 1: Lote válido (4 tarefas, médias e prioridades) | PASSED |
| `test_analyze_inconsistent_dates_raises_exception` | Cenário 2: Datas inconsistentes (`InconsistentDatesError` / `TaskValidationError`) | PASSED |
| `test_analyze_empty_payload_raises_error` | Cenário 3 (Fase 1): Lote vazio estrito (`EmptyDatasetError`) | PASSED |
| `test_analyze_empty_and_only_pending_tasks_returns_zero_metrics` | Caso de Borda (Fase 2): Prevenção de `ZeroDivisionError` (`0.0`) | PASSED |
| `test_analyze_supports_iso_strings_and_datetime_objects` | Entradas híbridas (`str` ISO 8601 e `datetime`) | PASSED |
