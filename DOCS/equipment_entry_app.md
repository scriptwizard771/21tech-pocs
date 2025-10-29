# Equipment Entry Assistant

The **Equipment Entry Assistant** is a Django application designed to streamline the process of adding new assets to the EAM system. It leverages a Large Language Model (LLM) to predict field values for new equipment based on the description of the asset and historical data from similar existing assets.

## Architecture and Data Flow

The assistant integrates directly into the HxGN EAM user interface through an extensible framework. The data flows as follows:

![Equipment Entry Architecture](./images/21%20Tech%20Use%20Cases-Generative%20Asset%20Creation.jpg)

1. **User Input**: An Asset Manager begins creating a new asset in HxGN EAM. They provide initial data, such as an asset description (e.g., "Air Handler Unit 5 Ton"), and select a field they want the AI to predict (e.g., "Category Code").
2. **Request to Django**: The EAM framework sends a request to the Django backend. This request includes the asset description, the target field to predict, and any values the user has already entered for other fields.
3. **Fuzzy Search for Similar Assets**: The Django application receives the request and uses the `EquipmentEntryElasticSearch` vector store to perform a fuzzy search on the "Assets Data" index in Elasticsearch. It looks for existing assets with descriptions similar to the new one.
4. **Context Building**: The results from the fuzzy search (i.e., historical values from similar assets) are collected. This historical context is combined with the user's input data and a detailed description of the target field.
5. **LLM Invocation**: This entire context package is formatted using a specialized prompt from the `PromptFactory` and sent to the OpenAI LLM.
6. **Prediction Generation**: The LLM analyzes the historical patterns and contextual information to predict the most likely value for the requested field.
7. **Response to User**: The predicted value is returned to the Django backend, which then sends it back through the EAM framework to the Asset Manager's user interface, populating the target field automatically.

## Key Components

### Views (`views.py`)

- `GenerateAssetView`: Handles single attribute prediction requests.
- `GenerateBulkAssetView`: Handles requests to predict values for multiple attributes in a single call, which improves efficiency.

Both views are responsible for orchestrating the data flow: validating input, calling the vector store, invoking the LLM, and returning the prediction.

### Vector Store (`vector_store/equipment_entry.py`)

- `EquipmentEntryElasticSearch`: A specialized class that communicates with the Elasticsearch index.
  - **`fuzzy_search`**: Its primary method for finding historical data.
  - **`label_mapping`**: A crucial dictionary that translates user-friendly field names (e.g., `category`) into the specific, and sometimes complex, field paths used in the Elasticsearch index (e.g., `CATEGORYID.CATEGORYCODE`).
  - **`field_descriptions`**: Contains plain-language descriptions for every possible field, which are used to give the LLM better context.

### Prompt Factory (`common/prompt_factory.py`)

- The `asset_entry_prompt` is used to structure the information sent to the LLM. It's engineered to instruct the model on how to prioritize information, handle cases with or without expected values, and format the output correctly.

## API Endpoints

The application exposes its functionality via a REST API.

*Note: The base path for these endpoints is likely `/api/equipment-entry/`, but you should confirm this in the main `urls.py` of the project.*

### Generate Single Asset Field

- **Endpoint**: `POST /generate/<asset_description>/`
- **Description**: Predicts a single value for a given attribute.
- **Request Body**:

    ```json
    {
        "attribute": "class",
        "accepted_values": {
            "department": "MAINT",
            "organization": "21T"
        },
        "expected_values": ["HVAC-R", "PUMP", "MOTOR"]
    }
    ```

- **Success Response**:

    ```json
    {
        "historical_values": ["HVAC-R", "HVAC-R"],
        "llm_response": "HVAC-R"
    }
    ```

### Generate Bulk Asset Fields

- **Endpoint**: `POST /generate-bulk/<asset_description>/`
- **Description**: Predicts values for a list of attributes in one request.
- **Request Body**:

    ```json
    {
        "attributes": ["class", "category", "criticality"],
        "accepted_values": {
            "department": "MAINT",
            "organization": "21T"
        },
        "attributes_expected_values": {
            "class": ["HVAC-R", "PUMP", "MOTOR"],
            "criticality": ["A", "B", "C"]
        }
    }
    ```

- **Success Response**:

    ```json
    {
        "predictions": {
            "class": "HVAC-R",
            "category": "AIR-EQUIP",
            "criticality": "A"
        }
    }
    ```