# ts-sdk <!-- omit in toc -->

Tetrascience Python SDK

## Version <!-- omit in toc -->

v2.6.0

## Table of Contents <!-- omit in toc -->

- [Install](#install)
- [Usage](#usage)
  - [Init a new protocol](#init-a-new-protocol)
  - [Upload artifact](#upload-artifact)
  - [IDS Validation](#ids-validation)
- [Task Script](#task-script)
  - [Config.json](#configjson)
    - [Overview](#overview)
    - [Allowed IDS](#allowed-ids)
- [Changelog](#changelog)
  - [v2.6.0](#v260)
  - [v2.5.1](#v251)
  - [v2.5.0](#v250)
  - [v2.4.1](#v241)
  - [v2.4.0](#v240)
  - [v2.3.0](#v230)
  - [v2.2.4](#v224)
  - [v2.2.3](#v223)
  - [v2.2.2](#v222)
  - [v2.2.1](#v221)
  - [v2.2.0](#v220)
  - [v2.1.3](#v213)
  - [v2.1.2](#v212)
  - [v2.1.1](#v211)
  - [v2.1.0](#v210)
  - [v2.0.2](#v202)
  - [v2.0.1](#v201)
  - [v2.0.0](#v200)
  - [v1.4.2](#v142)
  - [v1.4.1](#v141)
  - [v1.4.0](#v140)
  - [v1.3.10](#v1310)
  - [v1.3.9](#v139)
    - [CLI Improvements](#cli-improvements)
    - [Context Function Improvements](#context-function-improvements)
    - [Other](#other)
  - [v1.3.8](#v138)
  - [v1.3.7](#v137)
  - [v1.3.6](#v136)
  - [v1.3.5](#v135)
  - [v1.3.2](#v132)

## Install

```
pip3 install ts-sdk
```

## Usage

### Init a new protocol

```bash
ts-sdk init -o <org> -p <protocol-slug> -t <task-script-slug> -f <protocol-folder>
cd <protocol-folder>/task-script
pipenv install --dev
# task-script code modifications...
pipenv run pytest
```

### Upload artifact

```bash
export TS_ORG=<your-org-slug>
export TS_API_URL=https://api.tetrascience.com/v1
export TS_AUTH_TOKEN=<token>
ts-sdk put <ids|protocol|task-script> <namespace> <slug> <version> <artifact-folder>
```

It's also possible to use the configuration JSON file (`cfg.json`):

```bash
{
    "api_url": "https://api.tetrascience.com/v1",
    "auth_token": "your-token",
    "org": "your-org",
    "ignore_ssl": false
}
```

Usage: `ts-sdk put <ids|protocol|task-script> <namespace> <slug> <version> <artifact-folder> -c cfg.json`

### IDS Validation

When uploading IDS artifact, validation will be performed using `ts-ids-validator` package.
Validation failures for IDS will be printed on the console.

## Task Script

### Config.json

#### Overview

All Task Scripts have a `config.json` file that describes:

- what `language` a Task Script is written in
- the `functions` a Task Script has available for a Protocol to use
- the `runnerType`, an optional field that is only used when letting the artifact builder know a Windows script (identified by using the value “windows-script”) is being built
- the `maxCount` of container instances that will be used by the task
- and an optional field describing the amount of memory a task will need, `memoryInMB`

#### Allowed IDS

Within the `functions` object of the configuration, the optional field `allowedIds` describes the IDS types a Task Script can produce.

The `allowedIds` field is used by the Context API's [context.write_file](https://developers.tetrascience.com/docs/context-api#contextwrite_file) (when writing an IDS) and [context.write_ids](https://developers.tetrascience.com/docs/context-api#contextwrite_ids) functions to validate that the ids parameter of either function is allowed before writing an IDS.

`allowedIds` can be used in the following ways:

1. A single object with three properties: `namespace`, `slug`, `version`

   - When a function only generates one kind of IDS
   - The `ids` parameter of the [context.write_file](https://developers.tetrascience.com/docs/context-api#contextwrite_file) and [context.write_ids](https://developers.tetrascience.com/docs/context-api#contextwrite_ids) functions are optional since there is only one value in the `allowedIds` field
   - Example:

     ```json
     "functions": [
       {
         "slug": "generates-ids",
         "function": "main.generate_ids",
         "allowedIds": {
           "namespace": "common",
           "slug": "my-ids",
           "version": "v1.0.0"
         }
       }
     ]
     ```

2. An array of those objects with the three properties: `namespace`, `slug`, `version`

   - When a function can generate multiple IDS types
   - The `ids` parameter of the [context.write_file](https://developers.tetrascience.com/docs/context-api#contextwrite_file) and [context.write_ids](https://developers.tetrascience.com/docs/context-api#contextwrite_ids) functions is required and will be validated against the `allowedIds` to confirm the task script is allowed to write that IDS
   - Example:

     ```json
     "functions": [
       {
         "slug": "generates-ids",
         "function": "main.generate_ids",
         "allowedIds": [
           {
            "namespace": "common",
            "slug": "my-ids",
            "version": "v1.0.0"
           },
           {
            "namespace": "common",
            "slug": "my-ids",
            "version": "v1.1.0"
           },
           {
            "namespace": "common",
            "slug": "my-other-ids",
            "version": "v1.0.0"
           }
         ]
       }
     ]
     ```

3. `null`

   - When a function does not generate any IDS
   - Calls to [context.write_file](https://developers.tetrascience.com/docs/context-api#contextwrite_file) (when `file_category` is “IDS”) and [context.write_ids](https://developers.tetrascience.com/docs/context-api#contextwrite_ids) will raise an exception
     - When the `file_category` parameter is not "IDS", then [context.write_file](https://developers.tetrascience.com/docs/context-api#contextwrite_file) is not writing an IDS and therefore will not raise an exception
   - Example:

     ```json
     "functions": [
       {
         "slug": "generates-ids",
         "function": "main.generate_ids",
         "allowedIds": null
       }
     ]
     ```

4. `allowedIds` not defined

   - Any IDS JSON can be written via [context.write_file](https://developers.tetrascience.com/docs/context-api#contextwrite_file) or [context.write_ids](https://developers.tetrascience.com/docs/context-api#contextwrite_ids)
     - no allowed IDSs are specified, so no check is performed
   - Any IDS JSON passed to the [context.write_file](https://developers.tetrascience.com/docs/context-api#contextwrite_file) or [context.write_ids](https://developers.tetrascience.com/docs/context-api#contextwrite_ids) still has to pass validation against the IDS specified by the `ids` parameter

## Changelog

### v2.6.0

- Add support for running Task Scripts locally

<details>
<summary>example</summary>

```python
from ts_sdk.testing.models import *

local_file = LocalFile(path='test-file.json')

with Trigger(file=local_file) as trigger:
    result, error = Task(function='main').run({'hello': 'world'})
    print(result)
    print(local_file.labels)
```

</details>

- Add support for **Schema Artifact** integration in Task Scripts: introduced `get_schema_artifact` and **ArtifactUtilDict** for handling Schema Artifacts.

- Improve logger to include `tsSdkVersion` in each log entry (visible in debug mode). 

### v2.5.1

- Set `ts_user_id` s3 file meta for new file in datalake

### v2.5.0

- Adjust publish to support Codebuild build_id in response for all artifact types

### v2.4.1

- pass source_name and source_id in `context.write_detached_file` (default to pipeline name and id)

### v2.4.0

- new `context.write_detached_file` to write workflow input independent file

### v2.3.0

- Add `return_command` parameter to `context.run_cmd` and `context.run_command` (default: `False`) - When set to `True`, returns the entire command response object from TDP instead of just the response body. Default behavior continues to return `command.responseBody` on success or raise an exception containing `command.responseBody` on failure.

### v2.2.4

- Remove trailing comma from JSON changed in v2.2.2

### v2.2.3

- Restore the explicit signing version when generating a pre-signed URL

### v2.2.2

- Move `allowedIds` in the task script config.json schema from the Config object to the Function object
- Add the new `successWhen` and `onFailed` fields to the protocol v3 json schema

### v2.2.1

- Use timeout=300s for internal task endpoints

### v2.2.0

- Refactoring to avoid duplications with artifact-builder (for task script lambda feature)

### v2.1.3

- Update `context.validate_ids` to validate IDS instances using `ts-ids-validator:v1.1.0`
  - Check that the instance is valid against the schema
  - Check that the shape of `datacubes[*].measures[*].values` matches `datacubes[*].dimensions[*].scale`
- Update the cli's deprecation date

### v2.1.2

- Add exponential backoff to the task script runner

### v2.1.1

- Pass the current workflow id to the file info service when mutating labels

### v2.1.0

- Update logic for `context.run_cmd` method (also applied to `context.run_command`):
  - Implemented exponential backoff for polling the command service for command status
  - Introduced an optional `initial_delay_sec` parameter for initial delayed polling
  - Reduced the minimum `ttl_sec` threshold from 300 seconds to 60 seconds
- Adds an optional query argument to `context.search_eql`

### v2.0.2

- Update IDS artifact validation: now when using `ts-sdk put` to upload an IDS artifact, breaking change validation runs by downloading and comparing the previous version of the IDS from the Tetra Data Platform - see the `ts-ids-validator` package for more detail.

### v2.0.1

- Pin `tenacity` dependency to resolve compatibility issue with latest version

### v2.0.0

- Secure mode + bug fixes

### v1.4.2

- upgrade `smart_open` (`v4.2.0` &rarr; `v6.3.0`)

### v1.4.1

- Make `allowedIDS` non-mandatory for task-script, to maintain backward compatibility

### v1.4.0

- Added functionality to support `allowedIds` feature

### v1.3.10

- Internal fixes (`/update-status` API call retry)

### v1.3.9

#### CLI Improvements

- Make artifact build failure more evident to the user
- `ts-sdk put` will check for `requirements.txt` file before uploading

#### Context Function Improvements

- Add support to `write_file` to receive a dictionary instead of only strings
- Validate dictionary inputs to `write_file` against IDS
- Enforce IDS input to `write_ids` must be a dictionary
- Validate length of the name and value of labels
- Validate labels more thoroughly, in more places
- Add a new DataClass for better label definition

#### Other

- All code formatted with `black`
- Adjust abstract dependencies in `setup.py` to be less strict so that it will work better within task scripts
- Replace `json` library with `simplejson`for speed and usability

### v1.3.8

- Internal fixes (secrets handling)

### v1.3.7

- Add `--exclude-folders` argument to `ts-sdk put task-script` that excludes common folders that generally do not need to be part of the uploaded task script (e.g. `.git`, `example-input`, `__tests__`)
- Add local check to prevent uploading artifacts using `ts-sdk put` that would be rejected by the server for being too large
- Improve error messages for adding invalid labels to files

### v1.3.6

- Add new s3 meta:
  - DO_NOT_INHERIT_LABELS
  - CONTENT_CREATED_FROM_FILE_ID

### v1.3.5

- Fix bug where datalake file_key was incorrectly generated

### v1.3.2

- Update `context.write_file()` to validate file upload path
- Fix logging issues
- Improve namespace validation
- Update `print` functionality to be more accurate and group arguments to the same call together
