# KeySec

KeySec provides configurable service and cryptography providers for Python applications.

## Configuration

KeySec reads the YAML file named by `KEYSEC_CONFIG`; if the environment variable is unset, it looks for `./keysec.yaml`.

The repository includes a credential-free root `keysec.yaml` with a default local AES-GCM provider and a relative key-file path. Only that crypto provider is active by default; a commented Azure Key Vault service-provider example is included for reference. Run `keysec generate-key` from the repository root before using the default crypto provider. The generated `keysec.key` is ignored by Git. Put credentials or other sensitive settings in a separate configuration file and select it with `KEYSEC_CONFIG`; do not add them to the tracked default file.

The file is rooted at `keysec` and has `services` and `crypto` sections. Each section maps configured provider names to an implementation `type` and provider-specific `settings`, and may declare the default provider name:

```yaml
keysec:
  audit_logging:
    enabled: true
    file: ./audit.log
  services:
    default: vault
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
  crypto:
    default: local
    providers:
      local:
        type: aes-gcm
        settings:
          key_file: ./local.key
```

Provider names are the values selected by API calls. The `type` identifies the in-process implementation. Do not store raw credentials, encryption keys, or secret values in this file. Azure Key Vault uses the Azure identity available to the process.

The `services` and `crypto` categories each have a `cipher_prefix` for encrypted provider-setting values. Both default to `ENC`; a provider's `settings.cipher_prefix` overrides its category value. This is separate from the service `secret_prefix` used by `get_secret`, which defaults to `KEY`.

Configuration string values support `${NAME}` environment-variable references. KeySec expands references recursively in YAML values, including nested provider settings and lists; mapping keys and non-string values are left unchanged. Substituted text is treated literally and is not expanded again. If a referenced variable is unset, configuration loading fails with an explicit error. For example:

```yaml
keysec:
  services:
    providers:
      vault:
        type: azure-key-vault
        settings:
          client_secret: ${SEC_VAR}
```

Audit logging is disabled by default. To enable it, set `keysec.audit_logging.enabled` to `true` and optionally choose a log file path; the path also supports environment-variable expansion. Audit entries cover secret retrieval and crypto operations, recording operation, provider, timestamp, and outcome only. Secret names and values, plaintext, ciphertext, key material, and exception text are excluded. The file rotates daily. If an audit write fails, KeySec reports the logging failure through standard Python logging and continues the operation.

## Public API

`KeySec` loads the configuration from `KEYSEC_CONFIG` or `./keysec.yaml`. The `provider` argument selects a configured name from the relevant section; omitting it uses that section's default:

```python
from keysec import KeySec

keysec = KeySec()

# Retrieve a string secret using keysec.services.default ("vault").
database_password = keysec.get_secret("KEY(database-password)")

# Look up a crypto provider and use its crypto operations directly.
crypto = keysec.get_provider("local", provider_type="crypto")
key_path = crypto.generate_key()
ciphertext = crypto.encrypt("Hello, 世界")
plaintext = crypto.decrypt(ciphertext)
```

`get_secret` returns a string. `get_provider(name, provider_type=None)` returns an instantiated provider configured by name. `provider_type` may be `"service"` or `"crypto"`; when omitted, the name must exist in only one category, otherwise lookup raises an ambiguity error. Passing `name=None` with an explicit provider type selects that category's configured default. Unknown names and categories raise configuration errors. Crypto-provider instances expose `encrypt`, `decrypt`, and `generate_key`; `KeySec` itself does not.

Service providers use `KEY` as the default wrapper for secret identifiers. Existing unwrapped identifiers are also accepted. To use a different prefix for a particular service provider, set `secret_prefix` in that provider's `settings` and use the matching wrapper when calling `get_secret`:

```yaml
keysec:
  services:
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
          secret_prefix: AZURE
```

With that override, call `keysec.get_secret("AZURE(database-password)")`; without it, use `keysec.get_secret("KEY(database-password)")`.

## Command-Line Interface

The package installs a `keysec` command with these operations:

```text
keysec get-secret SECRET [--provider NAME]
keysec generate-key [--provider NAME] [--output PATH]
keysec encrypt [VALUE] [--provider NAME]
keysec decrypt [VALUE] [--provider NAME]
keysec list-providers
keysec list-available-providers
```

`get-secret` uses the default service provider unless `--provider` names another configured service provider. The secret argument may be a plain secret name or a wrapped reference such as `KEY(database-password)`. The command prints the retrieved secret value to standard output; take care when running it in terminals or environments that capture command output.

