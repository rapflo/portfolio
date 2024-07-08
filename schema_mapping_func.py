# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 10:29:28 2024

@author: rapflo
"""
import arcpy

arcpy.env.workspace = r"C:\Users\2024_Regs.gdb"
database = r"C:\Users\2024_Regs.gdb"

#all fields mapped as a reference dictionary
fields_mapped = {   #target field name (JNCC schema) : source field name (GeMS)
                   "Polygon" : "GEMS_ID",
                   "SurveyKey" : "SURVEYKEY", #easier to change "SURVEYKEY" and call '!SurveyKey!' later to assign SNCB_UID as new field
                   "Occurrence" : "BIOTOPEOCC",
                   "FeaturName" : "ANNEX_I", #this will be "ANNEX_I_PH" for some habitats e.g. lagoons
                   "FeaturSubt" : "ANNEX_I_SU",
                   "FeaDetDate" : "DATE_",
                   "OrigCode" : "CURRENT_BI",
                   "OrigName" : "CURRENT__1"}

#JNCC field values in dictionary
JNCC_fields = {"SNCB_Auth" : "'NatureScot'",
               "SNCB_UID" : '!SurveyKey!',
               "EMODnetGUI" : '!SurveyKey!',
               "FeaturCode" : "'XXX'", #update with specific code
               "FeaDetName": "'NatureScot'",
               "TranRelate" : "'>'", #maerl is =, others are >
             #  "TranComm" : remains NULL
               "OrigClass" : "'Marine Habitat Classification for Britain and Ireland v04.05'", 
               "SourceComp" : "'GeMS(2024-06-14)'" #'GeMS(' + str(datetime.datetime.now().strftime('%Y-%m-%d')) + ')' #date GeMS downloaded
             #  "Comments" : remains NULL
             }

def map_to_schema(gdb, input_fc, output_fc, pointline_or_polygon, fields_mapped, 
                  JNCC_fields) -> str:
    """
    Take raw GeMS feature class from a geodatabase and map to a new JNCC schema.
    The feature class in either point, line or polygon format.
    Output is a new feature class in a geodatabase.
    The function will compare the fields in the output_fc and the fields in the 
    desired schema and will print any which are missing from the output_fc.
    
    Variables:
    
    gdb is the geodatabase where the analysis is taking place (raw data is stored
    and output will be written) [str].
    
    input_fc is the name of the feature class where the raw GeMS data is stored
    [str].
    
    output_fc is the name of the final output feature class which has been mapped
    to the JNCC schema. Must not already exist in the gdb [str].
    
    pointline_or_polygon specifies whether data type of the input_fc feature 
    class. Takes "point", "pointline" or "polygon" [str].
    
    fields_mapped is the dictionary which contains the values and keys for the
    mapping between GeMS and JNCC schemas [dict].
    
    JNCC_fields is the dictionary where field values are defined according to 
    attribute template from JNCC [dict].

    Examples:
    
    >>>map_to_schema(database, mainLayer, "GeMS_to_JNCC_POINTS_REEFS", "point", 
    fields_mapped, JNCC_fields)
    
    >>>map_to_schema(database, mainLayer2, "GeMS_to_JNCC_POLYGONS_REEFS", "polygon", 
    fields_mapped, JNCC_fields)
    
    >>>map_to_schema(database, database + "\\GEMS_habitat_point_layer_maerl", 
    "GeMS_to_JNCC_POINTS_MAERL", "point", fields_mapped, JNCC_fields)
    
    >>>map_to_schema(database, database + "\\GEMS_habitat_polygon_layer_maerl", 
    "GeMS_to_JNCC_POLYGON_MAERL", "polygon", fields_mapped, JNCC_fields)
    
    """
    
    #required fields from GeMS
    fields = ["GEMS_ID", "SURVEYKEY", "BIOTOPEOCC", "ANNEX_I", "ANNEX_I_SU", 
          "DATE_", "CURRENT_BI", "CURRENT__1"] #include "ANNEX_I_PH" for lagoons
    
    JNCC_fields_points = ["SNCB_Auth", "Occurrence", "FeaturCode", "FeaturName", 
                      "FeaturSubt", "FeaDetDate", "FeaDetName", "TranRelate",
                        "TranComm", "OrigCode", "OrigName", "OrigClass", 
                        "SourceComp", "Comments"]

    JNCC_fields_polygon = ["SNCB_Auth", "SNCB_UID", "EMODnetGUI", "Polygon", 
                           "FeaturCode", "FeaturName", "FeaturSubt", "FeaDetDate", 
                           "FeaDetName", "TranRelate", "TranComm", "OrigCode", "OrigName", 
                           "OrigClass", "SourceComp", "Comments"]
    
    #source just fields required from GeMS as new feature class in gdb
    fieldMappings = arcpy.FieldMappings()
    for field in fields:
        map = arcpy.FieldMap()
        map.addInputField(input_fc, field)
        fieldMappings.addFieldMap(map)
    new_GeMS = arcpy.FeatureClassToFeatureClass_conversion(input_fc, 
                                                           gdb, 
                                                           output_fc, 
                                                           "#", 
                                                           fieldMappings)
   
    input_fc_subset = database + "\\" + output_fc
    
    #rename subset fields as in dictionary
    for item in fields_mapped:
        arcpy.management.AlterField(input_fc_subset, #input gdb table
                                    fields_mapped[item], #field that will be altered
                                    item, #new name for field
                                    item) #new field alias
    
    #select appropriate schema
    if pointline_or_polygon.lower() == "point" or "points" or "line" or "pointline":
        schema = JNCC_fields_points
    if pointline_or_polygon.lower() == "polygon": ##polygon schema not being picked up
        schema = JNCC_fields_polygon
        
#   print([f.name for f in arcpy.ListFields(input_fc_subset)])
    
    #add new fields from JNCC schema
    for field in schema:
        if field not in [f.name for f in arcpy.ListFields(input_fc_subset)]:
            arcpy.management.AddField(input_fc_subset, #input gdb table
                                    field, #field that will be added
                                    "TEXT", #field type
                                    field_is_nullable = "Nullable")
    
    #calculate new JNCC fields
    for field in schema:
        if field in JNCC_fields.keys():
            arcpy.management.CalculateField(input_fc_subset,
                                        field,
                                        JNCC_fields[field])