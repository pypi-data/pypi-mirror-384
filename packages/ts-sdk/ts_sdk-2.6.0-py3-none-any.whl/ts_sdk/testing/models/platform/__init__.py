from . import catchall, command, es_datalake, fileinfo, s3

replacements = [
    *es_datalake.replacements,
    *fileinfo.replacements,
    *command.replacements,
    # catchall MUST be last
    *catchall.replacements,
]
