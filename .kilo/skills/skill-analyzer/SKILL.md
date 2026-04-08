---
name: skill-analyzer
description: "Use when: analyzing an existing skill to understand its capabilities, use cases, triggers, limitations, and how to invoke it. Also use when evaluating skill quality, finding gaps, or determining if a skill fits a specific use case. Triggers: 'analyze skill', 'what does this skill do', 'skill review', 'evaluate skill', 'skill analysis', 'understand skill', 'skill capability', 'can this skill'. NOT for: creating new skills (use skill-creator), or when skill documentation is sufficient."
---

# Skill Analyzer

Analyze an existing skill to understand its capabilities, use cases, triggers, limitations, and how to properly invoke it.

## When to Use This Skill

Use this skill when:
- You encounter an unfamiliar skill and need to understand its purpose
- Evaluating if a skill fits a specific use case
- Finding gaps or limitations in existing skills
- Reviewing skill quality and completeness
- Understanding how to invoke a skill
- Determining skill dependencies and requirements
- Comparing multiple skills for a task

Do NOT use when:
- Creating new skills (use skill-creator skill)
- Skill documentation is already clear and complete
- Simple skill lookup (use skill-lookup)
- Direct skill execution is needed

## Analysis Process

### 1. Extract Skill Metadata
Read the skill's SKILL.md and extract:
- **Name**: The skill identifier
- **Description**: Use when / Triggers / NOT for pattern
- **Domain**: What category it belongs to
- **Complexity**: Beginner, Intermediate, Advanced

### 2. Identify Capabilities
Determine what the skill can do:
- Primary functions
- Supported operations
- Input/output patterns
- Integration points

### 3. Determine Triggers
Map when this skill should be activated:
- Explicit triggers (specific keywords)
- Implicit triggers (use case patterns)
- Context-based triggers

### 4. Identify Limitations
Document what the skill cannot do:
- Exclusions in description
- Known gaps
- Prerequisites not met

### 5. Assess Requirements
Evaluate dependencies:
- Required API keys
- External tools needed
- Environment setup
- Python packages or modules

### 6. Quality Assessment
Rate the skill on:
- Documentation clarity
- Example completeness
- Edge case handling
- Maintainability

## Output Format

```markdown
## Skill Analysis: [Skill Name]

### Overview
[Brief summary of what the skill does]

### Capabilities
- Primary: [Main function]
- Secondary: [Additional functions]
- Supported: [List of supported operations]

### Trigger Mapping
| Trigger Phrase | When to Use |
|----------------|-------------|
| [phrase 1] | [use case 1] |
| [phrase 2] | [use case 2] |

### Requirements
- **API Keys**: [List]
- **Dependencies**: [Packages/Tools]
- **Environment**: [Setup required]

### Limitations
- Cannot: [Limitations]
- NOT for: [Exclusions]

### Invocation
How to use: [Step-by-step]

### Quality Score
- Documentation: ⭐⭐⭐⭐⭐
- Examples: ⭐⭐⭐⭐☆
- Edge Cases: ⭐⭐⭐⭐⭐

### Similar Skills
- [Other skills that overlap]
```

## Example Analysis

### Input: Reading a Python Testing Skill

**Skill Content (simplified):**
```markdown
---
name: pytest-testing
description: "Use when: writing tests with pytest, running test suites, debugging test failures. Triggers: 'test', 'pytest', 'unittest', 'test coverage'. NOT for: production code."
---

# Pytest Testing

Write and run pytest tests...
```

**Analysis Output:**
```markdown
## Skill Analysis: pytest-testing

### Overview
Comprehensive pytest testing skill for writing, running, and debugging Python tests.

### Capabilities
- Primary: Write pytest tests
- Secondary: Run test suites, debug failures
- Supported: Unit tests, integration tests, fixtures, mocking

### Trigger Mapping
| Trigger Phrase | When to Use |
|----------------|-------------|
| "write tests" | Creating new test files |
| "run pytest" | Executing test suite |
| "test coverage" | Checking coverage reports |
| "debug test" | Troubleshooting failures |

### Requirements
- Python 3.8+
- pytest package
- Optional: pytest-cov, pytest-mock

### Limitations
- NOT for production code testing (only development)
- Doesn't cover E2E testing

### Quality Score
- Documentation: ⭐⭐⭐⭐⭐
- Examples: ⭐⭐⭐⭐⭐
- Edge Cases: ⭐⭐⭐⭐☆
```

## Comparison Feature

When comparing multiple skills:

```
### Skill Comparison

| Aspect | Skill A | Skill B |
|--------|---------|---------|
| Coverage | 80% | 95% |
| Complexity | Intermediate | Advanced |
| Dependencies | None | API Key |
| Best For | Quick tasks | Full workflows |
```

## Gap Analysis

Identify what the skill is missing:

```
### Gap Analysis

Missing from skill:
- [ ] Error handling documentation
- [ ] Examples for edge cases
- [ ] Performance considerations
- [ ] Alternative approaches

Recommendations:
1. Add examples for timeout handling
2. Document known limitations
3. Add troubleshooting section
```

## Invocation Recommendations

Based on analysis, provide guidance:

```
### How to Use This Skill

1. **Direct Invocation**: "Use pytest-testing to write tests for my auth module"
2. **As Subtask**: Include in workflow with specific requirements
3. **For Debugging**: "Run pytest-testing to diagnose why tests fail"

Best practices:
- Provide specific test file paths
- Mention expected coverage threshold
- Include any custom fixtures needed
```

## Constraints

- Focus on actionable insights, not just summarization
- Always provide invocation guidance
- Note version requirements explicitly
- Flag any security-sensitive operations
- Identify skill overlaps to avoid duplication