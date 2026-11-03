# Tasks

## 1. Azure service-principal authentication

- [x] 1.1 Simplify `AzureKeyVaultProvider` service-principal settings to flat `tenant_id`, `client_id`, `client_secret`, and `certificate_path` fields; treat `client_secret` as an environment-variable name, use the certificate when both credential sources are supplied, preserve ambient identity when none are supplied, and verify validation, precedence, no-fallback behavior, resource closure, and safe failures with mocked credential/client tests.
- [x] 1.2 Update Azure Key Vault documentation with flat service-principal settings, certificate precedence, environment-variable provisioning, and certificate-file constraints; verify the documented examples match the implementation and focused provider tests.

## 2. Integration verification

- [x] 2.1 Run the complete automatic test suite and verify Azure auth coverage remains mocked/offline and the manual live-service test is not discovered by the default command.
