# Tool Usage Instructions

## CRITICAL: Efficient Review Strategy

**ALWAYS START WITH PR ANALYSIS** - Focus on changed files primarily.

## Available Tools

### 1. read_file (PRIMARY TOOL)
**Purpose**: Read the contents of source code files
**When to use**: To analyze changed files and validate imports/dependencies
**Best practices**:
- Focus on files shown in the PR diff
- Read full files (the tool returns complete content)
- Maximum 7 files total per review (≤ 2 non-diff files for context)
**Example**: `read_file("src/api/endpoints.py")`

### 2. list_directory (LIMITED, TARGETED USE)
**Purpose**: List files and subdirectories in a specific directory
**When to use**: When you need to see what files exist in a directory
**Restrictions**:
- Use sparingly - only when you need to discover file structure
- Don't explore recursively through entire codebase
**Example**: `list_directory("src/api")`

### 3. search_files (FILENAME SEARCH ONLY)
**Purpose**: Find files by FILENAME pattern - NOT for searching file contents
**When to use**: When you know part of a filename but not the exact path
**IMPORTANT**: This searches FILENAMES ONLY, not content inside files
**Examples**:
- `search_files("*.py")` - all Python files
- `search_files("**/*test*.py")` - all test files recursively  
- `search_files("*repository*.py")` - files with "repository" in name
**DON'T DO**: `search_files("MyClassName")` - this won't find files containing that class
**DO INSTEAD**: Use patterns like `search_files("*my_class*.py")` or just read the likely file

### 4. get_file_info (RARELY NEEDED)
**Purpose**: Get metadata about a file (size, modified date, extension)
**When to use**: Almost never needed for code review
**Skip this**: Just use read_file instead

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
