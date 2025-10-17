# ADR-003: Security Model

**Status**: Accepted
**Date**: 2025-10-14
**Deciders**: Development Team
**Technical Story**: Executor security classification system

## Context and Problem Statement

Workflow blocks execute arbitrary code including shell commands, file operations, and network requests. Without a security model, malicious or poorly-written workflows could:

- Execute dangerous shell commands
- Delete or modify critical files
- Access sensitive data
- Make unauthorized network requests
- Consume excessive system resources

The system needs security boundaries that:
- **Classify executor risk levels**: Clear categorization of security implications
- **Enable security audits**: Easy identification of privileged operations
- **Support third-party plugins**: Security review of external executors
- **Follow least privilege**: Grant minimal permissions required
- **Remain extensible**: Support future runtime enforcement

The security model must balance protection with usability, avoiding over-engineering while establishing clear boundaries for future enhancement.

## Decision Drivers

- **Risk Mitigation**: Prevent malicious workflow execution
- **Plugin Security**: Audit third-party executors before use
- **Least Privilege**: Grant minimal required permissions
- **Clear Boundaries**: Obvious security classification per executor
- **Auditability**: Easy security review and monitoring
- **Extensibility**: Support future permission systems
- **Usability**: Don't hinder legitimate use cases
- **Performance**: Minimal runtime overhead

## Considered Options

### Option 1: No Security Model

Trust all executors and workflows:
- No classification or restrictions
- Simple implementation
- Complete user responsibility

### Option 2: Sandboxed Execution

Heavy isolation for all executors:
- Docker containers per block
- Restricted system calls (seccomp)
- Network isolation
- Resource limits (cgroups)

### Option 3: Security Classification with Capabilities (Chosen)

Classify executors by security level with capability flags:
- Three security levels (SAFE, TRUSTED, PRIVILEGED)
- Capability flags per executor (read_files, write_files, execute_commands, etc.)
- Documentation-only enforcement initially
- Foundation for future runtime enforcement

### Option 4: Permission-Based System

Android-style permission system:
- Runtime permission prompts
- User grants/denies per workflow
- Fine-grained permission model
- Persistent permission storage

## Decision Outcome

Chosen option: **Security Classification with Capabilities**, because it:

1. **Provides clear boundaries**: Security implications obvious at design time
2. **Enables auditing**: Security review before deployment
3. **Balances simplicity with protection**: Not over-engineered for MVP
4. **Extensible architecture**: Foundation for runtime enforcement
5. **Minimal overhead**: Documentation-only, no runtime cost
6. **Plugin-friendly**: Third-party executors declare security requirements

The classification system establishes architectural boundaries while deferring enforcement complexity to future phases when requirements are clearer.

### Positive Consequences

- ✅ **Clear Security Boundaries**: Obvious which executors are dangerous
- ✅ **Audit Trail**: Security review during executor development
- ✅ **Plugin Security**: Third-party executors declare capabilities
- ✅ **Developer Awareness**: Security implications visible in code
- ✅ **Extensible Foundation**: Easy to add runtime enforcement later
- ✅ **Zero Performance Impact**: Documentation-only initially
- ✅ **Simple Implementation**: Minimal code complexity
- ✅ **Gradual Enhancement**: Can add enforcement incrementally

### Negative Consequences

- ⚠️ **Not Enforced**: Runtime violations possible (documentation-only)
- ⚠️ **Requires Discipline**: Developers must classify executors correctly
- ⚠️ **Limited Protection**: No actual prevention of malicious workflows
- ⚠️ **Audit Burden**: Manual security review required
- ⚠️ **False Sense of Security**: Classification doesn't prevent execution

## Pros and Cons of the Options

### Option 1: No Security Model

**Good:**
- Simplest implementation
- Zero complexity
- No performance overhead
- No false sense of security

**Bad:**
- No protection against malicious workflows
- Cannot audit third-party plugins
- No security boundaries
- Complete user responsibility
- Difficult to add security later

### Option 2: Sandboxed Execution

**Good:**
- Strong isolation guarantees
- Prevents malicious execution
- Fine-grained resource control
- Industry-standard approach (containers)

**Bad:**
- Extremely complex implementation
- Significant performance overhead (container startup)
- External dependencies (Docker, runc)
- Breaks legitimate use cases (filesystem access)
- Overkill for most workflows
- Difficult to test and maintain

### Option 3: Security Classification with Capabilities (Chosen)

**Good:**
- Clear security boundaries
- Enables audit trail
- Extensible to enforcement
- Simple implementation
- No performance impact
- Gradual enhancement path
- Developer-friendly

**Bad:**
- Not enforced at runtime (documentation-only)
- Requires developer discipline
- Manual security review needed
- No prevention of malicious workflows
- Classification may be incorrect

### Option 4: Permission-Based System

