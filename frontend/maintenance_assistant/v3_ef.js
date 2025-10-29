    /*
        EF THAT HANDLES ATTACHMENT DOCUMENTS | BSDOCU.js
        HISTORY
        DATE 		    WHO 				PURPOSE
        ---------------------------------------------------------------------
        5/7/2025        @Lucky.djomo 		- Added checkbox "Generate PM" to Call the Webservice " Document attachement"

        5/12/2025	    @Mohamed.Mostafa	- Added simplified success message in popup instead of showing full API response
                                            - Improved error handling and messaging
                                            - Added ngrok URL to the API call

        5/12-13/2025	@Lucky.djomo	    - Added checkbox "Generate Service Manuals"
                                            - Refactored checkbox handling.
                                            - Refactored repeated API logic into a reusable function that accepts the endpoint 
                                            and document code as parameters to simplify calls across multiple blocks.
                                            - Formatted the logic that handle the checkbox "Generate Service manuals"
                                            - Formatted the Custom Response Call back
                                                
        05/15/2025	    @Mohamed.Mostafa	- Updated `formatServiceResponse` for detailed task plan extraction from service manuals.
                                            - Changed ngrok URL to `https://chief-unified-moccasin.ngrok-free.app`.
                                            - Modified API payload: `create_in_eam: false`.
                                            - Enhanced API error handling (e.g., 403 Forbidden) and refined pop-up messages.

        05/29/2025		@lucky.djomo		- Added checkbox "Generate Certification Requirements"
                                            - Update EF to handle the checkbox.

        01/15/2025		@Mohamed.Mostafa	- Updated `formatCertificationReqResponse` to handle new API response structure
                                            - Modified function to process `qualification_extraction.qualifications` array

        06/12/2025		@Mohamed.Mostafa	- Updated `handleAPIcall` to use the new URL `http://54.219.76.120:8001`
                                            - Updated `createCheckboxHandler` to use the new URL `http://54.219.76.120:8001`
    */

    Ext.define('EAM.custom.external_bsdocu', {
        extend: 'EAM.custom.AbstractExtensibleFramework',

        getSelectors: function () {
            const efc = this;

            // Format response for maintenance document
            const formatMaintenanceResponse = (data) => {
                let message = 'API Call Successful!';
                if (data.extracted_data) {
                    message += '\n\nPM Schedule:\n  ' + data.extracted_data.code;
                    message += '\n\nTask Plans:';
                    data.extracted_data.task_plans.forEach((taskPlan, index) => {
                        if (index > 0) message += '\n';
                        message += '\n  • ' + taskPlan.task_code;
                        (taskPlan.checklist || []).forEach(item => {
                            message += '\n    - ' + item.checklist_id;
                        });
                    });
                } else {
                    message += '\n\n' + (typeof data === 'object' ? JSON.stringify(data, null, 2) : data);
                }
                return message;
            };

            // Format response for service manual
            const formatServiceResponse = (data) => {
                let message = 'API Call Successful!';
                if (data.extracted_data && Array.isArray(data.extracted_data)) {
                    message += '\n\nExtracted Task Plans:';
                    if (data.extracted_data.length === 0) {
                        message += '\n  No task plans were extracted.';
                    } else {
                        data.extracted_data.forEach((taskPlan, index) => {
                            if (index > 0) message += '\n';
                            message += '\n  • ' + taskPlan.task_code + (taskPlan.description ? ` (${taskPlan.description})` : '');
                            (taskPlan.checklist || []).forEach(item => {
                                message += '\n    - ' + item.checklist_id + (item.description ? ` (${item.description})` : '');
                            });
                        });
                    }
                } else if (data.extracted_data) {
                    // Handle cases where extracted_data might not be an array or is an unexpected structure
                    message += '\n\nReceived unexpected data structure for extracted_data:';
                    message += '\n' + JSON.stringify(data.extracted_data, null, 2);
                } else if (data.error) {
                    message = 'API Call Failed:\n  ' + data.error;
                } else {
                    message += '\n\n' + (typeof data === 'object' ? JSON.stringify(data, null, 2) : data);
                }
                return message;
            };

            // Format response for Safety Procedure 
            const formatSafetyResponse = (data) => {
                let message = 'API Call Successful!';
                
                if (data.incident_analysis) {
                    const analysis = data.incident_analysis;
                    
                    // Display identified hazards
                    if (analysis.identified_hazards && analysis.identified_hazards.length > 0) {
                        message += '\n\nIdentified Hazards:';
                        analysis.identified_hazards.forEach((hazard, index) => {
                            if (index > 0) message += '\n';
                            message += '\n  • ' + hazard.hazard_code + ' (' + hazard.hazard_type + ')';
                            
                            if (hazard.precautions && hazard.precautions.length > 0) {
                                message += '\n    Precautions:';
                                hazard.precautions.forEach(precaution => {
                                    message += '\n      - ' + precaution.precaution_code + ' (' + precaution.timing + ')';
                                });
                            }
                        });
                    }
                    
                    // Display safety matrix
                    if (analysis.equipment_safety_links && analysis.equipment_safety_links.length > 0) {
                        message += '\n\nSafety Matrix:';
                        analysis.equipment_safety_links.forEach((link, index) => {
                            if (index > 0) message += '\n';
                            message += '\n  • Equipment ID: ' + link.equipment_details.equipment_id;
                            message += '\n    Precaution ID: ' + link.linked_precaution.precaution_code;
                            message += '\n    Parent Hazard: ' + link.parent_hazard_code;
                        });
                    }
                    
                    // If no hazards or equipment links found
                    if ((!analysis.identified_hazards || analysis.identified_hazards.length === 0) && 
                        (!analysis.equipment_safety_links || analysis.equipment_safety_links.length === 0)) {
                        message += '\n\nNo hazards or equipment safety links were identified in the analysis.';
                    }
                } else if (data.error) {
                    message = 'API Call Failed:\n  ' + data.error;
                } else {
                    message += '\n\n' + (typeof data === 'object' ? JSON.stringify(data, null, 2) : data);
                }
                return message;
            };

            // Format response for Certification Requirements
            const formatCertificationReqResponse = (data) => {
                let message = 'API Call Successful!';
                
                if (data.qualification_extraction && data.qualification_extraction.qualifications) {
                    const qualifications = data.qualification_extraction.qualifications;
                    const summary = data.summary;
                    
                    // Display summary first
                    if (summary) {
                        message += `\n\nTraining Manual Analysis Summary:`;
                        message += `\n  Total Qualifications Found: ${summary.total_qualifications}`;
                    }
                    
                    // Display detailed qualifications
                    message += '\n\nQualification Requirements:';
                    qualifications.forEach((qual, index) => {
                        if (index > 0) message += '\n';
                        message += `\n  • Code: ${qual.qualification_code}`;
                        message += `\n    Description: ${qual.qualification_description}`;
                    });
                    
                    // Display qualification codes list
                    if (summary && summary.qualification_codes) {
                        message += '\n\nQualification Codes Summary:';
                        summary.qualification_codes.forEach((code, index) => {
                            message += `\n  ${index + 1}. ${code}`;
                        });
                    }
                } else if (data.error) {
                    message = 'API Call Failed:\n  ' + data.error;
                } else {
                    message += '\n\n' + (typeof data === 'object' ? JSON.stringify(data, null, 2) : data);
                }
                return message;
            };

            return {
                // Form Panel loaded
                '[extensibleFramework] [tabName=HDR][isTabView=true]': {
                    afterrender: function () {
                        console.log('Form Panel rendered, processing fields and sections...');
                    },
                    afterloaddata: function () {
                        // Data loaded into the form
                    }
                },

                // Checkbox 1: Generate PM | Maintenance Document 
                '[extensibleFramework] [tabName=HDR][isTabView=true] [name=udfchkbox01]': {
                    change: efc.createCheckboxHandler('/api/maintenance/process-document/', formatMaintenanceResponse)
                },

                // Checkbox 2: Generate Service Manuals | Service Manual Document
                '[extensibleFramework] [tabName=HDR][isTabView=true] [name=udfchkbox02]': {
                    change: efc.createCheckboxHandler('/api/service-manuals/process-document/', formatServiceResponse)
                },

                // Checkbox 3: Generate Safety Procedure | Safety Procedure Document
                '[extensibleFramework] [tabName=HDR][isTabView=true] [name=udfchkbox03]': {
                    change: efc.createCheckboxHandler('/api/safety-procedures/process-incident-report/', formatSafetyResponse)
                },

                // Checkbox 4: Generate Training Manuals | Certification Requirements Document
                '[extensibleFramework] [tabName=HDR][isTabView=true] [name=udfchkbox04]': {
                    change: efc.createCheckboxHandler('/api/training-manuals/process-training-manual/', formatCertificationReqResponse)
                }
            };
        },

        // Pop-up error or success message
        popUpMsg: function (msg) {
            EAM.MsgBox.show({
                title: 'Message Box',
                msgs: [{
                    type: 'error',
                    msg: EAM.Lang.getCustomFrameworkMessage(msg)
                }],
                buttons: EAM.MsgBox.OK,
                fn: function () { },
                scope: this
            });
        },

            // Generic handler factory for checkbox APIs
    createCheckboxHandler: function (apiPath, formatResponseCallback) {
        debugger;
        const efc = this;
        const baseUrl = 'https://54.219.76.120:8001'; // Production URL (Nginx proxy on port 8001)

            return function (checkbox, newVal) {
                debugger;
                if (newVal === true) {
                    const p = EAM.Utils.getCurrentTab().getFormPanel();
                    const vals = p.getFldValues(["documentcode", "filepath"]);
                    const vDoccode = vals.documentcode;

                    if (!vDoccode) {
                        efc.popUpMsg('Missing Data : Document Code is required to call the API.');
                        checkbox.setValue(false);
                        return;
                    }

                    checkbox.setDisabled(true); // Optional UX feedback
                    efc.handleAPIcall(baseUrl, apiPath, vDoccode, formatResponseCallback, checkbox);
                }
            };
        },

        // Centralized API call handler
        handleAPIcall: function (baseUrl, apiPath, vDoccode, formatResponseCallback, checkbox) {
            debugger;
            const API_URL = `${baseUrl}${apiPath}`;
            const payload = {
                document_code: vDoccode,
                create_in_eam: true
            };

            console.log('API Request:', {
                method: 'POST',
                url: API_URL,
                body: payload,
                timestamp: new Date().toISOString()
            });

            const headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true'
            };

            fetch(API_URL, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            })
                .then(response => {
                    if (!response.ok) {
                        return response.text().then(text => {
                            let errorDetail = `API request failed with status ${response.status} (${response.statusText})`;
                            if (text) {
                                if (response.status === 403) {
                                    errorDetail += ': Forbidden. Check credentials, EAM permissions, tenant/org, and API access rules.';
                                } else if (text.length < 200 && !text.toLowerCase().includes("<html")) {
                                    errorDetail += ': ' + text;
                                } else {
                                    errorDetail += '. Server returned a detailed error (see console for full response).';
                                }
                            }
                            console.error("Raw error response from server:", text);
                            throw new Error(errorDetail);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    const messageContent = (typeof formatResponseCallback === 'function')
                        ? formatResponseCallback(data)
                        : 'API Call Successful.\n\n' + JSON.stringify(data, null, 2);

                    const messageType = data && data.error ? 'error' : 'info';

                    EAM.MsgBox.show({
                        title: messageType === 'error' ? 'API Error' : 'API Success',
                        msgs: [{
                            type: messageType,
                            msg: EAM.Lang.getCustomFrameworkMessage(messageContent)
                        }],
                        buttons: EAM.MsgBox.OK,
                        fn: function () { },
                        scope: this
                    });
                    console.log('API Response Data:', data);
                })
                .catch(error => {
                    console.error('API Call Error Object:', error);
                    const errorMessageToShow = (error && error.message)
                        ? error.message
                        : 'An unknown API error occurred. Check console for details.';
                    this.popUpMsg(errorMessageToShow);
                    if (checkbox) checkbox.setValue(false);
                })
                .finally(() => {
                    if (checkbox) checkbox.setDisabled(false); // Re-enable checkbox
                });
        }
    });
