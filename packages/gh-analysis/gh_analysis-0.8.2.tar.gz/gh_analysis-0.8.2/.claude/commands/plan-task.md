Think very carefully about this task planning request. I need you to:

1. **Analyze the current codebase architecture** by reading:
   - docs/architecture.md
   - docs/data-schemas.md  
   - docs/api-reference.md
   - docs/cli-reference.md
   - CLAUDE.md for development patterns

2. **Consider the task requirements critically**:
   - Break down the functionality into specific components
   - Identify dependencies and integration points
   - Consider edge cases and error handling
   - Think about testing requirements
   - Evaluate impact on existing systems

3. **Ask clarifying questions** if any of these are unclear:
   - Specific functionality details
   - User interface requirements
   - Data models and validation needs
   - Integration requirements
   - Performance or scalability concerns
   - Authentication/authorization needs

4. **Create a comprehensive task file** using the template structure with:
   - Clear, specific acceptance criteria
   - Detailed implementation notes
   - Validation steps with specific commands
   - Dependencies and architectural considerations

Do NOT start implementing code - this is planning only. Focus on understanding requirements thoroughly and creating a roadmap for implementation.

When you have a draft review it to verify that:
* The top level description provides a clear an concise description of new features. Do not use 'comprehensive' to describe a feature provide very clear and specific explanation of what new functionality will be available when the task is done.
* The implementation is specific and doesn't leave it up to the agent to decide implementation. The planning should have already designed the implementation and have a concrete approach documented. This doesn't mean all code is written but all features and functionality are well defined.
* Tests are spelled out exactly, not using placeholders like "test-repo" all tests have clearly defined commands and if data is needed it is collected.
* YOU MUST CRITICALLY make sure that label-updates if run always has "--dry-run" no testing or development should ever post a change back to github. It's ok to get a summary from the AI but not post to github.

Task to plan: $ARGUMENTS