**Good:**
- Fine-grained control
- User control over permissions
- Runtime enforcement
- Familiar model (Android)

**Bad:**
- Complex implementation
- Permission prompt fatigue
- Persistent storage required
- Unclear security boundaries for LLMs
- Premature for MVP

## Implementation Details

### Security Classification System

**Three Security Levels:**

```python
class ExecutorSecurityLevel(Enum):
    """Security classification for executors."""

    SAFE = "safe"
    # - Read-only operations
    # - No system access
    # - Pure computation
    # - Example: EchoBlock

    TRUSTED = "trusted"
    # - File I/O (limited scope)
    # - Safe operations only
    # - No arbitrary code execution
    # - Example: CreateFile, ReadFile, PopulateTemplate

    PRIVILEGED = "privileged"
    # - Full system access
    # - Arbitrary code execution
    # - Network access
    # - Git operations
    # - Example: Shell, ExecuteWorkflow
```

**Capability Flags:**

```python
class ExecutorCapabilities(BaseModel):
    """Fine-grained capability flags for executors."""

    can_read_files: bool = False
    # Can read files from filesystem

    can_write_files: bool = False
    # Can create/modify/delete files

    can_execute_commands: bool = False
    # Can execute shell commands

    can_network: bool = False
    # Can make network requests

    can_modify_state: bool = False
    # Can modify workflow execution state

    can_spawn_processes: bool = False
    # Can create new processes

    can_access_env_vars: bool = False
    # Can read environment variables
```

### Executor Security Declaration

Each executor declares its security level and capabilities:

```python
class EchoBlockExecutor(BlockExecutor):
    """Safe executor - only echoes input."""

    def security_level(self) -> ExecutorSecurityLevel:
        return ExecutorSecurityLevel.SAFE

    def capabilities(self) -> ExecutorCapabilities:
        return ExecutorCapabilities()  # No capabilities needed

class CreateFileExecutor(BlockExecutor):
    """Trusted executor - writes files."""

    def security_level(self) -> ExecutorSecurityLevel:
        return ExecutorSecurityLevel.TRUSTED

    def capabilities(self) -> ExecutorCapabilities:
        return ExecutorCapabilities(
            can_write_files=True
        )

class ShellExecutor(BlockExecutor):
    """Privileged executor - executes shell commands."""

    def security_level(self) -> ExecutorSecurityLevel:
        return ExecutorSecurityLevel.PRIVILEGED

    def capabilities(self) -> ExecutorCapabilities:
        return ExecutorCapabilities(
            can_execute_commands=True,
            can_read_files=True,
            can_write_files=True,
            can_network=True,
            can_spawn_processes=True,
            can_access_env_vars=True
        )
```

### Security Audit Tools

**List Executor Security:**

```python
def audit_executors(registry: ExecutorRegistry) -> List[Dict[str, Any]]:
    """Generate security audit report for all executors."""
    report = []
    for name, executor in registry.all():
        report.append({
            "executor": name,
            "security_level": executor.security_level().value,
            "capabilities": executor.capabilities().model_dump(),
            "privileged": executor.security_level() == ExecutorSecurityLevel.PRIVILEGED
        })
    return sorted(report, key=lambda x: x["security_level"], reverse=True)
```

**Workflow Security Analysis:**

```python
def analyze_workflow_security(workflow: WorkflowDefinition) -> Dict[str, Any]:
    """Analyze security implications of workflow."""
    max_security_level = ExecutorSecurityLevel.SAFE
    capabilities_used = set()

    for block in workflow.blocks:
        executor = ExecutorRegistry.get(block.type)
        level = executor.security_level()
        caps = executor.capabilities()

        if level == ExecutorSecurityLevel.PRIVILEGED:
            max_security_level = ExecutorSecurityLevel.PRIVILEGED
        elif level == ExecutorSecurityLevel.TRUSTED and max_security_level == ExecutorSecurityLevel.SAFE:
            max_security_level = ExecutorSecurityLevel.TRUSTED

        for cap, enabled in caps.model_dump().items():
            if enabled:
                capabilities_used.add(cap)

    return {
        "max_security_level": max_security_level.value,
        "capabilities_required": list(capabilities_used),
        "privileged_blocks": [
            block.id for block in workflow.blocks
            if ExecutorRegistry.get(block.type).security_level() == ExecutorSecurityLevel.PRIVILEGED
        ]
    }
```

### Plugin Security Review

Third-party plugins must declare security:

```python
# third_party_plugin.py
class CustomAPIExecutor(BlockExecutor):
    """Third-party executor for API calls."""

    def security_level(self) -> ExecutorSecurityLevel:
        # Must declare security level
        return ExecutorSecurityLevel.TRUSTED

    def capabilities(self) -> ExecutorCapabilities:
        # Must declare capabilities
        return ExecutorCapabilities(
            can_network=True
        )
```

