import base64
import binascii
from typing import Literal, Dict, Any, Optional, List, Tuple, Union
from pydantic import BaseModel, Field


class MBaseModel(BaseModel):
    class Config:
        populate_by_name = True


class MoveMouseRequest(MBaseModel):
    """Request model for moving mouse"""
    x: int = Field(0, description="x position", alias="PositionX")
    y: int = Field(0, description="y position", alias="PositionY")


class ClickMouseRequest(MBaseModel):
    """Request model for clicking mouse"""
    x: int = Field(0, description="x position", alias="PositionX")
    y: int = Field(0, description="y position", alias="PositionY")
    button: Literal["left", "right", "middle", "double_click", "double_left",
                    "Left", "Right", "Middle", "DoubleClick", "DoubleLeft"] = Field(
        "left", description="mouse button", alias="Button"
    )
    press: bool = Field(False, description="press mouse", alias="Press")
    release: bool = Field(False, description="release mouse", alias="Release")


class PressMouseRequest(MBaseModel):
    """Request model for pressing mouse"""
    x: int = Field(0, description="x position", alias="PositionX")
    y: int = Field(0, description="y position", alias="PositionY")
    button: Literal["left", "right", "middle",
                    "Left", "Right", "Middle"] = Field(
        "left", description="mouse button", alias="Button"
    )


class ReleaseMouseRequest(MBaseModel):
    """Request model for releasing mouse"""
    x: int = Field(0, description="x position", alias="PositionX")
    y: int = Field(0, description="y position", alias="PositionY")
    button: Literal["left", "right", "middle",
                    "Left", "Right", "Middle"] = Field(
        "left", description="mouse button", alias="Button"
    )


class DragMouseRequest(MBaseModel):
    """Request model for dragging mouse"""
    source_x: int = Field(0, description="source x position", alias="SourceX")
    source_y: int = Field(0, description="source y position", alias="SourceY")
    target_x: int = Field(0, description="target x position", alias="TargetX")
    target_y: int = Field(0, description="target y position", alias="TargetY")


class ScrollRequest(MBaseModel):
    """Request model for scrolling"""
    scroll_direction: Literal["up", "down", "left", "right",
                              "Up", "Down", "Left", "Right"] = Field(
        "up", description="scroll direction", alias="Direction")
    scroll_amount: int = Field(0, description="scroll amount", alias="Amount")
    x: int = Field(0, description="x position", alias="PositionX")
    y: int = Field(0, description="y position", alias="PositionY")


class PressKeyRequest(MBaseModel):
    """Request model for pressing key"""
    key: str = Field("", description="key", alias="Key")


class TypeTextRequest(MBaseModel):
    """Request model for typing text"""
    text: str = Field("", description="text", alias="Text")


class WaitRequest(MBaseModel):
    """Request model for waiting"""
    duration: int = Field(
        0, description="duration in milliseconds", alias="Duration")


class TakeScreenshotRequest(MBaseModel):
    """Request model for taking screenshot"""
    pass


class GetCursorPositionRequest(MBaseModel):
    """Request model for getting cursor position"""
    pass


class GetScreenSizeRequest(MBaseModel):
    """Request model for getting screen size"""
    pass


class ChangePasswordRequest(MBaseModel):
    """Request model for changing password"""
    username: str = Field("", description="username", alias="Username")
    new_password: str = Field(
        "", description="new password", alias="NewPassword")


class ResponseMetadataModel(BaseModel):
    """Response metadata model"""
    RequestId: str = ""
    Action: str
    Version: str
    Service: str = "ecs"
    Region: str = ""


class BaseResponse(BaseModel):
    """Base response model for all API calls"""
    ResponseMetadata: Optional[ResponseMetadataModel] = None
    Result: Optional[Dict[str, Any]] = None


class CursorPositionResource(MBaseModel):
    """Resource model for cursor position"""
    x: int = Field(0, description="x position", alias="PositionX")
    y: int = Field(0, description="y position", alias="PositionY")


class CursorPositionResponse(BaseResponse):
    """Response model for getting cursor position"""
    Result: Optional[CursorPositionResource] = None


class ScreenSizeResource(MBaseModel):
    """Resource model for screen size"""
    width: int = Field(0, description="width", alias="Width")
    height: int = Field(0, description="height", alias="Height")


class ScreenSizeResponse(BaseResponse):
    """Response model for getting screen size"""
    Result: Optional[ScreenSizeResource] = None


class ScreenshotResource(MBaseModel):
    """
        Resource model for screenshot
        Response example:
        {
            "Screenshot": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x+AAx4BoVgmXjgAAAAASUVORK5CYII="
        }
        The screenshot is a base64 encoded string of the screenshot.
    """
    screenshot: str = Field("", alias="Screenshot")


class ScreenshotResponse(BaseResponse):
    """Response model for taking screenshot"""
    Result: Optional[ScreenshotResource] = None