`generate-key` uses the default crypto provider unless `--provider` names another configured crypto provider. If `--output` is omitted, the selected provider's configured `key_file` path is used. The command creates the key file and prints only its path, never the key bytes. Existing files are not overwritten.

`encrypt` and `decrypt` use the default crypto provider or a named provider. Supply `VALUE` positionally, or omit it to read the value from standard input:

```sh
keysec encrypt 'Hello, world'
printf %s 'Hello, world' | keysec encrypt
keysec decrypt 'ENC(ciphertext)'
printf %s 'ENC(ciphertext)' | keysec decrypt
```

Positional plaintext may be recorded in shell history or visible in process arguments. Decryption prints plaintext to standard output, which may be captured by terminal logs or shell redirection; use stdin and handle output accordingly when values are sensitive.

`list-providers` shows configured service and crypto provider categories, names, and implementation types without displaying settings. `list-available-providers` shows provider implementation types registered with the runtime API and does not require a configuration file.

Configured commands load the file named by `KEYSEC_CONFIG`, or `./keysec.yaml` when that variable is unset. Errors are written to standard error and return a non-zero exit status. Run `keysec --help` or `keysec COMMAND --help` for command examples.

## Packaging Builds

The `.ci/` directory contains native-host build scripts for the `keysec` command. They require Python 3.10 or newer. On the first run, scripts create `.ci/.venv` and install the needed build tools; network access is required for those installations. Build outputs are written to `dist/`.

The Linux executable builder also requires `objdump` from the system's `binutils` package.

Build a wheel:

```powershell
.\.ci\build-wheel-windows.cmd
```

```sh
./.ci/build-wheel-unix.sh
./.ci/build-wheel-macos-arm64.sh
```

Build a standalone, one-file executable with PyInstaller:

```powershell
.\.ci\build-executable-windows.cmd
```

```sh
./.ci/build-executable-unix.sh
./.ci/build-executable-macos-arm64.sh
```

Run each script on its native target: Windows, Linux, or macOS ARM64. The macOS ARM64 scripts reject other operating systems and architectures. The wheel is built from the existing package metadata and is platform-independent; the executable is specific to the host platform and Python runtime.

## Azure Key Vault

The built-in `azure-key-vault` service provider requires an HTTPS `vault_url`. If `tenant_id`, `client_id`, `client_secret`, and `certificate_path` are all omitted, it uses Azure's `DefaultAzureCredential` chain; for local development, sign in with the Azure CLI. In deployed environments, use the workload's managed or federated identity. Grant the selected identity permission to read secrets from the configured vault (for example, the Key Vault Secrets User data-plane role when using Azure RBAC).

For service-principal authentication, set `tenant_id`, `client_id`, and either or both credential fields directly under the provider's `settings`. Prefer `${NAME}` to expand a protected environment variable to its value. An expanded `client_secret` is passed directly to Azure authentication:

```yaml
keysec:
  services:
    default: vault
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
          tenant_id: 00000000-0000-0000-0000-000000000000
          client_id: 11111111-1111-1111-1111-111111111111
          client_secret: ${SEC_VAR}
```

For backward compatibility, an unwrapped literal `client_secret` is still interpreted as the name of an environment variable containing the secret. Provision that variable through the deployment platform's protected environment or secret-injection mechanism, not in YAML:

```yaml
keysec:
  services:
    default: vault
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
          tenant_id: 00000000-0000-0000-0000-000000000000
          client_id: 11111111-1111-1111-1111-111111111111
          client_secret: KEYSEC_AZURE_CLIENT_SECRET
```

Alternatively, store the client secret as a wrapped ciphertext. First generate and securely provision the default crypto provider's key separately, then configure its key-file path in the main `keysec` YAML. Use that provider (with the same key and effective crypto cipher prefix) to encrypt the client-secret value. Put the resulting wrapped string in the Azure provider settings:

```yaml
keysec:
  services:
    cipher_prefix: ENC
    default: vault
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
          tenant_id: 00000000-0000-0000-0000-000000000000
          client_id: 11111111-1111-1111-1111-111111111111
          client_secret: ENC(<base64-payload>)
  crypto:
    default: local
    providers:
      local:
        type: aes-gcm
        settings:
          key_file: /run/secrets/keysec-encryption.key
```

The key file and the default crypto provider's bootstrap settings must remain available as plaintext configuration; provider-setting decryption cannot bootstrap its own key. When `client_secret` uses its effective service cipher prefix, KeySec decrypts it and passes the result directly to Azure authentication. If it is unwrapped, KeySec preserves the existing environment-variable-name behavior. A wrapped value that fails decryption is an error and is never retried as an environment-variable name.

