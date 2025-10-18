from dataclasses import dataclass
from typing import Any

@dataclass
class QuestionType:
    name: str
    value: str
    icon: Any  # This would typically be a UI component, but we'll use Any for this example

class QUESTION_TYPES:
    RADIO = QuestionType(name="Radio", value="radio", icon=None)
    CHECKBOX = QuestionType(name="Checkbox", value="checkbox", icon=None)
    SINGLE_DROPDOWN = QuestionType(name="Single Dropdown", value="single-dropdown", icon=None)
    MULTIPLE_DROPDOWN = QuestionType(name="Multiple Dropdown", value="multi-dropdown", icon=None)
    TREE_DROPDOWN = QuestionType(name="Tree Dropdown", value="tree-dropdown", icon=None)
    RANK = QuestionType(name="Rank", value="rank", icon=None)
    TEXT = QuestionType(name="Text", value="text", icon=None)