# Toolgen Template Catalog

This catalog lists the AssertLang tool specifications currently checked in under `toolgen/specs/`. Each entry shows the tool id, a one-line summary, and the adapter templates that will be rendered when the generator runs. Use this as the jumping-off point when designing new tools or extending template coverage to additional languages.

| Tool | Summary | Adapters |
| --- | --- | --- |
| api-auth | Generate API auth headers (API key, bearer). | python:auth_header, node:auth_header, go:auth_header, rust:auth_header, dotnet:auth_header |
| async | Simulate async execution results. | python:async_simulator, node:async_simulator, go:async_simulator, rust:async_simulator, dotnet:async_simulator |
| auth | Produce authentication headers for API calls (API key, JWT). | python:auth_header, node:auth_header, go:auth_header, rust:auth_header, dotnet:auth_header |
| branch | Select a branch based on value/cases mapping. | python:branch_select, node:branch_select, go:branch_select, rust:branch_select, dotnet:branch_select |
| conditional | Evaluate simple conditions (==, !=, regex). | python:conditional_eval, node:conditional_eval, go:conditional_eval, rust:conditional_eval, dotnet:conditional_eval |
| custom-tool-template | Provide template scaffolding metadata. | python:schema_stub |
| encryption | Provide basic hashing utilities. | python:schema_stub |
| error-log | Collect error log summaries. | python:error_log_collector, node:error_log_collector, go:error_log_collector, rust:error_log_collector, dotnet:error_log_collector |
| error | Report error state toggles. | python:error_toggle, node:error_toggle, go:error_toggle, rust:error_toggle, dotnet:error_toggle |
| http | Perform HTTP requests with configurable headers, body, and timeout. | python:http_client, node:http_client, go:http_client, rust:http_client, dotnet:http_client |
| input | Read content from files. | python:schema_stub |
| logger | Structured logging sink with stdout forwarding. | python:stdout_logger, node:stdout_logger, go:stdout_logger |
| loop | Iterate items and report iteration count. | python:loop_counter, node:loop_counter, go:loop_counter, rust:loop_counter, dotnet:loop_counter |
| marketplace-uploader | Simulate marketplace uploads and return artifact paths. | python:schema_stub |
| media-control | Placeholder media control operations. | python:schema_stub |
| output | Write content to stdout or files. | python:output_writer, node:output_writer, go:output_writer, rust:output_writer, dotnet:output_writer |
| plugin-manager | Simulate plugin management operations. | python:schema_stub |
| rest | Perform REST requests relative to a base URL. | python:rest_client, node:rest_client, go:rest_client, rust:rest_client, dotnet:rest_client |
| scheduler | Simulate scheduling operations. | python:schema_stub |
| storage | Filesystem-oriented storage operations (put/get/list/delete). | python:storage_fs, node:storage_fs, go:storage_fs, rust:storage_fs, dotnet:storage_fs |
| thread | Simulate threading operations. | python:schema_stub |
| timing | Measure elapsed time for sleep operations. | python:schema_stub |
| tracer | Emit simple trace IDs. | python:schema_stub |
| transform | Convert structured data between JSON and YAML. | python:transform_convert, node:transform_convert, go:transform_convert, rust:transform_convert, dotnet:transform_convert |
| validate-data | Validate JSON documents against JSON Schema. | python:json_validator, node:json_validator |

## Next Steps
- Extend specs with additional adapters (Node, Go, Rust, .NET) so multi-runtime programs can be generated automatically.
- Capture generated artifacts (schemas, adapters, tests) in an index to keep the catalog in sync.
- Wire `promptware toolgen --list` to surface this table programmatically for downstream tooling.
