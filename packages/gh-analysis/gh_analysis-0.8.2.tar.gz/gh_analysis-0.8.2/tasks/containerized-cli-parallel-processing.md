# Task: Containerized CLI for Parallel Case Processing

**Status:** ready

**⚠️ USER ACTION REQUIRED:**
Before the implementing agent can test, you must set:
```bash
export ISSUE_URL="<a-github-issue-url>"
```
Example: `export ISSUE_URL="https://github.com/microsoft/vscode/issues/12345"`

**Description:**
Create a containerized version of the GitHub Issue Analysis CLI that enables single-shot troubleshooting case processing via podman. The container will accept environment variables for configuration, process one case, output results to stdout, and exit - enabling parallel processing of multiple cases across multiple container instances.

## Acceptance Criteria

### Core Functionality
- [ ] **Container Build System**: Multi-stage Containerfile optimized for Python 3.13+ with all dependencies
- [ ] **Single-Shot CLI Mode**: Container entrypoint that calls existing `gh-analysis process troubleshoot` command and exits
- [ ] **Environment-Based Configuration**: Accept all parameters via environment variables (GITHUB_TOKEN, OPENAI_API_KEY, etc.)
- [ ] **Standardized Output**: JSON-formatted results to stdout with consistent schema
- [ ] **Error Handling**: Proper exit codes and error messages for container orchestration
- [ ] **Parallel Execution Support**: Multiple containers can run simultaneously without conflicts

### Container Interface
- [ ] **Podman Compatibility**: Container works seamlessly with podman launch commands
- [ ] **Volume Strategy**: Optional volume mounts for persistent storage/caching
- [ ] **Resource Management**: Configurable memory/CPU limits and timeouts
- [ ] **Network Independence**: Container runs without requiring external network dependencies beyond API calls

### UX Design  
- [ ] **Simplified Entry Point**: Single command interface for container execution
- [ ] **Interactive Mode Handling**: Interactive troubleshooting disabled in container mode by default, with optional enable flag
- [ ] **Progress Visibility**: Progress indicators and logging suitable for container environments
- [ ] **Documentation**: Complete usage examples for podman commands

### Quality Assurance
- [ ] **PR Container Tests**: Container builds successfully and shows help (no API testing in CI)
- [ ] **Container Build Tests**: Automated tests for Containerfile build process
- [ ] **Local Integration Tests**: End-to-end tests with podman execution (requires local ENV)
- [ ] **Parallel Processing Tests**: Validate multiple containers can run simultaneously (local only)
- [ ] **Memory/Resource Tests**: Verify container resource consumption and limits (local only)
- [ ] **GHCR Publishing**: Automated container publishing to GitHub Container Registry on tag
- [ ] **Multi-arch Builds**: Container builds for both AMD64 and ARM64 architectures
- [ ] **All existing tests pass**: No regression in current functionality

## Implementation Plan

### Phase 1: Container Infrastructure (Sub-agent: Containerfile & Build)
**Files to Create:**
- `Containerfile` - Multi-stage build with Python 3.13, UV, and all dependencies
- `.containerignore` - Optimize build context
- `scripts/container-entrypoint.sh` - Container startup script that calls existing CLI
- `.github/workflows/container-release.yml` - GitHub workflow for GHCR publishing on tag

**Files to Modify:**
- `.github/workflows/test.yml` - Add container build job that depends on quality-checks

**Technical Specifications:**
- **Base Image**: `python:3.13-slim` for size optimization
- **Build Stages**: 
  1. Dependencies stage with UV and package installation
  2. Runtime stage with minimal footprint
- **Working Directory**: `/app`  
- **User**: Non-root user (uid 1000) for security
- **Entry Point**: `/app/scripts/container-entrypoint.sh`
- **Important**: Copy pyproject.toml and uv.lock for reproducible builds

**Containerfile Structure Example:**
```dockerfile
# Stage 1: Dependencies
FROM python:3.13-slim as builder
WORKDIR /app
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Copy dependency files
COPY pyproject.toml uv.lock ./
# Install dependencies
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.13-slim
WORKDIR /app
# Create non-root user
RUN useradd -m -u 1000 appuser
# Copy uv and dependencies from builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv
# Copy application code
COPY . .
# Make entrypoint executable
RUN chmod +x /app/scripts/container-entrypoint.sh
# Switch to non-root user
USER appuser
# Set entrypoint
ENTRYPOINT ["/app/scripts/container-entrypoint.sh"]
```
- **GitHub Container Registry**: Automated publishing via GitHub Actions on tag creation
- **Multi-arch Support**: Build for linux/amd64 and linux/arm64 platforms

