# Safety Procedure Assistant

The **Safety Procedure Assistant** is a specialized Django application that analyzes incident reports to automatically identify hazards, recommend precautions, and establish safety links between equipment and procedures in HxGN EAM.

## Application Goal

While this application follows the same general PDF-processing architecture as the Maintenance Assistant, its goal is different. Instead of creating work orders, it populates the **Safety module** of EAM. It reads unstructured incident reports and creates structured **Hazards**, **Precautions**, and **Safety Matrix Links** that connect them to specific equipment.

![Safety Procedure Assistant Architecture](./images/21%20Tech%20Use%20Cases-Safety.jpg)

## Data Flow Differences

1. **Input**: The process starts with an **Incident Report PDF** identified by a `document_code`.
2. **LLM Goal**: The LLM is prompted to act as a safety expert. Its task is to parse the report and extract a detailed list of hazards, a comprehensive list of precautions for each hazard, and specific links between equipment mentioned in the report and the safety procedures.
3. **Structured Data**: The LLM returns a JSON object conforming to the `IncidentAnalysisOutput` schema, which is more complex than the maintenance schema. It includes separate lists for `identified_hazards` and `equipment_safety_links`.
4. **EAM Creation**: If `create_in_eam` is true, the application calls the `EAMApiService` to:
    - Create each `Hazard` and its associated `Precautions`.
    - Update the status of those hazards and precautions to "Approved".
    - Create a **Safety Matrix Link** record, which formally associates the approved hazard, precaution, and the specific piece of equipment in EAM.

## Key Components

### Views (`views.py`)

- **`ProcessIncidentReportView`**: The API endpoint that orchestrates the entire process, from fetching the report from EAM to calling the service and triggering the multi-step EAM creation process.

### Services (`services.py`)

- **`SafetyProcedureAssistantService`**: Contains the core logic. It dynamically builds the system prompt for the LLM by first calling the `EAMApiService` to get the latest lists of `equipment_categories` and `equipment_classes`. This ensures the LLM has the most up-to-date, valid options to choose from when identifying equipment details, making the output more accurate and reliable.

### Schemas (`schemas.py`)

- **`IncidentAnalysisOutput`**: The top-level Pydantic model.
- **`Hazard`**: Defines a hazard with its code, description, type (e.g., "Physical Hazards"), and a nested list of `Precaution` objects.
- **`Precaution`**: Defines a single precautionary measure.
- **`EquipmentSafetyLink`**: A specific data structure that links `EquipmentDetails` to a `Precaution` and its `parent_hazard_code`. This is used to create the Safety Matrix record in EAM.

## API Endpoint

### Process Incident Report

- **Endpoint**: `POST /api/safety/process-incident-report/` (Confirm base path in project `urls.py`)
- **Description**: Processes an incident report from EAM to extract safety data and optionally create corresponding records in the EAM safety module.
- **Request Body**:

    ```json
    {
        "document_code": "INC-REP-001",
        "create_in_eam": true
    }
    ```

- **Success Response**:

    ```json
    {
        "incident_analysis": {
            "identified_hazards": [
                {
                    "hazard_code": "HAZ-FALLING-OBJECTS-001",
                    "description": "Risk of injury from objects falling from improperly loaded shelves.",
                    "hazard_type": "Physical Hazards",
                    "precautions": [
                        {
                            "precaution_code": "PREC-SHEL-LOAD-001",
                            "description": "Ensure shelving units are not overloaded and items are stable.",
                            "timing": "Pre Work"
                        }
                    ]
                }
            ],
            "equipment_safety_links": [
                {
                    "equipment_details": {
                        "equipment_id": "MECO Pallet Rack System",
                        "class_code": "RACK"
                    },
                    "linked_precaution": {
                       "precaution_code": "PREC-SHEL-LOAD-001",
                       "description": "Ensure shelving units are not overloaded and items are stable.",
                       "timing": "Pre Work"
                    },
                    "parent_hazard_code": "HAZ-FALLING-OBJECTS-001"
                }
            ]
        },
        "eam_processing_summary": {
            "hazard_precaution_creation_log": [ ... ],
            "equipment_safety_link_processing_log": [ ... ]
        }
    }
    ```
