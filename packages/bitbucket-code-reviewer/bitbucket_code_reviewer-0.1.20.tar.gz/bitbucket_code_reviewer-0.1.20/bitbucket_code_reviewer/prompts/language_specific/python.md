# Python-Specific Review Guidelines

## Code Style & Conventions

### PEP 8 Compliance
- **Line Length**: Maximum 88 characters (Black default)
- **Imports**: One import per line, alphabetical ordering
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Whitespace**: 4 spaces for indentation, no tabs

### Type Hints
- Use type hints for function parameters and return values
- Include type hints for complex data structures
- Consider using `typing` module for advanced types

## Python Best Practices

### Error Handling
```python
# Good: Specific exception handling
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    return None
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise
```

```python
# Avoid: Bare except clauses
try:
    result = risky_operation()
except:  # ❌ Too broad
    pass
```

### List/Dict Comprehensions
- Use comprehensions for simple transformations
- Avoid nested comprehensions that reduce readability
- Consider generator expressions for large datasets

### Context Managers
```python
# Good: Using context managers
with open('file.txt', 'r') as f:
    content = f.read()

# Good: Custom context manager
class DatabaseConnection:
    def __enter__(self):
        self.conn = get_connection()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
```

### String Formatting
```python
# Preferred: f-strings (Python 3.6+)
name = "Alice"
message = f"Hello, {name}!"

# Also acceptable: .format()
message = "Hello, {}!".format(name)

# Avoid: % formatting for new code
message = "Hello, %s!" % name
```

## Performance Considerations

### Efficient Data Structures
- Use `set()` for membership testing
- Use `collections.deque` for frequent append/pop operations
- Consider `collections.Counter` for counting operations

### Memory Management
- Use generators for large data processing
- Avoid creating unnecessary lists
- Use `__slots__` for classes with many instances

### Database Operations
- Use connection pooling
- Implement proper transaction management
- Use parameterized queries to prevent SQL injection

## Security Guidelines

### Input Validation
```python
from pydantic import BaseModel

class UserInput(BaseModel):
    username: str
    email: str

    @validator('username')
    def username_must_be_valid(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
```

### Secrets Management
- Never hardcode secrets in source code
- Use environment variables or secure vaults
- Implement proper key rotation

### Web Security (Flask/Django)
- Always validate and sanitize user inputs
- Use CSRF protection
- Implement proper session management
- Sanitize database queries

## Testing Standards

### Unit Testing
```python
import pytest
from unittest.mock import Mock, patch

def test_user_creation():
    # Arrange
    mock_db = Mock()
    user_service = UserService(mock_db)

    # Act
    result = user_service.create_user("alice", "alice@example.com")

    # Assert
    assert result is not None
    mock_db.save.assert_called_once()
```

### Test Coverage
- Aim for 80%+ code coverage
- Test edge cases and error conditions
- Use fixtures for reusable test data

## Package Management

### Dependencies
- Pin dependency versions for reproducibility
- Use `requirements.txt` or `pyproject.toml`
- Regularly update dependencies for security patches
- Minimize the number of external dependencies

### Virtual Environments
- Always use virtual environments
- Include `.python-version` for pyenv users
- Document setup instructions

## Documentation

### Docstrings
```python
def calculate_total(items: List[Item]) -> float:
    """Calculate the total price of items in the cart.

    Args:
        items: List of Item objects to calculate total for

    Returns:
        The total price as a float

    Raises:
        ValueError: If any item has invalid pricing

    Example:
        >>> items = [Item(price=10.0), Item(price=5.0)]
        >>> calculate_total(items)
        15.0
    """
```

### README and Documentation
- Include setup and usage instructions
- Document API endpoints and data models
- Provide code examples and tutorials
