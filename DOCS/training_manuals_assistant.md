# Training Manuals Assistant

The **Training Manuals Assistant** is a Django application that automates the creation of technician **Qualifications** in HxGN EAM by analyzing training manuals and other technical documents.

## Application Goal

Following the same PDF-processing architecture, this assistant's specific purpose is to read a training manual and extract a list of all the qualifications, certifications, or skills required for a technician to work on the specified equipment. It then creates these as formal `Qualification` records in EAM.

![Training Manuals Assistant Architecture](./images/21%20Tech%20Use%20Cases-training%20manuals.jpg)

## Data Flow Differences

1. **Input**: The process starts with a **Training Manual PDF** identified by a `document_code` or uploaded directly.
2. **LLM Goal**: The LLM is prompted to act as an HR/training coordinator. Its task is to read the manual and identify all stated or implied qualification requirements (e.g., "Must be certified in AWS D1.1 structural welding," "Requires 2+ years of experience").
3. **Structured Data**: The LLM returns a JSON object conforming to the `TrainingManualQualificationExtraction` schema, which contains a list of `Qualification` objects. The schema is simple, requiring only a `qualification_code` and a `qualification_description`.
4. **EAM Creation**: If `create_in_eam` is true, the application iterates through the list of extracted qualifications and calls the `create_qualification` method in the `EAMApiService` for each one.

## Key Components

### Views (`views.py`)

- **`ProcessTrainingManualView`**: The API endpoint that orchestrates the workflow.

### Services (`services.py`)

- **`TrainingManualsAssistantService`**: Contains the core logic. The system prompt used here is specifically designed to identify and extract qualifications, enforcing constraints on the length of the description (max 80 characters) to comply with EAM limitations.

### Schemas (`schemas.py`)

- **`TrainingManualQualificationExtraction`**: The top-level Pydantic model that holds a list of `Qualification` objects.
- **`Qualification`**: A simple model with just two fields: `qualification_code` and `qualification_description`.

## API Endpoint

### Process Training Manual

- **Endpoint**: `POST /api/training-manuals/process-training-manual/` (Confirm base path in project `urls.py`)
- **Description**: Processes a training manual to extract qualifications and optionally create them in EAM.
- **Request Body**:

    ```json
    {
        "document_code": "TRAIN-WELD-01",
        "create_in_eam": true
    }
    ```

- **Success Response**:

    ```json
    {
        "qualification_extraction": {
            "qualifications": [
                {
                    "qualification_code": "QUAL-WELD-STRUCT-001",
                    "qualification_description": "AWS D1.1 structural welding cert, 2+ yrs exp, MIG/TIG techniques"
                }
            ]
        },
        "qualification_summary_for_eam": [
            {
                "qualification_code": "QUAL-WELD-STRUCT-001",
                "qualification_description": "AWS D1.1 structural welding cert, 2+ yrs exp, MIG/TIG techniques",
                "eam_integration_status": "success",
                "eam_creation_result": {
                    "status": "success",
                    "qualification_code": "QUAL-WELD-STRUCT-001",
                    "eam_response": { "...EAM response..." }
                }
            }
        ]
    }
    ```
