import aiohttp
import base64
import ssl
from typing import Dict, Any, Literal, Optional
from .entity import (
    MoveMouseRequest,
    ClickMouseRequest,
    PressMouseRequest,
    ReleaseMouseRequest,
    DragMouseRequest,
    ScrollRequest,
    PressKeyRequest,
    TypeTextRequest,
    WaitRequest,
    TakeScreenshotRequest,
    GetCursorPositionRequest,
    GetScreenSizeRequest,
    ChangePasswordRequest,
    BaseResponse,
    CursorPositionResponse,
    ScreenSizeResponse,
    ScreenshotResponse,
    ReadFileRequest,
    ReadMultiFilesRequest,
    ListDirectoryRequest,
    SearchFileRequest,
    SearchCodeRequest,
    GetFileInfoRequest,
    CreateFileRequest,
    ListSessionsRequest,
    ListProcessesRequest,
    ExecuteCommandRequest,
    ReadFileResponse,
    ReadMultiFilesResponse,
    ListDirectoryResponse,
    SearchFileResponse,
    SearchCodeResponse,
    GetFileInfoResponse,
    CreateFileResponse,
    ListSessionsResponse,
    ListProcessesResponse,
    ExecuteCommandResponse,
    FileOperationRequest,
    FileOperationResponse,
)


