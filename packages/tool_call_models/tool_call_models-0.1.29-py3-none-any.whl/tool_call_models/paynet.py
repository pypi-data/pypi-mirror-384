from pydantic import BaseModel, Field
from typing import List, Optional, Union
from .base import BaseToolCallModel
import json


class Category(BaseModel):
    id: Union[int, str] = Field(default=0)
    name: str = Field(default="")
    imagePath: Optional[str] = None
    s3Url: Optional[str] = None

    def filter_for_llm(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class Supplier(BaseModel):
    id: Union[int, str] = Field(default=0)
    name: str = Field(default="")
    categoryId: Union[int, str] = Field(default=0)
    s3Url: Optional[str] = Field(default="")

    def filter_for_llm(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class Value(BaseModel):
    value: int
    name: str

    def filter_for_llm(self):
        return {
            "value": self.value,
            "name": self.name,
        }


class FieldOptions(BaseModel):
    identName: str = Field(default="")
    name: str = Field(default="")
    order: int = Field(default=0)
    type: str = Field(default="")
    pattern: Optional[str] = None
    minValue: Optional[int] = None
    maxValue: Optional[int] = None
    fieldSize: Optional[int] = None
    isMain: Optional[bool] = None
    valueList: Optional[List[Value]] = None

    def filter_for_llm(self):
        return {
            "identName": self.identName,
            "name": self.name,
            "order": self.order,
            "type": self.type,
            "pattern": self.pattern if self.pattern else None,
            "minValue": self.minValue if self.minValue else None,
            "maxValue": self.maxValue if self.maxValue else None,
            "fieldSize": self.fieldSize if self.fieldSize else None,
            "isMain": self.isMain if self.isMain else None,
            "valueList": [x.filter_for_llm() for x in self.valueList]
            if self.valueList
            else [],
        }


class Response(BaseModel):
    payload: List[Category] = Field(default_factory=list)
    code: Optional[Union[int, str]] = Field(default=None)


class SuppliersField(Response):
    checkUp: bool = Field(default=False)
    checkUpWithResponse: bool = Field(default=False)
    checkUpAfterPayment: bool = Field(default=False)
    fieldList: List[FieldOptions] = Field(default_factory=list)


class SupplierFieldsResponse(BaseToolCallModel, Response):
    payload: SuppliersField = Field(default_factory=SuppliersField)

    def filter_for_llm(self):
        return json.dumps(
            self.payload.filter_for_llm(),
            ensure_ascii=False,
            indent=2,
        )


class SupplierByCategoryResponse(BaseToolCallModel, Response):
    payload: List[Supplier] = Field(default_factory=list)

    def filter_for_llm(self):
        return json.dumps(
            [x.filter_for_llm() for x in self.payload],
            ensure_ascii=False,
            indent=2,
        )


class CategoriesResponse(BaseToolCallModel, Response):
    payload: List[Category] = Field(default_factory=list)

    def filter_for_llm(self):
        return json.dumps(
            [x.filter_for_llm() for x in self.payload],
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.getcwd())
    from tests.cache_responses import (
        supplier_fields_response,
        suppliers_list_response,
    )

    a = SupplierByCategoryResponse(**suppliers_list_response)
    b = SupplierFieldsResponse(**supplier_fields_response)
    print(a)
    print(b)
