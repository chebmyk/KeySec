# Design

## Context

See proposal.md for motivation and specs/secret-retrieval/spec.md for the authentication behavior contract. `AzureKeyVaultProvider` currently validates `vault_url`, constructs `DefaultAzureCredential` in `get_secret`, and closes the credential and secret client after each request. The `azure-identity` dependency is already present. Provider settings are mappings loaded from YAML, and the existing documented policy keeps raw credentials out of that file.

## Goals / Non-Goals

**Goals:**
- Keep the existing ambient-identity path unchanged when explicit authentication is absent.
- Select a service-principal credential source explicitly and fail rather than falling back when it is misconfigured.
- Keep secret values out of YAML and diagnostics.

**Non-Goals:**
- Add certificate-password support, a new credential-storage service, or secret decryption through crypto providers.
- Change secret retrieval, provider registration, or KeySec facade APIs.
- Add an automatic test that connects to Azure.

## Decisions

- **Use flat provider settings for service-principal authentication.** Read `tenant_id`, `client_id`, `client_secret`, and `certificate_path` directly from the Azure provider's settings, without an `authentication` mapping or a separate auth `type`. If all four are absent, construct `DefaultAzureCredential` as today. If any service-principal setting is present, require both identity IDs and at least one credential source. A separate Azure service-provider implementation was considered, but rejected because only credential construction differs from existing retrieval behavior.

- **Interpret `client_secret` as an environment-variable name and prefer the certificate when both sources are configured.** Resolve the variable only when `certificate_path` is absent. If the certificate path is present, use it and do not read the client-secret variable. An unset selected environment variable is an explicit configuration error, not a reason to fall back to ambient credentials. Storing the raw value in YAML or decrypting it through a crypto provider was considered, but rejected to preserve the no-raw-credentials-in-configuration contract.

- **Use a local unencrypted certificate file without a password setting.** `certificate_path` identifies the certificate file available to the process. Do not copy certificate contents or private key material into YAML, and do not support password-protected certificates in this change. Validate the selected path and surface missing or unreadable files without exposing contents.

- **Keep credential construction behind the existing provider.** Add a small private credential-selection path used by `get_secret`; continue passing the resulting credential to `SecretClient` and closing both resources in `finally`. Translate Azure SDK failures to the existing safe `SecretRetrievalError` contract, preserving causes without including credentials in messages.

- **Keep tests offline and document credential precedence.** Unit tests mock Azure credential classes and the secret client, covering ambient, client-secret, certificate, certificate-precedence, incomplete settings, missing selected environment variables/files, resource closure, and safe errors. Update the Azure setup documentation with flat service-principal settings and environment-variable provisioning. The live connectivity test remains manually invoked only.

## Risks / Trade-offs

- [Environment variables may be exposed through process inspection or operational tooling] → Document use of the deployment platform's protected environment/secret injection and never log the value.
- [Certificate paths may differ across deployment environments or point to sensitive files] → Require a local path accessible to the process, document file access and protection, and fail safely when unavailable.
- [Azure SDK credential behavior can vary by certificate format] → Use the installed `azure-identity` credential API and exercise credential construction with mocks; keep any live verification opt-in.
- [Changing an existing Azure provider's auth construction could regress ambient identity] → Preserve the no-auth-settings path and retain explicit mocked coverage for it.

## Migration Plan

No migration is required: existing provider configurations without service-principal settings continue to use `DefaultAzureCredential`. To opt in, add `tenant_id`, `client_id`, and either `client_secret` (the environment-variable name) or `certificate_path` directly under the provider's `settings`. If both sources are present, the certificate is selected. Rollback consists of removing these service-principal settings to restore ambient identity.
