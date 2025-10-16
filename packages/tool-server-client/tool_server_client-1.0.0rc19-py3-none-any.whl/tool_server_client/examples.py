"""
Examples for Computer Use SDK
"""
import asyncio
from .client import new_computer_use_client
from .async_client import new_async_computer_use_client

# Run: PYTHONPATH=./src python -m tool_server_client.examples
def example_basic_operations():
    """
    Example of basic mouse and keyboard operations
    """
    # Initialize the client
    client = new_computer_use_client("http://localhost:8102", auth_key="your-secret-api-key-here")

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
    print(f"FileOperation response: {ret.Result.content[:100]}")

if __name__ == "__main__":
    print("Running basic operations example:")
    example_basic_operations()
    
    print("\nRunning async basic operations example:")
    asyncio.run(example_async_basic_operations())
    
    print("\nRunning async concurrent operations example:")
    asyncio.run(example_async_concurrent_operations())

    print("\nRunning recording and file operations example:")
    example_recording_and_file_operations()