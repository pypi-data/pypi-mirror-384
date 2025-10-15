# Code Cleanup - Phase 1: Critical DRY Violations and Function Decomposition

## Status
- **Status**: Not Started
- **Priority**: High
- **Estimated Time**: 4-6 hours
- **Dependencies**: None

## Overview
Address critical code quality issues identified in the codebase review, focusing on DRY violations and oversized functions that impact maintainability.

## Specific Issues to Address

### 1. Extract Duplicated GitHub Query Building Logic

**Problem**: Query building logic is duplicated across 3 locations:
- `github_client/client.py` lines 152-162 (search_issues)
- `github_client/client.py` lines 214-224 (search_organization_issues) 
- `github_client/search.py` lines 101-113 (build_github_query)

**Solution**: Create a unified query builder in `github_client/client.py`:
```python
def _build_github_query(
    scope: str,  # "repo:org/repo" or "org:org"
    labels: list[str] | None = None,
    state: str = "open",
    created_after: str | None = None,
) -> str:
    """Build GitHub search query with common parameters."""
    query_parts = [scope, "is:issue"]
    
    if state != "all":
        query_parts.append(f"state:{state}")
    
    if labels:
        for label in labels:
            query_parts.append(f"label:{label}")
    
    if created_after:
        query_parts.append(f"created:>{created_after}")
    
    return " ".join(query_parts)
```

Then refactor both search methods to use this helper.

### 2. Extract Duplicated Issue Processing Logic

**Problem**: Nearly identical issue processing loops in `github_client/client.py`:
- Lines 166-182 (search_issues)
- Lines 227-244 (search_organization_issues)

**Solution**: Extract to helper method:
```python
def _process_search_results(self, issues, limit: int) -> list[GitHubIssue]:
    """Process GitHub search results into GitHubIssue objects."""
    result_issues = []
    for i, github_issue in enumerate(issues):
        if i >= limit:
            break
        try:
            result_issues.append(self._convert_issue(github_issue))
            console.print(f"Processed issue #{github_issue.number}: {github_issue.title}")
        except Exception as e:
            console.print(f"Error processing issue #{github_issue.number}: {e}")
            continue
    return result_issues
```

### 3. Extract Duplicated Rate Limit Handling

**Problem**: Identical rate limit handling in both search methods:
- Lines 186-189 and 248-251 in `github_client/client.py`

**Solution**: Extract to helper method:
```python
def _handle_rate_limit_retry(self, func_name: str, *args, **kwargs):
    """Handle rate limit exceptions with retry logic."""
    try:
        if func_name == "search_issues":
            return self._search_issues_impl(*args, **kwargs)
        elif func_name == "search_organization_issues":
            return self._search_organization_issues_impl(*args, **kwargs)
    except RateLimitExceededException:
        console.print("Rate limit exceeded, waiting...")
        time.sleep(60)
        # Retry once
        if func_name == "search_issues":
            return self._search_issues_impl(*args, **kwargs)
        elif func_name == "search_organization_issues":
            return self._search_organization_issues_impl(*args, **kwargs)
```

### 4. Break Down Oversized Functions

#### 4a. Refactor `cli/collect.py:collect()` (214 lines)

**Problem**: Function handles multiple responsibilities in 214 lines.

**Solution**: Extract helper functions:
- `_validate_collection_parameters()` - parameter validation (lines 64-70)
- `_setup_attachments_processing()` - attachment setup (lines 143-168)
- `_save_issues_by_mode()` - issue saving logic (lines 177-192)
- `_display_collection_summary()` - table/summary display (lines 83-98)

#### 4b. Refactor `cli/process.py:_run_product_labeling()` (151 lines)

**Problem**: Function mixes file discovery, validation, and processing.

**Solution**: Extract helper functions:
- `_find_issue_files()` - file discovery logic (lines 90-131)
- `_process_issue_files()` - main processing loop (lines 167-220)
- `_validate_processing_parameters()` - parameter validation (lines 92-98)

## Implementation Steps

1. **Create unit tests** for existing functionality to ensure refactoring doesn't break behavior
2. **Extract GitHub client helpers** first (query building, issue processing, rate limit handling)
3. **Update both search methods** to use the new helpers
4. **Break down `collect()` function** into smaller, focused functions
5. **Break down `_run_product_labeling()` function** into smaller functions
6. **Run full test suite** to verify no regressions
7. **Update any affected tests** that may need adjustment

## Acceptance Criteria

- [ ] All duplicated query building logic consolidated into single helper method
- [ ] Issue processing loop extracted and reused in both search methods
- [ ] Rate limit handling extracted to single helper method
- [ ] `cli/collect.py:collect()` function reduced to < 50 lines with helper functions
- [ ] `cli/process.py:_run_product_labeling()` function reduced to < 50 lines with helper functions
- [ ] All existing tests pass
- [ ] Code quality checks pass: `uv run black . && uv run ruff check --fix --unsafe-fixes && uv run mypy . && uv run pytest`
- [ ] No new linting suppressions added
- [ ] Function complexity reduced (verified by tools like `radon` if available)

## Testing Strategy

1. **Before refactoring**: Run full test suite to establish baseline
2. **During refactoring**: Run affected test modules after each major change
3. **After refactoring**: Full test suite + manual CLI testing of collect and process commands
4. **Regression testing**: Test edge cases like rate limiting, error handling, file processing

## Notes

- Preserve all existing functionality and error handling behavior
- Maintain backward compatibility for CLI interface
- Keep the same console output patterns for user experience
- Ensure extracted functions have clear, single responsibilities
- Add proper type annotations to all new helper functions

## Definition of Done

- All acceptance criteria met
- Code review completed
- All tests passing
- Documentation updated if needed
- No performance regressions
- Ready for production deployment