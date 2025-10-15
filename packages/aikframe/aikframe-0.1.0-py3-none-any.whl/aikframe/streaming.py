import aiohttp
import asyncio
import typing

class Stream:
    def __init__(self):
        self.__stream: asyncio.Queue[typing.Optional[str]] = None
    async def pipe(self):
        while True:
            s = await self.__stream.get()
            if s is None:
                return
            yield s.encode("utf-8")
    async def write(self, content: typing.Optional[str]):
        await self.__stream.put(content)

class YunhuStreaming:
    def __init__(self, token: str, recvId: str, recvType: str, method: typing.Literal["text", "markdown", "html"]):
        self.token = token
        self.recvId = recvId
        self.recvType = recvType
        self.method = method
        self.result: typing.Any = None
        self.stream = Stream()
        asyncio.create_task(self.__sendpower())
    async def __sendpower(self):
        async with aiohttp.ClientSession() as session:
            result = await session.post(
                url=f"https://chat-go.jwzhd.com/open-apis/v1/bot/send-stream?token={self.token}&recvId={self.recvId}&recvType={self.recvType}&contentType={self.method}",
                data=self.stream.pipe()
            )
            self.result = await result.json()

class YunhuStreamingContext:
    def __init__(self, token: str, recvId: str, recvType: str, method: typing.Literal["text", "markdown", "html"]):
        self.token = token
        self.recvId = recvId
        self.recvType = recvType
        self.method = method
        self.__stream: typing.Optional[YunhuStreaming] = None
        self.__is_stopped = False
    async def attach(self, content: str):
        if self.__is_stopped:
            raise ReferenceError("Context are already exited!")
        if self.__stream is None:
            self.__stream = YunhuStreaming(
                token=self.token,
                recvId=self.recvId,
                recvType=self.recvType,
                method=self.method
            )
        self.__stream.stream.write(content)
    async def release(self):
        if not self.__is_stopped:
            self.__is_stopped = True
            if self.__stream is not None:
                self.__stream.stream.write(None)
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args, **kwargs):
        await self.release()
    @property
    def result(self):
        return self.__stream.result
    @property
    def state(self):
        if self.__is_stopped:
            return "released"
        if self.__stream is None:
            return "initial"
        return "connected"