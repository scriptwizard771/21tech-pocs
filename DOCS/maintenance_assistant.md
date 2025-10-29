# Maintenance Assistant

The **Maintenance Assistant** application is designed to automate the creation of Preventive Maintenance (PM) Schedules, Task Plans, and Checklists in HxGN EAM by analyzing unstructured PDF documents, such as maintenance procedures or service manuals.

## Architecture and Data Flow

This assistant follows a PDF-processing pattern that serves as a template for other similar applications in the project. The primary goal is to convert unstructured text from a PDF into structured, actionable data within the EAM system.

![Maintenance Assistant Architecture](./images/21%20Tech%20Use%20Cases-PM%20Schedule%20Generation.jpg)

1. **User Input**: A Maintenance Manager provides the document code of a Maintenance Procedure (MP) PDF that is already stored in HxGN EAM.
2. **Request to Django**: The EAM extensible framework sends a request to the Django backend containing the `document_code`. The request can also specify whether the extracted data should be automatically created in EAM.
3. **Fetch Document**: The `ProcessMaintenanceDocumentView` in Django calls the EAM Web Services API to fetch the specified PDF document.
4. **PDF Parsing**: The raw PDF document is passed to the **`unstructured` PDF Parsing Engine**, which extracts the plain text content from the file.
5. **LLM Invocation**: The extracted text is sent to the **OpenAI LLM**. The request is accompanied by a detailed prompt from `MaintenanceAssistantService` that instructs the model to identify and structure all relevant PM Schedules, Task Plans, and their associated Checklist items.
6. **Structured Data Generation**: The LLM returns a structured JSON object that conforms to the Pydantic schemas defined in the application (`MaintenanceSchedule`, `TaskPlan`, `ChecklistItem`).
7. **Create in EAM (Optional)**: If the `create_in_eam` flag was set to `true`, the application uses the `EAMApiService` to make a series of POST requests to the EAM Web Services API, creating the PM Schedules, Task Plans, and Checklists from the structured data.
8. **Response to User**: The final JSON response, containing the extracted data and the results of the EAM creation process, is sent back to the user.

## Key Components

### Views (`views.py`)

- **`ProcessMaintenanceDocumentView`**: The single entry point for the application. It manages the entire workflow, from fetching the document from EAM to calling the service and returning the final response.

### Services (`services/maintenance_assistant.py`)

- **`MaintenanceAssistantService`**: Contains the core business logic.
  - Handles saving the fetched PDF to a temporary file for processing.
  - Uses `UnstructuredPDFLoader` to parse the PDF.
  - Constructs a highly specific system prompt to guide the LLM's output.
  - Invokes the LLM and uses a `PydanticOutputParser` to validate that the LLM's output matches the expected `MaintenanceSchedule` schema.
  - Includes a `cleanup` method to remove temporary files.

### Schemas (`schemas.py`)

- **`MaintenanceSchedule`**: The main Pydantic model that defines the entire data structure, including a list of `TaskPlan` objects.
- **`TaskPlan`**: Defines the structure for a task plan, including a code, description, and a list of `ChecklistItem` objects.
- **`ChecklistItem`**: Defines the structure for an individual checklist item.

## API Endpoint

### Process Maintenance Document

- **Endpoint**: `POST /api/maintenance/process-document/` (Confirm base path in project `urls.py`)
- **Description**: Processes a maintenance document from EAM to extract structured data and optionally create it in the system.
- **Request Body**:

    ```json
    {
        "document_code": "MP-PUMP-001",
        "create_in_eam": true
    }
    ```

- **Success Response**:

    ```json
    {
        "extracted_data": {
            "code": "PM_PUMP_INSPECTION_2024",
            "description": "Preventive Maintenance for Centrifugal Pump",
            "duration": 4,
            "task_plans": [
                {
                    "task_code": "TP_LUBRICATION",
                    "description": "Lubrication and Grease Check",
                    "checklist": [
                        {
                            "checklist_id": "CL_VISUAL_CHECK",
                            "description": "Visually inspect for leaks"
                        },
                        {
                            "checklist_id": "CL_APPLY_GREASE",
                            "description": "Apply grease to fittings"
                        }
                    ]
                }
            ]
        },
        "created_in_eam": [
            {
                "task_code": "TP_LUBRICATION",
                "description": "Lubrication and Grease Check",
                "api_response": { "...EAM response for task creation..." },
                "checklists": [
                    {
                        "checklist_id": "CL_VISUAL_CHECK",
                        "description": "Visually inspect for leaks",
                        "api_response": { "...EAM response for checklist creation..." }
                    }
                ]
            }
        ]
    }
    ```