Alternatively, set `certificate_path` to an unencrypted local certificate file that includes its private key:

```yaml
keysec:
  services:
    default: vault
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
          tenant_id: 00000000-0000-0000-0000-000000000000
          client_id: 11111111-1111-1111-1111-111111111111
          certificate_path: /run/secrets/keysec-service-principal.pem
```

If both `client_secret` and `certificate_path` are supplied, the certificate is used and the client-secret environment variable is not read. The certificate may be PEM or PKCS#12 and must contain an RSA private key. The file must be readable by the KeySec process; absolute paths are recommended (relative paths are resolved from the process working directory). Password-protected certificates are not supported. Service-principal settings are validated explicitly; if the selected credential is unavailable, KeySec reports an error instead of falling back to ambient identity.

## Manual Azure connectivity test

The automatic test suite uses mocks and local test doubles; it does not connect to remote services. The one live Azure Key Vault check is in `tests/manual_azure_key_vault_integration.py` and is not included in default test discovery. Configure `KEYSEC_CONFIG` to a YAML file whose default service provider has type `azure-key-vault`, and ensure the current Azure identity can read the secret named by `KEYSEC_TEST_SECRET_NAME`. Run it explicitly from the repository root:

```sh
KEYSEC_CONFIG=/path/to/keysec.yaml \
KEYSEC_TEST_SECRET_NAME=connectivity-check \
python -m unittest discover -s tests -p manual_azure_key_vault_integration.py -v
```

The test requires both environment variables, verifies that the configured default is Azure Key Vault, and uses the identity mode configured for that provider. Never prints or includes the retrieved secret value in its assertions.

## Adding a service provider

Applications can register service providers in process. Provider implementations receive the configured provider name and its settings:

```python
from keysec.providers.service import ServiceProvider, register_service_provider


class EnvironmentServiceProvider(ServiceProvider):
    def get_secret(self, secret: str) -> str:
        # Resolve the secret using the application's chosen service.
        ...


register_service_provider("environment", EnvironmentServiceProvider)
```

The configuration entry's `type` must match the registration identifier, and callers select the configured entry by its name. Provider implementations should not log secret values or credentials.

## Adding a crypto provider

Crypto providers use the same registration pattern while implementing the separate `CryptoProvider` contract:

```python
from keysec.providers.crypto import CryptoProvider, register_crypto_provider


class CustomCryptoProvider(CryptoProvider):
    def encrypt(self, plaintext: str, key_file: str | None = None) -> str:
        encrypted = ...
        return self.wrap_ciphertext(encrypted)

    def decrypt(self, ciphertext: str, key_file: str | None = None) -> str:
        encoded = self.unwrap_ciphertext(ciphertext)
        ...

    def generate_key(self, output_path: str | None = None) -> str:
        ...


register_crypto_provider("custom-crypto", CustomCryptoProvider)
```

Set the crypto provider entry's `type` to `custom-crypto`; callers pass its configured name to `KeySec.get_provider(name, provider_type="crypto")`. The built-in `aes-gcm` type is registered automatically.

Crypto providers use `ENC` as the default output wrapper. Set a provider's `cipher_prefix` setting to override it. Custom crypto providers should use `wrap_ciphertext` for encrypted output and `unwrap_ciphertext` before decrypting; the latter leaves existing unwrapped values unchanged.

For example, set the override alongside the provider's other settings:

```yaml
keysec:
  crypto:
    providers:
      local:
        type: aes-gcm
        settings:
          key_file: ./local.key
          cipher_prefix: SEALED
```

## AES-GCM keys and ciphertext

The built-in AES-GCM provider uses AES-256-GCM. Its `key_file` setting names a binary 32-byte key file. Key generation can write to that configured path or to a call-level output path; it fails rather than overwriting an existing file. On POSIX systems the file is created with owner-only read/write permissions. Protect and back up the key file separately from ciphertext.

```python
from keysec.providers.crypto import AESGCMProvider

provider = AESGCMProvider("local", {"key_file": "./local.key"})
key_path = provider.generate_key()
ciphertext = provider.encrypt("Hello, 世界")
plaintext = provider.decrypt(ciphertext)
```

AES-GCM ciphertext is returned as `ENC(<payload>)` by default; `<payload>` is URL-safe Base64 of the 12-byte nonce followed by AES-GCM ciphertext and its 16-byte authentication tag. Set `cipher_prefix` in that provider's `settings` to choose another wrapper prefix. The nonce is freshly generated for each encryption. UTF-8 is used for text input and output. Decryption accepts the configured wrapped form and rejects malformed or unauthenticated ciphertext.
