# Changelog

Todas as mudanças notáveis neste projeto serão documentadas aqui.
O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- _Nenhuma_ (Use esta seção para novas funcionalidades antes do próximo lançamento).

### Changed
- _Nenhuma_ (Use esta seção para modificações em funcionalidades existentes).

### Fixed
- _Nenhuma_ (Use esta seção para correções de bugs).

### Deprecated
- _Nenhuma_ (Use esta seção para funcionalidades que serão removidas em versões futuras).

### Removed
- _Nenhuma_ (Use esta seção para funcionalidades que foram removidas).

### Security
- _Nenhuma_ (Use esta seção para melhorias de segurança).


## [0.5.1] - 2025-10-01

### Added
- Adicionada a função `validate_bi` ao módulo `text` para validar o formato de números de Bilhete de Identidade de Moçambique.
- **Configuração de Testes:** Adicionado `conftest.py` para gestão de `fixtures` e compatibilidade com `pytest-cov` em ambientes minimalistas.

### Changed
- **Compatibilidade Python 3.8:** Implementado `from __future__ import annotations` em todos os ficheiros de código e teste para garantir compatibilidade retroativa dos type hints.


## [0.5.0] - 2025-10-01

### Added
- **Módulo de Dicionários (`utils/dicts.py`):** Toolkit completo para manipulação de dicionários, incluindo `deep_get`, `deep_set`, `merge_dicts`, `flatten_dict`, `unflatten_dict`, `dict_diff`, `filter_dict`, `invert_dict`, `update_if` e `safe_get`.
- **Módulo de Formatação (`utils/formatting.py`):**
    - Implementação de um formatador de tabelas (`print_table`, `to_markdown_table`) sem dependências externas, com suporte para alinhamento e bordas.
    - Adicionadas funções de UI de terminal com estética "hacker": `print_table_hacker`, `ascii_banner_hacker`, `boxed_text_hacker`, `glitch_text`, e `matrix_rain_preview`.
    - Adicionada `progress_bar` para visualização de progresso.
- **Módulo de I/O (`utils/io.py`):**
    - Suporte transparente para compressão e descompressão de ficheiros **Gzip** (`.gz`).
    - Adicionada a função `atomic_write` para escrita segura de ficheiros.
    - Adicionada a função `backup_file` para criar backups rotativos de ficheiros.
    - Adicionada a função `stream_jsonl` para leitura/escrita eficiente de grandes volumes de dados JSONL.
    - Adicionadas `read_json`, `write_json`, `count_file_lines`, `merge_json_files`, `validate_json`.

### Changed
- **Arquitetura do Projeto:** Refatoração completa para uma estrutura `src/pybrige/` profissional, com código organizado em sub-pacotes (`core`, `decorators`, `utils`).
- **`@retry` Decorator (`decorators/robustness.py`):** Aprimorado para logar o sucesso (tanto na primeira tentativa como após retries) e permitir a configuração de quais exceções devem acionar uma nova tentativa (`only_for`).
- **`@timer` Decorator (`decorators/timing.py`):** Aprimorado para incluir um timestamp (`{timestamp}`) na mensagem de log e permitir a personalização completa do template.
- **`setup_logging` (`core/logging.py`):** Refatorado para ser compatível com `pytest` e mais robusto, usando `logging.basicConfig(force=True)`.
- **`slugify` (`utils/text.py`):** Lógica melhorada para lidar corretamente com caracteres Unicode e outros casos extremos.
- **`snake_to_camel` (`utils/text.py`):** Adicionado suporte para preservar acrónimos (ex: `api_id` -> `APIID`).
- **`extract_urls` (`utils/text.py`):** Melhorada para remover pontuação final comum dos links extraídos.
- **`read_json` (`utils/io.py`):** Aprimorado com type hints `@overload` para uma melhor experiência com análise estática de código.
- **Cobertura de Testes:** Aumentada para **+90%** em todo o projeto.


## [0.4.0] - 2025-09-27

### Changed
- **Renomeação do Projeto:** O projeto foi renomeado de **pydevhelper** para **pybrige** para uma identidade mais concisa e marcante.
- **Branding:** Nova identidade visual e foco da marca.


## [0.3.1] - 2025-09-27

### Added
- **Sistema de Importação por Namespaces:** Implementado um novo sistema de importação para permitir `from pybrige.text import slugify`, enquanto mantém a compatibilidade retroativa para `from pybrige import slugify`.

### Changed
- **`__init__.py`:** Reestruturado para maior clareza e flexibilidade na gestão de importações e na exposição da API.


## [0.3.0] - 2025-09-27

### Added
- **Módulo `text_utils` (agora `utils/text.py`):**
    - `slugify` com suporte a **Unicode** (`allow_unicode=True`).
    - Conversores `camel_to_snake` e `snake_to_camel`.
    - `normalize_whitespace` para limpar espaços extras.
    - `remove_html_tags` para sanitização de strings.
    - Extratores `extract_emails` e `extract_urls`.
- **Módulo `config` (agora `core/config.py`):**
    - Novo sistema de configuração com **esquema tipado** via `EnvSpec` e `VarSpec`.
    - Integração opcional com `.env` via `python-dotenv`.
    - Suporte a `parser` customizado e `validator` por variável.
    - Mensagens de erro claras e estruturadas via `MissingEnvVarsError`.
    - Suporte a prefixos (`prefix="APP_"`) para variáveis de ambiente.

### Changed
- **Testes Unitários:** Expansão significativa dos testes para o módulo `config`, cobrindo cenários como variáveis ausentes, defaults, falhas de casting, validação customizada e prefixos.
- **Cobertura de Testes:** Aumentada para garantir maior robustez e confiança nas novas e existentes funcionalidades.


## [0.2.0] - 2025-09-26

### Added
- **Decorator `@retry` (`decorators/robustness.py`):** Implementação para reexecução automática de funções em caso de exceções.
    - Suporte a `tries`, `delay`, `backoff` exponencial.
    - Permite especificar exceções capturadas (`exceptions=(Exception,)`).
    - Possibilidade de injetar `sleep_func` para testes.
    - Logging detalhado de falhas e sucessos.


## [0.1.1] - 2025-09-25

### Added
- **Logging Colorido:** `setup_logging(colors=True)` para logs visualmente distintos no terminal.
- **Timer Aprimorado:** Decorator `@timer` com suporte a timestamp e template de mensagem customizado.

### Changed
- **Qualidade de Código:** Cobertura de testes ampliada para as funcionalidades de logging e timing, garantindo maior estabilidade.


## [0.1.0] - 2025-09-24

### Added
- **Versão Inicial do Projeto `pydevhelper`:**
    - `setup_logging` para configuração básica de logs.
    - `require_vars` para validação simples de variáveis de ambiente.
    - `@timer` decorator inicial para medição de tempo de execução.
    - `print_table` para renderizar dados em formato de tabela no terminal.