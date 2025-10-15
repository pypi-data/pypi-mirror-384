# Fix Aggressive Comment Filtering

## Problem Statement

The label processor is aggressively filtering comment data before sending to the LLM, which prevents the AI from having access to all necessary context for accurate analysis. The current implementation:

1. **Limits comments to only the last 3** (`issue["comments"][-3:]`)
2. **Truncates each comment to 200 characters** (`comment["body"][:200]`)
3. **Truncates issue body to 1500 characters** (`issue["body"][:1500]`)

This filtering was never requested and prevents the LLM from doing its job correctly. The LLM needs access to ALL comments and content in a compact format to make accurate labeling decisions.

## Root Cause Analysis

The filtering occurs in `/github_issue_analysis/ai/processors.py` at lines 137-143 and 173:

```python
# Line 137-143: Comment filtering
recent_comments = issue["comments"][-3:]  # Last 3 comments
for comment in recent_comments:
    body = comment["body"][:200].replace("\n", " ").strip()  # 200 char limit

# Line 173: Issue body truncation  
**Body:** {issue["body"][:1500]}
```

## Architecture Review

**Good News**: No other unwanted filtering found in the architecture:
- ✅ **Data Collection**: All GitHub data collected completely intact 
- ✅ **Data Storage**: Full data preserved in JSON files
- ✅ **JSON Format**: Uses standard formatting (indent=2) - not a data loss issue
- ✅ **No Legacy Complexity**: Clean architecture, no backwards compatibility needed

**The filtering only occurs during AI processing**, not data collection/storage.

## Solution Requirements

### 1. Remove All Data Filtering
- **Comments**: Include ALL comments, not just last 3
- **Comment Length**: Include full comment body text, not truncated to 200 chars
- **Issue Body**: Include full issue body, not truncated to 1500 chars

### 2. Maintain Compact JSON Format
- Format JSON for AI processing without newlines/indentation (use `json.dumps()` with no spacing)
- Replace newlines within text content with spaces for readability
- This saves tokens without removing data

### 3. Preserve Token Optimization
- Keep the existing newline-to-space replacement for readability
- Keep user attribution format (`{user}: {body}`)
- Use compact JSON serialization when sending data to LLM

## Implementation Plan

### Files to Modify
- `github_issue_analysis/ai/processors.py` - Remove filtering logic in `_format_issue_prompt()`

### Specific Changes
1. **Remove comment count limit**: Change `issue["comments"][-3:]` to `issue["comments"]`
2. **Remove comment truncation**: Remove `[:200]` from comment body processing
3. **Remove issue body truncation**: Remove `[:1500]` from issue body
4. **Add compact JSON formatting**: When including structured data in prompts, use `json.dumps(data, separators=(',', ':'))` for compact format

### Expected Outcome
- LLM receives ALL comment data for accurate analysis
- Token usage optimized through compact formatting, not data removal
- No backwards compatibility issues (current architecture preserved)
- Better AI accuracy through complete context access

## Testing Requirements
- Test with issues containing many comments (>3) to verify all are included
- Test with issues containing long comments (>200 chars) to verify full content
- Test with issues containing long bodies (>1500 chars) to verify full content
- Verify compact JSON formatting reduces token usage vs pretty-printed JSON
- Confirm existing tests still pass

## Success Criteria
- [ ] All comments included in AI processing (no count limit)
- [ ] Full comment content preserved (no character truncation)
- [ ] Full issue body content preserved (no character truncation) 
- [ ] JSON formatted compactly to save tokens without data loss
- [ ] All existing functionality preserved
- [ ] Tests pass with new behavior

## Priority: HIGH
This fixes a fundamental issue where the AI lacks necessary context for accurate analysis.