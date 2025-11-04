from django.shortcuts import render
# from django.core.files.uploadedfile import UploadedFile # Keep if direct file upload is re-enabled
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile # For EAM content
from io import BytesIO # For EAM content
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import base64
from typing import List, Optional # Keep Optional if service can return None

# Updated schema imports
from .schemas import IncidentAnalysisOutput, Hazard, Precaution, EquipmentDetails 
from .services import SafetyProcedureAssistantService
from common import EAMApiService, LLMFactory, ConfigManager

class ProcessIncidentReportView(APIView):
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
            incident_report_file_direct = request.FILES.get("incident_report_file") # For direct uploads

            if not document_code and not incident_report_file_direct:
                return Response(
                    {"error": "No document_code or incident_report_file provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            create_in_eam = request.data.get("create_in_eam", False)
            processed_file_for_service: Optional[InMemoryUploadedFile] = None
            document_name_for_service = "incident_report.txt" # Default

            if document_code:
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
                    document_name_for_service = f"{document_code}_incident_report.dat" # Use a generic extension or derive from EAM if possible
                    
                    # Wrap bytes in BytesIO and then InMemoryUploadedFile
                    file_io = BytesIO(file_bytes)
                    processed_file_for_service = InMemoryUploadedFile(
                        file=file_io,
                        field_name=None, # Not tied to a form field
                        name=document_name_for_service,
                        content_type='application/octet-stream', # Or more specific if known
                        size=len(file_bytes),
                        charset=None
                    )
                except base64.binascii.Error as e:
                    return Response({"error": f"Failed to decode FILECONTENT: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            elif incident_report_file_direct:
                # If direct upload is re-enabled, ensure it's passed correctly
                # The service expects an UploadedFile, which incident_report_file_direct already is.
                processed_file_for_service = incident_report_file_direct
                document_name_for_service = incident_report_file_direct.name


            if not processed_file_for_service:
                 return Response({"error": "Failed to prepare document for processing."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            spa_service = SafetyProcedureAssistantService()
            eam_api = EAMApiService()
            llm_factory = LLMFactory()
            config_manager = ConfigManager()

            llm_params = config_manager.get_llm_config()
            if not llm_params.get("name"):
                return Response({"error": "LLM_NAME not found in environment variables."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            llm = llm_factory.get_llm(llm_name=llm_params.pop("name"), **llm_params)

            response_data = {}
            try:
                # Service now returns Optional[IncidentAnalysisOutput]
                analysis_output: Optional[IncidentAnalysisOutput] = spa_service.process_document(
                    file=processed_file_for_service, llm=llm
                )

                if not analysis_output:
                    return Response({"error": "Failed to analyze incident report or no data extracted."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                response_data["incident_analysis"] = analysis_output.model_dump()

                if create_in_eam:
                    eam_creation_summary = []
                    eam_hazard_codes_map = {}    # LLM code -> EAM code
                    eam_precaution_codes_map = {} # LLM code -> EAM code
                    eam_hazard_revisions = {}    # LLM code -> revision used
                    eam_precaution_revisions = {} # LLM code -> revision used

                    # 1. Create all identified Hazards and their Precautions
                    if analysis_output.identified_hazards:
                        for hazard_obj_from_llm in analysis_output.identified_hazards:
                            hazard_responses = []
                            precaution_responses_for_hazard = []

                            # Create Hazard if not already created (by LLM's proposed code)
                            if hazard_obj_from_llm.hazard_code not in eam_hazard_codes_map:
                                hazard_payload = hazard_obj_from_llm.model_dump(exclude={'precautions'}) # EAM API might not want nested precautions
                                hazard_eam_resp = eam_api.create_hazard(hazard_payload)
                                hazard_responses.append(hazard_eam_resp)
                                if hazard_eam_resp and not hazard_eam_resp.get("error"):
                                    eam_hazard_codes_map[hazard_obj_from_llm.hazard_code] = hazard_eam_resp.get("HAZARDCODE", hazard_obj_from_llm.hazard_code)
                                    # Store the revision used for status updates
                                    eam_hazard_revisions[hazard_obj_from_llm.hazard_code] = hazard_eam_resp.get("revision_used", 0)
                            
                            # Create Precautions for this hazard
                            for precaution_obj_from_llm in hazard_obj_from_llm.precautions:
                                if precaution_obj_from_llm.precaution_code not in eam_precaution_codes_map:
                                    precaution_eam_resp = eam_api.create_precaution(precaution_obj_from_llm.model_dump())
                                    precaution_responses_for_hazard.append(precaution_eam_resp)
                                    if precaution_eam_resp and not precaution_eam_resp.get("error"):
                                        eam_precaution_codes_map[precaution_obj_from_llm.precaution_code] = precaution_eam_resp.get("PRECAUTIONCODE", precaution_obj_from_llm.precaution_code)
                                        # Store the revision used for status updates
                                        eam_precaution_revisions[precaution_obj_from_llm.precaution_code] = precaution_eam_resp.get("revision_used", 0)
                            
                            eam_creation_summary.append({
                                "processed_hazard_code_llm": hazard_obj_from_llm.hazard_code,
                                "eam_hazard_creation_responses": hazard_responses,
                                "eam_precaution_creation_responses_for_hazard": precaution_responses_for_hazard
                            })
                    
                    # 2. Process EquipmentSafetyLinks for EAM (conceptual "Safety Procedure" or "Link Record")
                    equipment_link_eam_summaries = []
                    if analysis_output.equipment_safety_links:
                        for link_obj in analysis_output.equipment_safety_links:
                            # This is where a specific EAM record linking Equipment to a Hazard & Precaution would be created.
                            
                            # For now, just gather info for summary
                            equipment_link_summary = {
                                "equipment_details_from_link": link_obj.equipment_details.model_dump(),
                                "linked_precaution_code_llm": link_obj.linked_precaution.precaution_code,
                                "parent_hazard_code_llm": link_obj.parent_hazard_code,
                                "eam_hazard_code_ref": eam_hazard_codes_map.get(link_obj.parent_hazard_code),
                                "eam_precaution_code_ref": eam_precaution_codes_map.get(link_obj.linked_precaution.precaution_code),
                                # "eam_equipment_safety_link_creation_status": "NOT_ATTEMPTED - EAM API for this specific link is not yet defined/implemented."
                                # If a new API (e.g., eam_api.create_equipment_safety_link) existed, it would be called here:
                                # e.g., eam_link_response = eam_api.create_equipment_safety_link(payload_for_link)
                                # equipment_link_summary["eam_link_creation_response"] = eam_link_response
                            }

                            eam_hazard_code = eam_hazard_codes_map.get(link_obj.parent_hazard_code)
                            eam_precaution_code = eam_precaution_codes_map.get(link_obj.linked_precaution.precaution_code)
                            
                            hazard_eam_type_code = None
                            # Find the hazard type from the original hazard object
                            for hazard_in_list in analysis_output.identified_hazards:
                                if hazard_in_list.hazard_code == link_obj.parent_hazard_code:
                                    # Map hazard type to EAM type code
                                    hazard_type_to_eam_map = {
                                        "All Hazards": "GEN",
                                        "Biological Hazards": "BI",
                                        "Chemical Hazards": "CH",
                                        "Physical Hazards": "PH",
                                        "Radiological Hazards": "RA",
                                    }
                                    hazard_eam_type_code = hazard_type_to_eam_map.get(hazard_in_list.hazard_type, "PH")
                                    break
                            
                            equipment_details_for_eam = {}
                            if link_obj.equipment_details:
                                dumped_details = link_obj.equipment_details.model_dump()
                                equipment_details_for_eam = {
                                    "class_code": dumped_details.get("class_code"),
                                    "category": dumped_details.get("category"),
                                    "equipment_id": dumped_details.get("equipment_name_or_id") # Map to equipment_id
                                }

                            if eam_hazard_code and eam_precaution_code and hazard_eam_type_code:
                                # Get the revision numbers that were used when creating these records
                                hazard_revision = eam_hazard_revisions.get(link_obj.parent_hazard_code, 0)
                                precaution_revision = eam_precaution_revisions.get(link_obj.linked_precaution.precaution_code, 0)
                                
                                # Get the descriptions from the original objects
                                hazard_description = ""
                                precaution_description = link_obj.linked_precaution.description or ""
                                
                                # Find the hazard description from the original hazard object
                                for hazard_in_list in analysis_output.identified_hazards:
                                    if hazard_in_list.hazard_code == link_obj.parent_hazard_code:
                                        hazard_description = hazard_in_list.description or ""
                                        break
                                
                                eam_link_response = eam_api.create_safety_link_record(
                                    eam_hazard_code=eam_hazard_code,
                                    hazard_eam_type_code=hazard_eam_type_code,
                                    eam_precaution_code=eam_precaution_code,
                                    equipment_details=equipment_details_for_eam,
                                    hazard_revision=hazard_revision,
                                    precaution_revision=precaution_revision,
                                    hazard_description=hazard_description,
                                    precaution_description=precaution_description
                                    # organization_code can be specified if needed, defaults to "*" in the method
                                )
                                equipment_link_summary["eam_equipment_safety_link_creation_response"] = eam_link_response
                                equipment_link_summary["eam_equipment_safety_link_creation_status"] = "ATTEMPTED"
                            else:
                                equipment_link_summary["eam_equipment_safety_link_creation_status"] = "SKIPPED - Missing EAM hazard/precaution code or hazard type."
                                equipment_link_summary["eam_equipment_safety_link_creation_response"] = {
                                    "error": "Missing mapped EAM codes or hazard type for this link.",
                                    "details": {
                                        "eam_hazard_code_found": bool(eam_hazard_code),
                                        "eam_precaution_code_found": bool(eam_precaution_code),
                                        "hazard_eam_type_code_found": bool(hazard_eam_type_code)
                                    }
                                }
                            equipment_link_eam_summaries.append(equipment_link_summary)
                    
                    # Consolidate EAM creation feedback
                    response_data["eam_processing_summary"] = {
                        "hazard_precaution_creation_log": eam_creation_summary,
                        "equipment_safety_link_processing_log": equipment_link_eam_summaries
                    }

                return Response(response_data, status=status.HTTP_200_OK)
            
            except Exception as e: # Catch exceptions from service call or EAM processing
                import traceback
                print(f"Error during service processing or EAM creation: {traceback.format_exc()}")
                return Response({"error": f"An error occurred during processing: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            finally:
                # Ensure service cleanup is called if it was initialized
                if 'spa_service' in locals() and hasattr(spa_service, 'cleanup'):
                    spa_service.cleanup()

        except Exception as e:
            import traceback
            print(f"Unhandled exception in ProcessIncidentReportView: {traceback.format_exc()}") 
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