class ReadFileRequest(MBaseModel):
    file_path: str = Field("", description="file path", alias="FilePath")

class ReadFileResource(MBaseModel):
    content: bytes = Field(b"", description="content", alias="Content")
    error: str = Field("", description="error", alias="Error")
class ReadFileResponse(BaseResponse):
    """Response model for reading file"""
    Result: Optional[ReadFileResource] = None

    def _decode_content(self):
        if self.Result is None:
            return self
        if self.Result.content is None:
            return self
        self.Result.content = base64.b64decode(self.Result.content)
        return self

class ReadMultiFilesRequest(MBaseModel):
    file_paths: list[str] = Field([], description="file paths", alias="FilePaths")

class ReadMultiFilesResponse(BaseResponse):
    """Response model for reading multi files"""
    def _decode_content(self):
        if self.Result is None:
            return self
        print(f"result : {self.Result}")
        for _, v in self.Result.items():
            if isinstance(v, dict):
                if v.get("Content") is not None:
                    v["Content"] = base64.b64decode(v["Content"])
        return self

class ListDirectoryRequest(MBaseModel):
    dir_path: str = Field("", description="dir path", alias="DirPath")

class ListDirectoryResource(MBaseModel):
    files: list[str] = Field([], description="files", alias="Files")
    error: str = Field("", description="error", alias="Error")

class ListDirectoryResponse(BaseResponse):
    """Response model for listing directory"""
    Result: Optional[ListDirectoryResource] = None

class SearchFileRequest(MBaseModel):
    dir_path: str = Field("", description="dir path", alias="DirPath")
    pattern: str = Field("", description="pattern", alias="Pattern")

class SearchFileResource(MBaseModel):
    files: list[str] = Field([], description="files", alias="Files")
    error: str = Field("", description="error", alias="Error")

class SearchFileResponse(BaseResponse):
    """Response model for searching file"""
    Result: Optional[SearchFileResource] = None

class SearchCodeRequest(MBaseModel):
    file_path: str = Field("", description="file path", alias="FilePath")
    pattern: str = Field("", description="pattern", alias="Pattern")

class SearchCodeResource(MBaseModel):
    content: str = Field("", description="content", alias="Content")
    error: str = Field("", description="error", alias="Error")

class SearchCodeResponse(BaseResponse):
    """Response model for searching code"""
    Result: Optional[SearchCodeResource] = None

class GetFileInfoRequest(MBaseModel):
    file_path: str = Field("", description="file path", alias="FilePath")

class GetFileInfoResource(MBaseModel):
    info: dict = Field({}, description="info", alias="Info")
    error: str = Field("", description="error", alias="Error")

class GetFileInfoResponse(BaseResponse):
    """Response model for getting file info"""
    Result: Optional[GetFileInfoResource] = None

class CreateFileRequest(MBaseModel):
    file_path: str = Field("", description="file path", alias="FilePath")
    content: bytes = Field(b"", description="content", alias="Content")

class CreateFileResource(MBaseModel):
    error: str = Field("", description="error", alias="Error")

class CreateFileResponse(BaseResponse):
    """Response model for creating file"""
    Result: Optional[CreateFileResource] = None

class ListSessionsRequest(MBaseModel):
    pass

class ListSessionsResource(MBaseModel):
    ouptut: str = Field("", description="output", alias="Output")
    error: str = Field("", description="error", alias="Error")

class ListSessionsResponse(BaseResponse):
    """Response model for listing sessions"""
    Result: Optional[ListSessionsResource] = None

class ListProcessesRequest(MBaseModel):
    pass

class ListProcessesResource(MBaseModel):
    processes: list[dict] = Field([], description="processes", alias="Processes")

class ListProcessesResponse(BaseResponse):
    """Response model for listing processes"""
    Result: Optional[ListProcessesResource] = None


class ExecuteCommandRequest(MBaseModel):
    command: str = Field("", description="command", alias="Command")
    session: Optional[int] = Field(
        None, description="session", alias="Session")
    list_sessions: Optional[bool] = Field(
        False, description="list sessions", alias="ListSessions")
    check_session: Optional[int] = Field(
        None, description="check session", alias="CheckSession")
    timeout: int = Field(10, description="timeout", alias="Timeout")


class ExecuteCommandResource(MBaseModel):
    """Resource model for executing command"""
    stdout: Optional[str] = Field(None, description="stdout", alias="Stdout")
    stderr: Optional[str] = Field(None, description="stderr", alias="Stderr")
    code: Optional[int] = Field(None, description="code", alias="Code")
    sessions: Optional[List[str]] = Field(
        None, description="sessions", alias="Sessions")
    exists: Optional[bool] = Field(None, description="exists", alias="Exists")


class ExecuteCommandResponse(BaseResponse):
    """Response model for executing command"""
    Result: Optional[ExecuteCommandResource] = None

