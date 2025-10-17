from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class LLMConfig:
    id: str

    def __post_init__(self):
        if self.id is None or not isinstance(self.id, str):
            raise ValueError(f"LLMConfig.id must be a string, got {type(self.id).__name__}")

@dataclass
class NamingStrategy:
    type: str

@dataclass
class ChatAssetCreationConfig:
    number_of_assets: int
    storage_id: Optional[str] = None
    bucket_name: Optional[str] = None
    llm_config: Optional[LLMConfig] = None
    naming_strategy: Optional[NamingStrategy] = field(default_factory=lambda: NamingStrategy("random"))
    conversation_json: Optional[str] = None

    def __post_init__(self):
        if self.storage_id is not None and not isinstance(self.storage_id, str):
            raise ValueError("storage_id must be a string")
        if self.bucket_name is not None and not isinstance(self.bucket_name, str):
            raise ValueError("bucket_name must be a string")
        if self.llm_config is not None and not isinstance(self.llm_config, LLMConfig):
            raise ValueError("llm_config must be of type LLMConfig or None")
        if self.conversation_json is None and (not isinstance(self.number_of_assets, int) or self.number_of_assets <= 0):
            raise ValueError("number_of_assets is required and it must be an integer larger than 0")

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ChatAssetCreationConfig":
        llm_cfg = data.get("llm_config")
        llm_config = LLMConfig(**llm_cfg) if llm_cfg else None
       
        return ChatAssetCreationConfig(
            number_of_assets=data.get("number_of_assets", 0),
            storage_id=data.get("storage_id", None),
            bucket_name=data.get("bucket_name", None),
            llm_config=llm_config,
            naming_strategy=data.get("naming_strategy", NamingStrategy("random")),
            conversation_json=data.get("conversation_json", None)
        )