class AsyncComputerUseClient:
    """
    Asynchronous version of Computer Use Tool Server Client SDK
    """

    def __init__(self, base_url: str = "http://localhost:8102", api_version: str = "2020-04-01", auth_key: str = "", client_ca: Optional[str] = None):
        """
        Initialize the asynchronous Computer Use SDK client
        
        Args:
            base_url: Base URL of the Computer Use Tool Server
            api_version: API version to use
            auth_key: Authentication key
            client_ca: Path to client CA certificate file for HTTPS server certificate validation
        """
        self.base_url = base_url
        self.api_version = api_version
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": auth_key,
        }
        self.client_ca = client_ca
        self._session = None
        self._connector = None

    async def __aenter__(self):
        if self.client_ca:
            ssl_context = ssl.create_default_context()
            ssl_context.load_verify_locations(self.client_ca)
            self._connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(connector=self._connector)
        else:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None
        if self._connector:
            await self._connector.close()
            self._connector = None

    async def _make_request(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an asynchronous request to the Computer Use Tool Server
        
        Args:
            action: Action to perform
            params: Parameters for the action
            
        Returns:
            Response from the server
        """
        if not self._session:
            if self.client_ca:
                ssl_context = ssl.create_default_context()
                ssl_context.load_verify_locations(self.client_ca)
                self._connector = aiohttp.TCPConnector(ssl=ssl_context)
                self._session = aiohttp.ClientSession(connector=self._connector)
            else:
                self._session = aiohttp.ClientSession()
            
        url = self.base_url
        # Convert all parameters to strings
        str_params = {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in params.items()}
        str_params.update({
            "Version": self.api_version,
            "Action": action
        })
        
        async with self._session.get(
            url,
            params=str_params,
            headers=self.headers,
            allow_redirects=False
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def move_mouse(self, x: int, y: int) -> BaseResponse:
        """Move the mouse to the specified position"""
        request = MoveMouseRequest(PositionX=x, PositionY=y)
        response_data = await self._make_request("MoveMouse", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def click_mouse(
            self,
            x: int,
            y: int,
            button: Literal["left", "right", "middle", "double_click", "double_left",
                            "Left", "Right", "Middle", "DoubleClick", "DoubleLeft"] = "left",
            press: bool = False,
            release: bool = False
    ) -> BaseResponse:
        """Click the mouse at the specified position"""
        request = ClickMouseRequest(
            x=x,
            y=y,
            button=button,
            press=press,
            release=release
        )
        response_data = await self._make_request("ClickMouse", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def press_mouse(
            self,
            x: int,
            y: int,
            button: Literal["left", "right", "middle",
                            "Left", "Right", "Middle"] = "left"
    ) -> BaseResponse:
        """Press the mouse button at the specified position"""
        request = PressMouseRequest(
            x=x,
            y=y,
            button=button
        )
        response_data = await self._make_request("PressMouse", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def release_mouse(
            self,
            x: int,
            y: int,
            button: Literal["left", "right", "middle",
                            "Left", "Right", "Middle"] = "left"
    ) -> BaseResponse:
        """Release the mouse button at the specified position"""
        request = ReleaseMouseRequest(
            x=x,
            y=y,
            button=button
        )
        response_data = await self._make_request("ReleaseMouse", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def drag_mouse(
            self,
            source_x: int,
            source_y: int,
            target_x: int,
            target_y: int
    ) -> BaseResponse:
        """Drag the mouse from source to target position"""
        request = DragMouseRequest(
            source_x=source_x,
            source_y=source_y,
            target_x=target_x,
            target_y=target_y
        )
        response_data = await self._make_request("DragMouse", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def scroll(
            self,
            x: int,
            y: int,
            scroll_direction: Literal["up", "down", "left", "right",
                                      "Up", "Down", "Left", "Right"] = "up",
            scroll_amount: int = 1
    ) -> BaseResponse:
        """Scroll at the specified position"""
        request = ScrollRequest(
            x=x,
            y=y,
            scroll_direction=scroll_direction,
            scroll_amount=scroll_amount
        )
        response_data = await self._make_request("Scroll", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def press_key(self, key: str) -> BaseResponse:
        """Press the specified key"""
        request = PressKeyRequest(key=key)
        response_data = await self._make_request("PressKey", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def type_text(self, text: str) -> BaseResponse:
        """Type the specified text"""
        request = TypeTextRequest(text=text)
        response_data = await self._make_request("TypeText", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def wait(self, duration: int) -> BaseResponse:
        """Wait for the specified duration in milliseconds"""
        request = WaitRequest(duration=duration)
        response_data = await self._make_request("Wait", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)

    async def take_screenshot(self) -> ScreenshotResponse:
        """Take a screenshot"""
        request = TakeScreenshotRequest()
        response_data = await self._make_request("TakeScreenshot", request.model_dump(by_alias=True))
        return ScreenshotResponse(**response_data)

    async def get_cursor_position(self) -> CursorPositionResponse:
        """Get the current cursor position"""
        request = GetCursorPositionRequest()
        response_data = await self._make_request("GetCursorPosition", request.model_dump(by_alias=True))
        return CursorPositionResponse(**response_data)

    async def get_screen_size(self) -> ScreenSizeResponse:
        """Get the screen size"""
        request = GetScreenSizeRequest()
        response_data = await self._make_request("GetScreenSize", request.model_dump(by_alias=True))
        return ScreenSizeResponse(**response_data)

    async def change_password(self, username: str, new_password: str) -> BaseResponse:
        """Change the password for the specified user"""
        request = ChangePasswordRequest(
            username=username,
            new_password=new_password
        )
        response_data = await self._make_request("ChangePassword", request.model_dump(by_alias=True))
        return BaseResponse(**response_data)
    
    async def file_operation(self, **params) -> FileOperationResponse:
        """
        Execute a file operation
        Args:
            **params: Parameters for the file operation
        Returns:
            Response from the server
        """
        params = FileOperationRequest.model_validate(
            params).encde_content().model_dump(by_alias=True, exclude_unset=True)
        response_data = await self._make_request("FileOperation", params)
        return FileOperationResponse(**response_data).decode_content()
    

    async def read_file(self, file_path: str) -> ReadFileResponse:
        """
        Read the content of a file

        Args:
            file_path: Path to the file

        Returns:
            Response containing the file content in Result.content
        """
        request = ReadFileRequest(file_path=file_path)
        response_data = await self._make_request("ReadFile", request.model_dump(by_alias=True))
        return ReadFileResponse(**response_data)._decode_content()

    async def read_multi_files(self, file_paths: list[str]) -> ReadMultiFilesResponse:
        """
        Read the content of multiple files
        Args:
            file_paths: List of paths to the files
        Returns:
            Response containing the file contents in Result.contents
        """
        request = ReadMultiFilesRequest(file_paths=file_paths)
        response_data = await self._make_request("ReadMultiFiles", request.model_dump(by_alias=True))
        return ReadMultiFilesResponse(**response_data)._decode_content()

    async def list_directory(self, dir_path: str) -> ListDirectoryResponse:
        """
        List the files in a directory
        Args:
            dir_path: Path to the directory
        Returns:
            Response containing the list of files in Result.files
        """
        request = ListDirectoryRequest(dir_path=dir_path)
        response_data = await self._make_request("ListDirectory", request.model_dump(by_alias=True))
        print(f"list_directory response: {response_data}")
        return ListDirectoryResponse(**response_data)

    async def search_file(self, dir_path: str, pattern: str) -> SearchFileResponse:
        """
        Search for files in a directory
        Args:
            dir_path: Path to the directory
            pattern: Pattern to search for
        Returns:
            Response containing the list of files in Result.files
        """
        request = SearchFileRequest(dir_path=dir_path, pattern=pattern)
        response_data = await self._make_request("SearchFile", request.model_dump(by_alias=True))
        return SearchFileResponse(**response_data)

    async def search_code(self, file_path: str, pattern: str) -> SearchCodeResponse:
        """
        Search for code in a file
        Args:
            file_path: Path to the file
            pattern: Pattern to search for
        Returns:
            Response containing the code in Result.content
        """
        request = SearchCodeRequest(file_path=file_path, pattern=pattern)
        response_data = await self._make_request("SearchCode", request.model_dump(by_alias=True))
        return SearchCodeResponse(**response_data)

    async def get_file_info(self, file_path: str) -> GetFileInfoResponse:
        """
        Get information about a file
        Args:
            file_path: Path to the file
        Returns:
            Response containing the file information in Result.info
        """
        request = GetFileInfoRequest(file_path=file_path)
        response_data = await self._make_request("GetFileInfo", request.model_dump(by_alias=True))
        return GetFileInfoResponse(**response_data)

    async def create_file(self, file_path: str, content: bytes) -> CreateFileResponse:
        """
        Create a file
        Args:
            file_path: Path to the file
            content: Content of the file
        Returns:
            Response containing the file information in Result.info
        """
        request = CreateFileRequest(file_path=file_path, content=base64.encodebytes(content))
        response_data = await self._make_request("CreateFile", request.model_dump(by_alias=True))
        return CreateFileResponse(**response_data)

    async def list_sessions(self) -> ListSessionsResponse:
        """
        List the sessions of terminals
        Returns:
            Response containing the list of sessions in Result.output
        """
        request = ListSessionsRequest()
        response_data = await self._make_request("ListSessions", request.model_dump(by_alias=True))
        return ListSessionsResponse(**response_data)

    async def list_processes(self) -> ListProcessesResponse:
        """
        List the processes
        Returns:
            Response containing the list of processes in Result.processes
        """
        request = ListProcessesRequest()
        response_data = await self._make_request("ListProcesses", request.model_dump(by_alias=True))
        return ListProcessesResponse(**response_data)

    async def execute_command(self, command: str, timeout: int = 10) -> ExecuteCommandResponse:
        """
        Execute a command
        Args:
            command: Command to execute
            timeout: Timeout for the command in seconds
        Returns:
            Response containing the output of the command in Result.output
        """
        request = ExecuteCommandRequest(command=command, timeout=timeout)
        response_data = await self._make_request("ExecuteCommand", request.model_dump(by_alias=True))
        return ExecuteCommandResponse(**response_data)

async def new_async_computer_use_client(endpoint: str, auth_key: str = "", client_ca: Optional[str] = None) -> AsyncComputerUseClient:
    """Create a new asynchronous Computer Use client instance"""
    client = AsyncComputerUseClient(base_url=endpoint, auth_key=auth_key, client_ca=client_ca)
    await client.__aenter__()
    return client 