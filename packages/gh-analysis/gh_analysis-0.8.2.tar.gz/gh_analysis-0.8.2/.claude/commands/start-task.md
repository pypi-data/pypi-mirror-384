Think very carefully about starting this task. I need you to:

1. **Find and read the task file** by fuzzy matching the name "$ARGUMENTS" against files in the tasks/ directory

2. **Create the development environment** CRITICAL STEP:
   - Create worktree: `git worktree add trees/$ARGUMENTS -b feature/$ARGUMENTS`
   - Change to the worktree directory: `cd trees/$ARGUMENTS`
   - Install dependencies: `uv sync --all-extras`

3. **Begin implementation** following the task specification with careful attention to:
   - The exact requirements and acceptance criteria
   - Following existing code patterns and architecture
   - Implementing comprehensive tests
   - Adding proper type annotations
   - Following the quality standards in CLAUDE.md
   - Document your progress in the task as you go

4. **Use the todo system** to track your progress through the implementation

5. **Use Subagents** to implement and research things in parallel whenever it's reasonable to do so

Start working on task: $ARGUMENTS

Remember to think very carefully about the implementation approach and follow all the established patterns in the codebase.
