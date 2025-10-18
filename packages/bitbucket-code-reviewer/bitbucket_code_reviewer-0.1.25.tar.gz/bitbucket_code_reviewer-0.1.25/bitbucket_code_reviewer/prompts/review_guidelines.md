# Code Review Guidelines

## General Principles

### Code Quality
- **Readability**: Code should be self-documenting with clear variable names and structure
- **Maintainability**: Code should be easy to modify and extend
- **Consistency**: Follow established patterns and conventions
- **Simplicity**: Prefer simple solutions over complex ones

### Documentation
- **Code Comments**: Explain why, not what (what should be obvious from the code)
- **Function Documentation**: Document purpose, parameters, return values, and side effects
- **API Documentation**: Provide clear usage examples for public interfaces

### Error Handling
- **Defensive Programming**: Validate inputs and handle edge cases
- **Meaningful Errors**: Provide clear, actionable error messages
- **Graceful Degradation**: Fail safely when possible
- **Logging**: Include appropriate logging for debugging and monitoring

## Security Considerations

### Input Validation
- Validate all external inputs (user data, API responses, file contents)
- Use parameterized queries for database operations
- Sanitize data before processing or display

### Authentication & Authorization
- Never store sensitive credentials in code
- Use secure token handling practices
- Implement proper access controls

### Data Protection
- Encrypt sensitive data at rest and in transit
- Avoid logging sensitive information
- Follow data minimization principles

## Performance Guidelines

### Efficiency
- Avoid unnecessary operations in loops
- Use appropriate data structures for the use case
- Consider memory usage and garbage collection impact
- Profile performance-critical code paths

### Scalability
- Design for horizontal scaling when appropriate
- Avoid single points of failure
- Consider resource usage patterns

## Testing Requirements

### Test Coverage
- Unit tests for all business logic
- Integration tests for component interactions
- End-to-end tests for critical user journeys

### Test Quality
- Tests should be fast, reliable, and maintainable
- Use descriptive test names that explain the behavior being tested
- Test edge cases and error conditions

## Architecture & Design

### Separation of Concerns
- Each component should have a single responsibility
- Avoid tight coupling between modules
- Use dependency injection for testability

### Design Patterns
- Use established patterns appropriately
- Avoid over-engineering simple problems
- Document architectural decisions

### Code Organization
- Group related functionality together
- Use clear module and package structures
- Follow language-specific conventions
