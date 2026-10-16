# CONTEXT_RULES.md — Diretrizes de Contexto e Governança (SDD)

## 1. Identificação Acadêmica
- **Aluno:** Marco Antonio Rodrigues
- **Curso:** Engenharia de Software
- **Polo:** Asa Norte — UniCEUB
- **E-mail:** marco.rodrigues@sempreceub.com
- **Projeto:** `sdd-task-analyzer` (Desenvolvimento Orientado por Especificação — SDD)

---

## 2. Ambiente e Runtime
- **Linguagem:** Python moderno (compatível com Python 3.11+ e homologado nativamente em **Python 3.14**).
- **Gerenciamento de Pacotes e Testes:** Ambiente virtual padrão (`venv`) utilizando `pytest` (`pytest>=8.0.0`) como framework exclusivo de verificação automatizada (Test Harness).

---

## 3. Regras de Engenharia, Arquitetura e Estilo de Código
1. **Tipagem Estática Estrita (Type Hints Modernos):**
   - Uso obrigatório da sintaxe moderna do Python (PEP 585 e PEP 604: `X | Y`, `list[...]`, `dict[...]`) em **100% das assinaturas** de funções, métodos e atributos de classe/dados.
   - Proibido o uso de tipos legados de `typing` quando houver equivalente nativo (`List`, `Dict`, `Optional`, `Union`), mantendo `Any` de `typing` apenas para representar payloads dinâmicos de entrada/saída contratados.
2. **Princípio de Responsabilidade Única (SRP) e PEP 8:**
   - Conformidade estrita com a **PEP 8** (nomes em `snake_case` para funções/variáveis, `PascalCase` para classes/exceções, `UPPER_SNAKE_CASE` para constantes, limite de linha legível e modularização limpa).
   - Cada método ou função auxiliar deve possuir uma única razão para mudar: separação clara entre **validação/parsing de entrada**, **verificação de consistência cronológica** e **agregação/cálculo de métricas**.
3. **Documentação Padronizada (Google Style Docstrings):**
   - Todas as classes, métodos públicos/privados e funções devem conter docstrings no formato **Google Style**, especificando de forma explícita as seções `Args`, `Returns` e `Raises` (quando aplicável).
4. **Tratamento Estruturado de Exceções:**
   - Proibido capturar exceções genéricas silenciosamente (`except Exception: pass`).
   - O sistema deve utilizar hierarquia própria de exceções de domínio definida em `src/exceptions.py` e reexportada em `src/task_analyzer.py`:
     - `TaskAnalyzerError(Exception)`: Exceção base do domínio.
     - `TaskValidationError(TaskAnalyzerError)`: Erro de validação estrutural ou de domínio nas tarefas.
     - `InconsistentDatesError(TaskValidationError)`: Violação de invariante cronológica (`data_conclusao < data_criacao` ou `data_limite < data_criacao`), informando obrigatoriamente o `id` da tarefa infratora.
     - `EmptyDatasetError(TaskValidationError)`: Lote de tarefas vazio quando exigida validação estrita (`raise_on_empty=True`).
5. **Observabilidade com Logging Estruturado:**
   - Uso obrigatório do módulo nativo `logging` com níveis semânticos adequados (`INFO` para início/conclusão de processamento de lotes, `WARNING` para lotes vazios ou alertas operacionais e `ERROR` para falhas de validação e inconsistências de datas).

---

## 4. Proibições Explícitas (Guardrails Anti-Alucinação para IA)
- **PROIBIDO importar bibliotecas externas de manipulação de dados:** É terminantemente vedado o uso de `pandas`, `numpy`, `polars`, `scipy`, `pydantic` ou `dateutil`. Apenas módulos da biblioteca padrão do Python (`datetime`, `logging`, `typing`, `dataclasses`) são permitidos na implementação (`src/`).
- **PROIBIDO persistência em disco ou banco de dados:** O componente `TaskAnalyzer` deve operar de forma 100% pura e em memória (*stateless/in-memory*), sem criar arquivos temporários, conexões SQLite ou chamadas de rede.
- **PROIBIDO alterar assinaturas públicas contratadas:** A classe `TaskAnalyzer` (com `TaskAnalyzer.analyze(...)`) e a função de módulo `analyze_tasks(...)`, bem como todas as chaves do dicionário de saída especificadas em `specs/task_analyzer_spec.md`, são contratos imutáveis.
- **PROIBIDO permitir `ZeroDivisionError`:** Qualquer cálculo de média ou percentual sobre um conjunto com zero tarefas concluídas (ou lista vazia) deve retornar `0.0` de maneira determinística e segura.
