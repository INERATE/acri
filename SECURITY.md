# Security Policy

acri sits between your application and your LLM provider, and it reads every tool schema
you register. That makes it a sensitive position in your stack, and we treat it as one.

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Use GitHub's private
vulnerability reporting on this repository, or contact the maintainers via the profile.
Include reproduction steps and impact. You will get an acknowledgment within 72 hours.

## Scope

- **Tool-description injection.** A malicious tool description influencing which tools get
  resolved, or reaching the model as instructions rather than data.
- **Schema exfiltration.** Any path where registered tool schemas, arguments, or resolved
  payloads leave the process other than to the provider the caller configured.
- **Payload handles.** `press` stores full payloads outside the context window; any path
  that lets an unrelated session read another's stored payload.
- **`ledger` contents.** Traces record queries and tool arguments. Any default that writes
  them somewhere the user did not choose, or that ships them off-machine.
- **Dependency or install-time compromise**, including anything executed at package
  install.

## Principles we hold ourselves to

- acri never makes a network call the caller did not configure. There is no telemetry, no
  phone-home, and no remote index.
- Tool descriptions are **data, never instructions.** They are ranked, never executed, and
  never concatenated into a system prompt as directives.
- `ledger` writes only where the caller points it, defaults to local, and is trivially
  disabled.
- Credentials are read from the caller's environment and never persisted, logged, or
  written into a trace.
