# Tool Usage Instructions

## CRITICAL: Efficient Review Strategy

**ALWAYS START WITH PR ANALYSIS** - Focus on changed files primarily.

## Available Tools

### 1. get_pr_diff (PRIMARY TOOL)
**Purpose**: Get the actual files changed in this PR
**When to use**: FIRST THING in every review
**Best practices**:
- This tells you exactly what changed
- Use this to identify which 3-5 files to focus on
- Don't read files that aren't in the diff

### 2. list_directory (LIMITED, TARGETED USE)
**Purpose**: Locate specific imports/config/dependencies when necessary
**When to use**: When a changed file references code you must quickly locate
**Restrictions**:
- Do NOT explore entire codebase
- Use "." (root) sparingly to locate a specific known filename or pattern
- Avoid deep traversal; stop when the target is found

### 3. read_file_contents (SELECTIVE, WITH SMALL CONTEXT)
**Purpose**: Read specific sections of files
**When to use**: Primarily for changed files; if strictly necessary to validate correctness (imports/config), you may read up to 2 non-diff files
**Restrictions**:
- Maximum 7 files total per review (non-diff files ≤ 2)
- Focus on changed sections only; include 3-5 lines of context

## Tool Usage Rules

### ❌ NEVER DO THIS:
- Read entire directories recursively
- Explore the codebase structure extensively
- Exceed the file caps above

### ✅ ALWAYS DO THIS:
1. **Start with get_pr_diff** to see what actually changed
2. **Identify 3-5 key files** from the diff
3. **Read those files** with targeted sections; if required, read ≤ 2 supporting files to validate imports/config
4. **Complete review quickly** - don't over-analyze

### File Priority (when selecting which files to read):
1. **HIGH**: Files with security changes, API endpoints, database operations
2. **MEDIUM**: Business logic files, configuration changes
3. **LOW**: Test files, documentation, generated code
4. **NEVER**: Dependencies, third-party code, entire directories

## Efficiency Guidelines

- **MAX 7 FILES**: Read at most 7 files total (including ≤ 2 non-diff files)
- **TARGETED READING**: Read only changed sections + minimal context
- **STOP EARLY**: Complete review as soon as you have key findings
- **NO EXPLORATION**: Don't try to understand the entire codebase

## Response Format Reminder

Your final answer MUST be valid JSON with this structure:
- summary: Brief overview (string)
- severity_counts: Object with counts for critical/major/minor/info (integers)
- changes: Array of issue objects
- positives: Array of positive feedback strings
- recommendations: Array of suggestion strings
