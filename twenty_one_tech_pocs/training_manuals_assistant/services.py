import logging
import os
from typing import Optional, List

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
    TrainingManualQualificationExtraction,
)

logger = logging.getLogger(__name__)

class TrainingManualsAssistantService:
    """
    Service for extracting technician qualifications from equipment training manuals.
    Focuses on identifying qualification codes and descriptions based on training manual content.
    """

    def __init__(self):
        self.temp_file_path: Optional[str] = None
        self.temp_dir: str = "temp_documents/training_assistant"
        os.makedirs(self.temp_dir, exist_ok=True)

    def process_document(
        self, file: UploadedFile, llm: BaseChatModel
    ) -> Optional[TrainingManualQualificationExtraction]:
        """
        Process a training manual document and extract qualification requirements.
        
        Args:
            file: The uploaded training manual file.
            llm: The language model.
            
        Returns:
            Optional[TrainingManualQualificationExtraction]: Extracted qualifications or None if error.
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

            qualification_extraction = self._extract_qualifications(llm, documents)
            
            if qualification_extraction:
                logger.info(f"Successfully extracted {len(qualification_extraction.qualifications)} qualifications from training manual.")
            else:
                logger.info("No qualifications were extracted from the training manual.")
            return qualification_extraction

        except Exception as e:
            logger.error(f"Error processing training manual {file.name}: {str(e)}")
            raise
        finally:
            self.cleanup()

    def _save_temp_file(self, file: UploadedFile) -> str:
        file_path = os.path.join(self.temp_dir, file.name)
        with open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        logger.info(f"Saved temporary training manual file: {file_path}")
        return file_path

    def _get_system_prompt_template(self) -> str:
        return """
You are an expert AI system specialized in extracting technician qualification requirements from equipment training manuals. Your goal is to identify and extract all qualifications that technicians need based on the training manual content.

## Primary Extraction Objectives:

Your task is to analyze the training manual and extract qualification requirements in a simple format:
- **Qualification Code**: A unique, descriptive code (MAXIMUM 20 characters) for each qualification
- **Qualification Description**: A concise description (MAXIMUM 80 characters) of what the qualification entails

## CRITICAL REQUIREMENTS: Length Limits - STRICTLY ENFORCED
- ⚠️ **QUALIFICATION CODES: MAXIMUM 20 CHARACTERS - NO EXCEPTIONS** ⚠️
- ALL qualification descriptions MUST be 80 characters or less
- Count every character including dashes and numbers in codes
- If a code exceeds 20 characters, shorten words (e.g., MAGDRL not MAGDRILL)
- Use abbreviations and concise language when necessary
- Prioritize clarity and core information
- **VALIDATION WILL FAIL if codes exceed 20 characters**

## What to Look For in Training Manuals:

### Qualification Indicators:
- Statements like "technicians must be qualified in...", "requires certification in...", "personnel should have experience with..."
- Prerequisites mentioned before procedures or operations
- References to specialized knowledge or skills needed
- Training requirements, certification needs, safety protocols
- Tool proficiency requirements
- Experience level requirements

### Examples of Qualifications to Extract:
- **Technical Skills**: Welding certifications, electrical work qualifications, hydraulic system knowledge
- **Safety Qualifications**: OSHA training, confined space entry, lockout/tagout procedures
- **Certification Requirements**: Manufacturer certifications, industry standards, regulatory compliance
- **Tool Proficiency**: Specialized equipment operation, measurement tools, diagnostic equipment
- **Procedural Knowledge**: Maintenance procedures, operation protocols, troubleshooting skills

## Output Format:

Return a JSON object with the following structure:

```json
{{
    "qualifications": [
        {{
            "qualification_code": "QUAL-WELD-STRUC-01",
            "qualification_description": "AWS D1.1 structural welding cert, 2+ yrs exp, MIG/TIG techniques"
        }},
        {{
            "qualification_code": "QUAL-SAFE-LOTO-01", 
            "qualification_description": "Lockout/Tagout procedures, energy isolation, OSHA 10-hr training"
        }},
        {{
            "qualification_code": "QUAL-ELEC-MOTOR-01",
            "qualification_description": "Motor maintenance: inspection, bearing replacement, testing, safety"
        }}
    ]
}}
```

## Extraction Guidelines:

