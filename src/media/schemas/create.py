from typing import List, Optional, Union

from pydantic import BaseModel, AnyUrl


class CreateMediaUrlsSchema(BaseModel):
    urls: List[AnyUrl]
    category_id: Optional[int | str] = None
    category_name: Optional[str] = None
