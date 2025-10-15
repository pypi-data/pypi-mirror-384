# Knowrithm Python SDK

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PyPI version](https://badge.fury.io/py/knowrithm-py.svg)](https://badge.fury.io/py/knowrithm-py)

Knowrithm is a Python SDK for the Knowrithm platform. It wraps every documented
Flask blueprint route with typed helpers, covers authentication primitives, and
adds pragmatic conveniences such as automatic retries and multipart upload
handling.

---

## Installation

```bash
pip install knowrithm-py
```

For local development:

```bash
git clone https://github.com/Knowrithm/knowrithm-py.git
cd knowrithm-py
pip install -e .
```

---

## Quick Start

```python
from pathlib import Path
from knowrithm_py.knowrithm.client import KnowrithmClient

# Initialize the client (API key + secret OR provide JWT headers to each call)
client = KnowrithmClient(
    api_key="your-api-key",
    api_secret="your-api-secret"
)

# Create an agent (settings created automatically – provider/model names work too)
agent = client.agents.create_agent(
    {
        "name": "Support Bot",
        "description": "Customer support assistant",
        "status": "active",
    },
    settings={
        "llm_provider": "openai",
        "llm_model": "gpt-3.5-turbo-16k",
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-ada-002",
        "llm_temperature": 0.7,
    },
)
print(agent['agent']["id"])

# When provider/model names are supplied the SDK calls /v1/sdk/agent under the hood.
# Pass ID-based fields instead if you need explicit control over provider records.

# Upload supporting documents
client.documents.upload_documents(
    agent_id=agent['agent']["id"],
    file_paths=[Path("knowledge-base.pdf")]
)

# Start a conversation and send a message
conversation = client.conversations.create_conversation(agent_id=agent['agent']["id"])
queued = client.messages.send_message(
    conversation_id=conversation['conversation']["id"],
    message="Hello there!",
)

print(queued["status"])           # -> "queued"
print(queued["poll_url"])         # -> "/v1/conversation/<id>/messages"

# Poll the conversation for new messages once the task completes
messages = client.conversations.list_conversation_messages(
    conversation_id=conversation['conversation']["id"]
)
for entry in messages.get("messages", []):
    print(f"{entry['role']}: {entry['content']}")
```

### Streaming responses (optional)

The API can also push updates over Server-Sent Events (SSE). Configure the
stream endpoint once, or pass it per call.

```python
from knowrithm_py.dataclass.config import KnowrithmConfig

client = KnowrithmClient(
    api_key="your-api-key",
    api_secret="your-api-secret",
    config=KnowrithmConfig(
        base_url="https://app.knowrithm.org/api",
        stream_path_template="/conversation/{conversation_id}/messages/stream",  # Replace with your SSE route
    ),
)

conversation = client.conversations.create_conversation(agent_id=agent['agent']["id"])
stream = client.messages.send_message(
    conversation_id=conversation['conversation']["id"],
    message="Hello there!",
    stream=True,
    # Or supply stream_url=f"/conversation/{conversation['conversation']['id']}/messages/stream"
)

with stream:
    for event in stream:
        print(event.event, event.data)

# Alternatively open the stream directly:
direct_stream = client.messages.stream_conversation_messages(
    conversation_id=conversation['conversation']["id"]
)
```

The stream typically emits queue progress events (e.g. ``chat_status``) followed
by the final assistant payload (e.g. ``chat_response``). Adjust the loop as
needed. A ``503`` response indicates the streaming backend is temporarily
disabled; fall back to polling in that case.

> **Authentication** - Unless a route explicitly states otherwise, supply either
> `X-API-Key` + `X-API-Secret` with the proper scopes or `Authorization: Bearer <JWT>`.
> All service methods take an optional `headers` argument so you can override the
> default API key headers with JWT tokens when needed.

---

## Service Reference

Each service is accessible through `KnowrithmClient` (for example `client.agents`).
Every method forwards to the documented REST endpoint under `app/blueprints` and
returns the JSON payload (or raw text/bytes for non-JSON responses).

### AuthService (`client.auth`)

- `seed_super_admin(headers=None)` - `GET /v1/auth/super-admin`. No auth required.
  Seeds the platform super admin from environment variables.
- `register_admin(payload, headers=None)` - `POST /v1/auth/register`. Public
  registration for a company admin. Payload must include company ID, email,
  username, password, first and last name.
- `login(email, password, headers=None)` - `POST /v1/auth/login`. Returns access
  and refresh JWT tokens.
- `refresh_access_token(refresh_token, headers=None)` - `POST /v1/auth/refresh`.
  Send `Authorization: Bearer <refresh JWT>` to obtain a new access token.
- `logout(headers)` - `POST /v1/auth/logout`. Revoke the current JWT session.
- `send_verification_email(email, headers=None)` - `POST /v1/send`. Public route
  that kicks off the verification email flow.
- `verify_email(token, headers=None)` - `POST /v1/verify`. Confirms email ownership.
- `get_current_user(headers)` - `GET /v1/auth/user/me`. Returns the authenticated
  user together with the active company.
- `create_user(payload, headers=None)` - `POST /v1/auth/user`. Admin-only user
  creation. Accepts email, username, password, and optional company override.

### ApiKeyService (`client.api_keys`)

- `create_api_key(payload, headers=None)` - `POST /v1/auth/api-keys`. Create a
  new API key for the JWT user. Payload may include name, scopes, permissions, and expiry.
- `list_api_keys(headers)` - `GET /v1/auth/api-keys`. Lists active keys owned by the user.
- `delete_api_key(api_key_id, headers)` - `DELETE /v1/auth/api-keys/<id>`. Revokes a key.
- `validate_credentials(headers)` - `GET /v1/auth/validate`. Confirms the caller's
  credentials and returns metadata.
- `get_api_key_overview(days=None, headers=None)` - `GET /v1/overview`. High-level
  analytics for API key usage.
- `get_usage_trends(days=None, granularity=None, headers=None)` - `GET /v1/usage-trends`.
  Returns daily/hourly usage patterns.
- `get_top_endpoints(days=None, headers=None)` - `GET /v1/top-endpoints`. Shows the
  most-used endpoints per company.
- `get_api_key_performance(days=None, headers=None)` - `GET /v1/api-key-performance`.
  Performance metrics by key.
- `get_error_analysis(days=None, headers=None)` - `GET /v1/error-analysis`. Error distribution.
- `get_rate_limit_analysis(days=None, headers=None)` - `GET /v1/rate-limit-analysis`.
  Rate-limit consumption overview.
- `get_detailed_usage(api_key_id, days=None, headers=None)` -
  `GET /v1/detailed-usage/<api_key_id>`. Fine-grained request logs.

### UserService (`client.users`)

- `get_profile(headers)` - `GET /v1/user/profile`. Returns the authenticated profile.
- `update_profile(payload, headers)` - `PUT /v1/user/profile`. Update first/last
  name, timezone, language, or preferences.
- `get_user(user_id, headers)` - `GET /v1/user/<user_id>`. Fetch another user
  (requires admin privileges or appropriate scopes).

### AddressService (`client.addresses`)

- `seed_reference_data(headers=None)` - `GET /v1/address-seed`. Populates countries,
  states, and cities (public).
- `create_country(name, iso_code=None, headers=None)` - `POST /v1/country`.
  Admin-only country creation.
- `list_countries(headers=None)` - `GET /v1/country`. Fetch all countries.
- `get_country(country_id, headers=None)` - `GET /v1/country/<id>`. Returns a country
  with nested states.
- `update_country(country_id, name=None, iso_code=None, headers=None)` -
  `PATCH /v1/country/<id>`.
- `create_state(name, country_id, headers=None)` - `POST /v1/state`. Admin-only.
- `list_states_by_country(country_id, headers=None)` -
  `GET /v1/state/country/<country_id>`.
- `get_state(state_id, headers=None)` - `GET /v1/state/<id>`. Includes nested cities.
- `update_state(state_id, name=None, country_id=None, headers=None)` - `PATCH /v1/state/<id>`.
- `create_city(name, state_id, postal_code_prefix=None, headers=None)` - `POST /v1/city`.
- `list_cities_by_state(state_id, headers=None)` - `GET /v1/city/state/<state_id>`.
- `get_city(city_id, headers=None)` - `GET /v1/city/<id>`.
- `update_city(city_id, name=None, state_id=None, postal_code_prefix=None, headers=None)` -
  `PATCH /v1/city/<id>`.
- `create_address(...)` - `POST /v1/address`. Admin-only company address creation
  with support for `lat`, `lan`, `postal_code`, and `is_primary`.
- `get_company_address(headers=None)` - `GET /v1/address`. Fetch the authenticated
  company's address.

### AdminService (`client.admin`)

- `list_users(...)` - `GET /v1/admin/user` (or `/v1/super-admin/company/<id>/user`
  when `company_id` is provided). Supports pagination, status/role filters, search,
  date ranges, and sorting.
- `get_user(user_id, headers=None)` - `GET /v1/admin/user/<user_id>`.
- `get_company_system_metrics(company_id=None, headers=None)` -
  `GET /v1/admin/system-metric` or the super-admin variant.
- `get_audit_logs(...)` - `GET /v1/audit-log`. Filter by entity type, event type,
  risk level, and pagination.
- `get_system_configuration(headers=None)` - `GET /v1/config`. Reads configuration
  values (sensitive keys hidden from non super-admins).
- `upsert_system_configuration(...)` - `PATCH /v1/config`. Create or update a config entry.
- `force_password_reset(user_id, headers=None)` - `POST /v1/user/<id>/force-password-reset`.
- `impersonate_user(user_id, headers=None)` - `POST /v1/user/<id>/impersonate`.
- `update_user_status(user_id, status, reason=None, headers=None)` - `PATCH /v1/user/<id>/status`.
- `update_user_role(user_id, role, headers=None)` - `PATCH /v1/user/<id>/role`.

### AgentService (`client.agents`)

- `create_agent(payload, *, settings=None, headers=None)` - `POST /v1/agent` by default. When
  `settings` includes provider/model names the SDK transparently calls `POST /v1/sdk/agent`. Ensure
  the request includes `name` plus either ID-based fields or the name-based equivalents.
- `create_agent_with_provider_names(payload=None, *, settings=None, headers=None)` -
  Convenience wrapper around `POST /v1/sdk/agent`. Accepts the same `settings` keys as
  `/v1/sdk/settings` (provider/model names, optional overrides, credentials).
- `get_agent(agent_id, headers=None)` - `GET /v1/agent/<id>`. Public route.
- `list_agents(company_id=None, status=None, search=None, page=None, per_page=None, headers=None)` -
  `GET /v1/agent`.
- `update_agent(agent_id, payload, headers=None)` - `PUT /v1/agent/<id>`.
- `delete_agent(agent_id, headers=None)` - `DELETE /v1/agent/<id>` (soft delete).
- `restore_agent(agent_id, headers=None)` - `PATCH /v1/agent/<id>/restore`.
- `get_embed_code(agent_id, headers=None)` - `GET /v1/agent/<id>/embed-code`.
- `test_agent(agent_id, query=None, headers=None)` - `POST /v1/agent/<id>/test`.
- `get_agent_stats(agent_id, headers=None)` - `GET /v1/agent/<id>/stats`.
- `clone_agent(agent_id, name=None, llm_settings_id=None, headers=None)` -
  `POST /v1/agent/<id>/clone`.
- `fetch_widget_script(headers=None)` - `GET /widget.js`. Returns the public widget JavaScript.
- `render_test_page(body_html, headers=None)` - `POST /test`. Renders a test HTML snippet.

### SettingsService (`client.settings`)

- `create_settings(...)` - `POST /v1/settings`. Create settings with explicit provider/model IDs.
- `create_settings_with_provider_names(...)` - `POST /v1/sdk/settings`. Use provider/model names and
  optional overrides to let the API resolve IDs automatically.
- `get_settings(settings_id, headers=None)` - `GET /v1/settings/<id>`. Retrieve a settings record.
- `update_settings(settings_id, ..., headers=None)` - `PUT /v1/settings/<id>`. Update settings.
- Additional helpers mirror the full `/v1/settings` and `/v1/providers` API surface.

### AnalyticsService (`client.analytics`)

- `get_dashboard_overview(company_id=None, headers=None)` - `GET /v1/analytic/dashboard`.
- `get_agent_analytics(agent_id, start_date=None, end_date=None, headers=None)` -
  `GET /v1/analytic/agent/<agent_id>`.
- `get_agent_performance_comparison(agent_id, start_date=None, end_date=None, headers=None)` -
  `GET /v1/analytic/agent/<agent_id>/performance-comparison`.
- `get_conversation_analytics(conversation_id, headers=None)` -
  `GET /v1/analytic/conversation/<conversation_id>`.
- `get_lead_analytics(start_date=None, end_date=None, company_id=None, headers=None)` -
  `GET /v1/analytic/leads`.
- `get_usage_metrics(start_date=None, end_date=None, headers=None)` - `GET /v1/analytic/usage`.
- `search_documents(query, agent_id, limit=None, headers=None)` - `POST /v1/search/document`.
- `search_database(query, connection_id=None, headers=None)` - `POST /v1/search/database`.
- `trigger_system_metric_collection(headers=None)` - `POST /v1/system-metric`.
- `export_analytics(export_type, export_format, start_date=None, end_date=None, headers=None)` -
  `POST /v1/analytic/export`.
- `health_check(headers=None)` - `GET /health`. Public health probe.

### CompanyService (`client.companies`)

- `create_company(payload, logo_path=None, headers=None)` - `POST /v1/company`. Supports JSON
  or multipart form data.
- `list_companies(page=None, per_page=None, headers=None)` - `GET /v1/super-admin/company`.
- `get_company(headers=None)` - `GET /v1/company`.
- `get_company_statistics(company_id=None, days=None, headers=None)` -
  `GET /v1/company/statistics` or `/v1/company/<id>/statistics`.
- `list_deleted_companies(headers=None)` - `GET /v1/company/deleted`.
- `update_company(company_id, payload, logo_path=None, headers=None)` - `PUT /v1/company/<id>`.
- `patch_company(company_id, payload, headers=None)` - `PATCH /v1/company/<id>`.
- `delete_company(company_id, headers=None)` - `DELETE /v1/company/<id>`.
- `restore_company(company_id, headers=None)` - `PATCH /v1/company/<id>/restore`.
- `cascade_delete_company(company_id, delete_related=None, headers=None)` -
  `DELETE /v1/company/<id>/cascade-delete`.
- `get_related_data_summary(company_id, headers=None)` - `GET /v1/company/<id>/related-data`.
- `bulk_delete_companies(company_ids, headers=None)` - `DELETE /v1/company/bulk-delete`.
- `bulk_restore_companies(company_ids, headers=None)` - `PATCH /v1/company/bulk-restore`.

### DatabaseService (`client.databases`)

- `create_connection(name, url, database_type, agent_id, connection_params=None, headers=None)` -
  `POST /v1/database-connection`.
- `list_connections(params=None, headers=None)` - `GET /v1/database-connection`.
- `get_connection(connection_id, headers=None)` - `GET /v1/database-connection/<id>`.
- `update_connection(...)` - `PUT /v1/database-connection/<id>`.
- `patch_connection(connection_id, updates, headers=None)` - `PATCH /v1/database-connection/<id>`.
- `delete_connection(connection_id, headers=None)` - `DELETE /v1/database-connection/<id>`.
- `restore_connection(connection_id, headers=None)` - `PATCH /v1/database-connection/<id>/restore`.
- `list_deleted_connections(headers=None)` - `GET /v1/database-connection/deleted`.
- `test_connection(connection_id, headers=None)` - `POST /v1/database-connection/<id>/test`.
- `analyze_connection(connection_id, headers=None)` - `POST /v1/database-connection/<id>/analyze`.
- `analyze_multiple_connections(payload=None, headers=None)` - `POST /v1/database-connection/analyze`.
- `list_tables(connection_id, headers=None)` - `GET /v1/database-connection/<id>/table`.
- `get_table(table_id, headers=None)` - `GET /v1/database-connection/table/<table_id>`.
- `delete_table(table_id, headers=None)` - `DELETE /v1/database-connection/table/<table_id>`.
- `delete_tables_for_connection(connection_id, headers=None)` -
  `DELETE /v1/database-connection/<id>/table`.
- `restore_table(table_id, headers=None)` - `PATCH /v1/database-connection/table/<table_id>/restore`.
- `list_deleted_tables(headers=None)` - `GET /v1/database-connection/table/deleted`.
- `get_semantic_snapshot(connection_id, headers=None)` -
  `GET /v1/database-connection/<id>/semantic-snapshot`.
- `get_knowledge_graph(connection_id, headers=None)` -
  `GET /v1/database-connection/<id>/knowledge-graph`.
- `get_sample_queries(connection_id, headers=None)` -
  `GET /v1/database-connection/<id>/sample-queries`.
- `text_to_sql(connection_id, question, execute=None, result_limit=None, headers=None)` -
  `POST /v1/database-connection/<id>/text-to-sql`.
- `export_connection(connection_id, headers=None)` - `POST /v1/database-connection/export`.

### DocumentService (`client.documents`)

- `upload_documents(agent_id, file_paths=None, urls=None, url=None, metadata=None, headers=None)` -
  `POST /v1/document/upload`. Supports multipart files and JSON URL ingestion.
- `list_documents(page=None, per_page=None, status=None, headers=None)` - `GET /v1/document`.
- `list_deleted_documents(headers=None)` - `GET /v1/document/deleted`.
- `list_deleted_chunks(headers=None)` - `GET /v1/document/chunk/deleted`.
- `delete_document(document_id, headers=None)` - `DELETE /v1/document/<id>`.
- `restore_document(document_id, headers=None)` - `PATCH /v1/document/<id>/restore`.
- `delete_document_chunk(chunk_id, headers=None)` - `DELETE /v1/document/chunk/<chunk_id>`.
- `restore_document_chunk(chunk_id, headers=None)` - `PATCH /v1/document/chunk/<chunk_id>/restore`.
- `delete_document_chunks(document_id, headers=None)` - `DELETE /v1/document/<id>/chunk`.
- `restore_all_document_chunks(document_id, headers=None)` -
  `PATCH /v1/document/<id>/chunk/restore-all`.
- `bulk_delete_documents(document_ids, headers=None)` - `DELETE /v1/document/bulk-delete`.

### ConversationService (`client.conversations`) and MessageService (`client.messages`)

- `create_conversation(agent_id, title=None, metadata=None, max_context_length=None, headers=None)` -
  `POST /v1/conversation`.
- `list_conversations(page=None, per_page=None, headers=None)` - `GET /v1/conversation`.
- `list_conversations_for_entity(page=None, per_page=None, headers=None)` -
  `GET /v1/conversation/entity`.
- `list_deleted_conversations(headers=None)` - `GET /v1/conversation/deleted`.
- `list_conversation_messages(conversation_id, page=None, per_page=None, headers=None)` -
  `GET /v1/conversation/<id>/messages`.
- `delete_conversation(conversation_id, headers=None)` - `DELETE /v1/conversation/<id>`.
- `delete_conversation_messages(conversation_id, headers=None)` -
  `DELETE /v1/conversation/<id>/messages`.
- `restore_conversation(conversation_id, headers=None)` -
  `PATCH /v1/conversation/<id>/restore`.
- `restore_all_messages(conversation_id, headers=None)` -
  `PATCH /v1/conversation/<id>/message/restore-all`.
- `send_message(conversation_id, message, headers=None, stream=False, stream_url=None, stream_timeout=None, event_types=None, raw_events=False)` -
  `POST /v1/conversation/<id>/chat`. When `stream=True`, the method returns a `MessageStream`
  that yields `ChatEvent` instances from the Server-Sent Events channel (configure
  `stream_path_template` or pass `stream_url`).
- `stream_conversation_messages(conversation_id, headers=None, stream_url=None, stream_timeout=None, event_types=None, raw_events=False)` -
  `GET /v1/conversation/<id>/messages/stream`.
- `delete_message(message_id, headers=None)` - `DELETE /v1/message/<id>`.
- `restore_message(message_id, headers=None)` - `PATCH /v1/message/<id>/restore`.
- `list_deleted_messages(headers=None)` - `GET /v1/message/deleted`.

### LeadService (`client.leads`)

- `register_lead(payload, headers=None)` - `POST /v1/lead/register`. Public widget
  registration; payload includes agent ID, first/last name, email, phone, and
  optional consent flags.
- `create_lead(payload, headers=None)` - `POST /v1/lead`. Admin-created leads.
- `get_lead(lead_id, headers=None)` - `GET /v1/lead/<id>`.
- `list_company_leads(page=None, per_page=None, status=None, search=None, headers=None)` -
  `GET /v1/lead/company`.
- `update_lead(lead_id, payload, headers=None)` - `PUT /v1/lead/<id>`.
- `delete_lead(lead_id, headers=None)` - `DELETE /v1/lead/<id>`.

---

## Error Handling

All helper methods raise `KnowrithmAPIError` when the API returns a non-success
status code or when the request ultimately fails after retries. Inspect
`e.status_code`, `e.message`, and `e.response_data` for diagnostics.

```python
from knowrithm_py.dataclass.error import KnowrithmAPIError

try:
    client.messages.send_message(conversation_id, "Hi!")
except KnowrithmAPIError as exc:
    print(f"Request failed ({exc.status_code}): {exc.message}")
    print(exc.response_data)
```

---

## Support

- Documentation: [https://docs.knowrithm.org](https://docs.knowrithm.org)
- GitHub Issues: [https://github.com/Knowrithm/knowrithm-py/issues](https://github.com/Knowrithm/knowrithm-py/issues)
- Email: support@knowrithm.org

---

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.
