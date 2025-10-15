# Task: Fix CI/CD Container Build Hang and Clean Up Repository

## Problem Statement

The CI/CD pipeline is experiencing significant delays (10+ minutes) during container builds, causing workflow timeouts. Additionally, there are repository organization issues with a misplaced test file and unnecessary files being included in the production container image.

## Current Issues

1. **CI Build Hang**: The `container-release.yml` workflow attempts to build for both `linux/amd64` and `linux/arm64` platforms. ARM64 builds via QEMU emulation are extremely slow when compiling C++ extensions for snowflake-connector-python.

2. **Misplaced File**: A file named `test_cli.py` exists in the repository root that doesn't belong there.

3. **Bloated Production Image**: The Containerfile copies the entire `tests` directory into the production container, unnecessarily increasing image size.

## Required Changes

### 1. Remove Misplaced Test File

**File:** `/test_cli.py`

**Action:** Delete this file completely

**Details:**
- This is a simple test helper that was accidentally placed in root
- Contains only:
  ```python
  #!/usr/bin/env python3
  """Test CLI functionality."""
  from gh_analysis.cli.collect import app
  if __name__ == "__main__":
      app()
  ```
- No other files should reference this
- Verify with `grep -r "test_cli.py" .` before deletion

### 2. Fix Multi-Platform Build Configuration

**File:** `.github/workflows/container-release.yml`

**Line 47 - Current:**
```yaml
platforms: linux/amd64,linux/arm64
```

**Line 47 - Change to:**
```yaml
platforms: linux/amd64
```

**Rationale:**
- Removes ARM64 platform to eliminate QEMU emulation overhead
- Will reduce build time from 10+ minutes to <5 minutes
- ARM64 users can still build locally if needed

### 3. Remove Tests from Production Container

**File:** `Containerfile`

**Line 65 - Current:**
```dockerfile
COPY tests ./tests
```

**Action:** Delete this entire line

**Impact:**
- Tests will no longer be included in production image
- Reduces container image size
- Tests will be mounted as volumes during testing

### 4. Update Container Testing Script

**File:** `scripts/test-container-functional.sh`

**Required Modifications:**

For tests that need access to test files, add volume mount flag. Review each test command and modify as needed:

**Pattern to follow:**
```bash
# Commands that DON'T need test files (leave unchanged):
$CONTAINER_CMD run --rm \
  --entrypoint=/bin/sh \
  gh-analysis:test \
  -c "which sbctl && which kubectl"

# Commands that DO need test files (add volume mount):
$CONTAINER_CMD run --rm \
  -v $(pwd)/tests:/app/tests:ro \
  --entrypoint=/bin/sh \
  gh-analysis:test \
  -c "cd /app && uv run pytest tests/some_test.py"
```

**Specific changes needed:**
- Line 40-44: Test 1 - No change needed (checking binaries)
- Line 47-52: Test 2 - No change needed (import check)
- Line 56-67: Test 3 - No change needed (CLI help)
- Line 70-80: Test 4 - No change needed (environment validation)
- Any future tests that run pytest or access test files: Add `-v $(pwd)/tests:/app/tests:ro`

### 5. Verify MCP Integration Workflow

**File:** `.github/workflows/test-mcp-integration.yml`

**Review only - likely no changes needed:**
- Line 44 builds the container with podman
- Line 51 runs the test script with `SKIP_BUILD=1`
- Since the script handles the volume mounting, no workflow changes expected
- Verify this assumption during testing

## Testing Plan

### Local Testing Steps

1. **Build container:**
   ```bash
   podman build -t gh-analysis:test -f Containerfile .
   ```

2. **Verify tests not in image:**
   ```bash
   # This should fail with "No such file or directory"
   podman run --rm gh-analysis:test ls /app/tests
   ```

3. **Run functional tests:**
   ```bash
   ./scripts/test-container-functional.sh
   ```

4. **Test with explicit volume mount (if needed):**
   ```bash
   podman run --rm -v $(pwd)/tests:/app/tests:ro gh-analysis:test \
     uv run python -c "import os; print(os.path.exists('/app/tests'))"
   # Should print: True
   ```

### CI Testing

1. Push changes to a feature branch
2. Open PR to trigger workflows
3. Verify `MCP Functional Tests` workflow passes
4. Verify build time is <5 minutes (check workflow run time)

## Success Criteria

- [ ] `test_cli.py` removed from repository root
- [ ] Container builds complete in <5 minutes in CI
- [ ] Production container image does not contain `/app/tests` directory  
- [ ] All functional tests pass with volume-mounted approach
- [ ] Container image size reduced (measure before/after with `podman images`)
- [ ] No regression in MCP functional tests

## Git Commit Message

```
Fix CI container build hang and remove unnecessary files

- Change container build to AMD64 only (remove ARM64) to fix CI hang
- Remove test_cli.py from repository root (misplaced file)  
- Remove tests from production container image (reduce size)
- Update test script to mount tests as volume when needed

The CI was hanging at 10+ minutes due to QEMU emulation overhead
when building ARM64 images with C++ compilation. Tests are now
mounted as volumes during testing rather than baked into the image.
```

## Important Implementation Notes

1. **Volume Mount Security**: Always mount test directory as read-only (`:ro`)
2. **Selective Mounting**: Only add volume mounts where tests are actually needed
3. **Path Consistency**: Use `$(pwd)/tests` for relative path resolution
4. **No Multi-Stage**: Do NOT implement multi-stage builds for testing - use volume mounts only
5. **Backward Compatibility**: Ensure changes don't break existing functionality

## Rollback Plan

If issues arise:
1. Revert the commit
2. Re-add ARM64 platform (accept slow builds temporarily)
3. Re-add tests to Containerfile
4. Investigate alternative solutions (e.g., native ARM runners)

## References

- Current PR with hang: https://github.com/chris-sanders/github-issue-analysis/actions/runs/17592520165/job/49976529944
- Container testing script: `scripts/test-container-functional.sh`
- MCP workflow: `.github/workflows/test-mcp-integration.yml`
- Container release workflow: `.github/workflows/container-release.yml`