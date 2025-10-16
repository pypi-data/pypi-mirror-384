## [v0.1.4](https://pypi.org/project/amsdal_ml/0.1.4/) - 2025-10-15

### Fixed retriever initialization in K8s environments

- Fixed lazy initialization of OpenAIRetriever to ensure env vars are loaded
- Added missing env parameter to stdio_client for non-persistent sessions
- Environment variables now properly passed to MCP stdio subprocesses
- Updated README.md to be production-ready
- Added RELEASE.md with step-by-step release guide