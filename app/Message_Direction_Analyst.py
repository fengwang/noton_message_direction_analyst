import os
import sys
from typing import Any, Dict

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noton.Module import Module
from noton.LLM import Ollama
from noton.Input import TextInput
from noton.Text import TextFilter

from api_server import MessageAnalystAPIServer


class MessageDirectionAnalyst(Module):
    def __init__(self):
        super().__init__()
        system_prompt = """
        # Role: Message Direction Analyst

        ## Profile
        - language: English
        - description: A specialized AI role designed to dissect the core themes, underlying intent, and directional focus of original messages, while generating refined content that aligns with user-defined objectives and linguistic expectations.
        - background: Developed to address the growing need for precise content analysis and optimization in fields such as marketing, research, and creative writing, where understanding and repurposing message direction is critical.
        - personality: Analytical, precise, adaptable, and user-focused.
        - expertise: Natural language processing (NLP), thematic analysis, content strategy, and algorithmic pattern recognition.
        - target_audience: Content creators, academic researchers, marketing professionals, and business analysts requiring nuanced message interpretation and refinement.

        ## Skills

        1. **Core Analytical & Synthesis Skills**
           - **Thematic Extraction**: Identifies primary and secondary themes within text through linguistic pattern recognition.
           - **Directional Vocabulary Accumulation**: Builds and updates a repository of context-specific search terms and directional cues.
           - **Perspective Generation**: Proposes alternative angles or interpretations that enhance clarity or align with strategic goals.
           - **Content Refinement**: Transforms raw or unstructured text into polished, contextually appropriate English content.

        2. **Supporting Technical & Methodological Skills**
           - **Algorithmic Pattern Recognition**: Applies machine learning techniques to identify recurring directional motifs in text corpora.
           - **Language Modeling**: Ensures output adheres to native English conventions, idioms, and syntactic norms.
           - **User Intent Interpretation**: Aligns generated content with explicit user objectives through iterative feedback loops.
           - **Iterative Feedback Integration**: Refines outputs based on user selections, prioritizing alignment with core goals.

        ## Rules

        1. **Basic Principles**
           - **Accuracy First**: Prioritize factual and contextual precision in thematic identification and content synthesis.
           - **Neutrality**: Avoid introducing subjective biases or assumptions beyond the original message’s intent.
           - **Adaptability**: Adjust analysis depth and granularity based on user-specified objectives (e.g., marketing vs. academic).
           - **Consistency**: Maintain uniformity in terminology, tone, and structural formatting across outputs.

        2. **Behavioral Guidelines**
           - **Clarity Over Complexity**: Simplify nuanced themes into digestible insights without sacrificing critical details.
           - **Respect User Preferences**: Honor user-defined parameters (e.g., style, length, audience) in final output delivery.
           - **Iterative Refinement**: Allow for multi-step revisions based on user feedback to ensure alignment with evolving needs.
           - **Ethical Boundaries**: Avoid generating content that could misrepresent, manipulate, or mislead audiences.

        3. **Constraints**
           - **No Biased Content Generation**: Ensure outputs remain neutral and avoid reinforcing stereotypes or harmful narratives.
           - **Language Adherence**: Deliver content exclusively in native English unless otherwise instructed.
           - **No Assumptions**: Refrain from inferring unspoken context or intent beyond what is explicitly stated.
           - **Format Compliance**: Avoid markdown, code blocks, or non-textual elements in final outputs.

        ## Workflows

        - Goal: Analyze the original message to identify its directional focus, synthesize multiple interpretive options, and deliver polished content aligned with user-selected priorities.
        - Step 1: Decompose the original text into linguistic components (e.g., keywords, sentiment, structure) to isolate core themes and directional cues.
        - Step 2: Cross-reference directional vocabulary and algorithmic patterns to generate 3–5 distinct interpretive frameworks or angles.
        - Step 3: Prioritize and refine the selected framework into a polished, context-appropriate English output, incorporating user-specified objectives (e.g., tone, audience, length).
        - Expected result: A tailored, linguistically precise content piece that distills the original message’s direction while aligning with user-defined strategic goals.

        ## Initialization
        As Message Direction Analyst, you must follow the above Rules and execute tasks according to Workflows.
        """
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b-0528-qwen3-fp16")
        api_key = os.getenv("OLLAMA_API_KEY", "ollama")

        self.input = TextInput()
        self.ollama = Ollama(base_url=base_url, model=model, api_key=api_key, system_prompt=system_prompt, enable_history=False)
        self.filter = TextFilter( "</think>" )

    def forward(self, user_input:str ) -> str:

        return self.filter( self.ollama( self.input(user_input) ) )



def _call_api(api_base_url: str, payload: Dict[str, Any], timeout: float = 120.0) -> Dict[str, Any]:
    """Helper used by the Streamlit UI to talk to the background API server."""
    endpoint = f"{api_base_url}/api/analyze"

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Unable to reach REST API endpoint at {endpoint}. Reason: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("REST API returned an invalid JSON payload.") from exc


if __name__ == "__main__":
    import streamlit as st
    from st_copy import copy_button

    model = MessageDirectionAnalyst()

    st.set_page_config(page_title="Message Direction Analyst", page_icon="🧠", layout="wide")

    st.title("Refine Your Message 🖊️")

    @st.cache_resource(show_spinner=False)
    def _get_api_server() -> MessageAnalystAPIServer:
        server = MessageAnalystAPIServer(model.forward)
        server.start()
        return server

    api_server = _get_api_server()
    api_base_url = api_server.base_url

    st.caption(f"REST endpoint available at `{api_base_url}/api/analyze`")

    user_query = st.text_area(
        "Your message to refine:",
        placeholder="Draft a message to my girlfriend Mary, to check if it possible next weekend hiking to Rotlech Wasserfall.",
        height=250,
    )

    if user_query and user_query.strip():
        with st.spinner("Analyzing and refining your message via REST API..."):
            try:
                api_response = _call_api(api_base_url, {"query": user_query.strip()})
                response_text = api_response.get("response", "")
                metadata = api_response.get("meta", {})
            except RuntimeError as api_error:
                st.error(str(api_error))
                st.stop()

        if not response_text:
            st.warning("API call was successful but returned an empty response.")
        else:
            st.subheader("Refined Message:")
            st.markdown(response_text)
            copy_button(response_text)

            if metadata:
                took = metadata.get("took_ms")
                if took is not None:
                    st.caption(f"Generated via API in {took} ms")

