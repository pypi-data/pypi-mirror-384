# apierrors

_Transport-agnostic, typed error DTOs and envelopes for APIs._
Use the same domain error objects across HTTP, gRPC, GraphQL, WebSocket, JSON-RPC, 
and message queues—with first-class support for HTTP out of the box and 
a 422 format compatible with FastAPI.

---
 
## Why

Framework built-ins (e.g., `HTTPException`) are convenient but **hard-wire 
errors to one transport**. `apierrors` keeps your domain errors independent 
and **adds thin adapters per transport**. Your handlers build rich, typed errors; 
adapters serialize them for the wire.

---

### Features

- **Typed DTOs:** `Err400/401/403/404/405/409/422/...` with critical fields (e.g., 
`loc` for 422, `allowed_methods` for 405, `permission` for 403).
- **Transport-agnostic core:** domain errors don’t depend on HTTP.
- **HTTP envelopes:** `HttpErrorEnvelope[T]` with `status_code`, optional `headers`.
- **FastAPI-style 422:** `Err422` supports `loc`, `error_type` (aka type), `ctx`, `message` (aka msg).
- **Consistent JSON:** stable shape for clients & SDKs.
- **Headers helpers:** easy `WWW-Authenticate`, `Allow`, Retry-`After`.
- **Adapters (extensible):** examples for gRPC, GraphQL, WS.

---

### Install
```commandline
pip install apierrors
```

Python 3.11+.

---

### Why not just `HTTPException` (FastAPI / Starlette)?

| Aspect                   | `HTTPException`      | **apierrors**                                                     |
| ------------------------ | -------------------- |-------------------------------------------------------------------|
| Transport                | HTTP-only            | Transport-agnostic domain errors + HTTP adapter                   |
| Typing/DTOs              | Message + status     | Rich typed DTOs per status (401, 403, 405, 409, 422…)             |
| 422 details              | Framework-controlled | Explicit `loc`/`error_type`/`ctx`, same across transports         |
| Headers                  | Manual, ad-hoc       | DTO fields + helper factories (e.g., `Allow`, `WWW-Authenticate`) |
| Reuse in gRPC/GraphQL/WS | No                   | Yes, via adapters                                                 |
| Client SDKs              | Ad-hoc parsing       | Stable JSON shapes for codegen/SDKs                               |
| Testability              | Inspect exception    | Assert on DTO fields & envelopes                                  |

**Bottom line**: keep domain errors independent; adapt once per transport.

---

### Comparison to other libs

- **Starlette / FastAPI exceptions**: great for quick HTTP flows but hard-wire 
transport and shape; 422 format depends on framework internals. `apierrors` 
gives you the same clarity for 422 while remaining cross-transport.
- **DRF APIException / Marshmallow errors**: framework-centric, tightly coupled
to serializers/validators. `apierrors` can ingest their outputs and 
produce a consistent cross-transport error shape.
- **Werkzeug/HTTPX exceptions**: HTTP-only and less prescriptive about rich detail.

---

### Best practices

- **Build domain errors, not responses.** Keep HTTP concerns at the edge.
- **Use specific DTOs.** Prefer `Err403(resource=..., action=..., permission=...) `over a generic message.
- **422 consistently**. Use loc paths identical to your validator (`("body","items",0,"price")`).
- **Set headers via envelope**. Mirror DTO fields into `headers` (e.g., `Allow`).
- **Log** `request_id`. Populate for traceability; ship `timestamp` automatically.

---

# Roadmap

- More transports & adapters
  - gRPC error details (`google.rpc.BadRequest` / `ErrorInfo`)
  - GraphQL `extensions` & Apollo format
  - JSON-RPC 2.0 (`code`/`message`/`data`)
  - WebSocket/SSE payloads & close codes
  - Message buses (Kafka/RabbitMQ) error envelopes
- RFC7807 adapter (Problem Details) with per-status extensions
- Pydantic & Marshmallow bridges (auto-convert validation errors → `Err422`)
- i18n: message translation hooks
- Retry semantics: helpers for `Retry-After`, backoff hints
- Codegen: JSON Schema for errors to power SDKs
- 5xx suite: `Err500`..`Err504` with incident/trace fields
