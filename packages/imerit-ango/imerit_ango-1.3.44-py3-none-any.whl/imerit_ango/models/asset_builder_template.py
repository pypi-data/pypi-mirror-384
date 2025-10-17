from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, TypedDict, List, Union, Optional

class DataConfigItemTags(Enum):
    TEXT = 'text'
    LINK = 'link'
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'
    IFRAME = 'iframe'
    PDF = 'pdf'


@dataclass
class DataConfigItem:
    type: str
    storage: Optional[str] = None
    include_in_export: bool = False

    def __post_init__(self):
        # Validate that type is one of the supported tags
        supported_types = [tag.value for tag in DataConfigItemTags]
        if self.type not in supported_types:
            raise ValueError(f"type must be one of {supported_types}, got '{self.type}'")
        
        # Validate storage is provided for media types
        media_types = ['image', 'audio', 'video', 'pdf']
        if self.type in media_types and not self.storage:
            raise ValueError(f"storage is required for type '{self.type}'")

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "includeInExport": self.include_in_export
        }
        if self.storage:
            result["storage"] = self.storage
        return result

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "DataConfigItem":
        return DataConfigItem(
            type=data.get("type", ""),
            storage=data.get("storage"),
            include_in_export=data.get("includeInExport", False)
        )


class PreLabelOption(TypedDict):
    value: str
    schemaId: str

class PreLabelCla(TypedDict, total=False):
    schemaId: str
    tool: str
    title: str
    required: bool
    classifications: List[Any]
    multiple: bool
    options: List[PreLabelOption]
    shortcutKey: str
    frameSpecific: bool

class PreLabelConfigItem(TypedDict):
    cla: PreLabelCla
    value: str

PreLabelConfig = Dict[str, PreLabelConfigItem]

@dataclass
class AssetBuilderTemplate:
    name: str
    template: str
    external_id_column: str
    data_config: Dict[str, DataConfigItem]
    description: str = ""
    batch_column: str = ""
    pre_label_config: PreLabelConfig = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.batch_column, str):
            raise ValueError("batch_column must be a string")
        if not isinstance(self.data_config, dict):
            raise ValueError("data_config must be a dictionary")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")
        if not isinstance(self.name, str):
            raise ValueError("name must be a string")
        if not isinstance(self.external_id_column, str):
            raise ValueError("external_id_column must be a string")
        if not isinstance(self.template, str):
            raise ValueError("template must be a string")
        if not isinstance(self.pre_label_config, dict):
            raise ValueError("pre_label_config must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary format for API requests."""
        return {
            "description": self.description,
            "name": self.name,
            "template": self.template,
            "batchColumn": self.batch_column,
            "selectedExternalId": self.external_id_column,
            "dataConfig": {key: item.to_dict() for key, item in self.data_config.items()},
            "preLabelConfig": self.pre_label_config,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AssetBuilderTemplate":
        """Create an AssetBuilderTemplate from a dictionary."""
        # Convert data_config items to DataConfigItem objects
        data_config = {}
        for key, config_data in data.get("dataConfig", {}).items():
            data_config[key] = DataConfigItem.from_dict(config_data)

        return AssetBuilderTemplate(
            batch_column=data.get("batchColumn", ""),
            data_config=data_config,
            description=data.get("description", ""),
            name=data.get("name", ""),
            external_id_column=data.get("selectedExternalId", ""),
            template=data.get("template", ""),
            pre_label_config=data.get("preLabelConfig", {}),
        )

    def validate(self) -> bool:
        """Validate the template configuration."""
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.data_config:
            raise ValueError("data_config cannot be empty")
        if not self.external_id_column:
            raise ValueError("external_id_column cannot be empty")
        if not self.template:
            raise ValueError("template cannot be empty")
        
        # Validate that batch_column exists in data_config if provided
        if self.batch_column and self.batch_column not in self.data_config:
            raise ValueError(f"batch_column '{self.batch_column}' not found in data_config")

        if self.external_id_column not in self.data_config:
            raise ValueError(f"external_id_column '{self.external_id_column}' not found in data_config")
        
        return True 