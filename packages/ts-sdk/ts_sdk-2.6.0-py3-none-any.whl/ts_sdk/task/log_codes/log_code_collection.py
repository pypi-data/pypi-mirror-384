from ts_sdk.task.log_codes.log_code import LogCode
from ts_sdk.task.log_codes.log_code_collection_meta import LogCodeCollectionMeta


class LogCodeCollection(metaclass=LogCodeCollectionMeta):
    # Platform interaction -- used only by the machinery that runs Task Scripts
    platform_interaction = LogCode(code_message="PlatformInteraction", code=100)
    # Informational/Generic/Uncategorized
    generic = LogCode(code_message="Generic", code=1000)
    # Input Data validation
    input_data_valid = LogCode(code_message="InputDataValid", code=1100)
    invalid_raw_input_data = LogCode(code_message="InvalidRawInputData", code=1101)
    invalid_input_file_attribute = LogCode(
        code_message="InvalidInputFileAttribute", code=1102
    )
    # Output Data Validation
    output_data_valid = LogCode(code_message="OutputDataValid", code=1200)
    invalid_ids_data = LogCode(code_message="InvalidIdsData", code=1201)
    invalid_output_data = LogCode(code_message="InvalidOutputData", code=1202)
    invalid_output_file_attribute = LogCode(
        code_message="InvalidOutputFileAttribute", code=1203
    )
    # Configuration
    #: Copy of the configuration (e.g. show inputs to task script)
    configuration = LogCode(code_message="Configuration", code=1300)
    invalid_pipeline_configuration = LogCode(
        code_message="InvalidPipelineConfiguration", code=1301
    )
    # Processing
    processing_status = LogCode(code_message="ProcessingStatus", code=1400)
    processing_begin = LogCode(code_message="ProcessingBegin", code=1401)
    processing_end = LogCode(code_message="ProcessingEnd", code=1402)
    processing_error = LogCode(code_message="ProcessingError", code=1403)
    space_odyssey = LogCode(code_message="SpaceOdyssey", code=2001)
    logger_error = LogCode(code_message="LoggerError", code=4900)
