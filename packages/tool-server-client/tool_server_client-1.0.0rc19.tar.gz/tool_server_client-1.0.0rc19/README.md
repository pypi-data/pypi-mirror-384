# Tool Server SDK

A Python SDK for Tool Server that allows seamless control of computer desktop environments from your applications.

## Installation

```bash
# Install using pip
pip install tool-server-client
```

## Usage

### Basic Usage

```python
"""
Examples for Computer Use SDK
"""
import asyncio
from tool_server_client.client import new_computer_use_client
from tool_server_client.async_client import new_async_computer_use_client

# Run: PYTHONPATH=./src python -m tool_server_client.examples
def example_basic_operations():
    """
    Example of basic mouse and keyboard operations
    """
    # Initialize the client
    client = new_computer_use_client("http://localhost:8102", auth_key="1234567890")

    # Get screen size
    screen_size_response = client.get_screen_size()
    print(f"Screen size: {screen_size_response}")
    ret = client.move_mouse(100,100)
    print(f"MoveMouse response: {ret}")
    ret = client.click_mouse(100,120,"right")
    print(f"ClickMouse response: {ret}")
    client.type_text("Hello World")
    print(f"TypeText response: {client.type_text('Hello World')}")
    client.press_key("enter")
    print(f"PressKey response: {client.press_key('enter')}")
    client.click_mouse(100,100,"right")
    print(f"ClickMouse response: {client.click_mouse(100,100,"right")}")
    ret = client.get_cursor_position()
    print(f"Cursor position: {ret}")
    ret = client.take_screenshot()
    print(f"TakeScreenshot response: {ret.Result.screenshot[:100]}")


async def example_async_basic_operations():
    """
    Example of basic mouse and keyboard operations using async client
    """
    # Initialize the async client
    client = await new_async_computer_use_client("http://localhost:8102", auth_key="your-secret-api-key-here")
    try:
        # Get screen size
        screen_size_response = await client.get_screen_size()
        print(f"Screen size: {screen_size_response}")
        
        # Move mouse
        ret = await client.move_mouse(100, 100)
        print(f"MoveMouse response: {ret}")
        
        # Click mouse
        ret = await client.click_mouse(100, 120, "right")
        print(f"ClickMouse response: {ret}")
        
        # Type text
        ret = await client.type_text("Hello World")
        print(f"TypeText response: {ret}")
        
        # Press key
        ret = await client.press_key("enter")
        print(f"PressKey response: {ret}")
        
        # Click mouse again
        ret = await client.click_mouse(100, 100, "right")
        print(f"ClickMouse response: {ret}")
        
        # Get cursor position
        ret = await client.get_cursor_position()
        print(f"Cursor position: {ret}")
        
        # Take screenshot
        ret = await client.take_screenshot()
        print(f"TakeScreenshot response: {ret.Result.screenshot[:100]}")

    finally:
        await client.__aexit__(None, None, None)


async def example_async_concurrent_operations():
    """
    Example of concurrent operations using async client
    """
    client = await new_async_computer_use_client("http://localhost:8102", auth_key="your-secret-api-key-here")
    try:
        # Perform multiple operations concurrently
        tasks = [
            client.move_mouse(100, 100),
            client.type_text("Hello"),
            client.press_key("enter"),
            client.get_cursor_position(),
        ]
        
        # Wait for all operations to complete
        results = await asyncio.gather(*tasks)
        
        # Print results
        for i, result in enumerate(results):
            print(f"Operation {i+1} result: {result}")
    finally:
        await client.__aexit__(None, None, None)


def example_recording_and_file_operations():
    """
    Example of recording and file operations
    """
    import time
    client = new_computer_use_client("http://localhost:8102", auth_key="your-secret-api-key-here")
    ret = client.start_video_recording(quality="high", format="mp4", resolution="1920x1080", framerate=30, max_duration=10)
    print(f"StartVideoRecording response: {ret}")
    time.sleep(5)
    ret = client.stop_video_recording()
    print(f"StopVideoRecording response: {ret}")
    ret = client.file_operation(command="read", path=ret.Result.file_path, mode="binary")
    print(f"FileOperation response: {ret}")

if __name__ == "__main__":
    print("Running basic operations example:")
    example_basic_operations()
    
    print("\nRunning async basic operations example:")
    asyncio.run(example_async_basic_operations())
    
    print("\nRunning async concurrent operations example:")
    asyncio.run(example_async_concurrent_operations())

    print("\nRunning recording and file operations example:")
    example_recording_and_file_operations()
```

### Features

The SDK provides the following operations:

#### Mouse Operations

- `move_mouse(x, y)`: Move mouse to specified coordinates
- `click_mouse(x, y, button="left", press=False, release=False)`: Click mouse at specified position
- `press_mouse(x, y, button="left")`: Press mouse button at specified position
- `release_mouse(x, y, button="left")`: Release mouse button at specified position
- `drag_mouse(source_x, source_y, target_x, target_y)`: Drag from source position to target position
- `scroll(x, y, scroll_direction="up", scroll_amount=1)`: Scroll mouse wheel at specified position

#### Keyboard Operations

- `press_key(key)`: Press specified key
- `type_text(text)`: Type specified text

#### Screen Operations

- `take_screenshot()`: Take a screenshot
- `get_cursor_position()`: Get current cursor position
- `get_screen_size()`: Get screen size

#### System Operations

- `wait(duration)`: Wait for specified duration (milliseconds)
- `change_password(username, new_password)`: Change user password

## Examples

For more usage examples, see [examples.py](src/tool_server_client/examples.py).

## Advanced Usage

### Custom API Version

```python
from tool_server_client.client import ComputerUseClient

client = ComputerUseClient(base_url="http://your-server.com", api_version="2020-04-01")
```

### Handling Responses

API calls return a dictionary containing operation results that can be checked for success:

```python
response = client.move_mouse(100, 100)
if response.success:
    print("Mouse moved successfully")
else:
    print(f"Error: {response.error}")
```

## Error Handling

The SDK handles HTTP errors and raises exceptions when API calls fail:

```python
try:
    client.move_mouse(100, 100)
except Exception as e:
    print(f"Operation failed: {e}")
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
