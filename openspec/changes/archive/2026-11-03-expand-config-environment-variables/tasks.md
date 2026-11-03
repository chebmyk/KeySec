# Tasks

## 1. Configuration Environment Expansion

- [x] 1.1 Add one-pass recursive `${NAME}` substitution for parsed YAML string values in `src/keysec/config.py`; verify whole-value and embedded references, nested mappings/lists, unchanged keys and non-string values, literal replacement contents, and explicit unset-variable errors with focused `test_config.py` tests.
- [x] 1.2 Document `${NAME}` configuration interpolation, its recursive value-only scope, unset-variable errors, and an Azure `client_secret` example in `README.md`; verify the example matches the documented compatibility behavior.

## 2. Azure Client Secret Integration

- [x] 2.1 Preserve the origin of environment-expanded strings through provider configuration and pass expanded Azure `client_secret` values directly to authentication; verify focused Azure provider tests cover expanded values, legacy environment-variable names, encrypted values, and certificate precedence.
- [x] 2.2 Add or update a facade-level configuration test proving `client_secret: ${SEC_VAR}` reaches Azure authentication as the substituted value; verify it passes without making a second environment-variable lookup.

## 3. Integrated Validation

- [x] 3.1 Run the full unit test suite and strict OpenSpec change validation; verify all tests pass, all required artifacts validate, and `git diff --check` reports no whitespace errors.