### Phase 2: Container Entry Point (Sub-agent: Entrypoint Script Implementation)
**Files to Create:**
- `scripts/container-entrypoint.sh` - Parse environment variables and call existing CLI

**Entrypoint Script Logic:**
```bash
#!/bin/bash
set -e  # Exit on error

# Validate required environment variables
if [ -z "$ISSUE_URL" ]; then
    echo "ERROR: ISSUE_URL environment variable is required" >&2
    exit 2
fi

# Activate virtual environment
export PATH="/app/.venv/bin:$PATH"

# Build command with required --url flag
CMD="gh-analysis process troubleshoot --url \"$ISSUE_URL\""

# Add optional CLI arguments if provided
if [ -n "$CLI_ARGS" ]; then
    CMD="$CMD $CLI_ARGS"
fi

# Execute the command
eval exec $CMD
```

**Environment Variables:**
```bash
# Required API tokens
GITHUB_TOKEN=<token>
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
SBCTL_TOKEN=<token>  # Required for troubleshoot command

# Required case specification  
ISSUE_URL=<full-github-issue-url>

# Optional CLI arguments (space-separated string)
CLI_ARGS="--agent gpt5_mini_medium --interactive"

# Optional Snowflake (for MT runners)
SNOWFLAKE_ACCOUNT=<account>
SNOWFLAKE_USER=<user>
SNOWFLAKE_PRIVATE_KEY_PATH=<path>
```

### Phase 3: Output Standardization (Sub-agent: Result Processing)  
**Files to Modify:**
- `scripts/container-entrypoint.sh` - Handle output formatting and exit codes
- Existing CLI already outputs structured results - leverage that

**Output Schema:**
```json
{
  "status": "success|error",
  "case_id": "org_repo_issue_123", 
  "runner": "gpt5_mini_medium",
  "timestamp": "2024-01-01T12:00:00Z",
  "analysis": { /* TechnicalAnalysis object */ },
  "execution_time": 45.2,
  "token_usage": 15420,
  "error": null
}
```

### Phase 4: Testing & Validation (Sub-agent: Container Testing)
**Files to Create:**
- `tests/test_container/test_build.py` - Container build validation
- `tests/test_container/test_entrypoint.py` - Test entrypoint script parsing
- `scripts/test-container-examples.sh` - Manual testing scripts with mock data

**Critical Test Scenarios:**
1. **Missing ISSUE_URL** - Should exit with code 2
2. **Invalid agent name** - Should pass error through from CLI
3. **Missing API tokens** - Should fail with appropriate error
4. **Valid execution** - Should return JSON output
5. **Parallel execution** - Multiple containers should not conflict

**Test Script Example** (`scripts/test-container-examples.sh`):
```bash
#!/bin/bash
set -e

echo "=== Tests that work without API keys (CI-safe) ==="

echo "Test 1: Missing ISSUE_URL should fail with exit code 2"
podman run --rm localhost/gh-analysis:latest || [ $? -eq 2 ]
echo "✓ Test 1 passed"

echo "Test 2: Help flag should work without API keys"
podman run --rm \
  -e ISSUE_URL="https://github.com/test/test/issues/1" \
  -e CLI_ARGS="--help" \
  localhost/gh-analysis:latest > /dev/null
echo "✓ Test 2 passed"

echo "=== Tests that require API keys (local only) ==="

if [ -n "$GITHUB_TOKEN" ] && [ -n "$ISSUE_URL" ]; then
  echo "Test 3: Valid execution with real issue"
  podman run --rm \
    -e GITHUB_TOKEN="${GITHUB_TOKEN}" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
    -e SBCTL_TOKEN="${SBCTL_TOKEN}" \
    -e ISSUE_URL="${ISSUE_URL}" \
    -e CLI_ARGS="--agent gpt5_mini_medium" \
    localhost/gh-analysis:latest
  echo "✓ Test 3 passed"
else
  echo "⚠ Skipping Test 3: API keys not available (this is normal in CI)"
fi

echo "All available tests passed!"
```

## Technical Implementation Details

### Container Architecture
- **Multi-stage build** to minimize final image size
- **UV integration** for fast dependency resolution
- **Temporary directory management** for isolated execution
- **Signal handling** for graceful shutdown
- **Resource limits** configurable via container runtime

### GitHub Actions Workflow Specifications

