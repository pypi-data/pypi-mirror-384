# Chorey: The Asynchronous, Type-Safe Python Pipeline Framework 🚀

**Chorey** is a modern, lightweight, and highly testable framework for building complex data and control flows in Python. It allows you to chain asynchronous functions, manage shared state, implement conditional routing, and handle concurrency, **all while preserving end-to-end type safety**.


## Key Features ✨

- **Asynchronous by Design** ⚡️: Built on `asyncio` for efficient, non-blocking I/O-bound tasks.
- **Intuitive Chaining**  🔗: Construct complex workflows using a fluent `.next()` API.
- **Advanced Control Flow**  🚦: Built-in support for concurrent execution (`.branch()`) and conditional logic (`.route()`).
- **Resilience**  🛡️: Configure automatic retries and custom failure callbacks for any step.
- **Type Safety** ✅: **Chorey**'s biggest selling point: **enforces strict type contracts between all pipeline stages**.
- **Visualization**  📊: Automatically generate **Mermaid diagrams** for visual inspection and debugging.

## Quick Start  🏁

### Installation  🛠️

```bash
pip install chorey
# or with cli tools
pip install chorey[cli]
```

### Example Pipeline  🧑‍💻

Define a pipeline by chaining asynchronous functions with the `step` factory:

```python
from chorey import step
from dataclasses import dataclass
import asyncio

@dataclass
class User:
    id: int
    name: str

async def fetch_user(user_id: int) -> User:
    # Simulate API call
    return User(id=user_id, name="Jane Doe")

async def welcome_user(user: User) -> str:
    return f"Welcome, {user.name}!"

# Define the pipeline chain
pipeline = step(fetch_user).next(welcome_user)

if __name__ == "__main__":
    result = asyncio.run(pipeline.feed(42))
    print(result) # Output: Welcome, Jane Doe!
```

## Documentation  📚

For comprehensive guides on shared context, routing, branching, and CLI usage, please visit the [Official Chorey Documentation](https://anwitars.github.io/chorey). Currently the code documentation is not reliable, so please refer to the docs for the most accurate information.

## Roadmap 🛤️

This is the first iteration of **Chorey**. Other than documentation, I do not have more plans yet, as I am currently collecting feedback. If you have any feature requests or ideas, - until I set up a more formal process on GitHub - please [email me](mailto:anwitarsbusiness@gmail.com?subject=chorey%3A%20).

---

© 2025 anwitars | Licensed under the MIT License
