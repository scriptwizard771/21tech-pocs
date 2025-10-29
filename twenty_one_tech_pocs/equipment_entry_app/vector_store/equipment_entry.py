from .elasticsearch_vector_store import ElasticSearchVectorStore
import os


class EquipmentEntryElasticSearch(ElasticSearchVectorStore):
    # Include label mappings - Updated to include all fields from descriptions.js
    label_mapping = {
        # Existing Standard Fields
        "equipmentno": "ASSETID.EQUIPMENTCODE",
        "equipmentdesc": "ASSETID.DESCRIPTION",
        "department": "DEPARTMENTID.DEPARTMENTCODE",
        "eqtype": "TYPE.TYPECODE",
        "organization": "ASSETID.ORGANIZATIONID.ORGANIZATIONCODE",
        "assetstatus": "STATUS.STATUSCODE",
        "operationalstatus": "OPERATIONALSTATUS",
        "loanedtodepartment": "LOANEDTODEPARTMENTID",
        "pmwodepartment": "PMWODEPARTMENTID",  # Assuming this maps to PMWODEPARTMENTID
        "category": "CATEGORYID.CATEGORYCODE",
        "class": "CLASSID.CLASSCODE",
        "costcode": "COSTCODEID",
        "production": "INPRODUCTION",
        "safety": "SAFETY",
        "profile": "PROFILEID",
        "outofservice": "OUTOFSERVICE",
        "preventwocompletion": "PREVENTWOCOMPLETION",  # Assuming this maps to PREVENTWOCOMPLETION
        "commissiondate": "COMMISSIONDATE",
        "transferdate": "TRANSFERDATE",  # Assuming this maps to TRANSFERDATE
        "withdrawaldate": "WITHDRAWALDATE",  # Assuming this maps to WITHDRAWALDATE
        "equipmentvalue": "ASSETVALUE",
        "assignedto": "ASSIGNEDTO",
        "meterunit": "METERUNIT",
        "criticality": "CRITICALITYID",
        "state": "EQUIPMENTSTATEID",
        "cnnumber": "CNID",  # Assuming this maps to CNID
        "cgmp": "CGMP",
        "trackresource": "RESOURCEENABLED",
        "inventoryverificationdate": "INVENTORYVERIFICATIONDATE",  # Assuming this maps to INVENTORYVERIFICATIONDATE
        "lotodatereviewrequired": "LOTODATEREVIEWREQUIRED",  # Assuming this maps to LOTODATEREVIEWREQUIRED
        "lotoreviewedby": "LOTOREVIEWEDBY",  # Assuming this maps to LOTOREVIEWEDBY
        "originalreceiptdate": "ORIGINALRECEIPTDATE",  # Assuming this maps to ORIGINALRECEIPTDATE
        "latestreceiptdate": "LATESTRECEIPTDATE",  # Assuming this maps to LATESTRECEIPTDATE
        "originalinstalldate": "ORIGINALINSTALLDATE",  # Assuming this maps to ORIGINALINSTALLDATE
        "latestinstalldate": "LATESTINSTALLDATE",  # Assuming this maps to LATESTINSTALLDATE
        "documotobookid": "DOCUMOTOBOOKID",  # Assuming this maps to DOCUMOTOBOOKID
        "imageurl": "URL",  # Assuming this maps to URL
        "consist": "CONSISTID",  # Assuming this maps to CONSISTID
        "consistposition": "CONSISTPOSITION",  # Assuming this maps to CONSISTPOSITION
        "temperaturemonitored": "TEMPMONITORED",  # Assuming this maps to TEMPMONITORED
        "driver": "DRIVER",  # Assuming this maps to DRIVER
        "phonenumber": "PHONENUMBER",  # Assuming this maps to PHONENUMBER
        "accessible": "ACCESSIBLE",  # Assuming this maps to ACCESSIBLE
        "nonsmoking": "NONSMOKING",  # Assuming this maps to NONSMOKING
        "pidno": "PIDNUMBER",  # Assuming this maps to PIDNUMBER
        "piddrawing": "PIDDRAWING",  # Assuming this maps to PIDDRAWING
        "hardwareversion": "HARDWAREVER",  # Assuming this maps to HARDWAREVER
        "softwareversion": "SOFTWAREVER",  # Assuming this maps to SOFTWAREVER
        "purchasingassetid": "PURCHASINGASSET",  # Assuming this maps to PURCHASINGASSET
        "biomedicalassetid": "BIOMEDICALASSET",  # Assuming this maps to BIOMEDICALASSET
        "umdnscode": "UMDNS",  # Assuming this maps to UMDNS
        "oemsitesystemid": "OEMSITE",  # Assuming this maps to OEMSITE
        "vendor": "VENDOR",
        "coveragetype": "COVERAGETYPE",
        "lockouttagout": "LOCKOUT",
        "personalprotectiveequipment": "PERSONALPROTECTIVEEQUIP",
        "confinedspace": "CONFINEDSPACE",
        "statementofconditions": "STATEMENTOFCOND",  # Assuming this maps to STATEMENTOFCOND
        "buildingmaintenanceprogram": "BUILDMAINTPROGRAM",  # Assuming this maps to BUILDMAINTPROGRAM
        "hipaaconfidentiality": "HIPAACONFIDENTIALITY",  # Assuming this maps to HIPAACONFIDENTIALITY
        "disposaltype": "DISPOSALTYPE",
        "checklistfilter": "CHECKLISTFILTER",  # Assuming this maps to CHECKLISTFILTER
        "sizefortolerance": "TOLERANCESIZE",  # Assuming this maps to TOLERANCESIZE
        "primaryfuel": "FUELID",  # Assuming this maps to FUELID
        "profilepicture": "PROFILEPICTURE",  # Assuming this maps to PROFILEPICTURE
        "purchaseorder": "PURCHASEORDERCODE",
        "purchasedate": "PURCHASEDATE",
        "purchasecost": "PURCHASECOST",
        "vehicle": "FleetVehicleInfo",  # Special case? Or map to VEHICLE? Using FleetVehicleInfo for now.
        "vehiclestatus": "VEHICLESTATUS",
        "vehicletype": "VEHICLETYPE",
        "reservationcalendarownerslist": "RESERVATIONCALENDAROWNERSLIST",  # Assuming this maps to RESERVATIONCALENDAROWNERSLIST
        "reservationcalendarowner": "RESERVATIONCALENDAROWNER",  # Assuming this maps to RESERVATIONCALENDAROWNER
        "rentalequipment": "RENTALEQUIPMENT",
        "contractequipment": "CONTRACTEQUIPMENT",
        "customer": "CUSTOMER",
        "availabilitystatus": "AVAILABILITYSTATUS",
        "issuedto": "ISSUEDTO",
        "calendargroup": "CALENDARGROUP",
        "minimumpenalty": "MINIMUMPENALTY",
        "penaltyfactor": "PENALTYFACTOR",
        "sdmflag": "SDMFLAG",
        "vmrsdesc": "VMRSCODE",  # Mapping to VMRSCODE based on description
        "currentworkspace": "WORKSPACEID",  # Assuming this maps to WORKSPACEID
        "componentlocation": "PARTLOCATIONCODE",  # Assuming this maps to PARTLOCATIONCODE
        "alias": "EQUIPMENTALIAS",  # Assuming this maps to EQUIPMENTALIAS
        "safetydatereviewrequired": "SAFETYDATEREVIEWREQUIRED",  # Assuming this maps to SAFETYDATEREVIEWREQUIRED
        "safetyreviewedby": "SAFETYREVIEWEDBY",  # Assuming this maps to SAFETYREVIEWEDBY
        "permitdatereviewrequired": "PERMITDATEREVIEWREQUIRED",  # Assuming this maps to PERMITDATEREVIEWREQUIRED
        "permitreviewedby": "PERMITREVIEWEDBY",  # Assuming this maps to PERMITREVIEWEDBY
        "equipmentconfiguration": "EQUIPMENTCONFIGURATIONID",  # Assuming this maps to EQUIPMENTCONFIGURATIONID
        "setcode": "SETID",  # Assuming this maps to SETID
        "setposition": "SETPOSITION",  # Assuming this maps to SETPOSITION
        "rcmlevel": "RCMLEVELID",
        "riskprioritynumber": "RISKPRIORITYNUMBER",
        "facilityconditionindex": "FacilityConditionIndex",  # Special case? Using FacilityConditionIndex for now.
        "conditionindex": "CONDITIONINDEX",
        "conditionscore": "CONDITIONSCORE",
        # Added UDF Fields
        "udfchkbox01": "USERDEFINEDAREA.UDFCHKBOX01",
        "udfchar01": "USERDEFINEDAREA.UDFCHAR01",
        "udfchar02": "USERDEFINEDAREA.UDFCHAR02",
        "udfchar03": "USERDEFINEDAREA.UDFCHAR03",
        "udfchar04": "USERDEFINEDAREA.UDFCHAR04",
        "udfchar05": "USERDEFINEDAREA.UDFCHAR05",
        # Add other UDF types (num, date) if they exist, following the pattern
        # Added Custom Fields
        "cust_1_NUM_OBJ_SPACE": "cust_1_NUM_OBJ_SPACE",
        "cust_1_CODE_OBJ_AREATYPE": "cust_1_CODE_OBJ_AREATYPE",
        "cust_1_NUM_OBJ_HEIGHT": "cust_1_NUM_OBJ_HEIGHT",
        "cust_1_NUM_OBJ_CUBICMET": "cust_1_NUM_OBJ_CUBICMET",
        "cust_1_NUM_OBJ_PERIMTR": "cust_1_NUM_OBJ_PERIMTR",
        "cust_1_NUM_OBJ_SMWALLS": "cust_1_NUM_OBJ_SMWALLS",
        "cust_1_CODE_OBJ_T1": "cust_1_CODE_OBJ_T1",
        "cust_3_CHAR_OBJ_TIRESN": "cust_3_CHAR_OBJ_TIRESN",
        "cust_3_CODE_OBJ_TIREPOS": "cust_3_CODE_OBJ_TIREPOS",
        # Added Other Missing Fields (Using uppercase name as placeholder mapping)
        "syslevel": "SYSLEVEL",
        "asslevel": "ASSLEVEL",
        "complevel": "COMPLEVEL",
        "soldscrapdate": "SOLDSCRAPDATE",
        "dormantstart": "DORMANTSTART",
        "dormantend": "DORMANTEND",
        "reusedormantperiod": "REUSEDORMANTPERIOD",
        "manufacturer": "MANUFACTURER",
        "serialnumber": "SERIALNUMBER",
        "model": "MODEL",
        "revision": "REVISION",
        "zcoordinate": "ZLOCATION",  # Assuming ZLOCATION
        "xcoordinate": "XLOCATION",  # Assuming XLOCATION
        "ycoordinate": "YLOCATION",  # Assuming YLOCATION
        "part": "PART",  # Needs clarification - might map to PARTID.PARTCODE?
        "store": "STORE",  # Needs clarification - might map to STOREID.STORECODE?
        "bin": "BIN",
        "lot": "LOT",
        "variable1": "VARIABLE1",
        "variable2": "VARIABLE2",
        "variable3": "VARIABLE3",
        "variable4": "VARIABLE4",
        "variable5": "VARIABLE5",
        "variable6": "VARIABLE6",
        "rentaltemplate": "RENTALTEMPLATE",
        "contracttemplate": "CONTRACTTEMPLATE",
        "minimumpenaltycur": "MINIMUMPENALTYCUR",
        "riskleveldesc": "RISKLEVELDESC",
        "unmitigatedriskleveldesc": "UNMITIGATEDRISKLEVELDESC",
        "unmitigatedrpn": "UNMITIGATEDRPN",
        "performanceformula": "PERFORMANCEFORMULA",
        "performanceformulaorg": "PERFORMANCEFORMULAORG",
        "performance": "PERFORMANCE",
        "pfflastupdate": "PFFLASTUPDATE",
        "conditionrating": "CONDITIONRATING",
        "capacityrating": "CAPACITYRATING",
        "mtbfrating": "MTBFRATING",
        "mubfrating": "MUBFRATING",
        "mttrrating": "MTTRRATING",
        "variablerating1": "VARIABLERATING1",
        "variablerating2": "VARIABLERATING2",
        "variablerating3": "VARIABLERATING3",
        "variablerating4": "VARIABLERATING4",
        "variablerating5": "VARIABLERATING5",
        "variablerating6": "VARIABLERATING6",
        "capacitycode": "CAPACITYCODE",
        "availablecapacity": "AVAILABLECAPACITY",
        "desiredcapacity": "DESIREDCAPACITY",
        "nooffailures": "NOOFFAILURES",
        "mtbfdays": "MTBFDAYS",
        "mubf": "MUBF",
        "mubfuom": "MUBFUOM",
        "mttrhrs": "MTTRHRS",
        "variableresult1": "VARIABLERESULT1",
        "variableresult2": "VARIABLERESULT2",
        "variableresult3": "VARIABLERESULT3",
        "variableresult4": "VARIABLERESULT4",
        "variableresult5": "VARIABLERESULT5",
        "variableresult6": "VARIABLERESULT6",
        "parentasset": "PARENTASSET",  # Needs clarification - might map to PARENTASSETID.EQUIPMENTCODE?
        "dependentonparentasset": "DEPENDENTONPARENTASSET",
        "costrollupparentasset": "COSTROLLUPPARENTASSET",
        "position": "POSITION",  # Needs clarification - might map to POSITIONID.POSITIONCODE?
        "dependentonposition": "DEPENDENTONPOSITION",
        "costrollupposition": "COSTROLLUPPOSITION",
        "primarysystem": "PRIMARYSYSTEM",  # Needs clarification - might map to PRIMARYSYSTEMID.SYSTEMCODE?
        "dependentonsystem": "DEPENDENTONSYSTEM",
        "costrollupsystem": "COSTROLLUPSYSTEM",
        "location": "LOCATION",  # Needs clarification - might map to LOCATIONID.LOCATIONCODE?
        "positionparent": "POSITIONPARENT",  # Needs clarification - might map to POSITIONPARENTID.POSITIONCODE?
        "gisobjid": "GISOBJID",
        "mapcode": "MAPCODE",
        "gislayer": "GISLAYER",
        "xlocation": "XLOCATION",  # Kept this one
        "ylocation": "YLOCATION",  # Kept this one
        "equipmentlength": "EQUIPMENTLENGTH",
        "equipmentlengthuom": "EQUIPMENTLENGTHUOM",
        "linearreferenceuom": "LINEARREFERENCEUOM",
        "linearreferenceprecision": "LINEARREFERENCEPRECISION",
        "geographicalreference": "GEOGRAPHICALREFERENCE",
        "inspectiondirection": "INSPECTIONDIRECTION",
        "flow": "FLOW",
        "frompoint": "FROMPOINT",
        "frompointuom": "FROMPOINTUOM",
        "topoint": "TOPOINT",
        "topointuom": "TOPOINTUOM",
        "linearequipmenttype": "LINEAREQUIPMENTTYPE",
        "direction": "DIRECTION",
        "equipmentlengthoverride": "EQUIPMENTLENGTHOVERRIDE",
        "costofneededrepairs": "COSTOFNEEDEDREPAIRS",
        "costofneededrepairscur": "COSTOFNEEDEDREPAIRSCUR",
        "replacementvalue": "REPLACEMENTVALUE",
        "replacementvaluecur": "REPLACEMENTVALUECUR",
        "energystareligible": "ENERGYSTARELIGIBLE",
        "billable": "BILLABLE",
        "gastracked": "GASTRACKED",
        "floorarea": "FLOORAREA",
        "floorareauom": "FLOORAREAUOM",
        "estimatedrevenue": "ESTIMATEDREVENUE",
        "estimatedrevenuecur": "ESTIMATEDREVENUECUR",
        "region": "REGION",
        "primaryuse": "PRIMARYUSE",
        "yearbuilt": "YEARBUILT",
        "servicelife": "SERVICELIFE",
        "reliabilityrankinglocked": "RELIABILITYRANKINGLOCKED",
        "reliabilityrank": "RELIABILITYRANK",
        "reliabilityrankindex": "RELIABILITYRANKINDEX",
        "reliabilityrankscore": "RELIABILITYRANKSCORE",
        "reliabilityrankingoutofsync": "RELIABILITYRANKINGOUTOFSYNC",
        "reliabilityrankinglastcalc": "RELIABILITYRANKINGLASTCALC",
        "reliabilitysurveylastupdated": "RELIABILITYSURVEYLASTUPDATED",
        "reliabilitysetuplastupdated": "RELIABILITYSETUPLASTUPDATED",
        "rankingcalculationerror": "RANKINGCALCULATIONERROR",
        "riskpriorityindex_display": "RISKPRIORITYINDEX_DISPLAY",
        "criticalityscore": "CRITICALITYSCORE",
        "correctionconditionscore": "CORRECTIONCONDITIONSCORE",
        "correctionreason": "CORRECTIONREASON",
        "correctiondate": "CORRECTIONDATE",
        "correctionusage": "CORRECTIONUSAGE",
        "correctionusageuom": "CORRECTIONUSAGEUOM",
        "endofusefullife": "ENDOFUSEFULLIFE",
        "servicelifeusage": "SERVICELIFEUSAGE",
        "servicelifeusageuom": "SERVICELIFEUSAGEUOM",
        "targetpowerfactor": "TARGETPOWERFACTOR",
        "targetpeakdemand": "TARGETPEAKDEMAND",
        "billingperiodstartdate": "BILLINGPERIODSTARTDATE",
        "billevery": "BILLEVERY",
        "billeveryuom": "BILLEVERYUOM",
        "phaseimbeff1": "PHASEIMBEFF1",
        "phaseimbeff2": "PHASEIMBEFF2",
        "phaseimbeff3": "PHASEIMBEFF3",
        "phaseimbeff4": "PHASEIMBEFF4",
        "phaseimbeff5": "PHASEIMBEFF5",
        "performancemanager": "PERFORMANCEMANAGER",
        "electricsubmeterinterval": "ELECTRICSUBMETERINTERVAL",
        "electricthresholdusage": "ELECTRICTHRESHOLDUSAGE",
        "ownershiptype": "OWNERSHIPTYPE",
        "purchasecostcur": "PURCHASECOSTCUR",
    }

    # Add field descriptions - Updated to include all fields from descriptions.js
    field_descriptions = {
        # Existing Descriptions
        "equipmentno": "Unique identifier for the equipment/asset.",
        "equipmentdesc": "A brief description of the equipment.",
        "department": "The department responsible for the equipment.",
        "eqtype": "The type or category of the equipment.",
        "organization": "The organization the equipment belongs to.",
        "assetstatus": "The current status of the asset (e.g., Active, Inactive).",
        "operationalstatus": "The operational status (e.g., Operating, Down).",
        "loanedtodepartment": "Department the equipment is currently loaned to.",
        "pmwodepartment": "Department responsible for preventive maintenance work orders.",
        "category": "A broader classification category for the equipment.",
        "class": "A specific class within the category.",
        "costcode": "Associated cost code for financial tracking.",
        "production": "Indicates if the equipment is used in production.",
        "safety": "Indicates if the equipment has specific safety considerations.",
        "profile": "Associated profile ID.",
        "outofservice": "Indicates if the equipment is currently out of service.",
        "preventwocompletion": "Flag to prevent work order completion.",
        "commissiondate": "Date the equipment was commissioned.",
        "transferdate": "Date the equipment was transferred.",
        "withdrawaldate": "Date the equipment was withdrawn from service.",
        "equipmentvalue": "The monetary value of the equipment.",
        "assignedto": "Person or entity the equipment is assigned to.",
        "meterunit": "Unit of measurement for the equipment's meter.",
        "criticality": "Criticality level of the equipment.",
        "state": "Current state or condition of the equipment.",
        "cnnumber": "Associated CN (Change Notice) number.",
        "cgmp": "Indicates compliance with Current Good Manufacturing Practices.",
        "trackresource": "Flag indicating if the equipment is tracked as a resource.",
        "inventoryverificationdate": "Date of the last inventory verification.",
        "lotodatereviewrequired": "Indicates if Lockout/Tagout date review is required.",
        "lotoreviewedby": "Person who reviewed the Lockout/Tagout procedures.",
        "originalreceiptdate": "Date the equipment was originally received.",
        "latestreceiptdate": "Date the equipment was most recently received.",
        "originalinstalldate": "Date the equipment was originally installed.",
        "latestinstalldate": "Date the equipment was most recently installed.",
        "documotobookid": "Associated Documoto book ID.",
        "imageurl": "URL of an image of the equipment.",
        "consist": "Consist ID if part of a larger assembly.",
        "consistposition": "Position within the consist.",
        "temperaturemonitored": "Indicates if temperature is monitored for this equipment.",
        "driver": "Assigned driver (if applicable, e.g., vehicles).",
        "phonenumber": "Associated phone number.",
        "accessible": "Indicates if the equipment is accessible.",
        "nonsmoking": "Indicates if it's a non-smoking asset (e.g., vehicle, room).",
        "pidno": "Piping and Instrumentation Diagram (P&ID) number.",
        "piddrawing": "P&ID drawing reference.",
        "hardwareversion": "Hardware version of the equipment.",
        "softwareversion": "Software version installed on the equipment.",
        "purchasingassetid": "Identifier used in the purchasing system.",
        "biomedicalassetid": "Identifier used for biomedical assets.",
        "umdnscode": "Universal Medical Device Nomenclature System code.",
        "oemsitesystemid": "OEM site system identifier.",
        "vendor": "The vendor or supplier of the equipment.",
        "coveragetype": "Type of warranty or service coverage.",
        "lockouttagout": "Indicates if Lockout/Tagout procedures apply.",
        "personalprotectiveequipment": "Required Personal Protective Equipment (PPE).",
        "confinedspace": "Indicates if it involves a confined space.",
        "statementofconditions": "Reference to the Statement of Conditions.",
        "buildingmaintenanceprogram": "Indicates inclusion in the building maintenance program.",
        "hipaaconfidentiality": "Indicates HIPAA confidentiality requirements.",
        "disposaltype": "Method or type of disposal.",
        "checklistfilter": "Filter criteria for associated checklists.",
        "sizefortolerance": "Size specification for tolerance checks.",
        "primaryfuel": "Primary fuel type used by the equipment.",
        "profilepicture": "Profile picture associated with the asset.",
        "purchaseorder": "Purchase order number used to acquire the equipment.",
        "purchasedate": "Date the equipment was purchased.",
        "purchasecost": "Original purchase cost of the equipment.",
        "vehicle": "Information specific to fleet vehicles.",
        "vehiclestatus": "Current status of the vehicle.",
        "vehicletype": "Type of vehicle.",
        "reservationcalendarownerslist": "List of owners for the reservation calendar.",
        "reservationcalendarowner": "Primary owner of the reservation calendar.",
        "rentalequipment": "Indicates if the equipment is for rental.",
        "contractequipment": "Indicates if the equipment is under contract.",
        "customer": "Associated customer.",
        "availabilitystatus": "Current availability status.",
        "issuedto": "Person or entity the equipment is currently issued to.",
        "calendargroup": "Group for scheduling or calendar purposes.",
        "minimumpenalty": "Minimum penalty associated with the equipment (if applicable).",
        "penaltyfactor": "Factor used to calculate penalties.",
        "sdmflag": "Service Delivery Management flag.",
        "vmrsdesc": "Vehicle Maintenance Reporting Standards code description.",
        "currentworkspace": "The current workspace or location identifier.",
        "componentlocation": "Location code of the component part.",
        "alias": "An alternative name or alias for the equipment.",
        "safetydatereviewrequired": "Indicates if safety date review is required.",
        "safetyreviewedby": "Person who reviewed the safety procedures.",
        "permitdatereviewrequired": "Indicates if permit date review is required.",
        "permitreviewedby": "Person who reviewed the permits.",
        "equipmentconfiguration": "Identifier for the equipment's configuration.",
        "setcode": "Code identifying the set the equipment belongs to.",
        "setposition": "Position within the set.",
        "rcmlevel": "Reliability Centered Maintenance (RCM) level ID.",
        "riskprioritynumber": "Calculated Risk Priority Number (RPN).",
        "facilityconditionindex": "Index representing the facility's condition.",
        "conditionindex": "General condition index score.",
        "conditionscore": "Numerical score representing the equipment's condition.",
        # Added UDF Descriptions
        "udfchkbox01": "User Defined Checkbox 1",
        "udfchar01": "User Defined Character Field 1",
        "udfchar02": "User Defined Character Field 2",
        "udfchar03": "User Defined Character Field 3",
        "udfchar04": "User Defined Character Field 4",
        "udfchar05": "User Defined Character Field 5",
        # Added Custom Field Descriptions
        "cust_1_NUM_OBJ_SPACE": "Custom: Object Space (Number)",
        "cust_1_CODE_OBJ_AREATYPE": "Custom: Object Area Type (Code)",
        "cust_1_NUM_OBJ_HEIGHT": "Custom: Object Height (Number)",
        "cust_1_NUM_OBJ_CUBICMET": "Custom: Object Cubic Meters (Number)",
        "cust_1_NUM_OBJ_PERIMTR": "Custom: Object Perimeter (Number)",
        "cust_1_NUM_OBJ_SMWALLS": "Custom: Object Square Meter Walls (Number)",
        "cust_1_CODE_OBJ_T1": "Custom: Object T1 (Code)",
        "cust_3_CHAR_OBJ_TIRESN": "Custom: Tire Serial Number (Character)",
        "cust_3_CODE_OBJ_TIREPOS": "Custom: Tire Position (Code)",
        # Added Generic Descriptions for Other Missing Fields
        "syslevel": "System Level",
        "asslevel": "Assembly Level",
        "complevel": "Component Level",
        "soldscrapdate": "Date when equipment was sold or scrapped. It must be after the commission date.",
        "dormantstart": "Dormant Period Start Date",
        "dormantend": "Dormant Period End Date",
        "reusedormantperiod": "Reuse Dormant Period Flag",
        "manufacturer": "Manufacturer of the equipment",
        "serialnumber": "Serial number of the equipment",
        "model": "Model number or name",
        "revision": "Revision number or identifier",
        "zcoordinate": "Z-coordinate for location mapping",
        "xcoordinate": "X-coordinate for location mapping",
        "ycoordinate": "Y-coordinate for location mapping",
        "part": "Associated Part ID",
        "store": "Associated Store ID",
        "bin": "Storage Bin location",
        "lot": "Lot number",
        "variable1": "User Defined Variable 1",
        "variable2": "User Defined Variable 2",
        "variable3": "User Defined Variable 3",
        "variable4": "User Defined Variable 4",
        "variable5": "User Defined Variable 5",
        "variable6": "User Defined Variable 6",
        "rentaltemplate": "Rental Template ID",
        "contracttemplate": "Contract Template ID",
        "minimumpenaltycur": "Minimum Penalty Currency",
        "riskleveldesc": "Risk Level Description",
        "unmitigatedriskleveldesc": "Unmitigated Risk Level Description",
        "unmitigatedrpn": "Unmitigated Risk Priority Number",
        "performanceformula": "Performance Formula",
        "performanceformulaorg": "Performance Formula Organization",
        "performance": "Performance Metric",
        "pfflastupdate": "Performance Formula Last Update Date",
        "conditionrating": "Condition Rating",
        "capacityrating": "Capacity Rating",
        "mtbfrating": "Mean Time Between Failures (MTBF) Rating",
        "mubfrating": "Mean Usage Between Failures (MUBF) Rating",
        "mttrrating": "Mean Time To Repair (MTTR) Rating",
        "variablerating1": "Variable Rating 1",
        "variablerating2": "Variable Rating 2",
        "variablerating3": "Variable Rating 3",
        "variablerating4": "Variable Rating 4",
        "variablerating5": "Variable Rating 5",
        "variablerating6": "Variable Rating 6",
        "capacitycode": "Capacity Code",
        "availablecapacity": "Available Capacity",
        "desiredcapacity": "Desired Capacity",
        "nooffailures": "Number of Failures",
        "mtbfdays": "Mean Time Between Failures (MTBF) in Days",
        "mubf": "Mean Usage Between Failures (MUBF)",
        "mubfuom": "Mean Usage Between Failures (MUBF) Unit of Measure",
        "mttrhrs": "Mean Time To Repair (MTTR) in Hours",
        "variableresult1": "Variable Result 1",
        "variableresult2": "Variable Result 2",
        "variableresult3": "Variable Result 3",
        "variableresult4": "Variable Result 4",
        "variableresult5": "Variable Result 5",
        "variableresult6": "Variable Result 6",
        "parentasset": "Parent Asset ID",
        "dependentonparentasset": "Dependent on Parent Asset Flag",
        "costrollupparentasset": "Cost Roll-up from Parent Asset Flag",
        "position": "Position ID within Asset/System/Location",
        "dependentonposition": "Dependent on Position Flag",
        "costrollupposition": "Cost Roll-up from Position Flag",
        "primarysystem": "Primary System ID",
        "dependentonsystem": "Dependent on System Flag",
        "costrollupsystem": "Cost Roll-up from System Flag",
        "location": "Location ID",
        "positionparent": "Parent Position ID",
        "gisobjid": "GIS Object ID",
        "mapcode": "Map Code",
        "gislayer": "GIS Layer Name",
        "xlocation": "X-Location (GIS or Map)",  # Kept this one
        "ylocation": "Y-Location (GIS or Map)",  # Kept this one
        "equipmentlength": "Length of the linear equipment",
        "equipmentlengthuom": "Unit of Measure for Equipment Length",
        "linearreferenceuom": "Unit of Measure for Linear Referencing",
        "linearreferenceprecision": "Precision for Linear Referencing",
        "geographicalreference": "Geographical Reference Point or Marker",
        "inspectiondirection": "Direction of Inspection for Linear Assets",
        "flow": "Flow Direction",
        "frompoint": "Start Point for Linear Referencing",
        "frompointuom": "Unit of Measure for Start Point",
        "topoint": "End Point for Linear Referencing",
        "topointuom": "Unit of Measure for End Point",
        "linearequipmenttype": "Type of Linear Equipment",
        "direction": "Direction (e.g., North, South)",
        "equipmentlengthoverride": "Override Equipment Length Flag",
        "costofneededrepairs": "Estimated Cost of Needed Repairs",
        "costofneededrepairscur": "Currency for Cost of Needed Repairs",
        "replacementvalue": "Replacement Value of the Asset",
        "replacementvaluecur": "Currency for Replacement Value",
        "energystareligible": "Energy Star Eligible Flag",
        "billable": "Billable Asset Flag",
        "gastracked": "Gas Tracked Flag",
        "floorarea": "Floor Area",
        "floorareauom": "Unit of Measure for Floor Area",
        "estimatedrevenue": "Estimated Revenue",
        "estimatedrevenuecur": "Currency for Estimated Revenue",
        "region": "Geographical or Organizational Region",
        "primaryuse": "Primary Use of the Asset",
        "yearbuilt": "Year the Asset was Built or Manufactured",
        "servicelife": "Expected Service Life",
        "reliabilityrankinglocked": "Reliability Ranking Locked Flag",
        "reliabilityrank": "Reliability Rank",
        "reliabilityrankindex": "Reliability Rank Index",
        "reliabilityrankscore": "Reliability Rank Score",
        "reliabilityrankingoutofsync": "Reliability Ranking Out of Sync Flag",
        "reliabilityrankinglastcalc": "Reliability Ranking Last Calculation Date",
        "reliabilitysurveylastupdated": "Reliability Survey Last Updated Date",
        "reliabilitysetuplastupdated": "Reliability Setup Last Updated Date",
        "rankingcalculationerror": "Ranking Calculation Error Message",
        "riskpriorityindex_display": "Risk Priority Index (Display Value)",
        "criticalityscore": "Criticality Score",
        "correctionconditionscore": "Correction Condition Score",
        "correctionreason": "Reason for Correction",
        "correctiondate": "Date of Correction",
        "correctionusage": "Usage at Time of Correction",
        "correctionusageuom": "Unit of Measure for Correction Usage",
        "endofusefullife": "End of Useful Life Date",
        "servicelifeusage": "Service Life Usage",
        "servicelifeusageuom": "Unit of Measure for Service Life Usage",
        "targetpowerfactor": "Target Power Factor",
        "targetpeakdemand": "Target Peak Demand",
        "billingperiodstartdate": "Billing Period Start Date",
        "billevery": "Billing Frequency Value",
        "billeveryuom": "Billing Frequency Unit of Measure",
        "phaseimbeff1": "Phase Imbalance Effect 1",
        "phaseimbeff2": "Phase Imbalance Effect 2",
        "phaseimbeff3": "Phase Imbalance Effect 3",
        "phaseimbeff4": "Phase Imbalance Effect 4",
        "phaseimbeff5": "Phase Imbalance Effect 5",
        "performancemanager": "Performance Manager",
        "electricsubmeterinterval": "Electric Submeter Interval",
        "electricthresholdusage": "Electric Threshold Usage",
        "ownershiptype": "Ownership Type (e.g., Owned, Leased)",
        "purchasecostcur": "Currency for Purchase Cost",
    }

    def _create_index_mapping(self):
        # NOTE: This is a basic mapping. Adjust types and analyzers as needed.
        return {
            "properties": {
                "asset_description": {"type": "text"},
                "attribute_key": {"type": "keyword"},  # Use keyword for exact matching
                "attribute_value": {"type": "text"},  # Use text for potential analysis
                "embedding": {
                    "type": "dense_vector",
                    "dims": self.embedding_dims,
                    "index": True,
                    "similarity": "cosine",  # Or "l2_norm", "dot_product"
                },
                # Add other fields from your data source if needed
            }
        }

    def __init__(self, index_name: str = "assets_index"):
        es_host = os.environ.get("ES_URL", "http://localhost:9201")
        super().__init__(es_host=es_host, index_name=index_name)

    def fuzzy_search(self, user_input: str, label_key: str):
        # Get the Elasticsearch attribute for the provided label key
        attribute = self.label_mapping.get(label_key)
        if attribute is None:
            print(f"Warning: Invalid label_key '{label_key}' provided.")
            return []

        # Split the user input into terms
        search_terms = user_input.split()
        if not search_terms:
            return []

        # Build the boolean query with should clauses for each term
        should_clauses = []
        for term in search_terms:
            should_clauses.append(
                {
                    "match": {
                        "ASSETID.DESCRIPTION": {  # Changed from ASSETID.EQUIPMENTCODE
                            "query": term,
                            "fuzziness": "AUTO",
                            "operator": "or",  # Keep operator 'or' if needed per term, or remove/change if not
                        }
                    }
                }
            )

        query = {
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1,  # Match documents containing at least one term
                }
            },
            "_source": [attribute],  # Request only the target attribute
        }

        # print(f"Executing ES Query: {query}")  # Optional: for debugging
        response = self.search(query)

        # Use a set to store unique results
        unique_results = set()

        if response and "hits" in response and "hits" in response["hits"]:
            for hit in response["hits"]["hits"]:
                source = hit.get("_source", {})
                # Navigate nested structure if attribute contains dots
                attr_parts = attribute.split(".")
                value = source
                try:
                    for part in attr_parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None  # Attribute path not found in this hit
                            break
                    if value is not None:
                        # Add the found value to the set
                        unique_results.add(value)
                except Exception as e:
                    # Log errors during processing
                    print(f"Error processing hit: {hit}, Error: {e}")

        # Convert the set back to a list before returning
        return list(unique_results)