#### PR Testing Workflow: Update `.github/workflows/test.yml`
- **Existing Workflow**: Already runs quality checks on PRs
- **Add Container Job**: New job that runs AFTER quality-checks pass
- **Container Job Name**: `container-build`
- **Container Job Steps**:
  ```yaml
  container-build:
    name: Container Build Test
    runs-on: ubuntu-latest
    needs: quality-checks  # Only run if tests pass
    steps:
      - uses: actions/checkout@v4
      - name: Build container
        run: podman build -f Containerfile -t test-container .
      - name: Test container runs and shows help
        run: |
          # Only test that container builds and can show help
          # No API tokens available in CI, so can't test actual processing
          podman run --rm \
            -e ISSUE_URL="https://github.com/test/repo/issues/1" \
            -e CLI_ARGS="--help" \
            test-container
      - name: Test missing ISSUE_URL error handling
        run: |
          # Should exit with code 2 when ISSUE_URL is missing
          podman run --rm test-container || [ $? -eq 2 ]
  ```
- **No Push**: Only builds, doesn't push to registry
- **Fast Feedback**: Single-arch build (linux/amd64) for speed

#### Release Workflow: `.github/workflows/container-release.yml`
- **Trigger**: On tag creation (same trigger as PyPI release)
- **Jobs**: 
  1. Build multi-arch container (linux/amd64, linux/arm64)
  2. Push to `ghcr.io/chris-sanders/github-issue-analysis`
  3. Tag with both `latest` and version tag (e.g., `v0.2.0`)
- **Authentication**: Uses `GITHUB_TOKEN` (automatic)
- **Build Args**: Pass version from git tag to container
- **Registry**: GitHub Container Registry (ghcr.io)

**Workflow Structure:**
```yaml
name: Container Release
on:
  push:
    tags:
      - "*.*.*"
jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/chris-sanders/github-issue-analysis
          tags: |
            type=ref,event=tag
            type=raw,value=latest
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Containerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

### Data Handling Strategy
- **Ephemeral storage** by default - container processes case and exits
- **Optional volume mounts** for caching dependencies or persistent storage
- **Temporary directories** cleaned up automatically
- **No persistent state** between container runs

### Interactive Mode Considerations
- **Default**: Interactive mode disabled in containers
- **Override**: `INTERACTIVE_MODE=true` enables interactive troubleshooting
- **Output handling**: Interactive prompts routed to stderr, results to stdout
- **Timeout protection**: Container exits after maximum execution time

### Error Handling & Exit Codes
```bash
0   - Success
1   - General error  
2   - Configuration error (missing env vars, invalid runner)
3   - GitHub API error (authentication, rate limits)
4   - AI model error (API failures, timeout)
5   - Resource error (memory, disk space)
```

## Usage Examples

### Basic Usage
```bash
# Build container locally (for development)
podman build -f Containerfile -t gh-analysis .

# Or use published container from GHCR
podman pull ghcr.io/chris-sanders/github-issue-analysis:latest

# Process single case with specific agent
# ISSUE_URL must be set in environment
podman run --rm \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e SBCTL_TOKEN=$SBCTL_TOKEN \
  -e ISSUE_URL="$ISSUE_URL" \
  -e CLI_ARGS="--agent gpt5_mini_medium" \
  ghcr.io/chris-sanders/github-issue-analysis:latest > results.json
```

### Parallel Processing
```bash
# Process multiple cases in parallel
# Note: For testing with single ISSUE_URL, you can run same issue multiple times:
# for i in 1 2 3; do ... done
# In production, set multiple URLs: ISSUE_URL_1, ISSUE_URL_2, etc.
for issue_url in "${ISSUE_URL_1:-$ISSUE_URL}" "${ISSUE_URL_2:-$ISSUE_URL}" "${ISSUE_URL_3:-$ISSUE_URL}"; do
  podman run --rm -d \
    -e GITHUB_TOKEN=$GITHUB_TOKEN \
    -e OPENAI_API_KEY=$OPENAI_API_KEY \
    -e ISSUE_URL="$issue_url" \
    -e CLI_ARGS="--agent gpt5_mini_medium" \
    ghcr.io/chris-sanders/github-issue-analysis:latest > "results-$(basename $issue_url).json" &
done
wait
```

### Interactive Mode
```bash
# Enable interactive troubleshooting
podman run --rm -it \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ISSUE_URL="$ISSUE_URL" \
  -e CLI_ARGS="--agent gpt5_mini_medium --interactive" \
  ghcr.io/chris-sanders/github-issue-analysis:latest
```

### Memory+Tool Runners
```bash
# With Snowflake integration for enhanced troubleshooting
podman run --rm \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e SNOWFLAKE_ACCOUNT=$SNOWFLAKE_ACCOUNT \
  -e SNOWFLAKE_USER=$SNOWFLAKE_USER \
  -v ~/.snowflake:/root/.snowflake:ro \
  -e ISSUE_URL="$ISSUE_URL" \
  -e CLI_ARGS="--agent gpt5_mini_medium_mt" \
  ghcr.io/chris-sanders/github-issue-analysis:latest
```

## Validation Commands

```bash
# Setup and build
uv sync --all-extras
podman build -f Containerfile -t gh-analysis .

