from pydantic import BaseModel, Field


class Episode(BaseModel):
    """Represents a single chapter/episode of the bedtime storybook."""
    chapter: int = Field(description="The chapter number of this episode.")
    title: str = Field(description="Title of the episode/chapter.")
    narration_text: str = Field(description="Soothing, spoken narration text of this chapter.")
    illustration_prompt: str = Field(description="Detailed visual prompt for scene illustration generation.")

class StoryMetadata(BaseModel):
    """Represents pacing and child demographics metadata for the generated storybook."""
    target_age: int = Field(description="Target age of the child reader.")
    target_duration_minutes: int = Field(description="Bedtime listening duration in minutes.")
    total_word_count: int = Field(description="Calculated target word count constraint.")

class BedtimeStorySchema(BaseModel):
    """Defines the complete bedtime storybook structure returned by the Gemini API."""
    title: str = Field(description="The overall title of the bedtime story.")
    metadata: StoryMetadata = Field(description="Story duration pacing metadata details.")
    cover_art_prompt: str = Field(description="Vivid visual prompt for generating the cover illustration.")
    episodes: list[Episode] = Field(description="Three sequential chapters representing beginning, middle, and climax.")

def get_bedtime_prompt(child_name: str, child_age: int, duration_minutes: int, topic: str) -> str:
    """
    Generates a personalized system prompt tailored for Lele's target parameters and pacing constraints.

    Args:
        child_name: The name of the child protagonist.
        child_age: The age of the child reader.
        duration_minutes: The target bedtime listening duration in minutes.
        topic: The user/vision/voice inspired story theme.

    Returns:
        The fully formatted system prompt string.
    """
    wpm_rate: int = 140
    target_words: int = duration_minutes * wpm_rate
    words_per_chapter: int = int(target_words / 3)

    return (
        f"You are a master bedtime story generator. Create a personalized bedtime story for {child_name} (Age: {child_age}) "
        f"about the theme/topic: '{topic}'.\n\n"
        f"Strict Guidelines:\n"
        f"- Pacing Engine: The story must contain exactly {target_words} words in total. Spoken narration for each of the "
        f"3 chapters should contain approximately {words_per_chapter} words to sync with the {duration_minutes} minute duration.\n"
        f"- Guardrails: Limit vocabulary complexity to an age-appropriate level. Ban all scary themes, monsters, violence, "
        f"or loud actions. Keep the tone soft, soothing, and sleep-inducing with a comforting resolution.\n"
        f"- Structured Schema: Render the storybook exactly inside the requested JSON Schema format."
    )

