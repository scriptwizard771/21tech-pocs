import logging
import os
from typing import Optional

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
from langchain_openai import ChatOpenAI
from ..schemas import MaintenanceSchedule

logger = logging.getLogger(__name__)


class MaintenanceAssistantService:
    """Service for processing maintenance documents and extracting structured data."""

    def __init__(self):
        self.temp_file_path: Optional[str] = None
        self.temp_dir: str = "temp_documents"
        os.makedirs(self.temp_dir, exist_ok=True)

    def process_document(
        self, file: UploadedFile, llm: BaseChatModel
    ) -> MaintenanceSchedule:
        """
        Process a maintenance procedure document using LangChain and generate structured output.

        Args:
            file: The uploaded PDF file to process
            llm: The language model to use for processing

        Returns:
            MaintenanceSchedule: Structured maintenance data extracted from document

        Raises:
            ValueError: If file format is not supported
            IOError: If file cannot be read or processed
        """
        if not file.name.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported")

        try:
            # Save the uploaded file temporarily
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
                raise ValueError("No content could be extracted from the PDF")

            # Process the document to extract maintenance information
            processed_data = self._process_maintenance_data(llm, documents)

            return processed_data
        
        except Exception as e:
            logger.error(f"Error processing document {file.name}: {str(e)}")
            raise
        finally:
            # Clean up temporary file
            self.cleanup()

    def _save_temp_file(self, file: UploadedFile) -> str:
        """
        Save the uploaded file to a temporary location.

        Args:
            file: The uploaded file to save

        Returns:
            str: Path to the saved temporary file
        """
        file_path = os.path.join(self.temp_dir, file.name)

        # Save the file content
        with open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        logger.info(f"Saved temporary file: {file_path}")
        return file_path

    def _create_maintenance_prompt(self) -> ChatPromptTemplate:
        """
        Create the prompt template for maintenance data extraction.

        Returns:
            ChatPromptTemplate: The configured prompt template
        """
        system_template = self._get_system_prompt_template()

        # Create a prompt for the maintenance processing
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )

        human_template = """Please analyze the following maintenance procedure document and extract the required information:
        
        {text}
        
        Respond with ONLY the JSON structure containing the extracted maintenance data.
        """

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

    def _get_system_prompt_template(self) -> str:
        """
        Get the system prompt template for maintenance data extraction.

        Returns:
            str: The system prompt template
        """
        return """You are an expert maintenance planner analyzing maintenance procedure documents.
Extract information to create:
1. Maintenance schedules with task plans
2. Task plans with specific checklists
3. Comprehensive checklists with steps

For each entity (PM Schedule, Task Plan, Checklist), generate codes and IDs that are:
- Descriptive: Incorporate key terms or abbreviations from the procedure, equipment, or task.
- Unique: Ensure each code/ID is distinct within the document, using a combination of procedure name, task type, sequence number, or other relevant context.
- Human-readable: Avoid random strings; prefer meaningful, context-based identifiers.

Format your response as a JSON matching this schema:

{{
    "code": string, // PM Schedule code, descriptive and unique (e.g., 'PM_PUMP_INSPECTION_2024') max length 20
    "description": string, // PM Schedule description max length 80
    "duration": int,
    "task_plans": [
        {{
            "task_code": string, // Task plan code, descriptive and unique (e.g., 'TP_LUBRICATION') max length 20
            "description": string, // Task plan description max length 80
            "checklist": [
                {{
                    "checklist_id": string, // Checklist ID, descriptive and unique (e.g., 'CL_VISUAL_CHECK') max length 20
                    "description": string // Checklist description max length 80    
                }}
            ]
        }}
    ]
}}

Extract all relevant information from the document and ensure it fits into this structure.
For any missing required fields, use reasonable defaults based on industry standards.
All durations should be integers (e.g., 2, 3, 69).
Each checklist should be associated with an appropriate task plan.
"""

    def _process_maintenance_data(
        self, llm: ChatOpenAI, documents: list[Document]
    ) -> MaintenanceSchedule:
        """
        Process the document chunks to extract maintenance information.

        Args:
            llm: The language model to use for processing
            documents: The document chunks to process

        Returns:
            MaintenanceSchedule: Structured maintenance data
        """
        logger.info(f"Processing {len(documents)} document chunks")

        # Create the prompt template
        chat_prompt = self._create_maintenance_prompt()

        # Configure the output parser for the expected schema
        parser = PydanticOutputParser(pydantic_object=MaintenanceSchedule)

        # Create a chain for document processing
        summarize_chain = load_summarize_chain(
            llm,
            chain_type="stuff",
            verbose=True,
            prompt=chat_prompt,
        )

        # Get a response from the model with the structured data
        try:
            response = summarize_chain.invoke({"input_documents": documents})
            parsed_response = parser.invoke(response["output_text"])
            logger.info("Successfully extracted maintenance data")
            return parsed_response
        except Exception as e:
            logger.error(f"Error extracting maintenance data: {str(e)}")
            raise ValueError(
                f"Failed to extract structured data from document: {str(e)}"
            )

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
                logger.info(f"Cleaned up temporary file: {self.temp_file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")
