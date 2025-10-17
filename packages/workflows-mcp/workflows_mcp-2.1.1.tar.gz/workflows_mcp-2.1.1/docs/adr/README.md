# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the workflows_mcp project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## ADR Process

1. **Proposal**: Create a new ADR with status "Proposed"
2. **Discussion**: Review with stakeholders and iterate
3. **Decision**: Update status to "Accepted" or "Rejected"
4. **Implementation**: Reference ADR in code and documentation
5. **Superseding**: If a decision is replaced, update status to "Superseded" and link to new ADR

## ADR Format

Each ADR follows a standard template:

- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Date**: Decision date
- **Context**: Problem statement and background
- **Decision Drivers**: Key factors influencing the decision
- **Considered Options**: Alternative approaches evaluated
- **Decision Outcome**: Chosen option with justification
- **Consequences**: Positive and negative impacts
- **Pros and Cons**: Detailed analysis of each option

## Index of ADRs

- [ADR-001: Executor Pattern Redesign](ADR-001-executor-pattern-redesign.md) - Transition from mutable WorkflowBlock to stateless BlockExecutor pattern
- [ADR-002: Checkpoint Strategy](ADR-002-checkpoint-strategy.md) - In-memory checkpoint store for pause/resume and crash recovery
- [ADR-003: Security Model](ADR-003-security-model.md) - Security classification and capability flags for workflow blocks

## Creating a New ADR

1. Copy the template from an existing ADR
2. Number it sequentially (ADR-XXX)
3. Use a descriptive kebab-case filename
4. Follow the standard format
5. Update this README index
6. Submit for review with status "Proposed"

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
