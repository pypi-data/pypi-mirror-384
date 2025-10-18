# AssertLang Framework Overview

## Lifecycle Verbs
Every program is structured around five verbs:
- **Plan** → Define intent and architecture.
- **Apply** → Materialize files and dependencies.
- **Run** → Execute in sandbox/container.
- **Validate** → Test output and verify correctness.
- **Report** → Provide results, logs, artifacts.

## Numeric Tool Families
- **2**: Input & Output  
- **3**: Data Handling  
- **4**: Control Flow  
- **5**: Core Lifecycle Verbs  
- **6**: Specialized Tools (AV, networking, concurrency, security, extensibility, debugging)

## File Extension
All programs use the `.pw` extension.

## Port Standard
Default: `23456`  
Reserved for AssertLang agents.  
Secondary ephemeral sockets spun up per run.  
Sandbox fallback: if 23456 cannot be bound (e.g., CI seatbelts), the daemon exposes direct host/port access and reports it via CLI + report verbs.

## Execution Flow
1. Parse `.pw` file → verbs & tools
2. Sandbox container → chosen language runtime
3. Execute & validate → ephemeral microservice
4. Report → summary, logs, artifacts, API endpoint



