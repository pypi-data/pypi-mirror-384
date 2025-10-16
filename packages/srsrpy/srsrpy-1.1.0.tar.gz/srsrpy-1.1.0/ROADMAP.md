# SRSR Python Client Roadmap

Ideas for future improvements to usability and robustness.

---

## Code Quality Improvements

### Add type hints throughout
Modern Python (3.8+) should have type annotations. Currently missing on all methods.

### Add missing docstrings
Methods lacking documentation: `register()`, `deregister()`, `keep_alive()`

---

## Test Coverage Gaps (Medium Priority)

Missing test cases for:
- `keep_alive()` thread stopping conditions
- Registration response missing 'id' field
- Invalid address format exceptions
- Generic exceptions in heartbeat handler
- Non-200 status codes during registration (only 500 tested currently)

### Add pytest-cov to requirements
Enable coverage reporting in CI/local development

---

## Code Improvements (Lower Priority)

### Inconsistent internal naming
- `self.server_address` (registry address)
- `self.client_name` (service name)
- `self.client_address` (service address)

Should align with public parameter names for clarity.

### Port validation in `from_env()`
Doesn't validate dual-port specification until `register()` is called. Should fail fast.

### Thread safety in `deregister()`
`self.stop` is None until `register()` is called. Currently protected by `is_registered` check but fragile.

### Consider standard logging
Currently uses callback pattern for heartbeat errors. Could use stdlib logging instead.

---

## Automatic Retry Logic on Registration Failure

Add configurable retry logic for transient registration failures.

**Considerations:**
- Retry count and backoff strategy (exponential?)
- When to retry vs. fail fast (distinguish transient vs. config errors?)
- Could add parameters: `retry_count`, `retry_delay`, `retry_backoff`
- Users can currently implement their own retry logic if needed

**Status:** Backlog idea, not planned for near term
