import pandera as pa
from pandera.typing import Series,DateTime
from typing import Optional


class BaseCostSchema(pa.DataFrameModel):
    employer_id: Series[str] = pa.Field(coerce=True, nullable=False)
    blocked: Series[bool] = pa.Field(coerce=True, nullable=False)

    class Config:
        coerce = True
        strict = False

# Cost Carrier schema
from pydantic import BaseModel, Field

class CostCarrierCreateSchema(BaseModel):
    """
    Pydantic schema for creating cost carriers
    """
    # Required Fields
    employer_id: str = Field(..., description="Employer identifier")
    blocked: bool = Field(..., description="Whether the cost carrier is blocked")
    cost_carrier_id: str = Field(..., description="Cost carrier identifier")
    cost_carrier_description: str = Field(..., description="Description of the cost carrier")

    class Config:
        from_attributes = True

class CostCarrierUpdateSchema(CostCarrierCreateSchema):
    """
    Pydantic schema for updating cost carriers.
    Inherits all fields from CostCarrierCreateSchema.
    """
    pass

class CostCarrierGetSchema(pa.DataFrameModel):
    employer_id: Series[str] = pa.Field(coerce=True)
    cost_carrier: Series[str] = pa.Field(coerce=True)
    description: Series[str] = pa.Field(coerce=True)
    blocked: Series[bool] = pa.Field(coerce=True)
    modified_date: Series[str] = pa.Field(coerce=True)

    class Config:
        coerce = True
        strict = True

class CostCenterSchema(BaseModel):
    """
    Pydantic schema for cost centers
    """
    # Required Fields from BaseCostSchema
    employer_id: str = Field(..., description="Employer identifier")
    blocked: bool = Field(..., description="Whether the cost center is blocked")

    # Required Fields
    cost_center_id: str = Field(..., description="Cost center identifier")
    cost_center_description: str = Field(..., description="Description of the cost center")

    # Optional Fields
    cost_center_type: str | None = Field(None, description="Type of the cost center")
    default_currency: str | None = Field(None, description="Default currency for the cost center")

    class Config:
        from_attributes = True

class CostCenterGetSchema(pa.DataFrameModel):
    employer_id: Series[str] = pa.Field(coerce=True)
    cost_center: Series[str] = pa.Field(coerce=True)
    description: Series[str] = pa.Field(coerce=True)
    blocked: Series[bool] = pa.Field(coerce=True)
    modified_date: Series[str] = pa.Field(coerce=True)

    class Config:
        coerce = True
        strict = True
