# Documentation

This directory describes the repository as it is implemented today. It complements the root README with implementation-level detail.

- [Architecture](architecture.md) explains the application boundaries, data ownership, and request flow.
- [API reference](api.md) lists the current HTTP interface, authentication, request shapes, and common responses.
- [Ingestion and retrieval](ingestion-and-rag.md) describes supported sources, background ingestion, grounding, and citation handling.
- [Testing](testing.md) explains the isolated test suite, the opt-in live smoke test, and the test log.
- [Operations](operations.md) records local setup, data locations, and the known implementation limitations.

The supplied assignment brief is retained unchanged in `refrence_docs/`. The directory name is preserved to avoid breaking existing references.
