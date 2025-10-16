"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.
"""

import datetime as dt
from boto3_assist.utilities.string_utility import StringUtility
from boto3_assist.dynamodb.dynamodb_model_base import (
    DynamoDBModelBase,    
)
from boto3_assist.utilities.serialization_utility import JsonConversions
from typing import Optional, Dict, Any, Union, List


class BaseModel(DynamoDBModelBase):
    """
    The Base DB Model
    Sets a common set of properties for all models
    """

    def __init__(self) -> None:
        super().__init__()
        self.id: str | None= None  # make the id's sortable
        self.tenant_id: str | None = None
        self.user_id: str | None = None
        self.created_utc_ts: float | None = None
        self.updated_utc_ts: float | None = None
        self.deleted_utc_ts: Optional[float] = None

        self.__model_version: str = "1.0.0"
        self._metadata: Dict[str, Any] | None = None
        
        self._table_name: Optional[str] = None
        self.created_by_id: Optional[str]= None
        self.updated_by_id: Optional[str]= None
        self.deleted_by_id: Optional[str]= None
        self.version: float= 1.0
        self.is_multi_record: bool = False
    
    def prep_for_save(self):
        """
        Prepares the model for saving by setting the id and timestamps
        """
        self.id = self.id or StringUtility.generate_sortable_uuid()
        self.created_utc_ts = self.created_utc_ts or dt.datetime.now(dt.UTC).timestamp()
        # always update the updated ts to the latest timestamp
        self.updated_utc_ts = dt.datetime.now(dt.UTC).timestamp()

    def is_deleted(self) -> bool:
        """
        Returns True if the model is deleted (has a deleted timestamp).
        """
        from decimal import Decimal
        return self.deleted_utc_ts is not None and isinstance(self.deleted_utc_ts, (int, float, Decimal))
    
    

    @property
    def model_version(self) -> str:
        """
        Returns the model version for this model
        """
        return self.__model_version

    @model_version.setter
    def model_version(self, value: str):
        """
        Defines a model version.  All will start with the base model
        version, but you can override this as your model changes.
        Use your services to parse the older models correct (if needed)
        Which means a custom mapping of data between versioning for
        backward compatibility
        """
        self.__model_version = value

    @property
    def model_name(self) -> str:
        """
        Returns the record type for this model
        """
        return StringUtility.camel_to_snake(self.__class__.__name__)

    @model_name.setter
    def model_name(self, value: str):
        """
        This is read-only but we don't want an error during serialization
        """
        pass

    @property
    def model_name_plural(self) -> str:
        """
        Returns the record type for this model
        """
        return self.model_name + "s"

    @model_name_plural.setter
    def model_name_plural(self, value: str):
        """
        This is read-only but we don't want an error during serialization
        """
        pass

    @property
    def table_name(self) -> str | None:
        """
        Returns the table name for this model.
        This is useful if you create multiple tables
        For a single table design you can leave this as null
        """
        return self._table_name

    @table_name.setter
    def table_name(self, value: str | None):
        """
        Defines the table name for this model
        """
        self._table_name = value

    
    @property
    def metadata(self) -> Dict[str, Any] | None:
        """
        Returns the metadata for this model
        """
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any] | None):
        """
        Defines the metadata for this model
        """

        if value is not None and not isinstance(value, dict):
            raise ValueError("metadata must be a dictionary")

        self._metadata = value

    def get_pk_id(self) -> str:
        """
        Returns the fully formed primary key for this model.
        This is typically in the form of "<resource_type>#<guid>"
        """
        pk = self.to_resource_dictionary().get("pk", None)
        if not pk:
            raise ValueError("The primary key is not set")
        return pk

    def get_sk_id(self) -> str | None:
        """
        Returns the fully formed sort key for this model.
        This is typically in the form of "<resource_type>#<guid>"
        """
        sk = self.to_resource_dictionary().get("sk", None)
        
        return sk

    def to_float_or_none(self, value: Any) -> float | None:
        """
        Converts a value to a float or None
        """
        if isinstance(value, str):
            value = value.strip().replace("$", "").replace(",", "").replace(".", "")

        if value is None:
            return None
        try:
            return float(value)
        except:
            return None

    @classmethod
    def load(cls, payload: Dict[str, Any]) -> 'BaseDBModel':
        """
        Create a model instance from a UI payload (camelCase).
        Automatically converts camelCase to snake_case before model creation.
        
        Args:
            payload: Dictionary with camelCase keys from the UI
            
        Returns:
            Model instance with data loaded from the converted payload
            
        Raises:
            ValueError: If payload is None or not a dictionary
        """
        if payload is None:
            raise ValueError("Payload cannot be None")
        if not isinstance(payload, dict):
            raise ValueError(f"Payload must be a dictionary, got {type(payload)}")
        
        # Convert camelCase to snake_case
        snake_case_payload = JsonConversions.json_camel_to_snake(payload)
        
        # Create instance and load data
        instance = cls()
        instance.load_from_dictionary(snake_case_payload)
        return instance

    def to_camel_case(self) -> Dict[str, Any]:
        """
        Convert model to UI payload format (camelCase).
        Automatically converts snake_case to camelCase for UI consumption.
        
        Returns:
            Dictionary with camelCase keys for the UI
        """
        # Get the model as a dictionary
        model_dict = self.to_dictionary()
        
        # Convert snake_case to camelCase
        return JsonConversions.json_snake_to_camel(model_dict)

    @staticmethod
    def to_snake_case(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Static method to convert UI payload to backend format.
        Useful for preprocessing payloads before model operations.
        
        Args:
            payload: Dictionary with camelCase keys from the UI
            
        Returns:
            Dictionary with snake_case keys for backend processing
        """
        if payload is None:
            raise ValueError("Payload cannot be None")
        if not isinstance(payload, dict):
            raise ValueError(f"Payload must be a dictionary, got {type(payload)}")
            
        return JsonConversions.json_camel_to_snake(payload)

    
