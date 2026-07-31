import asyncio
import sys
from pathlib import Path
from typing import Any

import streamlit as st

# Ensure project root is in sys.path
root_dir: Path = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from config.settings import settings
from src.core.orchestrator import BedtimeStoryOrchestrator


def main() -> None:
    """Main entry point for running the DreamWeaver AI Streamlit web application prototype."""
    st.set_page_config(
        page_title="DreamWeaver AI 🪄",
        page_icon="🪄",
        layout="centered",
        initial_sidebar_state="expanded"
    )

    st.title("DreamWeaver AI 🪄")
    st.write("Turning toys, voice sparks, and bedtime names into personalized illustrated stories.")

    st.sidebar.header("Bedtime Setup")
    child_name: str = st.sidebar.text_input("Child Name", value=settings.default_child_name)
    child_age: int = st.sidebar.slider("Child Age", min_value=1, max_value=12, value=settings.default_child_age)
    story_duration: int = st.sidebar.slider("Story Duration (minutes)", min_value=3, max_value=20, value=settings.default_duration_minutes)

    st.sidebar.subheader("Inputs & Outputs Configuration")
    input_mode: str = st.sidebar.selectbox("Spark Input Mode", options=["Voice Spark", "Image Spark"])
    
    enable_audio: bool = st.sidebar.checkbox("Voice Story (Audio Narration)", value=settings.enable_voice_story)
    enable_images: bool = st.sidebar.checkbox("Illustrated Story (1 Cover + 3 Scenes)", value=settings.enable_illustrated_story)

    # Core interface
    st.write(f"### Let's create a story for **{child_name}**!")
    topic: str = st.text_input("Base Story Idea", placeholder="e.g. A friendly little panda that wanted to explore the stars...")

    if st.button("Create My Storybook", type="primary"):
        if not topic.strip():
            st.warning("Please specify a story topic to spark our narrative.")
            return

        st.info("Creating magical bedtime storybook...")
        orchestrator = BedtimeStoryOrchestrator(
            child_name=child_name,
            child_age=child_age,
            duration_minutes=story_duration,
            mode="Image" if "Image" in input_mode else "Voice"
        )

        # Run async orchestrator pipeline
        result: dict[str, Any] = asyncio.run(orchestrator.run_pipeline(topic, enable_audio=enable_audio, enable_images=enable_images))
        story_json: dict[str, Any] = result["story"]

        st.success(f"✨ Storybook Generated: {story_json['title']} ✨")
        
        # Display metadata info
        meta: dict[str, Any] = story_json["metadata"]
        st.write(f"*Word Count: {meta['total_word_count']} words | Target Pacing: {meta['target_duration_minutes']} mins (Age {meta['target_age']})*")

        # Display cover page image
        if enable_images and len(result["image_paths"]) > 0:
            st.image(result["image_paths"][0], caption=f"Cover: {story_json['title']}", use_column_width=True)

        st.write("---")

        # Display chapters
        for i, ep in enumerate(story_json["episodes"]):
            st.write(f"### Chapter {ep['chapter']}: {ep['title']}")
            if enable_images and len(result["image_paths"]) > i + 1:
                st.image(result["image_paths"][i + 1], caption=ep["illustration_prompt"], use_column_width=True)
            st.write(ep["narration_text"])
            st.write("---")

        # Display audio narration player
        if enable_audio and len(result["audio_paths"]) > 0:
            st.write("### Narration Audio Track")
            st.audio(result["audio_paths"][0])

if __name__ == "__main__":
    main()

