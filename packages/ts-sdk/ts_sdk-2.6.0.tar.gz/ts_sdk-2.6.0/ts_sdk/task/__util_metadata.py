# These should be kept in sync with S3MetadataFields.js in ts-lib-shared-schema
# https://github.com/tetrascience/ts-lib-shared-schema/blob/master/src/S3MetadataFields.js
FIELDS = {
    "VERSION": "ts_version",
    "INTEGRATION_TYPE": "ts_integration_type",
    "INTEGRATION_NAME": "ts_integration_name",
    "INTEGRATION_ID": "ts_integration_id",  # TODO new?
    "FILE_ID": "ts_file_id",
    # FILE_TYPE is deprecated. This field is no longer used, it could contain not valid file type
    #  as some sources were not setting it correctly
    "FILE_TYPE": "ts_processed_file_type",
    "FILE_PATH": "ts_file_path",  # how to specify this?
    "FILE_NAME": "ts_file_name",
    "SOURCE_ID": "ts_integration_source",
    "SOURCE_TYPE": "ts_source_type",
    "SOURCE_NAME": "ts_source_name",
    "DESTINATION_ID": "ts_destination_id",
    "RAW_FILE_ID": "ts_source_file_id",
    "RAW_FILE_VERSION": "ts_raw_file_version",
    "IDS": "ts_ids",
    "IDS_NAMESPACE": "ts_ids_namespace",
    "IDS_TYPE": "ts_ids_type",
    "IDS_VERSION": "ts_ids_type_version",
    "CUSTOM_METADATA": "ts_integration_metadata",
    "CUSTOM_TAGS": "ts_integration_tags",
    "PIPELINE_ID": "ts_pipeline_id",
    "PIPELINE_MASTER_SCRIPT": "ts_master_script",
    "PIPELINE_TASK_SCRIPT": "ts_task_script",
    "PIPELINE_TASK_SLUG": "ts_task_slug",
    "PIPELINE_TASK_EXECUTION_ID": "ts_task_execution_id",
    "PIPELINE_WORKFLOW_ID": "ts_workflow_id",
    "PIPELINE_HISTORY": "ts_pipeline_history",
    "TRACE_ID": "ts_trace_id",
    "CONTENT_CREATED_FROM_FILE_ID": "ts_content_created_from_file_id",
    "DO_NOT_INHERIT_LABELS": "ts_do_not_inherit_labels",
    "API_USER_ID": "ts_user_id",
}