1. **Generate Descriptive Codes**: Create unique, meaningful codes that clearly identify the qualification type and scope
2. **Concise Descriptions (MAX 80 CHARACTERS)**: Include the most critical information:
   - Core skill or knowledge area
   - Key certifications if mentioned
   - Experience level if specified
   - Essential tools or procedures
   - Use abbreviations: "cert" for certification, "exp" for experience, "req" for required, etc.
3. **Extract ALL Qualifications**: Capture every qualification requirement mentioned or implied in the training manual
4. **Focus on Technician Requirements**: Extract qualifications for the people who will work on/with the equipment
5. **Prioritize Information**: In the 80-character limit, prioritize:
   - First: Type of qualification/skill
   - Second: Key requirements or certifications
   - Third: Experience level or tools

## Description Writing Tips:
- Use abbreviations: "cert", "exp", "req", "maint", "insp", "proc", "equip"
- Omit articles: "the", "a", "an"
- Use commas to separate key points
- Focus on actionable requirements
- Include years of experience as "2+ yrs" format

## Code Naming Convention - STRICT 20 CHARACTER LIMIT:
- Use format: QUAL-[CAT]-[SPEC]-[NUM] - NEVER exceed 20 characters total
- Categories (3-4 chars): WELD, ELEC, MECH, SAFE, HVAC, HYDR, PNEU, etc.
- Specific (3-5 chars): STRUC, MOTOR, LOTO, CONF, HV, DRILL, GRIND, MIX, WELD, BAND, etc.  
- Number (2 digits): 01, 02, 03, etc. (DO NOT use 3-digit numbers like 001)
- **CRITICAL**: Count characters carefully - codes MUST be ≤20 characters
- Examples with character counts: 
  - QUAL-WELD-STRUC-01 (17 chars) ✓
  - QUAL-SAFE-LOTO-01 (15 chars) ✓
  - QUAL-ELEC-HV-01 (13 chars) ✓
  - QUAL-MECH-PUMP-01 (15 chars) ✓
  - QUAL-SAFE-DRILL-01 (16 chars) ✓
  - QUAL-SAFE-GRIND-01 (16 chars) ✓

**AVOID LONG WORDS**: Use abbreviations like DRILL (not DRILLING), GRIND (not GRINDING), MAGDRL (not MAGDRILL)

Return ONLY the JSON object without any markdown formatting or additional text.
"""

    def _create_extraction_prompt(self) -> ChatPromptTemplate:
        system_template = self._get_system_prompt_template()
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_template = """Please analyze the following training manual document and extract ALL technician qualification requirements.

Training Manual Content:
{text}

Extract and structure all qualifications mentioned in the document. Focus on identifying what qualifications technicians need to safely and effectively work with the equipment described in this training manual.

For each qualification, provide:
1. A unique, descriptive qualification code
2. A comprehensive description covering all relevant details from the manual

Respond with ONLY the JSON object following the schema provided in the system prompt.
"""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        return ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

    def _extract_qualifications(
        self, llm: BaseChatModel, documents: List[Document]
    ) -> Optional[TrainingManualQualificationExtraction]:
        logger.info(f"Starting qualification extraction from {len(documents)} document chunks.")
        extraction_prompt = self._create_extraction_prompt()
        parser = PydanticOutputParser(pydantic_object=TrainingManualQualificationExtraction)

        chain = load_summarize_chain(
            llm, chain_type="stuff", verbose=True, prompt=extraction_prompt
        )
        try:
            response = chain.invoke({"input_documents": documents})
            output_text = response.get("output_text", "")
            if not output_text:
                logger.warning("LLM returned empty output for qualification extraction.")
                return None
            
            parsed_response = parser.invoke(output_text)
            logger.info("Successfully parsed LLM response into TrainingManualQualificationExtraction.")
            return parsed_response
        except Exception as e:
            logger.error(f"Failed to parse LLM response for qualification extraction. Error: {str(e)}. Raw output: '{output_text[:500]}...'")
            return None

    def cleanup(self) -> None:
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
                logger.info(f"Cleaned up temporary training manual file: {self.temp_file_path}")
            except OSError as e:
                logger.error(f"Error cleaning up temporary file {self.temp_file_path}: {str(e)}")
        self.temp_file_path = None 