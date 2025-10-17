# Output Format Instructions

## Response Format Specification

You MUST respond with valid JSON containing exactly these fields:

**REQUIRED FIELDS:**
- **summary**: String describing overall code quality and findings
- **severity_counts**: Object with four integer counts: critical, major, minor, info
- **changes**: Array of issue objects (each with: file_path, line, severity, category, title, description, suggestion, code_snippet, suggested_code, rationale)
- **positives**: Array of strings with positive feedback
- **recommendations**: Array of strings with suggestions

**VALID SEVERITY VALUES:** "critical", "major", "minor", "info"
**VALID CATEGORY VALUES:** "security", "performance", "maintainability", "architecture", "style"

**EXAMPLE STRUCTURE:**
- summary: "Code review summary here" (string)
- severity_counts: Object like (critical: 0, major: 1, minor: 2, info: 0)
- changes: Array of objects, each with fields: file_path, line, severity, category, title, description, suggestion, code_snippet, suggested_code, rationale
- positives: Array of strings like (Good practice found)
- recommendations: Array of strings like (Suggestion here)

## Important Notes
- Respond with **raw JSON only** - no markdown, no explanations
- Use the exact field names and types specified in the schema
- Arrays can be empty if no items apply
- All severity counts should be integers (0 or higher)

