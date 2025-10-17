from typing import ByteString, Optional, Union

from pydantic import BaseModel, Field


class ChatTextInput(BaseModel):
    text_message: str = Field(...)


class ChatFileInput(BaseModel):
    text_message: Optional[str] = Field(None)
    file: ByteString = Field(...)


class ChatCanvanReferenceInput(BaseModel):
    text_message: str = Field(...)
    start_position: int = Field(...)
    end_position: int = Field(...)


class ChatInput(BaseModel):
    input_string: Union[ChatTextInput, ChatFileInput, ChatCanvanReferenceInput]
