class ExecutionProgressTracker:
    """Helper class to track execution progress throughout the edit process."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def add(self, message: str) -> None:
        """Add a progress message."""
        self.messages.append(message)

    def add_step_start(self, step_num: int, total_steps: int) -> None:
        """Add a step start message."""
        self.add(f"Executing step {step_num + 1} of {total_steps}")

    def add_step_success(self, step_num: int, total_steps: int) -> None:
        """Add a step success message."""
        self.add(f"Successfully performed the edits for step {step_num + 1} of {total_steps}")

    def add_step_error(self, step_num: int, total_steps: int, error: Exception) -> None:
        """Add a step error message."""
        message = (
            f"I encountered an error while executing step {step_num + 1} of {total_steps}: {error}"
        )
        self.add(message)

    def add_step_retry(self, step_num: int, total_steps: int) -> None:
        """Add a step retry message."""
        self.add(f"I will retry step {step_num + 1} of {total_steps}")

    def get_messages(self) -> list[str]:
        """Get all progress messages."""
        return self.messages.copy()
