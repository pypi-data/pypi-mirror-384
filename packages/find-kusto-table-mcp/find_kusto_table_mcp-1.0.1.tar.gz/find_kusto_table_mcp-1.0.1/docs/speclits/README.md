# Feature Speclits

This directory contains feature-specific documentation ("speclits") that describe individual features, enhancements, or significant changes to the codebase.

## Purpose

Speclits serve as:
- **Feature Documentation**: Detailed descriptions of specific features
- **Implementation Records**: How features were implemented and why
- **Change History**: What changed, when, and for what reason
- **Technical Specifications**: Design decisions and technical details

## Naming Convention

Speclits document features and architectural patterns:
- `FEATURE_<name>.md` - For major features (e.g., FEATURE_query_handle_system.md)
- `REFACTOR_<name>.md` - For architectural changes (e.g., REFACTOR_tool_organization.md)
- `POLICY_<name>.md` - For policies and requirements (e.g., POLICY_free_models_only.md)

**DO NOT create FIX or ENHANCEMENT speclits:**
- Bug fixes belong in CHANGELOG.md only
- Feature enhancements should update the existing feature speclit
- Use "Changes" sections within feature speclits to track evolution

## Structure

Each speclit should include:
1. **Title**: Clear feature/change name
2. **Date**: When the work was completed
3. **Overview**: Brief summary of the change
4. **Motivation**: Why this change was needed
5. **Implementation**: Technical details of what was done
6. **Files Changed**: List of modified/created files
7. **Impact**: How this affects users/agents
8. **Future Considerations**: Any follow-up work needed

## When to Create a Speclit

Create a NEW speclit when:
- Adding a **new feature** (document what it does and how to use it)
- Performing **major refactoring** (document new architecture and patterns)
- Establishing a **policy** (document requirements and rationale)

Update an EXISTING speclit when:
- Enhancing a feature (add to "Changes" section)
- Changing feature behavior (update documentation and add change note)
- Adding configuration options (update feature documentation)

## When NOT to Create a Speclit

**NEVER create speclits for:**
- Bug fixes (use CHANGELOG.md instead)
- Minor enhancements (update existing feature speclit)
- Typo corrections
- Simple configuration changes
- Routine maintenance
- Documentation-only updates

**Rule of thumb**: Speclits answer "What is this feature?" not "What did I fix today?"
