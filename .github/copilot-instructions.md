# GitHub Copilot Instructions for Python Preferences

## General Guidelines
- **String Quotes**: Always use single quotes for strings.
    ```python
    example_string = 'This is a string'
    ```
- **Docstrings**: Always add docstring comments to functions using triple quotes.
    ```python
    def add(a: int, b: int) -> int:
        """
        Calculate the sum of two integers.
        
        Args:
            a: The first integer
            b: The second integer
            
        Returns:
            The sum of a and b
        """
        return a + b
    ```

- **Type Hints**: Always add type hints for function arguments and return types.
    ```python
    def greet(name: str) -> str:
            return f'Hello, {name}'
    ```

- **Validation**: Use Pydantic for any data validation.
    ```python
    from pydantic import BaseModel

    class User(BaseModel):
            id: int
            name: str
            email: str

    user = User(id=1, name='John Doe', email='john.doe@example.com')
    ```

- **Code Quality**: Validate the accuracy and proper usage of code including:
    - Check for and update calls to deprecated apis
    - Validate code conventions for the language and framework are being followed
    - Suggest applicable patterns for solving common problems
    - Place models in the models package at src/app/models