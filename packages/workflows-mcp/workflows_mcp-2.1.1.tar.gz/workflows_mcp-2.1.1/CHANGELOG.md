# Changelog

All notable changes to this project will be documented in this file.

## [2.1.1](https://github.com/qtsone/mcp-workflows/compare/v2.1.0...v2.1.1) (2025-10-16)


### Bug Fixes

* **workflows:** correct PopulateTemplate output reference in commit-and-push workflow ([cefee15](https://github.com/qtsone/mcp-workflows/commit/cefee151a3fd8965635518e327e8891d764ac0f1))

# [2.1.0](https://github.com/qtsone/mcp-workflows/compare/v2.0.0...v2.1.0) (2025-10-14)


### Features

* rename BashCommand to shell ([3e78d68](https://github.com/qtsone/mcp-workflows/commit/3e78d68a8420d36c51827106e8130e0398b41b1e))

# [2.0.0](https://github.com/qtsone/mcp-workflows/compare/v1.2.0...v2.0.0) (2025-10-13)


### Bug Fixes

* add blank line for improved readability in conftest.py ([852ec66](https://github.com/qtsone/mcp-workflows/commit/852ec66fbbb5dce92f0d3a3c38b2846be3e2776a))
* add missing comma for continue-on-error alias in ShellInput ([6eef6d4](https://github.com/qtsone/mcp-workflows/commit/6eef6d4a29bc7e0896103f59b3a9df730b8b0f7d))
* add missing newline in setup_test_environment fixture for clarity ([61f0eee](https://github.com/qtsone/mcp-workflows/commit/61f0eee48f28641ecfe09203e95289568eb15ee1))
* add session fixture to initialize MCP server for integration tests ([979f652](https://github.com/qtsone/mcp-workflows/commit/979f652754d87a183e1088e7c8a63216fcdf684e))
* correct WorkflowRegistry API call in session fixture ([b4f47f2](https://github.com/qtsone/mcp-workflows/commit/b4f47f2031cf470195e53235fb39f129e753b9f4))
* Normalize test method name for environment variable expansion ([b6c470f](https://github.com/qtsone/mcp-workflows/commit/b6c470fe8f85f7e58b8b6bc922216258c92bc078))
* Refactor condition checks in YAML workflows to use 'in' operator ([cbdc662](https://github.com/qtsone/mcp-workflows/commit/cbdc662164e98ace72a9245823659ba734af2829))
* reorder security checks in validate_output_path ([a3e37cb](https://github.com/qtsone/mcp-workflows/commit/a3e37cbaca7b54c8ef19461716def8c4a212cad2))
* resolve test failures in PR [#2](https://github.com/qtsone/mcp-workflows/issues/2) ([52b5c8c](https://github.com/qtsone/mcp-workflows/commit/52b5c8ce060619f127cad3ffe02b8c831b99df20))
* resolve WorkflowRegistry API error and skip slow tests in CI ([54021fb](https://github.com/qtsone/mcp-workflows/commit/54021fb9aca60419ec34502c2f0aaa5b10637e69)), closes [#2](https://github.com/qtsone/mcp-workflows/issues/2)
* restore global executor after checkpoint tests to prevent interference ([b82e91e](https://github.com/qtsone/mcp-workflows/commit/b82e91e46cbd948519ec1c150efaeebcbb53e0da)), closes [#2](https://github.com/qtsone/mcp-workflows/issues/2)
* simplify session fixture - clear and reload workflows ([c835373](https://github.com/qtsone/mcp-workflows/commit/c8353738a3c59033371cf290ffa2e0465bb3c4e6))


### Features

* Add parallel execution configuration and enhance file handling in workflows ([95e5b4f](https://github.com/qtsone/mcp-workflows/commit/95e5b4f97f4ec5130e46a305a5442fd9d180757c))
* Add TDD workflow for documentation and deployment readiness ([1454272](https://github.com/qtsone/mcp-workflows/commit/145427202ee7da81f373bcca1df53faf668609ac))
* allow CI to continue on mypy type checking errors ([3fcb02c](https://github.com/qtsone/mcp-workflows/commit/3fcb02c1d0e2e217ec9e2642e7a39823e5e5e17c))
* Enhance output handling and dynamic field support across workflow blocks ([26f8175](https://github.com/qtsone/mcp-workflows/commit/26f81755c07f9463c31533b15aa2814cb64fa8ef))
* **git:** add LLM-powered commit message generation mode ([bb8f9f4](https://github.com/qtsone/mcp-workflows/commit/bb8f9f4f1fe3f04ceb2d0abd5f7c0a5f0e5b9683))
* implement pause checkpointing in workflow execution ([fa794fc](https://github.com/qtsone/mcp-workflows/commit/fa794fc50b3e6db772deb76fc40f5d282dc41a8b))
* optimize list_workflows API to reduce MCP calls by 50% ([89e09a9](https://github.com/qtsone/mcp-workflows/commit/89e09a937da37d5e9bbe332fb03da0c031bd7c62))
* Refactor custom output handling in tests and workflows ([c796b98](https://github.com/qtsone/mcp-workflows/commit/c796b9807241095893451016377a80ec973e5e58))
* Refactor variable resolution syntax to use new namespace structure ([ea710cc](https://github.com/qtsone/mcp-workflows/commit/ea710cc70d93dfc7b0002efc48896f931560cae1))
* standardize continue-on-error semantics (GitHub Actions standard) ([c71dbce](https://github.com/qtsone/mcp-workflows/commit/c71dbce4dfc9f640f7acba2d2c2cadc718c2d929))
* Update condition checks to use exit codes for command validation and installation logic ([9f79194](https://github.com/qtsone/mcp-workflows/commit/9f791943c3f877c73297af81ac08ce69af46c383))


### BREAKING CHANGES

* YAML workflows must use continue-on-error (not check_returncode)

🤖 Generated with Claude Code

# [1.2.0](https://github.com/qtsone/mcp-workflows/compare/v1.1.1...v1.2.0) (2025-10-09)


### Features

* Add integration and unit tests for pause/resume functionality ([5287e35](https://github.com/qtsone/mcp-workflows/commit/5287e3542dd6a20582b224d4361a5be256b1f9e8))

## [1.1.1](https://github.com/qtsone/mcp-workflows/compare/v1.1.0...v1.1.1) (2025-10-08)


### Bug Fixes

* **pyproject:** add author ([c5bc7c5](https://github.com/qtsone/mcp-workflows/commit/c5bc7c5a90df81f7419ece7237cf4545e7ed7405))
* update publish workflow and pyproject for dynamic versioning ([9614904](https://github.com/qtsone/mcp-workflows/commit/961490474aa32726dd0b2b508aea7117fc285704))

# [1.1.0](https://github.com/qtsone/mcp-workflows/compare/v1.0.0...v1.1.0) (2025-10-08)


### Features

* refactor documentation ([2ddde3f](https://github.com/qtsone/mcp-workflows/commit/2ddde3fb80c181d2b36e37491d7a31bbb0c3e0de))

# 1.0.0 (2025-10-08)


### Bug Fixes

* skipped blocks ([8c7b9ad](https://github.com/qtsone/mcp-workflows/commit/8c7b9ad6ad3b563378ff9a00bd73cbbb07033bf5))


### Features

* add custom outputs ([acbe0ca](https://github.com/qtsone/mcp-workflows/commit/acbe0caef1742e086a541d670dfe842d2c2e9a86))
* Add example workflows and templates for various use cases ([ecc2f17](https://github.com/qtsone/mcp-workflows/commit/ecc2f177ab7a0bf3bb16ece7f3ee478a29390220))
* Add Next Steps document for MCP Testing and Phase 3 Planning ([0dfdfd7](https://github.com/qtsone/mcp-workflows/commit/0dfdfd7d110df84f02e9463ae11eb3abaa9a6c96))
* add semantic release configuration ([257c76c](https://github.com/qtsone/mcp-workflows/commit/257c76c5afc93fa6baaff5c129b7a79e83609a6a))
* add tools support ([9462d90](https://github.com/qtsone/mcp-workflows/commit/9462d904b049c12a29c49ac7f96aadaf07e0e21c))
* Bump version to 0.3.1 in project files ([4391618](https://github.com/qtsone/mcp-workflows/commit/4391618c3d0502ad2c98bfe98a63856be98ebbd3))
* Complete Phase 0 - MCP Server Integration ([34d34c9](https://github.com/qtsone/mcp-workflows/commit/34d34c9d17b574fce6139e6b6112698a39dde9f3))
* Complete Phase 1 - YAML Workflow Loading System ([95b5579](https://github.com/qtsone/mcp-workflows/commit/95b5579aeadb9395735faf9f906008dd16e8b979))
* Enhance documentation and testing for Phase 2.1 Shell block and validate example workflows ([e94c810](https://github.com/qtsone/mcp-workflows/commit/e94c8101ff50bb9923497746d154f599ba2c5910))
* Implement Shell block (Phase 2.1) ([ea05f93](https://github.com/qtsone/mcp-workflows/commit/ea05f93409aef0f07aa9117a238c772c8fcf6699))
* Implement core workflow engine components ([55ccb07](https://github.com/qtsone/mcp-workflows/commit/55ccb07c7f874968a01ef076c6f4231d78a9fee5))
* **phase 2.1:** Add jinja2 and markupsafe dependencies to project ([70c3197](https://github.com/qtsone/mcp-workflows/commit/70c319774f408d09548e02177def79d6084ee769))
* **phase-0:** Implement variable resolution and conditional evaluation system ([3d6ba34](https://github.com/qtsone/mcp-workflows/commit/3d6ba345f9e49ba2dbebbc2a1fa1c5d901a07a1c))
