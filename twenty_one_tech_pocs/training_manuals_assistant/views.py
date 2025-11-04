from django.shortcuts import render
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import base64
from typing import Optional

from .schemas import TrainingManualQualificationExtraction
from .services import TrainingManualsAssistantService
from common import LLMFactory, ConfigManager
from common.eam_api import EAMApiService

class ProcessTrainingManualView(APIView):
    def __init__(self):
        self.base_eam_url = "https://us1.eam.hxgnsmartcloud.com:443/axis/restservices"
        self.username = "MOHAMED.MOSTAFA@21TECH.COM"
        self.password = "Password0!"
        self.eam_headers = {
            'Content-Type': 'application/json',
            'tenant': 'TWENTY1TECH_TST',
            'organization': '21T'
        }

    def _get_eam_auth_header(self):
        auth_str = f"{self.username}:{self.password}"
        auth_bytes = auth_str.encode('ascii')
        return f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"

    def post(self, request):
        try:
            document_code = request.data.get("document_code")
            training_manual_file_direct = request.FILES.get("training_manual_file")
            
            if not document_code and not training_manual_file_direct:
                return Response(
                    {"error": "No document_code or training_manual_file provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # For future EAM integration - currently just extracting qualification data
            create_qualifications_in_eam = request.data.get("create_in_eam", False)
            processed_file_for_service: Optional[InMemoryUploadedFile] = None
            document_name_for_service = "training_manual.pdf"

            if document_code:
                # Fetch document from EAM
                eam_doc_api_url = f"{self.base_eam_url}/documentattachments"
                headers = self.eam_headers.copy()
                headers["Authorization"] = self._get_eam_auth_header()
                headers["accept"] = "application/json"
                
                payload = {"DOCUMENTCODE": document_code, "UPLOADTYPE": "MOBILE"}
                try:
                    eam_response = requests.put(eam_doc_api_url, headers=headers, json=payload)
                    eam_response.raise_for_status()
                    eam_data = eam_response.json()
                except requests.exceptions.RequestException as e:
                    error_message = f"Failed to fetch document from EAM: {str(e)}"
                    if hasattr(e, 'response') and e.response is not None:
                        error_message += f" | Response: {e.response.text}"
                    return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                file_content_base64 = eam_data.get("Result", {}).get("ResultData", {}).get("Attachment", {}).get("FILECONTENT")
                if not file_content_base64:
                    error_detail = eam_data.get("ErrorAlert")
                    error_message = f"EAM API Error: {error_detail}" if error_detail else "FILECONTENT not found in EAM response."
                    return Response({"error": error_message, "eam_response": eam_data}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                try:
                    file_bytes = base64.b64decode(file_content_base64)
                    document_name_for_service = f"{document_code}_training_manual.pdf"
                    
                    file_io = BytesIO(file_bytes)
                    processed_file_for_service = InMemoryUploadedFile(
                        file=file_io,
                        field_name=None,
                        name=document_name_for_service,
                        content_type='application/pdf',
                        size=len(file_bytes),
                        charset=None
                    )
                except base64.binascii.Error as e:
                    return Response({"error": f"Failed to decode FILECONTENT: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            elif training_manual_file_direct:
                processed_file_for_service = training_manual_file_direct
                document_name_for_service = training_manual_file_direct.name

            if not processed_file_for_service:
                return Response({"error": "Failed to prepare document for processing."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Initialize services
            training_service = TrainingManualsAssistantService()
            llm_factory = LLMFactory()
            config_manager = ConfigManager()

            # Get LLM configuration
            llm_params = config_manager.get_llm_config()
            if not llm_params.get("name"):
                return Response({"error": "LLM_NAME not found in environment variables."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            llm = llm_factory.get_llm(llm_name=llm_params.pop("name"), **llm_params)

            response_data = {}
            try:
                # Process the training manual to extract qualification requirements
                qualification_extraction: Optional[TrainingManualQualificationExtraction] = training_service.process_document(
                    file=processed_file_for_service, llm=llm
                )

                if not qualification_extraction:
                    return Response({"error": "Failed to extract qualifications from training manual or no qualification data found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                response_data["qualification_extraction"] = qualification_extraction.model_dump()

                # Add summary statistics
                response_data["summary"] = {
                    "total_qualifications": len(qualification_extraction.qualifications),
                    "qualification_codes": [q.qualification_code for q in qualification_extraction.qualifications],
                }

                # Future enhancement: EAM integration for creating qualification records
                if create_qualifications_in_eam:
                    # Initialize EAM API service
                    eam_service = EAMApiService()
                    
                    qualification_summary = []
                    eam_creation_results = []
                    
                    for qualification in qualification_extraction.qualifications:
                        # Create qualification in EAM
                        qualification_data = {
                            "qualification_code": qualification.qualification_code,
                            "qualification_description": qualification.qualification_description
                        }
                        
                        eam_result = eam_service.create_qualification(
                            qualification_data=qualification_data,
                            organization_code="*",
                            class_code="*"
                        )
                        
                        eam_creation_results.append(eam_result)
                        
                        qualification_summary_item = {
                            "qualification_code": qualification.qualification_code,
                            "qualification_description": qualification.qualification_description,
                            "eam_integration_status": eam_result.get("status", "unknown"),
                            "eam_creation_result": eam_result
                        }
                        qualification_summary.append(qualification_summary_item)
                    
                    response_data["qualification_summary_for_eam"] = qualification_summary
                    response_data["eam_creation_summary"] = {
                        "total_qualifications_processed": len(qualification_extraction.qualifications),
                        "successful_creations": len([r for r in eam_creation_results if r.get("status") == "success"]),
                        "failed_creations": len([r for r in eam_creation_results if r.get("status") == "failed"]),
                        "creation_results": eam_creation_results
                    }

                return Response(response_data, status=status.HTTP_200_OK)
            
            except Exception as e:
                import traceback
                print(f"Error during service processing: {traceback.format_exc()}")
                return Response({"error": f"An error occurred during processing: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            finally:
                if 'training_service' in locals() and hasattr(training_service, 'cleanup'):
                    training_service.cleanup()

        except Exception as e:
            import traceback
            print(f"Unhandled exception in ProcessTrainingManualView: {traceback.format_exc()}") 
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
