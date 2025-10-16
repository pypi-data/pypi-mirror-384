# retry-function-plugin

A reusable async retry handler with exponential backoff and structured logging.

### 🚀 Features
- Handles retries automatically with exponential backoff and jitter.
- Logs all attempts with correlation IDs for traceability.
- Supports timeout and async/await-based retry patterns.

### 🧩 Example Usage
```python
import asyncio
from retry_function_plugin import execute_with_retry

async def unstable_task():
    import random
    if random.random() < 0.7:
        raise Exception("Random failure!")
    return "Success!"

async def main():
    result, error = await execute_with_retry(unstable_task, max_retries=3, base_delay=1)
    if error:
        print(f"Task failed: {error}")
    else:
        print(f"Task succeeded: {result}")

asyncio.run(main())
