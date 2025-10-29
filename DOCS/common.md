# Common Application Documentation

The `common` application provides a set of shared services and utilities used across the entire Django project. It encapsulates logic for interacting with external systems, managing configuration, and creating reusable components.

## Architecture Overview

The `common` app is a core part of the "AI Development" backend, providing the necessary integrations for the system to function, as shown in the architecture diagram.

![Architecture Diagram](./images/21%20Tech%20Use%20Cases-Template.jpg)

## Modules

### `config_manager.py`

- **Purpose**: Manages application configuration loaded from `.env` files.
- **Class**: `ConfigManager`
- **Functionality**:
  - Loads environment variables from a `.env` file.
  - Provides methods to retrieve specific configuration groups, such as `get_llm_config()` for LLM settings.
  - Handles type casting for configuration values.

### `eam_api.py`

- **Purpose**: Provides a service layer for interacting with the **HxGN EAM (Enterprise Asset Management)** REST API.
- **Class**: `EAMApiService`
- **Functionality**:
  - Handles authentication with the EAM system.
  - Provides methods to create and manage various EAM entities:
    - `create_task_plan`
    - `create_checklist`
    - `create_maintenance_schedule`
    - `create_hazard`
    - `create_precaution`
    - `create_safety_link_record`
    - `create_qualification`
  - Includes helper methods to fetch data like equipment categories and classes (`get_equipment_categories`, `get_equipment_classes`).
  - Transforms internal data structures into the format required by the EAM API.

### `eam_lov_fetcher.py`

- **Purpose**: A specialized client for fetching **List of Values (LOV)** from the EAM system. LOVs are used for populating dropdowns and providing users with predefined options in the UI.
- **Class**: `EAMLOVFetcher`
- **Functionality**:
  - `fetch_category_values`: Fetches equipment category values.
  - `fetch_cost_code_values`: Fetches cost code values.
  - A helper function `get_all_lov_data` orchestrates fetching multiple LOV types.

### `llm_factory.py`

- **Purpose**: A factory for creating instances of Large Language Models (LLMs) from different providers. This allows the application to be model-agnostic.
- **Class**: `LLMFactory`
- **Enum**: `LLMsEnum` (Defines supported LLMs like `GEMMA`, `LLAMA3`, `GPT4O`, etc.)
- **Functionality**:
  - The `get_llm` method returns a configured LLM instance (`ChatOllama`, `ChatOpenAI`) based on the provided name.
  - It standardizes the configuration parameters (temperature, max_tokens, etc.) across different models.

### `prompt_factory.py`

- **Purpose**: Manages and provides `PromptTemplate` instances for use with LLMs. This centralizes prompt engineering.
- **Class**: `PromptFactory`
- **Functionality**:
  - The `get_prompt` method returns a pre-defined `PromptTemplate` based on a given name.
  - Currently, it contains the `asset_entry_prompt`, which is a sophisticated prompt for predicting asset information based on historical data and rules.
