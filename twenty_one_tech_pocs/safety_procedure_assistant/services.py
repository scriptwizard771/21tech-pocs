# Add your service classes here. 
from django.core.files.base import ContentFile
from typing import List, Optional
from langchain_core.language_models.base import BaseLanguageModel
import logging
import os

from django.core.files.uploadedfile import UploadedFile
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
import fitz  # PyMuPDF
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser

from .schemas import (
    Hazard,
    Precaution,
    HazardTypeChoices,
    PrecautionTimingChoices,
    IncidentAnalysisOutput
)
from common.eam_api import EAMApiService

logger = logging.getLogger(__name__)

class SafetyProcedureAssistantService:
    """
    Service for processing incident report documents and extracting structured safety analysis.
    """

    def __init__(self):
        self.temp_file_path: Optional[str] = None
        self.temp_dir: str = "temp_documents/safety_assistant"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.eam_api_service = EAMApiService()

    def process_document(
        self, file: UploadedFile, llm: BaseChatModel
    ) -> Optional[IncidentAnalysisOutput]:
        """
        Process an incident report document and generate a structured analysis.
        Args:
            file: The uploaded document file.
            llm: The language model.
        Returns:
            Optional[IncidentAnalysisOutput]: Structured analysis or None if error.
        """
        try:
            file_path = self._save_temp_file(file)
            self.temp_file_path = file_path
            
            # Use PyMuPDF to extract text from the PDF
            doc = fitz.open(file_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()

            # Create a single LangChain Document
            documents = [Document(page_content=full_text)]

            if not documents or not documents[0].page_content.strip():
                logger.warning(f"No content extracted from {file.name}")
                return None

            analysis_output = self._extract_incident_analysis(llm, documents)
            
            if analysis_output:
                logger.info(f"Successfully extracted incident analysis. Identified {len(analysis_output.identified_hazards)} hazards and {len(analysis_output.equipment_safety_links)} equipment links.")
            else:
                logger.info("No structured analysis was extracted by the LLM.")
            return analysis_output

        except Exception as e:
            logger.error(f"Error processing incident report {file.name}: {str(e)}")
            raise
        finally:
            self.cleanup()

    def _save_temp_file(self, file: UploadedFile) -> str:
        file_path = os.path.join(self.temp_dir, file.name)
        with open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        logger.info(f"Saved temporary incident report file: {file_path}")
        return file_path

    def _get_system_prompt_template(self) -> str:
        hazard_type_options = ", ".join([f"\"{e.value}\"" for e in HazardTypeChoices])
        precaution_timing_options = ", ".join([f"\"{e.value}\"" for e in PrecautionTimingChoices])
        equipment_category_options = ", ".join([f"\"{category}\"" for category in self.eam_api_service.get_equipment_categories()])
        equipment_class_options = ", ".join([f"\"{class_item}\"" for class_item in self.eam_api_service.get_equipment_classes()])

        return """
You are an AI expert in workplace safety incident analysis. Your task is to thoroughly analyze an incident report and structure the findings into two main components:
1.  A comprehensive list of all hazards identified or inferred, each with a detailed list of ALL its relevant precautions.
2.  A list of specific links between equipment mentioned in the incident, a KEY precaution related to that equipment and incident, and the hazard this precaution addresses.

Output Requirements:
Generate a single JSON object. This object must have two top-level keys: "identified_hazards" and "equipment_safety_links".

1.  `identified_hazards`: This must be a LIST of Hazard objects.
    -   Each Hazard object must have:
        -   `hazard_code`: A unique, LLM-proposed code (e.g., "HAZ-INC001-BURN").
        -   `description`: Detailed description of the hazard.
        -   `hazard_type`: Must be one of: {{hazard_type_options}}.
        -   `precautions`: A LIST of Precaution objects. This list should include ALL precautions relevant to THIS hazard.
            -   Each Precaution object must have:
                -   `precaution_code`: A unique, LLM-proposed code (e.g., "PREC-HAZ001-001").
                -   `description`: Detailed description of the precaution.
                -   `timing` (optional): Must be one of: {{precaution_timing_options}}.

2.  `equipment_safety_links`: This must be a LIST of EquipmentSafetyLink objects.
    -   This list should only be populated if the incident clearly describes specific equipment involved in a safety lapse related to a specific precaution for an identified hazard.
    -   Each EquipmentSafetyLink object must have:
        -   `equipment_details`: An object with:
            -   `equipment_id`: (Mandatory) Specific name/model of the equipment (e.g., "Blowtorch Model X23").
            -   `class_code` (optional): Must be one of: {{equipment_class_options}} if specified.
            -   `category` (optional): Must be one of: {{equipment_category_options}} if specified.
        -   `linked_precaution`: A Precaution object. This precaution MUST BE an exact copy of one of the precautions listed under the corresponding hazard in the `identified_hazards` list.
        -   `parent_hazard_code`: The `hazard_code` of the hazard (from the `identified_hazards` list) to which the `linked_precaution` belongs.

Example JSON structure:
{{
    "identified_hazards": [
        {{
            "hazard_code": "HAZ-BTORCH-001",
            "description": "Risk of burn injury from direct flame or heated parts of the blowtorch.",
            "hazard_type": "Physical Hazards",
            "precautions": [
                {{"precaution_code": "PREC-BT001-PPE01", "description": "Wear appropriate heat-resistant gloves and face shield.", "timing": "Pre Work"}},
                {{"precaution_code": "PREC-BT001-AREA02", "description": "Clear work area of flammable materials before starting.", "timing": "Pre Work"}},
                {{"precaution_code": "PREC-BT001-OPER03", "description": "Never leave a lit blowtorch unattended.", "timing": "During"}}
            ]
        }},
        {{
            "hazard_code": "HAZ-GASLEAK-002",
            "description": "Risk of explosion or fire due to gas leak from faulty blowtorch connection.",
            "hazard_type": "Chemical Hazards",
            "precautions": [
                {{"precaution_code": "PREC-GL002-INSP01", "description": "Inspect hose and connections for leaks before each use with soapy water.", "timing": "Pre Work"}},
                {{"precaution_code": "PREC-GL002-SHUTOFF02", "description": "Ensure gas cylinder valve is closed when not in use.", "timing": "Post Work"}}
            ]
        }}
    ],
    "equipment_safety_links": [
        {{
            "equipment_details": {{
                "equipment_id": "SuperFlame Blowtorch SF-5000",
                "class_code": "HWEQ",
                "category": "Welding Tools"
            }},
            "linked_precaution": {{
                "precaution_code": "PREC-BT001-PPE01", 
                "description": "Wear appropriate heat-resistant gloves and face shield.", 
                "timing": "Pre Work"
            }},
            "parent_hazard_code": "HAZ-BTORCH-001",
        }}
    ]
}}

Ensure all codes are unique and descriptive. If no specific equipment links are clear from the report, `equipment_safety_links` can be an empty list. However, `identified_hazards` should always be populated if any hazards can be inferred.
Strictly adhere to this JSON structure. Do not use markdown formatting for the JSON output.
""".replace("{{hazard_type_options}}", hazard_type_options).replace("{{precaution_timing_options}}", precaution_timing_options).replace("{{equipment_category_options}}", equipment_category_options).replace("{{equipment_class_options}}", equipment_class_options)

    def _create_extraction_prompt(self) -> ChatPromptTemplate:
        system_template = self._get_system_prompt_template()
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_template = """Please analyze the following incident report document and extract the structured safety analysis based on the requirements provided.
Incident Report Text:
{text}

Respond with ONLY the JSON object adhering to the schema described in the system prompt.
"""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        return ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

    def _extract_incident_analysis(
        self, llm: BaseChatModel, documents: List[Document]
    ) -> Optional[IncidentAnalysisOutput]:
        logger.info(f"Starting incident analysis extraction from {len(documents)} document chunks.")
        extraction_prompt = self._create_extraction_prompt()
        parser = PydanticOutputParser(pydantic_object=IncidentAnalysisOutput)

        chain = load_summarize_chain(
            llm, chain_type="stuff", verbose=True, prompt=extraction_prompt
        )
        try:
            response = chain.invoke({"input_documents": documents})
            output_text = response.get("output_text", "")
            if not output_text:
                logger.warning("LLM returned empty output for incident analysis.")
                return None
            
            parsed_response = parser.invoke(output_text)
            logger.info("Successfully parsed LLM response into IncidentAnalysisOutput.")
            return parsed_response
        except Exception as e:
            logger.error(f"Failed to parse LLM response for incident analysis. Error: {str(e)}. Raw output: '{output_text[:500]}...'")
            return None

    def cleanup(self) -> None:
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
                logger.info(f"Cleaned up temporary incident report file: {self.temp_file_path}")
            except OSError as e:
                logger.error(f"Error cleaning up temporary file {self.temp_file_path}: {str(e)}")
        self.temp_file_path = None 