FileAction = Literal[
    "read",
    "read_multi",
    "exists",
    "append",
    "write",
    "delete",
    "search",
    "move",
    "copy",
    "list",
    "view",
    "create",
    "info",
]


class FileOperationRequest(MBaseModel):
    """Request model for file operation"""
    command: FileAction = Field(description="command", alias="Command")
    path: Optional[str] = Field(None, description="path", alias="Path")
    paths: Optional[List[str]] = Field(
        None, description="paths", alias="Paths")
    content: Optional[bytes] = Field(
        None, description="content", alias="Content")
    # e.g., "binary" for read/write
    mode: Optional[str] = Field(None, description="mode", alias="Mode")
    recursive: Optional[bool] = Field(
        None, description="recursive", alias="Recursive")  # For delete directory
    src: Optional[str] = Field(
        None, description="src", alias="Src")  # For move/copy
    dst: Optional[str] = Field(
        None, description="dst", alias="Dst")  # For move/copy
    pattern: Optional[str] = Field(
        None, description="pattern", alias="Pattern")  # For search
    view_range: Optional[Union[List[int], Tuple[int, int]]] = Field(
        None, description="view range", alias="ViewRange")  # For view command

    def encde_content(self):
        """Encode content to base64"""
        if "content" in self.model_fields_set and self.content:
            self.content = base64.encodebytes(self.content)
        return self


class SingleFileContent(MBaseModel):
    """Resource model for single file content"""
    content: Optional[bytes] = Field(
        None, description="content", alias="Content")
    error: Optional[str] = Field(None, description="error", alias="Error")


class FileOperationResource(MBaseModel):
    """Resource model for file operation"""
    content: Optional[bytes] = Field(
        None, description="content", alias="Content")
    contents: Optional[dict[str, SingleFileContent]] = Field(
        None, description="contents", alias="Contents")
    exists: Optional[bool] = Field(None, description="exists", alias="Exists")
    files: Optional[List[str]] = Field(
        None, description="files", alias="Files")
    success: bool = Field(True, description="success", alias="Success")
    message: Optional[str] = Field(
        None, description="message", alias="Message")
    info: Optional[dict[str, Any]] = Field(
        None, description="info", alias="Info")
    view_content: Optional[str] = Field(
        None, description="view content", alias="ViewContent")  # For view command
    error: Optional[str] = Field(
        None, description="error", alias="Error")  # For error


class FileOperationResponse(BaseResponse):
    """Response model for file operation"""
    Result: Optional[FileOperationResource] = None

    def decode_content(self):
        """Decode content from base64"""
        if self.Result and self.Result.content and is_base64(self.Result.content):
            self.Result.content = base64.b64decode(self.Result.content)
        if self.Result and self.Result.contents:
            for key, value in self.Result.contents.items():
                if value and value.content and is_base64(value.content):
                    value.content = base64.b64decode(value.content)
        if self.Result and self.Result.view_content:
            self.Result.view_content = base64.b64decode(
                self.Result.view_content).decode("utf-8")
        return self


def is_base64(s: bytes) -> bool:
    try:
        base64.decodebytes(s)
        return True
    except (binascii.Error, ValueError):
        return False


class StartVideoRecordingRequest(MBaseModel):
    """Request model for starting video recording"""
    quality: str = Field(
        "", description="recording quality: low/medium/high/custom, empty means medium", alias="Quality")
    format: str = Field(
        "", description="recording format: mp4/avi/mkv, empty means mp4", alias="Format")
    resolution: str = Field(
        "", description="custom resolution, e.g., '1920x1080', only valid when quality=custom", alias="Resolution")
    framerate: int = Field(
        0, description="custom framerate, only valid when quality=custom", alias="Framerate")
    max_duration: int = Field(
        0, description="max recording duration (seconds), 0 means use default value", alias="MaxDuration")


class StopVideoRecordingRequest(MBaseModel):
    """Request model for stopping video recording"""
    pass


class VideoRecordingResource(MBaseModel):
    """Resource model for video recording operations"""
    output: Optional[str] = Field(
        None, description="output message", alias="Output")
    file_name: Optional[str] = Field(
        None, description="recording file name", alias="FileName")
    file_path: Optional[str] = Field(
        None, description="recording file path", alias="FilePath")
    file_size: Optional[str] = Field(
        None, description="recording file size", alias="FileSize")
    status: Optional[str] = Field(
        None, description="recording status", alias="Status")
    message: Optional[str] = Field(
        None, description="status message", alias="Message")
    error: Optional[str] = Field(
        None, description="error message", alias="Error")


class StartVideoRecordingResponse(BaseResponse):
    """Response model for starting video recording"""
    Result: Optional[VideoRecordingResource] = None


class StopVideoRecordingResponse(BaseResponse):
    """Response model for stopping video recording"""
    Result: Optional[VideoRecordingResource] = None
