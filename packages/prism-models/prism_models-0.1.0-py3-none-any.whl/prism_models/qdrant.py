from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4, ValidationError
from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.engine.interfaces import Dialect
from enum import Enum

class ChunkTypeEnum(str, Enum):
    TEXT = "TEXT"
    Q_AND_A = "Q/A"
    AUGMENTED_TEXT = "AUGMENTED_TEXT"
    AUGMENTED_Q_AND_A = "AUGMENTED_Q/A"

class QdrantVectorPayload(BaseModel):
    virtual_collection_names: Optional[List[str]] = Field(
        default=None, description="Names of the virtual collections"
    )
    uuid: Optional[UUID4] = Field(
        default=None, description="Unique identifier for the vector"
    )
    chunk_text: Optional[str] = Field(
        default=None, description="Text content of the chunk"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the vector is active"
    )
    deleted_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the vector was deleted"
    )

    chunk_type: ChunkTypeEnum = Field(
        default=ChunkTypeEnum.TEXT, 
        description="Type of the chunk"
    )

    class Config:
        orm_mode = True


class DestinationVectorPayload(QdrantVectorPayload):
    destination_id: Optional[int] = Field(
        default=None, description="ID of the destination associated with the chunk"
    )
    report_title: Optional[str] = Field(
        default=None, description="Title of the report"
    )
    destination_name: Optional[str] = Field(
        default=None, description="Name of the destination"
    )


class PydanticType(TypeDecorator):
    """
    A SQLAlchemy column type that validates JSON data against a Pydantic model.
    
    Usage:
        class MyModel(Base):
            data: Mapped[dict] = mapped_column(PydanticType(MyPydanticModel))
    """
    impl = JSON
    cache_ok = True
    
    def __init__(self, pydantic_model: type[BaseModel], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pydantic_model = pydantic_model
    
    def process_bind_param(self, value: Any, dialect: Dialect) -> dict | None:
        """
        Validate and convert Pydantic model to dict before storing in database.
        """
        if value is None:
            return None
        
        if isinstance(value, self.pydantic_model):
            return value.model_dump(mode='json')
        
        if isinstance(value, dict):
            try:
                validated = self.pydantic_model(**value)
                return validated.model_dump(mode='json')
            except ValidationError as e:
                raise ValueError(f"Invalid data for {self.pydantic_model.__name__}: {e}")
        
        raise ValueError(f"Expected {self.pydantic_model.__name__} or dict, got {type(value)}")
    
    def process_result_value(self, value: dict | None, dialect: Dialect) -> BaseModel | None:
        """
        Convert dict from database to Pydantic model instance.
        """
        if value is None:
            return None
        
        try:
            return self.pydantic_model(**value)
        except ValidationError as e:
            print(f"Warning: Invalid data in database for {self.pydantic_model.__name__}: {e}")
            return None