# Test container functionality (uses --help, no real issues)
./scripts/test-container-examples.sh

# Run quality checks
uv run ruff format . && uv run ruff check --fix --unsafe-fixes && uv run mypy . && uv run pytest

# Test with actual GitHub issue (requires ISSUE_URL to be set)
# The user will provide this URL for testing
podman run --rm \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ISSUE_URL="$ISSUE_URL" \
  -e CLI_ARGS="--agent gpt5_mini_medium" \
  gh-analysis:latest
```

## Development Workflow Recommendations

1. **Create worktree**: `git worktree add trees/containerized-cli -b feature/containerized-cli`
2. **Parallel sub-agents**: Use 3-4 sub-agents for concurrent development:
   - Sub-agent 1: Containerfile and container infrastructure  
   - Sub-agent 2: Entrypoint script and environment handling
   - Sub-agent 3: Output standardization and result processing
   - Sub-agent 4: Testing framework and validation scripts
3. **Integration testing**: Use actual GitHub repositories for end-to-end validation
4. **Resource testing**: Validate memory usage and performance with various runner types
5. **Documentation**: Update README with GHCR usage and container examples

## Release Integration

### Automated Release Workflow
When you create a git tag (e.g., `v0.2.1`), the workflow will:

1. **PyPI Release**: Your existing workflow publishes the Python package
2. **Container Release**: New workflow builds and publishes container to GHCR
3. **Tagging Strategy**: 
   - `ghcr.io/chris-sanders/github-issue-analysis:v0.2.1` (version-specific)
   - `ghcr.io/chris-sanders/github-issue-analysis:latest` (latest release)
4. **Multi-arch Support**: Builds for both AMD64 and ARM64 architectures

### Container Registry Access
```bash
# Public access (no authentication needed)
podman pull ghcr.io/chris-sanders/github-issue-analysis:latest

# Use specific version
podman pull ghcr.io/chris-sanders/github-issue-analysis:v0.2.1
```

This implementation enables efficient parallel case processing while maintaining all existing functionality and following the established architectural patterns.

**Agent Notes:**
[Agent will document progress, decisions, validation steps, and any information needed for handoff here]

## Troubleshooting Guide for Implementation

### Common Issues and Solutions:

1. **UV not found in container**: Ensure UV is copied from the official UV image and PATH is set correctly
2. **Permission denied on entrypoint**: Make sure to `chmod +x` the entrypoint script in Containerfile
3. **Module not found errors**: Virtual environment path must be activated in entrypoint script
4. **ISSUE_URL with spaces**: Use proper quoting in the entrypoint script
5. **Container runs but no output**: Check if the CLI is outputting to stderr instead of stdout
6. **Timeout on large issues**: Consider adding timeout handling in the entrypoint script
7. **Multi-arch build fails**: Ensure Docker Buildx is properly configured in GitHub Actions

### Validation Checklist:
- [ ] Container builds successfully locally
- [ ] Entrypoint script handles missing ISSUE_URL (exit code 2)
- [ ] Container shows help with --help flag (testable in CI without API keys)
- [ ] Container processes a real issue from $ISSUE_URL environment variable (local testing only)
- [ ] Output is produced to stdout (may be text or JSON depending on CLI defaults)
- [ ] Container exits cleanly after processing
- [ ] GitHub Actions workflow passes on PR (builds container, tests help/error handling only)
- [ ] Release workflow is ready for multi-arch builds (not testable until tag)

### Final Testing Command:
```bash
# After everything is built, this should work:
podman run --rm \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e SBCTL_TOKEN="$SBCTL_TOKEN" \
  -e ISSUE_URL="$ISSUE_URL" \
  -e CLI_ARGS="--agent gpt5_mini_medium" \
  localhost/gh-analysis:latest
```

If this command successfully processes the issue and returns output, the implementation is complete.

## Critical Security Notes

**NEVER commit or document real customer issue URLs**
- Use environment variables for all issue URLs
- The implementing agent must NOT hardcode any real GitHub issue URLs

## Required Environment Setup for Development

**Already Available in Environment:**
- ✅ `GITHUB_TOKEN`
- ✅ `OPENAI_API_KEY`
- ✅ `ANTHROPIC_API_KEY`
- ✅ `SBCTL_TOKEN` (required for troubleshoot command)
- ✅ `SNOWFLAKE_*` variables (for MT runners)

**USER MUST PROVIDE before agent can test:**
```bash
# Set any GitHub issue URL for testing
export ISSUE_URL="https://github.com/microsoft/vscode/issues/12345"
```

The implementing agent will use `$ISSUE_URL` from environment for all testing.
Never hardcode actual URLs in scripts or documentation.