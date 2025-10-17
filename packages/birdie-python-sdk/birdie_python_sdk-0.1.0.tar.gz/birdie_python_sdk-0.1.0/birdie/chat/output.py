from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ChatImageOutput(BaseModel):
    image: str = Field(..., description="A base64 image")


class ChatVideoOutput(BaseModel):
    video: str = Field(..., description="A base64 video file")


class ChatSoundOutput(BaseModel):
    sound: str = Field(..., description="A base64 sound file")


class MarkdownParagraph(BaseModel):
    candidates: List[str] = Field(
        ..., description="", min_length=3, max_length=3
    )


class ChatMarkdownOutput(BaseModel):
    markdown: Union[str, MarkdownParagraph] = Field(...)


class ChatOOXMLOutput(BaseModel):
    document: str = Field(...)
    type: Literal["pptx", "docx"]


class ChatMessageOutput(BaseModel):
    chat_message: str = Field(...)


class ChatStructuredOutput(BaseModel):
    output: Dict[str, Any]


class ChatOutput(BaseModel):
    message: ChatMessageOutput = Field(...)
    image: Optional[ChatImageOutput] = Field(None)
    markdown: Optional[ChatMarkdownOutput] = Field(None)
    ooxml: Optional[ChatOOXMLOutput] = Field(None)
    sound: Optional[ChatSoundOutput] = Field(None)
    video: Optional[ChatVideoOutput] = Field(None)
