import os

from twenty_one_tech_pocs.common import LLMFactory, LLMsEnum, PromptFactory
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .vector_store.equipment_entry import EquipmentEntryElasticSearch

vector_store = EquipmentEntryElasticSearch()
llm_factory = LLMFactory()
load_dotenv()


class GenerateAssetView(APIView):
    def options(self, request, asset_description, *args, **kwargs):
        """
        Handle OPTIONS preflight requests for CORS
        """
        response = Response(status=status.HTTP_200_OK)
        # Adjust the allowed origins, methods, and headers as needed
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = (
            "Accept, Content-Type, ngrok-skip-browser-warning"
        )
        return response

    def post(self, request, asset_description):
        attribute_key = request.data.get("attribute", None)
        accepted_values_dict = request.data.get("accepted_values", {})
        expected_values_list = request.data.get("expected_values", None)  # Added

        print(f"attribute_key: {attribute_key}")
        print(f"accepted_values_dict: {accepted_values_dict}")
        print(f"expected_values_list: {expected_values_list}")

        if attribute_key is None:
            return Response(
                {"error": "Please provide the 'attribute' in the request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate accepted_values format (should be a dictionary)
        if not isinstance(accepted_values_dict, dict):
            return Response(
                {
                    "error": "'accepted_values' must be a JSON object (dictionary) in the request body"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate expected_values format (should be a list if provided)
        if expected_values_list is not None and not isinstance(
            expected_values_list, list
        ):
            return Response(
                {"error": "'expected_values' must be a list if provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # validate attribute_key not in accepted_values_dict
        if attribute_key in accepted_values_dict:
            return Response(
                {
                    "error": f"'{attribute_key}' key should not be present in 'accepted_values' dictionary"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Format accepted values for the prompt
        accepted_values_str = "\n".join(
            [f"- {key}: {value}" for key, value in accepted_values_dict.items()]
        )
        if not accepted_values_str:
            accepted_values_str = "None provided."
            return Response(
                {"error": "No accepted values provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )  # This line seems problematic, if accepted_values is optional, this might be an issue. Keeping as is for now.

        # Prepare expected_values for the prompt
        expected_values_for_prompt = expected_values_list
        if not expected_values_list:  # Handles None or empty list
            expected_values_for_prompt = "None provided."

        # Use the vector store’s fuzzy_search (which uses label_mapping internally)
        historical_values = vector_store.fuzzy_search(asset_description, attribute_key)
        target_field = vector_store.label_mapping.get(attribute_key)
        field_description = vector_store.field_descriptions.get(
            attribute_key, "No description available."
        )

        if target_field is None:
            # Use 400 Bad Request for invalid client input
            return Response(
                {"error": "Invalid attribute provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Return early if no historical values found, but with a 200 OK status as the request was valid
        # if not historical_values:
        #     return Response({"historical_values": [], "llm_response": None}, status=status.HTTP_200_OK)

        # Use prompt factory for asset_entry_prompt
        try:
            equipment_prompt = PromptFactory.get_prompt("asset_entry_prompt")
        except ValueError as e:
            print(f"Error getting prompt: {e}")
            return Response(
                {"error": "Server configuration error: Could not load prompt."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # API key is now handled internally by LLMFactory if needed (e.g., for OpenAI)
        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            return Response(
                {"error": "Server configuration error: OpenAI API key not found."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # Get LLM instance from factory
            # Assuming GPT4O_MINI is desired here, adjust if needed
            model = llm_factory.get_llm(
                llm_name=LLMsEnum.GPT4O.value, temperature=0, api_key=api_key
            )
            chain = equipment_prompt | model
            llm_result = chain.invoke(
                {
                    "asset_description": asset_description,
                    "historical_values": historical_values,
                    "target_field": target_field,
                    "field_description": field_description,
                    "accepted_values": accepted_values_str,
                    "expected_values": expected_values_for_prompt,  # Added
                }
            )
        except ValueError as e:  # Catch specific validation errors from factory
            print(f"LLM Configuration Error: {e}")
            return Response(
                {"error": f"Invalid LLM configuration: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            # Log the exception e for debugging
            print(f"Error invoking LLM chain: {e}")
            # Use 500 Internal Server Error for issues during LLM call
            return Response(
                {"error": "Error generating response from LLM."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "historical_values": historical_values,
                "llm_response": llm_result.content,
            },
            status=status.HTTP_200_OK,
        )


class GenerateBulkAssetView(APIView):
    """
    API View for generating predictions for multiple asset attributes in bulk.
    """

    def options(self, request, asset_description, *args, **kwargs):
        """
        Handle OPTIONS preflight requests for CORS
        """
        response = Response(status=status.HTTP_200_OK)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = (
            "Accept, Content-Type, ngrok-skip-browser-warning"
        )
        return response

    def post(self, request, asset_description):
        """
        Handles POST requests to generate bulk predictions.
        Expects 'attributes' (list) and 'accepted_values' (dict) in the request body.
        Optionally accepts 'attributes_expected_values' (dict) where keys are attribute names
        and values are lists of expected values for that attribute.
        """
        attributes_to_predict = request.data.get("attributes", None)
        accepted_values_dict = request.data.get("accepted_values", {})
        attributes_expected_values_map = request.data.get(
            "attributes_expected_values", {}
        )  # Added

        print(f"attributes_to_predict: {attributes_to_predict}")
        print(f"accepted_values_dict: {accepted_values_dict}")
        print(f"attributes_expected_values_map: {attributes_expected_values_map}")
        
        # --- Input Validation ---
        if attributes_to_predict is None:
            return Response(
                {"error": "Please provide the 'attributes' list in the request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(attributes_to_predict, list) or not attributes_to_predict:
            return Response(
                {"error": "'attributes' must be a non-empty list in the request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(accepted_values_dict, dict):
            return Response(
                {
                    "error": "'accepted_values' must be a JSON object (dictionary) in the request body"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(attributes_expected_values_map, dict):  # Added validation
            return Response(
                {
                    "error": "'attributes_expected_values' must be a JSON object (dictionary) if provided"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Setup ---
        predictions = {}
        # API key handled by factory
        api_key = os.environ.get("LLM_API_KEY")
        if not api_key:
            return Response(
                {"error": "Server configuration error: OpenAI API key not found."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # Get LLM and prompt once
            model = llm_factory.get_llm(
                llm_name=LLMsEnum.GPT4O_MINI.value, temperature=0, api_key=api_key
            )
            equipment_prompt = PromptFactory.get_prompt("asset_entry_prompt")
            chain = equipment_prompt | model
        except ValueError as e:  # Catch specific validation errors from factory
            print(f"LLM/Prompt Configuration Error: {e}")
            return Response(
                {"error": f"Invalid LLM/Prompt configuration: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            print(f"Error initializing LLM components: {e}")
            return Response(
                {"error": "Error initializing LLM components."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Format accepted values once
        accepted_values_str = "\n".join(
            [f"- {key}: {value}" for key, value in accepted_values_dict.items()]
        )
        if not accepted_values_str:
            accepted_values_str = "None provided."

        # --- Prediction Loop ---
        for attribute_key in attributes_to_predict:
            target_field = vector_store.label_mapping.get(attribute_key)
            field_description = vector_store.field_descriptions.get(
                attribute_key, "No description available."
            )

            if target_field is None:
                print(
                    f"Warning: Invalid attribute '{attribute_key}' requested for asset '{asset_description}'. Skipping."
                )
                predictions[attribute_key] = None  # Indicate invalid attribute
                continue

            historical_values = vector_store.fuzzy_search(asset_description, attribute_key)

            # Prepare expected_values for the current attribute
            current_expected_list = attributes_expected_values_map.get(
                attribute_key, []
            )
            expected_values_for_prompt = current_expected_list
            if (
                not current_expected_list
            ):  # Handles empty list from map or if key not found
                expected_values_for_prompt = "None provided."

            # if not historical_values:
            #     # Indicate no historical data
            #     predictions[attribute_key] = None
            #     continue

            # Invoke LLM for the current attribute
            try:
                llm_result = chain.invoke(
                    {
                        "asset_description": asset_description,
                        "historical_values": historical_values,
                        "target_field": target_field,
                        "field_description": field_description,
                        "accepted_values": accepted_values_str,
                        "expected_values": expected_values_for_prompt,  # Added
                    }
                )
                predictions[attribute_key] = llm_result.content
            except Exception as e:
                print(
                    f"Error invoking LLM chain for attribute '{attribute_key}' on asset '{asset_description}': {e}"
                )
                predictions[attribute_key] = None  # Indicate prediction error

        # --- Return Results ---
        return Response({"predictions": predictions}, status=status.HTTP_200_OK)
