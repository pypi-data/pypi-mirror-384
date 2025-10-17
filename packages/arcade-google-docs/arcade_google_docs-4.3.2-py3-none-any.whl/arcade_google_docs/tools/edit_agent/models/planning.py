from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from arcade_google_docs.models.requests import EditRequestType


class ReasoningEffort(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    def minimum_number_of_thoughts(self) -> int:
        return {
            ReasoningEffort.MINIMAL: 0,
            ReasoningEffort.LOW: 1,
            ReasoningEffort.MEDIUM: 2,
            ReasoningEffort.HIGH: 3,
        }[self]


class EditItem(BaseModel):
    """A single edit request with its type and associated thoughts"""

    edit_request_type: EditRequestType = Field(
        ..., title="The type of edit request to be made to the document"
    )
    edit_instruction: str = Field(
        ..., title="Natural language description of the desired change to the document"
    )
    thoughts: list[str] = Field(
        ..., title="Thoughts that led to identifying this specific edit request"
    )


class Step(BaseModel):
    """A step containing one or more edit requests to be executed together"""

    model_config = ConfigDict(
        title="Step for Document Editing",
        json_schema_extra={
            "description": "A step containing edit requests that can be executed together",
            "examples": [
                {
                    "edit_items": [
                        {
                            "edit_request_type": "updateTextStyle",
                            "edit_instruction": "Make 'Performance' bold in the objectives section",
                            "thoughts": [
                                "(thought) I am asked to make 'Performance' bold in the "
                                "objectives section",
                                "(thought) I need to find where 'Performance' appears",
                                "(thought) 'Performance' is at index 150-161 in the document",
                                "(thought) I'll use updateTextStyle to make it bold",
                            ],
                        },
                    ],
                }
            ],
        },
    )
    edit_items: list[EditItem] = Field(
        ..., title="List of edit requests to be executed in this step"
    )


class Plan(BaseModel):
    """The final ordered plan with proper dependencies"""

    steps: list[Step] = Field(
        ..., title="Ordered list of steps, each containing one or more edit requests"
    )

    @property
    def number_of_steps(self) -> int:
        return len(self.steps)

    @property
    def number_of_edit_requests(self) -> int:
        return sum(len(step.edit_items) for step in self.steps)

    def to_log_string(self) -> str:
        log_string = ""
        for step_num, step in enumerate(self.steps):
            log_string += f"Step {step_num + 1}:\n"
            for edit_item in step.edit_items:
                log_string += f"  - {edit_item.edit_instruction}\n"
        return log_string
