from typing import List


class Augmentation:
    def _build_augmentation_text(self, guidelines: List[str]) -> str:
        """
        Formats guidelines for injection into prompts.

        Args:
            guidelines: List of guideline strings to format

        Returns:
            Formatted text to append to prompts
        """
        if not guidelines:
            return ""

        return (
            "\n\nIMPORTANT POLICY DIRECTIVES:\n"
            + "\n".join([f"• {g}" for g in guidelines])
            + "\n\nYou MUST adhere to these directives in your response."
        )
