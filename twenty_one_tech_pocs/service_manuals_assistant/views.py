from django.shortcuts import render
from django.core.files.uploadedfile import UploadedFile
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import base64
from django.core.files.base import ContentFile
from typing import List # Added for type hinting

# Try to import magic, fall back to signature-based detection if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic not available, falling back to signature-based file detection")

from .schemas import TaskPlan # Changed from MaintenanceSchedule
from .services import ServiceManualsAssistantService # Changed service
from common import EAMApiService, LLMFactory, ConfigManager


class ProcessServiceManualDocumentView(APIView): # Changed class name
    def __init__(self):
        self.base_url = "https://us1.eam.hxgnsmartcloud.com:443/axis/restservices"
        self.username = "MOHAMED.MOSTAFA@21TECH.COM"
        self.password = "Password0!" # Consider using environment variables for credentials
        self.headers = {
            'Content-Type': 'application/json',
            'tenant': 'TWENTY1TECH_TST',
            'organization': '21T'
        }

    def get_auth(self):
        """Get the basic authentication header value."""
        auth_str = f"{self.username}:{self.password}"
        auth_bytes = auth_str.encode('ascii')
        return f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"

    def detect_file_type(self, file_bytes):
        """
        Detect file type based on file content using magic numbers.
        Returns the file extension and MIME type.
        """
        if MAGIC_AVAILABLE:
            try:
                # Get MIME type from file content
                mime_type = magic.from_buffer(file_bytes, mime=True)
                
                # Map common MIME types to extensions
                mime_to_extension = {
                    'application/pdf': 'pdf',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
                    'application/vnd.ms-excel': 'xls',
                    'application/msword': 'doc',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                    'text/plain': 'txt',
                    'image/jpeg': 'jpg',
                    'image/png': 'png',
                    'image/gif': 'gif',
                }
                
                extension = mime_to_extension.get(mime_type, 'pdf')  # Default to pdf
                
                return extension, mime_type
                
            except Exception as e:
                # Fallback: try to detect based on file signature bytes
                return self.detect_by_signature(file_bytes)
        else:
            # Magic not available, use signature-based detection
            return self.detect_by_signature(file_bytes)

    def detect_by_signature(self, file_bytes):
        """
        Fallback method to detect file type by examining file signature bytes.
        Returns the file extension and a description.
        """
        if not file_bytes or len(file_bytes) < 4:
            return 'pdf', 'application/pdf'
        
        # Check file signatures (magic numbers)
        signature = file_bytes[:4]
        
        # PDF signature
        if file_bytes.startswith(b'%PDF'):
            return 'pdf', 'application/pdf'
        
        # Excel (.xlsx) signature - ZIP-based format
        elif signature == b'PK\x03\x04':
            # Need to check deeper for xlsx vs other zip formats
            if b'xl/' in file_bytes[:1024]:  # xlsx contains xl/ directory
                return 'xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return 'zip', 'application/zip'
        
        # Old Excel (.xls) signature
        elif signature[:2] == b'\xd0\xcf':  # OLE2 signature
            return 'xls', 'application/vnd.ms-excel'
        
        # JPEG signature
        elif signature[:3] == b'\xff\xd8\xff':
            return 'jpg', 'image/jpeg'
        
        # PNG signature
        elif signature == b'\x89PNG':
            return 'png', 'image/png'
        
        # Default to PDF if unknown
        else:
            return 'pdf', 'application/pdf'

    def post(self, request):
        try:
            document_code = request.data.get("document_code")
            if not document_code:
                return Response(
                    {"error": "No document_code provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            create_in_eam = request.data.get("create_in_eam", False)

            eam_api_url = "https://us1.eam.hxgnsmartcloud.com:443/axis/restservices/documentattachments"
            headers = {
                "accept": "application/json",
                "tenant": "TWENTY1TECH_TST",
                "organization": "21T",
                "Authorization": self.get_auth(),
                "Content-Type": "application/json",
            }
            payload = {"DOCUMENTCODE": document_code, "UPLOADTYPE": "MOBILE"}

            try:
                eam_response = requests.put(eam_api_url, headers=headers, json=payload)
                eam_response.raise_for_status()
                eam_data = eam_response.json()
            except requests.exceptions.RequestException as e:
                return Response(
                    {"error": f"Failed to fetch document from EAM: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            file_content_base64 = (
                eam_data.get("Result", {})
                .get("ResultData", {})
                .get("Attachment", {})
                .get("FILECONTENT")
            )
            if not file_content_base64:
                error_detail = eam_data.get("ErrorAlert")
                if error_detail:
                    error_message = f"EAM API Error: {error_detail}"
                else:
                    error_message = "FILECONTENT not found in EAM response or EAM response structure is unexpected."
                return Response(
                    {"error": error_message},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            try:
                file_bytes = base64.b64decode(file_content_base64)
            except base64.binascii.Error as e:
                return Response(
                    {"error": f"Failed to decode FILECONTENT: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Detect file type based on file content
            file_extension, mime_type = self.detect_file_type(file_bytes)
            
            # Ensure we support the file type for processing
            supported_types = ['pdf', 'xlsx', 'xls']
            if file_extension not in supported_types:
                file_extension = 'pdf'  # Default to PDF for unsupported types
                
            document_name = f"{document_code}.{file_extension}"
            document = ContentFile(file_bytes, name=document_name)

            service = ServiceManualsAssistantService() # Changed service
            eam_api = EAMApiService()
            response_data = {}
            llm_factory = LLMFactory()
            config_manager = ConfigManager()

            llm_params = config_manager.get_llm_config()

            if not llm_params.get("name"):
                return Response(
                    {"error": "LLM_NAME not found in environment variables."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            llm = llm_factory.get_llm(llm_name=llm_params.pop("name"), **llm_params)
            try:
                # Process the document to extract a list of task plans
                extracted_task_plans: List[TaskPlan] = service.process_document(document, llm=llm)
                # Serialize each TaskPlan object in the list
                response_data["extracted_data"] = [tp.model_dump() for tp in extracted_task_plans]

                if create_in_eam:
                    created_tasks_summary = []
                    # Iterate through each task plan in the extracted data
                    for task_plan_obj in extracted_task_plans:
                        # Create the task plan in EAM
                        task_response = eam_api.create_task_plan(task_plan_obj)
                        task_info = {
                            "task_code": task_plan_obj.task_code,
                            "description": task_plan_obj.description,
                            "api_response": task_response,
                            "checklists": [],
                        }

                        # Create each checklist for this task plan
                        for i, checklist_item in enumerate(task_plan_obj.checklist):
                            checklist_response = eam_api.create_checklist(
                                task_plan_obj.task_code,
                                checklist_item,
                                sequence=(i + 1) * 10,
                            )
                            task_info["checklists"].append(
                                {
                                    "checklist_id": checklist_item.checklist_id,
                                    "description": checklist_item.description,
                                    "api_response": checklist_response,
                                }
                            )
                        created_tasks_summary.append(task_info)
                    response_data["created_in_eam"] = created_tasks_summary

                return Response(response_data, status=status.HTTP_200_OK)
            finally:
                service.cleanup()

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