Security review checklist for plugins:
1. ✅ Security level declared correctly?
2. ✅ Capabilities match actual operations?
3. ✅ No undeclared system access?
4. ✅ Input validation implemented?
5. ✅ Error handling prevents information leaks?

### JSON Schema Integration

Security metadata included in auto-generated JSON schema:

```json
{
  "blocks": {
    "Shell": {
      "security": {
        "level": "privileged",
        "capabilities": {
          "can_execute_commands": true,
          "can_read_files": true,
          "can_write_files": true,
          "can_network": true,
          "can_spawn_processes": true,
          "can_access_env_vars": true
        }
      },
      "input": { ... },
      "output": { ... }
    }
  }
}
```

Editors can display security warnings based on schema metadata.

## Future Extensions

### Phase 2: Runtime Enforcement

**Permission Checks:**

```python
class SecurityPolicy:
    """Runtime security policy enforcement."""

    def __init__(self, allowed_capabilities: ExecutorCapabilities):
        self.allowed = allowed_capabilities

    def check_executor(self, executor: BlockExecutor) -> Result[None]:
        """Verify executor capabilities are allowed."""
        required = executor.capabilities()
        for cap, needed in required.model_dump().items():
            if needed and not getattr(self.allowed, cap):
                return Result.failure(f"Permission denied: {cap}")
        return Result.success(None)
```

**Workflow Security Policies:**

```yaml
# workflow-security.yaml
name: my-workflow
security:
  policy: restricted
  allowed_capabilities:
    can_read_files: true
    can_write_files: true
    can_execute_commands: false  # Block shell access
blocks:
  - id: safe_operation
    type: CreateFile  # Allowed

  - id: blocked_operation
    type: Shell  # DENIED: can_execute_commands = false
```

### Phase 3: Sandboxed Execution

**Containerized Blocks:**

```python
class SandboxedShellExecutor(ShellExecutor):
    """Shell executor with Docker isolation."""

    def execute(self, block_id: str, inputs: ShellInput, context: Dict[str, Any]) -> Result[ShellOutput]:
        # Execute in isolated container
        container = docker.run(
            image="alpine:latest",
            command=inputs.command,
            network="none",  # No network access
            volumes={inputs.working_dir: "/workspace"},
            user="nobody",
            memory_limit="512m",
            cpu_quota=50000,
        )
        # Return result
```

### Phase 4: Audit Logging

**Security Event Logging:**

```python
class SecurityAuditLogger:
    """Log security-sensitive operations."""

    def log_privileged_execution(
        self,
        workflow_id: str,
        block_id: str,
        executor: BlockExecutor,
        inputs: BlockInput
    ):
        log.warning(
            "Privileged execution",
            workflow_id=workflow_id,
            block_id=block_id,
            executor=executor.__class__.__name__,
            security_level=executor.security_level().value,
            capabilities=executor.capabilities().model_dump(),
            inputs=inputs.model_dump_json()
        )
```

### Phase 5: User Consent

**Permission Prompts:**

```python
def prompt_for_permission(executor: BlockExecutor, context: str) -> bool:
    """Ask user for permission to execute privileged block."""
    print(f"⚠️  Security Warning ⚠️")
    print(f"Workflow requests: {executor.security_level().value} access")
    print(f"Capabilities: {executor.capabilities().model_dump()}")
    print(f"Context: {context}")
    response = input("Allow? [y/N]: ")
    return response.lower() == "y"
```

## Security Best Practices

### Workflow Development

1. **Minimize Privileges**: Use lowest security level possible
2. **Validate Inputs**: Sanitize user input before shell execution
3. **Limit Scope**: File operations should use specific paths, not wildcards
4. **Avoid Secrets**: Never hardcode credentials in workflows
5. **Review Dependencies**: Audit workflows that use ExecuteWorkflow

### Plugin Development

1. **Declare Correctly**: Security level must match actual operations
2. **Document Capabilities**: Explain why each capability is needed
3. **Validate Everything**: Treat all inputs as untrusted
4. **Fail Securely**: Errors should not leak sensitive information
5. **Test Security**: Include tests for malicious inputs

### Production Deployment

1. **Review Workflows**: Audit all workflows before production
2. **Limit Privileges**: Run workflow server as non-root user
3. **Monitor Execution**: Log privileged operations
4. **Isolate Environments**: Separate development and production
5. **Regular Audits**: Periodic security review of workflows

## Links

- [ADR-001: Executor Pattern Redesign](ADR-001-executor-pattern-redesign.md) - Executor architecture enabling security model
- [ExecutorBase Implementation](../../src/workflows_mcp/engine/executor_base.py)
- [Security Classification Examples](../../src/workflows_mcp/engine/executors_core.py)
- [Shell Executor Security](../../src/workflows_mcp/engine/executors_core.py)
