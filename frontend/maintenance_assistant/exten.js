Ext.define('EAM.custom.EquipmentEntryPredictions', {
    extend: 'EAM.custom.AbstractExtensibleFramework',

    // Store references to dynamically created buttons (predict buttons next to fields)
    fieldButtons: {},

    // Central cache for expected values fetched from GRIDDATA
    // Structure: { fieldName: { params: {param1: value1, ...}, data: [...] } }
    expectedValuesCache: {},

    // Hardcoded expected values
    hardcodedExpectedValues: {
        'criticality': [
            "Equipment criticality",
            "MISSION CRITICAL",
            "IMPACT IF DELAYED",
            "NOT MISSION CRITICAL",
            "High",
            "Low",
            "Moderate",
            "Very High",
            "Very Low"
        ],
        'state': [
            "CN complete",
            "CN in process",
            "CN pending",
            "Defective",
            "Good"
        ],
        'assetstatus': [
            "Active",
            "Installed",
            "Withdrawn"
        ],
        'operationalstatus': [
            "Not Operational",
            "Operational"
        ],
        'outofservice': [true, false],
        'safety': [true, false],
        'production': [true, false],
        'trackresource': [true, false],
        'udfchkbox01': [true, false]
    },

    // --- Helper Functions ---

    /**
     * Fetches expected values for a given field from GRIDDATA and caches them.
     * @param {String} fieldName The name of the field (e.g., 'category', 'class').
     * @param {Ext.form.Panel} formPanel The form panel to get context values from.
     * @param {Boolean} forceUpdate If true, fetches data even if cached.
     * @returns {Promise<Array|null>} A promise that resolves with the fetched data array or null on error/no data.
     */
    fetchAndCacheExpectedValues: function (fieldName, formPanel, forceUpdate = false) {
        var self = this;
        console.log('Fetch/Cache check for:', fieldName, 'Force update:', forceUpdate);

        return new Promise(function (resolve) { // Use Promise for async handling
            var gridConfig = self.getGridConfigForField(fieldName);
            if (!gridConfig) {
                console.warn('No GRIDDATA configuration found for field:', fieldName);
                resolve(null); // Cannot fetch without config
                return;
            }

            var currentParams = {};
            try {
                currentParams = formPanel.getFldValues(gridConfig.paramFields);
            } catch (e) {
                console.error('Error getting form values for', fieldName, 'params:', gridConfig.paramFields, e);
                resolve(null); // Cannot proceed without params
                return;
            }

            // Add static params from config
            Ext.Object.merge(currentParams, gridConfig.staticParams || {});

            var cacheEntry = self.expectedValuesCache[fieldName];

            // Check cache validity
            if (!forceUpdate && cacheEntry && self.areParamsEqual(cacheEntry.params, currentParams)) {
                console.log('Using cached expected values for:', fieldName, 'Params:', currentParams);
                resolve(cacheEntry.data); // Return cached data
                return;
            }

            console.log('Fetching expected values for:', fieldName, 'with params:', currentParams);
            var ajaxParams = {
                GRID_NAME: gridConfig.gridName,
                REQUEST_TYPE: "LIST.HEAD_DATA.STORED"
            };

            // Add LOV aliases from currentParams based on gridConfig.paramMap
            var aliasIndex = 1;
            Ext.Object.each(gridConfig.paramMap, function (formField, aliasName) {
                ajaxParams['LOV_ALIAS_NAME_' + aliasIndex] = aliasName;
                ajaxParams['LOV_ALIAS_VALUE_' + aliasIndex] = currentParams[formField];
                ajaxParams['LOV_ALIAS_TYPE_' + aliasIndex] = gridConfig.paramTypes[formField] || 'text'; // Default to text
                aliasIndex++;
            });
            // Add static LOV aliases from gridConfig.staticParamsMap
            Ext.Object.each(gridConfig.staticParamsMap, function (aliasName, aliasValue) {
                ajaxParams['LOV_ALIAS_NAME_' + aliasIndex] = aliasName;
                ajaxParams['LOV_ALIAS_VALUE_' + aliasIndex] = aliasValue;
                ajaxParams['LOV_ALIAS_TYPE_' + aliasIndex] = 'text'; // Assume text for static params
                aliasIndex++;
            });


            try {
                var resp = EAM.Ajax.request({
                    url: "GRIDDATA",
                    params: ajaxParams,
                    async: false, // Keeping sync based on original code, consider async if possible
                    method: "POST"
                });

                var records = [];
                var cnt = resp.responseData.pageData.grid.GRIDRESULT.GRID.METADATA.RECORDS;
                let numericCnt = parseInt(cnt); // Ensure it's a number

                if (!isNaN(numericCnt) && numericCnt > 0) {
                    // Extract only the code (first column, assuming 'code' is the relevant value)
                    // Adjust 'code' if the actual field name in the grid data is different
                    records = Ext.Array.map(resp.responseData.pageData.grid.GRIDRESULT.GRID.DATA, function (item) {
                        // Use the configured valueField for this grid
                        return item[gridConfig.valueField];
                    });
                    console.log('Fetched', records.length, 'expected values for:', fieldName);
                } else {
                    console.log('No expected values found for:', fieldName);
                }

                // Update cache
                self.expectedValuesCache[fieldName] = {
                    params: currentParams,
                    data: records
                };
                console.log('Cached expected values for', fieldName, ':', records); // Log the fetched/cached records
                resolve(records);

            } catch (e) {
                console.error("Error fetching GRIDDATA for", fieldName, ":", e);
                // Cache error state (empty data) to prevent repeated failed requests for the same params
                self.expectedValuesCache[fieldName] = {
                    params: currentParams,
                    data: []
                };
                resolve(null); // Indicate error
            }
        });
    },

    /**
     * Retrieves cached expected values for a field.
     * @param {String} fieldName The name of the field.
     * @returns {Array|null} The cached data array or null if not found/cached.
     */
    getExpectedValuesForField: function (fieldName) {
        // Prioritize hardcoded values
        if (this.hardcodedExpectedValues.hasOwnProperty(fieldName)) {
            console.log('Using hardcoded expected values for:', fieldName);
            return this.hardcodedExpectedValues[fieldName];
        }

        var cacheEntry = this.expectedValuesCache[fieldName];
        // We only return the data if it's cached for the *current* form state,
        // but for sending to the API, we just need the latest fetched list.
        // The fetchAndCacheExpectedValues function should be called before this
        // if fresh data based on current context is needed.
        return cacheEntry ? cacheEntry.data : null;
    },

    /**
     * Compares two parameter objects for equality.
     * @param {Object} params1 First parameter object.
     * @param {Object} params2 Second parameter object.
     * @returns {Boolean} True if objects have the same keys and values.
     */
    areParamsEqual: function (params1, params2) {
        if (!params1 || !params2) return false;
        var keys1 = Object.keys(params1);
        var keys2 = Object.keys(params2);
        if (keys1.length !== keys2.length) return false;
        for (var i = 0; i < keys1.length; i++) {
            var key = keys1[i];
            if (params1[key] !== params2[key]) {
                return false;
            }
        }
        return true;
    },

    /**
    * Defines the GRIDDATA parameters for each field that needs expected values.
    * @param {String} fieldName The name of the field.
    * @returns {Object|null} Configuration object or null.
    */
    getGridConfigForField: function (fieldName) {
        // Maps field names to their GRIDDATA configuration
        const gridConfigs = {
            'category': {
                gridName: 'LVCAT',
                paramFields: ['organization', 'class', 'classorganization'],
                paramMap: { // Maps form field name to LOV alias name
                    'organization': 'control.org',
                    'class': 'parameter.class',
                    'classorganization': 'parameter.classorg'
                },
                staticParamsMap: { // Static LOV parameters
                    'parameter.onlymatchclass': ''
                },
                paramTypes: {}, // All default to 'text'
                valueField: 'category' // Changed from 'code' to 'category' based on user input
            },
            'class': {
                gridName: 'LVCLAS',
                paramFields: ['organization'],
                paramMap: {
                    'organization': 'control.org'
                },
                staticParamsMap: {
                    'parameter.rentity': 'OBJ'
                },
                paramTypes: {},
                valueField: 'classorganization'
            },
            'department': {
                gridName: 'LVMRCS',
                paramFields: ['organization'],
                paramMap: {
                    'organization': 'control.org'
                },
                staticParamsMap: {},
                paramTypes: {},
                valueField: 'department'
            },
            'loanedtodepartment': {
                gridName: 'LVLOANDEPT',
                paramFields: ['organization'],
                paramMap: {
                    'organization': 'control.org'
                },
                staticParamsMap: {},
                paramTypes: {},
                valueField: 'department'
            },
            'meterunit': {
                gridName: 'LVUOMS',
                paramFields: ['organization'],
                paramMap: {
                    'organization': 'control.org'
                },
                staticParamsMap: {},
                paramTypes: {},
                valueField: 'uomcode'
            },
            'assignedto': {
                gridName: 'LVPERS',
                paramFields: ['organization'],
                paramMap: {
                    'organization': 'control.org'
                },
                staticParamsMap: {
                    'parameter.per_type': ''
                },
                paramTypes: {},
                valueField: 'personcode'
            },
            'syslevel': {
                gridName: 'LVSYSLEVELCLSCNTXT',
                paramFields: ['class', 'classorganization'],
                paramMap: {
                    'class': 'parameter.class',
                    'classorganization': 'parameter.classorg'
                },
                staticParamsMap: {
                    'param.rentity': 'OBJ'
                },
                paramTypes: {},
                valueField: 'code'
            },
            'asslevel': {
                gridName: 'LVASSLEVELCLSCNTXT',
                paramFields: ['syslevel', 'class', 'classorganization'],
                paramMap: {
                    'syslevel': 'param.syslevel',
                    'class': 'parameter.class',
                    'classorganization': 'parameter.classorg'
                },
                staticParamsMap: {
                    'param.rentity': 'OBJ'
                },
                paramTypes: {},
                valueField: 'code'
            },
            'complevel': {
                gridName: 'LVCOMPLEVELCLSCNTXT',
                paramFields: ['syslevel', 'asslevel', 'class', 'classorganization'],
                paramMap: {
                    'syslevel': 'param.syslevel',
                    'asslevel': 'param.asslevel',
                    'class': 'parameter.class',
                    'classorganization': 'parameter.classorg'
                },
                staticParamsMap: {
                    'param.rentity': 'OBJ'
                },
                paramTypes: {},
                valueField: 'code'
            },
            'costcode': {
                gridName: 'LVOBJCOST',
                paramFields: ['organization', 'flcust', 'fleetcustorg'],
                paramMap: {
                    'organization': 'control.org',
                    'flcust': 'param.flcust',
                    'fleetcustorg': 'param.fleetcustorg'
                },
                staticParamsMap: {},
                paramTypes: {},
                valueField: 'costcode'
            },
            'profile': {
                gridName: 'LVPROFILE',
                paramFields: ['organization'],
                paramMap: {
                    'organization': 'control.org'
                },
                staticParamsMap: {},
                paramTypes: {},
                valueField: 'profile'
            }
        };
        return gridConfigs[fieldName] || null;
    },


    // --- Event Handlers and Selectors ---

    getSelectors: function () {
        var self = this;
        var selectors = {
            // Target the form panel within the 'HDR' tab
            '[extensibleFramework] [tabName=HDR][isTabView=true]': {
                afterrender: function (formPanel) {
                    console.log('EAM.custom.EquipmentEntryPredictions: Form Panel rendered.');
                    var form = formPanel.getForm();

                    // Attach focus/blur handlers for predict buttons
                    form.getFields().each(function (field) {
                        // --- START TEMPORARY DIAGNOSTIC LOG ---
                        if (field && field.getName) { // Ensure field and getName method exist
                            console.log('Initial check in getSelectors for field:', field.getName(), 'Is readOnly:', field.readOnly, 'XType:', field.xtype);
                        }
                        // --- END TEMPORARY DIAGNOSTIC LOG ---

                        // Don't add handlers to equipmentno or read-only fields etc.
                        if (field.getName() !== 'equipmentno' && field.getName() !== 'equipmentdesc' && !field.readOnly && field.xtype !== 'hiddenfield') {
                            // The readOnly check prevents adding prediction functionality to fields that cannot be edited
                            // Read-only fields are display-only and don't accept user input, so predictions wouldn't be applicable
                            // Delay adding focus/blur to avoid conflicts with framework/other scripts
                            Ext.defer(function () {
                                if (!field.destroyed) { // Check if field still exists
                                    field.on('focus', self.handleFieldFocus, self, { buffer: 50 }); // Buffer to prevent rapid firing
                                    field.on('blur', self.handleFieldBlur, self, { buffer: 100 });
                                    console.log('Attached focus/blur handlers to:', field.getName());
                                }
                            }, 100); // Small delay
                        }
                    });

                    // Add Section Header Buttons
                    console.log('--- Discovering components for section buttons ---');
                    // Use ComponentQuery for potentially more reliable targeting of panels/fieldsets
                    var sections = formPanel.query('panel[collapsible], fieldset[collapsible]');
                    console.log('Found potential sections:', sections.length);
                    Ext.each(sections, function (section) {
                        if (section.header && section.title && !section.isFormField) { // Ensure it's not a form field itself
                            console.log('-> Processing potential section:', section.title);
                            var buttonText = 'Suggest All'; // Changed button text
                            self.addSectionHeaderButton(section, buttonText);
                        } else {
                            console.log('-> Skipping component (not a collapsible panel/fieldset with header/title):', section.id, section.xtype, section.title);
                        }
                    });
                    console.log('--- End of section button discovery ---');
                }
            }
        };

        // Dynamically add selectors for fields needing expected value fetching
        var fieldsToFetch = [
            'category', 'class', 'department', 'loanedtodepartment', 'meterunit',
            'assignedto', 'syslevel', 'asslevel', 'complevel', 'costcode', 'profile'
            // Add other field names here
        ];

        Ext.each(fieldsToFetch, function (fieldName) {
            var selector = '[extensibleFramework] [tabName=HDR][isTabView=true] [name=' + fieldName + ']';
            // Use 'beforetriggerclick' for LOV fields, 'customonblur' might be needed for others
            // Assuming most are LOVs for simplicity here
            var eventToUse = 'beforetriggerclick'; // Or determine based on field xtype if possible

            selectors[selector] = selectors[selector] || {}; // Ensure object exists
            selectors[selector][eventToUse] = function (fieldComponent) {
                var panel = EAM.Utils.getCurrentTab().getFormPanel();
                // Fetch data (don't force update unless necessary)
                self.fetchAndCacheExpectedValues(fieldName, panel, false);
                // Allow the default trigger action to proceed (return true or nothing)
            };
            // Add customonblur as well to catch cases where LOV isn't opened
            selectors[selector]['customonblur'] = function (fieldComponent) {
                var panel = EAM.Utils.getCurrentTab().getFormPanel();
                self.fetchAndCacheExpectedValues(fieldName, panel, false);
            };
        });

        return selectors;
    },

    handleFieldFocus: function (focusedField) {
        var self = this;
        var fieldName = focusedField.getName();
        var fieldId = focusedField.getId();

        // Detailed log for any focused field
        console.log('Field Focused:', {
            name: fieldName,
            id: fieldId,
            xtype: focusedField.xtype,
            isFormField: focusedField.isFormField,
            isReadOnly: focusedField.readOnly,
            isHidden: focusedField.hidden,
            isDisabled: focusedField.isDisabled(),
            value: focusedField.getValue(),
            rawLabel: focusedField.fieldLabel,
            itemId: focusedField.itemId
        });

        // Basic checks - Don't add button for equipmentno, equipmentdesc, or if button already exists or field is readOnly
        if (fieldName === 'equipmentno' || fieldName === 'equipmentdesc' || this.fieldButtons[fieldId] || focusedField.readOnly) {
            return;
        }

        console.log('Focus on field:', fieldName, 'ID:', fieldId);

        // Defer button creation slightly
        Ext.defer(function () {
            // Double-check if field still exists and is focused (or contains focus)
            if (focusedField.destroyed || !focusedField.hasFocus) {
                console.log('Field focus lost or destroyed before button creation for ID:', fieldId);
                return;
            }

            var componentEl = focusedField.getEl(); // Main component element (e.g., the x-form-item div)
            if (!componentEl) {
                console.warn('Could not find element for field:', fieldName);
                return;
            }

            // Create the button
            var predictButton = Ext.create('Ext.button.Button', {
                // Use an icon for less intrusion? cls: 'x-fa fa-magic', text: null,
                text: 'Suggest',
                tooltip: 'Get suggestion for ' + (focusedField.fieldLabel || fieldName),
                renderTo: componentEl.dom, // Render adjacent to field components
                style: {
                    marginLeft: '5px',
                    verticalAlign: 'middle', // Adjust alignment as needed
                    display: 'inline-block'
                },
                handler: function () {
                    // Pass the field *instance* at the time of creation
                    self.onPredictButtonClick(focusedField);
                }
            });

            // Store button reference
            this.fieldButtons[fieldId] = predictButton;
            console.log('Predict button created for field:', fieldName, 'ID:', fieldId);

        }, 50, this); // Small delay
    },

    handleFieldBlur: function (blurredField) {
        var fieldId = blurredField.getId();
        var button = this.fieldButtons[fieldId];

        console.log('Blur on field:', blurredField.getName(), 'ID:', fieldId);

        if (button) {
            // Defer destruction to handle rapid focus/blur or focus moving to the button itself
            Ext.defer(function () {
                // Check if focus has moved *away* from the field *and* the button
                if (!button || button.destroyed) {
                    delete this.fieldButtons[fieldId]; // Cleanup map if button already gone
                    return;
                }

                var activeComponent = Ext.ComponentManager.getActiveComponent();
                var keepButton = false; // Assume we will destroy unless a condition to keep is met

                if (activeComponent) {
                    if (activeComponent.id === button.id) {
                        // Focus is on the predict button itself
                        keepButton = true;
                        console.log('Predict button for field', blurredField.getName(), '(ID:', fieldId, ') has focus. Not destroying.');
                    } else if (activeComponent.id === blurredField.id) {
                        // Focus is still on the field associated with this button
                        keepButton = true;
                        console.log('Field', blurredField.getName(), '(ID:', fieldId, ') has focus. Not destroying its predict button.');
                    }
                }

                if (!keepButton) {
                    console.log('Destroying predict button for field:', blurredField.getName(), '(ID:', fieldId, '). Active component:', activeComponent ? activeComponent.id : 'None');
                    button.destroy();
                    delete this.fieldButtons[fieldId];
                } else {
                    console.log('Predict button for field:', blurredField.getName(), '(ID:', fieldId, ') not destroyed. Active component:', activeComponent ? activeComponent.id : 'None');
                }
            }, 20, this); // Reduced delay from 60ms to 20ms for quicker disappearance
        }
    },

    onPredictButtonClick: function (targetFieldInstance) {
        // Important: Use the passed instance, not just the name,
        // as the field might be destroyed/recreated.
        if (!targetFieldInstance || targetFieldInstance.destroyed) {
            console.warn('Target field instance is destroyed. Cannot predict.');
            Ext.toast({ html: 'Cannot predict: Field not available.', title: 'Warning', width: 300, align: 't' });
            return;
        }

        var self = this;
        var fieldName = targetFieldInstance.getName();
        var fieldLabel = targetFieldInstance.fieldLabel || fieldName;
        console.log('Predict button clicked for field:', fieldName);

        // 1. Get the form panel and asset description
        var formPanel = EAM.Utils.getCurrentTab().getFormPanel();
        if (!formPanel) {
            console.error("Could not find the form panel.");
            Ext.toast({ html: 'Error: Could not find form.', title: 'Error', width: 300, align: 't' });
            return;
        }
        var form = formPanel.getForm();
        var assetDescValue = formPanel.getFldValue('equipmentdesc'); // New: equipment description

        if (!assetDescValue || String(assetDescValue).trim() === '') { // New check
            console.warn('Equipment Description (equipmentdesc) is not set.');
            Ext.toast({ html: 'Please enter the Equipment Description first!', title: 'Warning', width: 300, align: 't' });
            return;
        }
        assetDescValue = String(assetDescValue).trim(); // New trim

        // 2. Get other accepted field values
        var acceptedValues = {};
        form.getFields().each(function (field) {
            // Ensure field exists, has a name, is not the target, not equipmentno, not equipmentdesc, and has a value
            if (field && !field.destroyed && field.getName() &&
                field.getName() !== fieldName &&
                field.getName() !== 'equipmentno' && field.getName() !== 'equipmentdesc' &&
                field.getValue()) {
                acceptedValues[field.getName()] = field.getValue();
            }
        });

        // 3. Get expected values for the target field (fetch if needed, though blur/trigger should handle it)
        // We call fetch here again (force=false) just to be sure cache is checked against current params
        this.fetchAndCacheExpectedValues(fieldName, formPanel, false).then(function (expectedValuesFromAPI) {
            // expectedValuesFromAPI is now the array from cache/fetch, or null

            console.log('Calling API for field:', fieldName, 'with asset description:', assetDescValue);
            console.log('Accepted values:', acceptedValues);

            // Get the final list, prioritizing hardcoded values.
            // expectedValuesFromAPI is the result from fetchAndCacheExpectedValues promise
            var finalExpectedValues = self.hardcodedExpectedValues[fieldName] || expectedValuesFromAPI || [];
            console.log('Final Expected values for API (single predict):', finalExpectedValues);

                                // 4. Call the fetch API
                    const BASE_URL = 'https://54.219.76.120:8001'; // Production URL (Nginx proxy on port 8001)
                    const API_URL = `${BASE_URL}/api/equipment-entries/generate/${encodeURIComponent(assetDescValue)}/`; // Use assetDescValue

            const payload = {
                attribute: fieldName,
                accepted_values: acceptedValues,
                // Send the array of expected values, or an empty list if null/undefined
                expected_values: finalExpectedValues
            };

            console.log('API Request Payload:', payload);

            fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify(payload)
            })
                .then(async (response) => {
                    const text = await response.text();
                    console.log('API Raw Response:', text);

                    if (!response.ok) {
                        console.error('API Error Response:', response.status, text);
                        Ext.toast({ html: `Error predicting ${fieldLabel}: ${response.statusText}`, title: 'Error', width: 300, align: 't' });
                        return;
                    }

                    try {
                        const data = JSON.parse(text);
                        console.log('API Parsed Response:', data);

                        if (data.llm_response) {
                            // Get fresh form panel reference inside callback
                            var currentFormPanel = EAM.Utils.getCurrentTab().getFormPanel();
                            if (currentFormPanel && !targetFieldInstance.destroyed) {
                                console.log(`Attempting to set value for ${fieldName} (xtype: ${targetFieldInstance.xtype}). LLM Response:`, data.llm_response);
                                var fieldToUpdate = currentFormPanel.getForm().findField(fieldName);
                                if (fieldToUpdate && !fieldToUpdate.destroyed) {
                                    console.log(`Attempting to set value for ${fieldName} (xtype: ${fieldToUpdate.xtype}). LLM Response:`, data.llm_response);
                                    var valueToSet = data.llm_response;

                                    if (fieldToUpdate.isXType('combobox') || fieldToUpdate.isXType('uxcombobox')) {
                                        var store = fieldToUpdate.getStore();
                                        var displayTpl = fieldToUpdate.displayTpl;
                                        var displayField = fieldToUpdate.displayField || 'description'; // Common EAM default or standard ExtJS
                                        var valueField = fieldToUpdate.valueField || 'code'; // Common EAM default or standard ExtJS
                                        console.log(`  Combo box detected. Store: ${store ? store.storeId || 'inline' : 'No Store! '}, DisplayField: ${displayField}, ValueField: ${valueField}`);

                                        if (store) {
                                            var recordIndex = store.findExact(displayField, data.llm_response);
                                            if (recordIndex !== -1) {
                                                var record = store.getAt(recordIndex);
                                                valueToSet = record.get(valueField);
                                                console.log(`  Found record in store for display value '${data.llm_response}'. Using actual value: '${valueToSet}' (from ${valueField}).`);
                                            } else {
                                                console.warn(`  Could not find record in store for display value '${data.llm_response}' using displayField '${displayField}'. Will attempt to set raw LLM response.`);
                                                // Fallback: try to find by valueField if llm_response happens to be the actual code
                                                var recordByValueIndex = store.findExact(valueField, data.llm_response);
                                                if (recordByValueIndex !== -1) {
                                                    var recordByValue = store.getAt(recordByValueIndex);
                                                    valueToSet = recordByValue.get(valueField); // ensure it's the actual value from the record
                                                    console.log(`  Fallback: Found record by valueField '${valueField}' with '${data.llm_response}'. Setting actual value: '${valueToSet}'.`);
                                                } else {
                                                    console.warn(`  Fallback: Could not find record by valueField '${valueField}' either. Raw LLM response will be used.`);
                                                }
                                            }
                                        } else {
                                            console.warn('  Combo box has no store. Will attempt to set raw LLM response.');
                                        }
                                    }

                                    // Handle Date fields: Convert string to Date object
                                    if (fieldToUpdate.isXType('datefield') || fieldToUpdate.isXType('xdatefield') || fieldToUpdate.isXType('uxdate')) {
                                        console.log(`  Date field detected (xtype: ${fieldToUpdate.xtype}). Original LLM response string:`, data.llm_response);
                                        var dateObject = new Date(data.llm_response); // data.llm_response is the original string here
                                        if (!isNaN(dateObject.getTime())) {
                                            valueToSet = dateObject;
                                            console.log(`  Parsed to Date object:`, dateObject, `Using this for setValue.`);
                                        } else {
                                            console.warn(`  Could not parse date string '${data.llm_response}' into a valid Date object. Will attempt to set raw string/original valueToSet:`, valueToSet);
                                        }
                                    }

                                    // Handle Checkbox fields: Convert string "True"/"False" to boolean
                                    if (fieldToUpdate.isXType('checkbox') || fieldToUpdate.isXType('checkboxfield')) {
                                        console.log(`  Checkbox field detected (xtype: ${fieldToUpdate.xtype}). Original LLM response string:`, data.llm_response);
                                        if (typeof data.llm_response === 'string') {
                                            if (data.llm_response.toLowerCase() === 'true') {
                                                valueToSet = true;
                                                console.log(`  Parsed to boolean: true`);
                                            } else if (data.llm_response.toLowerCase() === 'false') {
                                                valueToSet = false;
                                                console.log(`  Parsed to boolean: false`);
                                            } else {
                                                console.warn(`  Unrecognized string for boolean: '${data.llm_response}'. Defaulting to false or current valueToSet:`, valueToSet);
                                            }
                                        } else if (typeof data.llm_response === 'boolean') {
                                            valueToSet = data.llm_response; // Already a boolean
                                            console.log(`  LLM response is already boolean:`, valueToSet);
                                        }
                                    }

                                    fieldToUpdate.setValue(valueToSet);
                                    console.log(`After setValue for ${fieldName} - getValue():`, fieldToUpdate.getValue(), ", getRawValue():", fieldToUpdate.getRawValue());

                                    if (fieldToUpdate.validate) {
                                        fieldToUpdate.validate();
                                    }
                                    console.log(`Successfully updated ${fieldName}`);
                                    Ext.toast({ html: `Prediction applied to ${fieldLabel}`, title: 'Success', width: 300, align: 't' });
                                } else {
                                    console.warn(`Form panel or target field (${fieldName}) not available after prediction.`);
                                    Ext.toast({ html: `Could not apply prediction to ${fieldLabel}.`, title: 'Warning', width: 300, align: 't' });
                                }
                            } else {
                                console.warn(`Form panel or target field (${fieldName}) not available after prediction.`);
                                Ext.toast({ html: `Could not apply prediction to ${fieldLabel}.`, title: 'Warning', width: 300, align: 't' });
                            }
                        } else {
                            console.log(`No prediction returned for ${fieldName}.`);
                            Ext.toast({ html: `No prediction available for ${fieldLabel}`, title: 'Info', width: 300, align: 't' });
                        }
                    } catch (e) {
                        console.error('JSON Parse Error:', e, 'Raw text:', text);
                        Ext.toast({ html: 'Error processing prediction response.', title: 'Error', width: 300, align: 't' });
                    }
                })
                .catch(error => {
                    console.error('API Request Failed:', error);
                    Ext.toast({ html: 'Network error or API unreachable.', title: 'Error', width: 300, align: 't' });
                })
                .finally(() => { // Ensure button is destroyed regardless of success/failure of API
                    if (targetFieldInstance && !targetFieldInstance.destroyed) {
                        var fieldId = targetFieldInstance.getId();
                        var buttonToDestroy = self.fieldButtons[fieldId];
                        if (buttonToDestroy && !buttonToDestroy.destroyed) {
                            console.log('Destroying predict button after action for field ID:', fieldId);
                            buttonToDestroy.destroy();
                            delete self.fieldButtons[fieldId];
                        }
                    }
                });
        }); // End of .then for fetchAndCacheExpectedValues
    },

    /**
     * Adds a 'Predict All' button to a section's header.
     * @param {Ext.Component} section The section component (panel, fieldset).
     * @param {String} buttonText Text for the button.
     */
    addSectionHeaderButton: function (section, buttonText) {
        var self = this;
        if (!section || !section.header || !section.header.rendered || !section.header.el) {
            console.warn('Cannot add button: Section or header not ready for:', section ? section.title : 'Unknown Section');
            // Optionally, retry on afterrender if header wasn't ready
            if (section && section.header && !section.header.rendered) {
                section.header.on('afterrender', function () {
                    console.log('Retrying addSectionHeaderButton after render for:', section.title);
                    self.addSectionHeaderButton(section, buttonText);
                }, self, { single: true });
            }
            return;
        }

        var header = section.header;
        var sectionTitle = section.title || 'Section';
        var checkCls = 'custom-bulk-predict-btn'; // Class to prevent duplicates

        // Check if button already exists
        if (header.down('button[cls~=' + checkCls + ']')) {
            console.log('Bulk predict button already exists for:', sectionTitle);
            return;
        }

        var titleCmp = header.down('title');
        if (!titleCmp) {
            console.warn('Could not find title component in header for:', sectionTitle);
            return;
        }

        var titleIndex = header.items.indexOf(titleCmp);
        if (titleIndex === -1) {
            console.warn('Could not find title component index for:', sectionTitle);
            return;
        }

        // Create and insert the button
        var button = Ext.create('Ext.button.Button', {
            text: buttonText,
            cls: checkCls, // Add the check class
            tooltip: 'Predict values for all fields in the ' + sectionTitle + ' section',
            style: { marginLeft: '10px', verticalAlign: 'middle' },
            handler: function (buttonCmp, event) {
                event.stopEvent(); // Prevent header click (collapse/expand)

                debugger;
                console.log('Bulk predict button clicked for section:', sectionTitle);
                var formPanel = EAM.Utils.getCurrentTab().getFormPanel();
                if (!formPanel) {
                    console.error("Could not find form panel for bulk prediction.");
                    Ext.toast({ html: 'Error: Could not find form.', title: 'Error', width: 300, align: 't' });
                    return;
                }
                var form = formPanel.getForm();

                // 1. Get Asset Description (instead of Asset Name/Number)
                var assetDescValueBulk = formPanel.getFldValue('equipmentdesc'); // New

                if (!assetDescValueBulk || String(assetDescValueBulk).trim() === '') { // New check
                    Ext.toast({ html: 'Please enter the Equipment Description first!', title: 'Warning', width: 300, align: 't' });
                    return;
                }
                assetDescValueBulk = String(assetDescValueBulk).trim(); // New trim

                // 2. Get field names within this section
                var sectionFields = section.query('field'); // Query fields within the section
                var attributesToPredict = [];
                var sectionFieldNames = new Set();
                var fetchPromises = []; // For fetching expected values

                Ext.each(sectionFields, function (field) {
                    if (field && !field.destroyed && field.getName() &&
                        field.getName() !== 'equipmentno' && field.getName() !== 'equipmentdesc' &&
                        !field.readOnly) {
                        var fieldName = field.getName();
                        attributesToPredict.push(fieldName);
                        sectionFieldNames.add(fieldName);
                        // Trigger fetch for expected values (force=false, rely on prior fetch or cache)
                        fetchPromises.push(self.fetchAndCacheExpectedValues(fieldName, formPanel, false));
                    }
                });

                if (attributesToPredict.length === 0) {
                    Ext.toast({ html: 'No eligible fields to predict in this section.', title: 'Info', width: 300, align: 't' });
                    return;
                }
                console.log('Fields to predict in section:', attributesToPredict);

                // Wait for all expected value fetches to complete (or use cached data)
                Promise.all(fetchPromises).then(function () {
                    // PRESERVE VALUES START
                    var fieldsToPreserve = ['equipmentdesc', 'department', 'equipmentvalue'];
                    var preservedValues = {};
                    // Ensure formPanel is the correct one related to the current section button
                    var formForPreservation = EAM.Utils.getCurrentTab().getFormPanel().getForm();

                    Ext.each(fieldsToPreserve, function (fieldName) {
                        var field = formForPreservation.findField(fieldName);
                        if (field && !field.destroyed) {
                            preservedValues[fieldName] = field.getValue();
                            console.log('Preserving value for', fieldName, ':', preservedValues[fieldName]);
                        } else {
                            console.warn('Could not find field to preserve:', fieldName);
                        }
                    });
                    // PRESERVE VALUES END

                    // 3. Get accepted values from fields *outside* this section
                    var acceptedValues = {};
                    form.getFields().each(function (field) {
                        if (field && !field.destroyed && field.getName() &&
                            field.getName() !== 'equipmentno' && field.getName() !== 'equipmentdesc' &&
                            !sectionFieldNames.has(field.getName()) &&
                            field.getValue()) {
                            acceptedValues[field.getName()] = field.getValue();
                        }
                    });
                    console.log('Accepted values from other sections:', acceptedValues);

                    // 4. Prepare expected values map
                    var attributesExpectedValuesMap = {};
                    Ext.each(attributesToPredict, function (fieldName) {
                        attributesExpectedValuesMap[fieldName] = self.getExpectedValuesForField(fieldName) || [];
                    });
                    console.log('Expected values map for bulk request:', attributesExpectedValuesMap);

                    // 5. Call the Bulk Prediction API
                    const BASE_URL = 'https://54.219.76.120:8001'; // Production URL (Nginx proxy on port 8001)
                    const API_URL = `${BASE_URL}/api/equipment-entries/generate-bulk/${encodeURIComponent(assetDescValueBulk)}/`; // Use assetDescValueBulk

                    const payload = {
                        attributes: attributesToPredict,
                        accepted_values: acceptedValues,
                        attributes_expected_values: attributesExpectedValuesMap
                    };

                    console.log('Bulk API Request Payload:', payload);
                    Ext.toast({
                        html: `Requesting bulk predictions for ${sectionTitle}...`,
                        title: 'Info',
                        width: 300,
                        align: 't'
                    });


                    fetch(API_URL, {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                            'ngrok-skip-browser-warning': 'true'
                        },
                        body: JSON.stringify(payload)
                    })
                        .then(async (response) => {
                            const text = await response.text();
                            console.log('Bulk API Raw Response:', text);

                            if (!response.ok) {
                                console.error('Bulk API Error Response:', response.status, text);
                                Ext.toast({ html: `Error fetching bulk predictions: ${response.statusText}`, title: 'Error', width: 300, align: 't' });
                                return;
                            }

                            try {
                                const data = JSON.parse(text);
                                console.log('Bulk API Parsed Response:', data);
                                // Log all keys from the predictions object
                                if (data && data.predictions) {
                                    console.log('Bulk API Prediction Keys Received:', Object.keys(data.predictions));
                                }

                                // 6. Update fields with predictions
                                if (data.predictions) {
                                    let updatedCount = 0;
                                    let errorCount = 0;
                                    // Get fresh form panel reference
                                    var currentFormPanel = EAM.Utils.getCurrentTab().getFormPanel();
                                    if (currentFormPanel) {
                                        Ext.Object.each(data.predictions, function (fieldName, value) {
                                            var normalizedFieldName = String(fieldName).toLowerCase().trim();
                                            debugger;
                                            console.log('Normalized field name:', normalizedFieldName);
                                            // Explicitly skip equipmentno, equipmentdesc, and equipmentvalue from being updated by bulk predict (case-insensitive)
                                            if (normalizedFieldName === 'equipmentno' || normalizedFieldName === 'equipmentdesc' || normalizedFieldName === 'equipmentvalue') {
                                                console.log(`Bulk predict: Skipping update for protected field: ${fieldName} (normalized: ${normalizedFieldName})`);
                                                return; // Equivalent to 'continue' in a for loop
                                            }

                                            if (value !== null && value !== undefined) { // Only update if a prediction was returned
                                                try {
                                                    // Find the field within the *current* form panel
                                                    var fieldToUpdate = currentFormPanel.getForm().findField(fieldName);
                                                    if (fieldToUpdate && !fieldToUpdate.destroyed) {
                                                        console.log(`Bulk update for ${fieldName} (xtype: ${fieldToUpdate.xtype}). LLM Response:`, value);
                                                        var valueToSetBulk = value;

                                                        if (fieldToUpdate.isXType('combobox') || fieldToUpdate.isXType('uxcombobox')) {
                                                            var storeBulk = fieldToUpdate.getStore();
                                                            var displayFieldBulk = fieldToUpdate.displayField || 'description';
                                                            var valueFieldBulk = fieldToUpdate.valueField || 'code';
                                                            console.log(`  Bulk Combo detected. Store: ${storeBulk ? storeBulk.storeId || 'inline' : 'No Store! '}, DisplayField: ${displayFieldBulk}, ValueField: ${valueFieldBulk}`);
                                                            if (storeBulk) {
                                                                var recordIndexBulk = storeBulk.findExact(displayFieldBulk, value);
                                                                if (recordIndexBulk !== -1) {
                                                                    valueToSetBulk = storeBulk.getAt(recordIndexBulk).get(valueFieldBulk);
                                                                    console.log(`  Bulk: Found record for '${value}'. Using actual value: '${valueToSetBulk}'.`);
                                                                } else {
                                                                    console.warn(`  Bulk: Could not find record for display value '${value}' using displayField '${displayFieldBulk}'. Will attempt to set raw LLM response.`);
                                                                    var recordByValueIndexBulk = storeBulk.findExact(valueFieldBulk, value);
                                                                    if (recordByValueIndexBulk !== -1) {
                                                                        valueToSetBulk = storeBulk.getAt(recordByValueIndexBulk).get(valueFieldBulk);
                                                                        console.log(`  Bulk Fallback: Found by valueField '${valueFieldBulk}'. Setting: '${valueToSetBulk}'.`);
                                                                    } else {
                                                                        console.warn(`  Bulk Fallback: Could not find by valueField '${valueFieldBulk}' either.`);
                                                                    }
                                                                }
                                                            }
                                                        }

                                                        // Handle Date fields for bulk update
                                                        if (fieldToUpdate.isXType('datefield') || fieldToUpdate.isXType('xdatefield') || fieldToUpdate.isXType('uxdate')) {
                                                            console.log(`  Bulk Date field detected (xtype: ${fieldToUpdate.xtype}). Original LLM response string:`, value);
                                                            var dateObjectBulk = new Date(value);
                                                            if (!isNaN(dateObjectBulk.getTime())) {
                                                                valueToSetBulk = dateObjectBulk;
                                                                console.log(`  Bulk Parsed to Date object:`, dateObjectBulk, `Using this for setValue.`);
                                                            } else {
                                                                console.warn(`  Bulk Could not parse date string '${value}' into a valid Date object. Will attempt to set raw string/original valueToSetBulk:`, valueToSetBulk);
                                                            }
                                                        }

                                                        // Handle Checkbox fields for bulk update: Convert string "True"/"False" to boolean
                                                        if (fieldToUpdate.isXType('checkbox') || fieldToUpdate.isXType('checkboxfield')) {
                                                            console.log(`  Bulk Checkbox field detected (xtype: ${fieldToUpdate.xtype}). Original LLM response string:`, value);
                                                            if (typeof value === 'string') {
                                                                if (value.toLowerCase() === 'true') {
                                                                    valueToSetBulk = true;
                                                                    console.log(`  Bulk Parsed to boolean: true`);
                                                                } else if (value.toLowerCase() === 'false') {
                                                                    valueToSetBulk = false;
                                                                    console.log(`  Bulk Parsed to boolean: false`);
                                                                } else {
                                                                    console.warn(`  Bulk Unrecognized string for boolean: '${value}'. Defaulting to false or current valueToSetBulk:`, valueToSetBulk);
                                                                }
                                                            } else if (typeof value === 'boolean') {
                                                                valueToSetBulk = value; // Already a boolean
                                                                console.log(`  Bulk LLM response is already boolean:`, valueToSetBulk);
                                                            }
                                                        }

                                                        fieldToUpdate.setValue(valueToSetBulk);
                                                        console.log(`After setValue (bulk) for ${fieldName} - getValue():`, fieldToUpdate.getValue(), ", getRawValue():", fieldToUpdate.getRawValue());

                                                        if (fieldToUpdate.validate) {
                                                            fieldToUpdate.validate();
                                                        }
                                                        console.log(`Bulk update successful for ${fieldName}`);
                                                        updatedCount++;
                                                    } else {
                                                        console.warn(`Field ${fieldName} not found or destroyed during bulk update.`);
                                                        errorCount++;
                                                    }
                                                } catch (fieldError) {
                                                    console.error(`Error bulk updating field ${fieldName}:`, fieldError);
                                                    errorCount++;
                                                }
                                            } else {
                                                console.log(`No prediction returned or invalid attribute for ${fieldName} in bulk response.`);
                                            }
                                        });

                                        // RESTORE PRESERVED VALUES START
                                        console.log('Attempting to restore values for fields potentially affected by side-effects...');
                                        var formForRestoration = currentFormPanel.getForm(); // currentFormPanel is from the API response scope
                                        Ext.each(fieldsToPreserve, function (fieldName) {
                                            var originalValue = preservedValues[fieldName];
                                            // Ensure originalValue was actually captured; if not, we can't restore.
                                            if (originalValue === undefined && preservedValues.hasOwnProperty(fieldName) === false) {
                                                console.warn(`Original value for ${fieldName} was not preserved. Skipping restoration.`);
                                                return; // Continue to next field
                                            }

                                            var fieldToRestore = formForRestoration.findField(fieldName);
                                            if (fieldToRestore && !fieldToRestore.destroyed) {
                                                var currentValue = fieldToRestore.getValue();
                                                // Only restore if the value actually changed.
                                                if (currentValue !== originalValue) {
                                                    console.log(`Restoring ${fieldName} from "${currentValue}" back to originally preserved "${originalValue}".`);
                                                    fieldToRestore.setValue(originalValue);
                                                    if (fieldToRestore.validate) {
                                                        fieldToRestore.validate();
                                                    }
                                                } else {
                                                    console.log(`${fieldName} current value "${currentValue}" matches preserved value. No restoration needed.`);
                                                }
                                            } else {
                                                console.warn(`Field ${fieldName} for restoration not found or destroyed.`);
                                            }
                                        });
                                        // RESTORE PRESERVED VALUES END

                                        let message = `Applied ${updatedCount} bulk prediction(s) to ${sectionTitle}.`;
                                        if (errorCount > 0) message += ` ${errorCount} error(s) occurred.`;
                                        Ext.toast({ html: message, title: (errorCount > 0) ? 'Warning' : 'Success', width: 300, align: 't' });

                                    } else {
                                        console.error("Could not find form panel to apply bulk updates.");
                                        Ext.toast({ html: 'Error: Could not find form for bulk update.', title: 'Error', width: 300, align: 't' });
                                    }
                                } else {
                                    console.log('No predictions object returned in bulk response.');
                                    Ext.toast({ html: 'No bulk predictions were returned.', title: 'Warning', width: 300, align: 't' });
                                }
                            } catch (e) {
                                console.error('Bulk JSON Parse Error:', e, 'Raw text:', text);
                                Ext.toast({ html: 'Error processing bulk prediction response.', title: 'Error', width: 300, align: 't' });
                            }
                        })
                        .catch(error => {
                            console.error('Bulk API Request Failed:', error);
                            Ext.toast({ html: 'Network error or bulk API unreachable.', title: 'Error', width: 300, align: 't' });
                        });

                }); // End Promise.all().then()
            } // End handler
        }); // End Ext.create Button

        // Insert button after the title component
        header.insert(titleIndex + 1, button);
        console.log('Bulk predict button inserted into header for:', sectionTitle);
    },

    // --- Cleanup ---
    destroy: function () {
        console.log('Destroying EAM.custom.EquipmentEntryPredictions instance.');
        // Clean up any remaining buttons
        Ext.Object.each(this.fieldButtons, function (fieldId, button) {
            if (button && !button.destroyed) {
                button.destroy();
            }
        });
        this.fieldButtons = {};
        this.expectedValuesCache = {}; // Clear cache

        // IMPORTANT: Detach listeners added in afterrender to prevent memory leaks
        // This requires storing references or using ComponentQuery to find and remove
        // For simplicity, relying on ExtJS garbage collection here, but proper detachment is better.
        // Example (conceptual - needs actual implementation):
        // if (this.formPanelRef) {
        //     this.formPanelRef.getForm().getFields().each(function(field) {
        //         field.un('focus', this.handleFieldFocus, this);
        //         field.un('blur', this.handleFieldBlur, this);
        //         // Remove beforetriggerclick/customonblur listeners too
        //     }, this);
        // }

        this.callParent(arguments);
    }
}); 