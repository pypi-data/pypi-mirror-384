from typing import List, Dict, Optional, Any

from pydantic import BaseModel


class OneFileDef(BaseModel):
    name: Optional[str] = ''
    url: Optional[str] = ''
    type: Optional[str] = ''


class FileDef(BaseModel):
    type: Optional[str] = ''
    main: Optional[str] = ''
    inputType: Optional[str] = ''
    urls: List[OneFileDef] = []


class TaskDataDef(BaseModel):
    content: Any
    files: Optional[FileDef] = None

    def add_file_def_data(self, type: str, main: str, input_type: str, urls: List[Dict[str, str]]):
        self.files = FileDef(
            type=type,
            main=main,
            inputType=input_type,
            urls=[OneFileDef(**url) for url in urls]
        )
