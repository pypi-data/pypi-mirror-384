# SRSR Python Client Roadmap

Ideas for future improvements to usability and robustness.

---

## Automatic Retry Logic on Registration Failure

Add configurable retry logic for transient registration failures.

**Considerations:**
- Retry count and backoff strategy (exponential?)
- When to retry vs. fail fast (distinguish transient vs. config errors?)
- Could add parameters: `retry_count`, `retry_delay`, `retry_backoff`
- Users can currently implement their own retry logic if needed

**Status:** Backlog idea, not planned for near term
