# .NET Adapter Template Spec

Defines the canonical surface for toolgen-generated .NET adapters so C# runtimes stay aligned with other languages.

## Goals
- Emit `Adapter.cs` under `tools/<package>/adapters/` exposing a static `Adapter` class.
- Provide `public const string Version = "v1";` and `public static Dictionary<string, object> Handle(Dictionary<string, object> request)`.
- Stay dependency-free beyond the .NET Base Class Library (BCL).
- Keep implementations synchronous; rely on daemon orchestration for concurrency.

## File Layout
```
tools/
  <package>/
    adapters/
      Adapter.cs
```
- `<package>` derives from `_package_name(tool_id)` (e.g., `api-auth` → `api_auth`).
- Additional resources (schemas/docs) remain language-agnostic.

## API Expectations
- Validate `request` for null/mismatched types (`E_SCHEMA`).
- Use helper methods (`Ok`, `Error`, typed getters) to centralise response shaping.
- Map runtime errors to `E_ARGS`, `E_UNSUPPORTED`, `E_RUNTIME`, or `E_NETWORK` codes.
- Successful results return `Ok(new Dictionary<string, object> { ... })` with `ok=true` and `version=Version`.
- Prefer `System.Text.Json` for serialisation when needed; avoid Newtonsoft dependencies.

## Environment & Packaging
- No per-tool `.csproj`. The daemon bootstraps an SDK-style project targeting `net7.0` (or current LTS) and includes the adapter source as a compile item.
- All adapters must compile with `dotnet build` using the daemon-provided project; keep code within `net7.0` BCL APIs.
- Avoid static initialization side-effects; adapters should be pure functions over the request dictionary.

## Smoke Test Guidance
- Plan to generate `AdapterTests.cs` during Wave 2 that:
  1. Instantiate representative request dictionaries.
  2. Invoke `Adapter.Handle` and assert response payloads and error codes.
  3. Run under `dotnet test` using the harness-provided project.
- Manual validation (until automated tests land):
```
dotnet script <<'CSX'
#r "./.promptware/tmp/AssertLangAdapters.dll"
Console.WriteLine(AssertLang.ApiAuth.Adapter.Handle(new()
{
  ["type"] = "apiKey",
  ["token"] = "t"
})["ok"]);
CSX
```
  (The actual harness will supply compiled assemblies; the snippet illustrates expected usage.)

Automated smoke coverage now runs via `tests/tools/test_dotnet_adapters.py`, which scaffolds a temporary `net8.0` console project, copies `Adapter.cs`, executes it with fixtures stored in `tests/fixtures/dotnet_adapters/`, and compares responses to expected subsets. Override the SDK via `DOTNET_BIN` when multiple installations exist.

## Open Questions
- Should we emit partial classes or namespaces to support future shared utilities?
- How do we manage HttpClient lifetime across repeated calls without leaking sockets?
- Will we need async counterparts once the daemon supports streaming responses?

Track follow-up work in `docs/execution-plan.md` under Adapter Packaging Notes and the Wave 2 tracker.
