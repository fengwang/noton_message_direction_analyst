import os
import sys
import textwrap
from datetime import datetime
from typing import Any, Dict, List

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
        - language: English, Chinese, German, French, Spanish
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
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
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


def _depth_description(level: str) -> str:
    descriptions = {
        "Snapshot": "Deliver a succinct, high-level rewrite that keeps only the essential intent.",
        "Balanced": "Balance brevity and elaboration, surfacing the main direction plus one supporting idea.",
        "Immersive": "Provide a more detailed refinement with layered structure and directional cues.",
    }
    return descriptions.get(level, descriptions["Balanced"])


def _length_advice(length_pref: str) -> str:
    mapping = {
        "Concise": "Stay under 120 words and prioritize crisp sentences.",
        "Standard": "Roughly 120-200 words with natural pacing.",
        "Expanded": "Allow up to 250 words, weaving in nuance and supporting context.",
    }
    return mapping.get(length_pref, mapping["Standard"])


def _compose_analysis_prompt(
    message: str,
    *,
    tone: str,
    direction: str,
    focus_points: List[str],
    audience: str,
    depth_mode: str,
    length_pref: str,
    energy: int,
    actionable: bool,
    empathy: bool,
) -> str:
    focus_section = ", ".join(focus_points) if focus_points else "core clarity and authentic intent"
    action_clause = (
        "Close with 1 actionable nudge or next step tailored to the audience."
        if actionable
        else "Only rewrite the message; no explicit next steps are required."
    )
    empathy_clause = (
        "Infuse subtle empathy and reassurance without sounding overly sentimental."
        if empathy
        else "Maintain professional neutrality without adding emotional framing."
    )
    direction_briefs = {
        "Clarify": "distill the message to its sharpest narrative so the receiver instantly grasps the ask.",
        "Persuade": "emphasize benefits, momentum, and compelling language that nudges agreement.",
        "Inspire": "elevate the tone with motivating language that sparks curiosity or action.",
        "Reassure": "project stability, confidence, and calm authority to reduce any doubts.",
    }
    energy_labels = {
        1: "calm and measured",
        2: "steady and composed",
        3: "engaged and confident",
        4: "dynamic and forward-leaning",
        5: "bold and high-energy",
    }

    prompt = textwrap.dedent(
        f"""
        You are the Message Direction Analyst. Refine the user's message using the controls below.

        Primary directive: {direction} — {direction_briefs.get(direction, '')}
        Audience emphasis: {audience}
        Tone palette: {tone} with an overall energy that feels {energy_labels.get(energy, 'confident')}.
        Depth mode: {depth_mode} ({_depth_description(depth_mode)})
        Length preference: {length_pref} ({_length_advice(length_pref)})
        Focus priorities: {focus_section}
        Guidelines: {action_clause} {empathy_clause}

        Output requirements:
        - Deliver a single refined message (plain text, no markdown bullets).
        - Keep the prose fluent and human, mirroring a native English writer.
        - Honor the requested length and tone even if you must rearrange content.

        Original message:
        ---
        {message.strip()}
        ---
        """
    ).strip()

    return prompt


def _get_message_stats(message: str) -> Dict[str, Any]:
    cleaned = message.strip()
    words = len(cleaned.split()) if cleaned else 0
    sentences = max(cleaned.count(".") + cleaned.count("!") + cleaned.count("?"), 1) if cleaned else 0
    chars = len(cleaned)
    reading_time_min = round(words / 200, 2) if words else 0
    return {
        "words": words,
        "sentences": sentences,
        "chars": chars,
        "reading_time": reading_time_min,
    }


def _custom_css() -> str:
    return """
    <style>
    body {
        background-color: #07090f;
    }
    .hero-card {
        background: radial-gradient(circle at top left, rgba(84,117,255,0.45), rgba(7,9,15,0.95));
        border-radius: 28px;
        padding: 32px 36px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 24px 65px rgba(10,13,35,0.4);
        color: #f2f5ff;
        margin-bottom: 1.5rem;
    }
    .hero-card h1 {
        font-size: 2.2rem;
        margin-bottom: 0.4rem;
    }
    .hero-chip {
        display: inline-flex;
        padding: 0.35rem 0.8rem;
        margin-right: 0.4rem;
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.22);
        background-color: rgba(255,255,255,0.05);
        font-size: 0.85rem;
        margin-top: 0.4rem;
    }
    .stTextArea textarea {
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.18);
        background-color: rgba(255,255,255,0.03);
        color: #ee4266;
        font-size: 0.98rem;
        caret-color: #ff00ff;
    }
    .stTextArea textarea::placeholder {
        color: rgba(255,255,255,0.6);
    }
    .stButton button {
        border-radius: 999px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .metrics-card {
        padding: 1rem;
        border-radius: 18px;
        background-color: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    </style>
    """


if __name__ == "__main__":
    import streamlit as st
    from st_copy import copy_button

    model = MessageDirectionAnalyst()

    st.set_page_config(
        page_title="Message Direction Analyst",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(_custom_css(), unsafe_allow_html=True)

    @st.cache_resource(show_spinner=False)
    def _get_api_server() -> MessageAnalystAPIServer:
        server = MessageAnalystAPIServer(model.forward)
        server.start()
        return server

    api_server = _get_api_server()
    api_internal_base_url = api_server.internal_base_url
    api_public_base_url = api_server.base_url

    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_latency_ms" not in st.session_state:
        st.session_state.last_latency_ms = None

    st.markdown(
        """
        <div class="hero-card">
            <h1>Directional intelligence for every message</h1>
            <p>Design concise, purpose-driven messages with adaptive tone, audience sensitivity, and instant refinement.</p>
            <div>
                <span class="hero-chip">Intent mapping</span>
                <span class="hero-chip">Tone orchestration</span>
                <span class="hero-chip">Audience focus</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("Live REST endpoint")
        st.code(f"POST {api_public_base_url}/api/analyze", language="text")
        st.caption('Payload: {"query": "..."}')
        st.divider()
        st.subheader("Session signals")
        latency = st.session_state.last_latency_ms
        st.metric("Last latency", f"{latency} ms" if latency else "—")
        st.metric("Saved runs", len(st.session_state.history))
        st.divider()
        st.caption("Tips")
        st.write(
            "- Be direct about the recipient and intent.\n"
            "- Use the focus chips below to guide the rewrite.\n"
            "- Keep drafts between 80-200 words for best results."
        )

    left_col, right_col = st.columns([3, 2], gap="large")

    tone_options = ["Warm", "Neutral", "Energetic", "Formal"]
    direction_options = ["Clarify", "Persuade", "Inspire", "Reassure"]
    focus_options = [
        "Call-to-action clarity",
        "Benefit-forward framing",
        "Risk mitigation",
        "Emotionally aware tone",
        "Data-backed credibility",
        "Momentum and urgency",
    ]
    audience_options = [
        "Executive stakeholder",
        "Internal team",
        "Customer / client",
        "Partner or vendor",
        "General audience",
        "Loved one / partner",
        "Trusted friend or ally",
        "Someone you are upset with",
        "Someone you are celebrating with",
        "Stranger / cold outreach",
        "Authority figure you feel uneasy around",
        "Person you empathize with",
        "Adversarial or skeptical recipient",
        "High-trust collaborator",
    ]

    with left_col:
        st.subheader("Craft your brief")

        tone = st.select_slider("Tone palette", options=tone_options, value="Warm")
        direction = st.segmented_control(
            "Primary direction",
            options=direction_options,
            default="Clarify",
            help="Select the overarching intent for the refinement.",
        )
        length_pref = st.segmented_control(
            "Length profile",
            options=["Concise", "Standard", "Expanded"],
            default="Standard",
            key="length_pref",
        )
        depth_mode = st.select_slider(
            "Depth mode",
            options=["Snapshot", "Balanced", "Immersive"],
            value="Balanced",
            help="Choose how elaborate the analyst should go.",
        )
        energy = st.slider(
            "Energy level",
            min_value=1,
            max_value=5,
            value=3,
            help="1 is calm & composed · 5 is bold & high-energy.",
        )
        focus_points = st.multiselect(
            "Directional focus",
            options=focus_options,
            default=["Call-to-action clarity"],
            help="Pick up to three areas to emphasize.",
            max_selections=3,
        )
        audience = st.selectbox("Audience", options=audience_options, index=0)
        actionable = st.toggle("Highlight actionable next steps", value=True)
        empathy = st.toggle("Include empathetic framing", value=False)

        user_query = st.text_area(
            "Draft or paste your message",
            placeholder="Need a confident yet warm note to the product team about moving the launch by one week...",
            height=260,
        )

        submit = st.button(
            "Generate direction plan",
            type="primary",
            use_container_width=True,
        )

    with right_col:
        st.subheader("Message snapshot")
        stats = _get_message_stats(user_query)
        with st.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("Words", stats["words"])
            m2.metric("Sentences", stats["sentences"])
            m3.metric("Est. read", f"{stats['reading_time']} min")

        completeness = min(stats["words"] / 180, 1.0) if stats["words"] else 0
        st.progress(
            completeness,
            text="Ideal briefing range: 80-180 words" if stats["words"] else "Waiting for your draft...",
        )

        st.subheader("Guidance hints")
        hints = []
        if stats["words"] < 40:
            hints.append("Consider adding more context so the refinement can stay grounded.")
        if stats["words"] > 260:
            hints.append("Long drafts may dilute direction—trim supporting detail where possible.")
        if direction == "Persuade" and "Benefit-forward framing" not in focus_points:
            hints.append("Persuasive messages often benefit from explicit value framing.")
        if direction == "Reassure" and not empathy:
            hints.append("Reassurance pairs well with empathy—toggle it on if stability is key.")
        if not hints:
            hints.append("Great balance! Hit Generate to see an optimized direction plan.")
        for hint in hints:
            st.markdown(f"- {hint}")

    analysis_container = st.container()
    analysis_result = None
    composed_prompt = ""

    if submit:
        trimmed = user_query.strip()
        if not trimmed:
            st.warning("Add a message draft to analyze.")
        else:
            composed_prompt = _compose_analysis_prompt(
                trimmed,
                tone=tone,
                direction=direction,
                focus_points=focus_points,
                audience=audience,
                depth_mode=depth_mode,
                length_pref=length_pref,
                energy=energy,
                actionable=actionable,
                empathy=empathy,
            )

            with st.status("Synthesizing direction...", expanded=True) as status:
                status.write("Aligning your controls with the analyst brief.")
                status.write("Contacting analysis API.")
                try:
                    api_response = _call_api(api_internal_base_url, {"query": composed_prompt})
                except RuntimeError as api_error:
                    status.update(label="Analysis failed", state="error")
                    analysis_container.error(str(api_error))
                else:
                    status.update(label="Analysis complete", state="complete")
                    response_text = api_response.get("response", "").strip()
                    metadata = api_response.get("meta", {})
                    if not response_text:
                        analysis_container.warning(
                            "The API call succeeded but returned an empty response. Try adjusting the controls."
                        )
                    else:
                        latency = metadata.get("took_ms")
                        st.session_state.last_latency_ms = latency
                        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                        history_entry = {
                            "ts": timestamp,
                            "direction": direction,
                            "tone": tone,
                            "audience": audience,
                            "length": length_pref,
                            "depth": depth_mode,
                            "focus": focus_points,
                            "response": response_text,
                        }
                        st.session_state.history.insert(0, history_entry)
                        st.session_state.history = st.session_state.history[:5]
                        analysis_result = {
                            "response": response_text,
                            "meta": metadata,
                            "timestamp": timestamp,
                        }

    if analysis_result:
        st.toast("Refined message ready ✨", icon="✅")
        tabs = st.tabs(["Refined narrative", "Guidance summary", "Recent runs"])

        with tabs[0]:
            st.markdown(analysis_result["response"])
            copy_button(analysis_result["response"])
            meta = analysis_result.get("meta", {}) or {}
            latency = meta.get("took_ms")
            if latency:
                st.caption(f"Generated via REST API in {latency} ms at {analysis_result['timestamp']}.")
            with st.expander("Prompt context sent to analyst", expanded=False):
                st.code(composed_prompt, language="markdown")

        with tabs[1]:
            st.subheader("Directional briefing")
            summary_points = [
                f"**Direction:** {direction}",
                f"**Tone palette:** {tone} · energy level {energy}/5",
                f"**Audience:** {audience}",
                f"**Length profile:** {length_pref}",
                f"**Depth mode:** {depth_mode}",
                f"**Focus points:** {', '.join(focus_points) if focus_points else 'Core clarity'}",
                f"**Actionable close:** {'Enabled' if actionable else 'Disabled'}",
                f"**Empathy layer:** {'Enabled' if empathy else 'Neutral'}",
            ]
            st.markdown("\n".join(f"- {p}" for p in summary_points))

        with tabs[2]:
            st.subheader("Session history (latest 5)")
            if not st.session_state.history:
                st.caption("No prior runs yet.")
            else:
                for entry in st.session_state.history:
                    st.markdown(f"**{entry['ts']}** — {entry['direction']} · {entry['tone']} · {entry['length']}")
                    st.caption(f"Audience: {entry['audience']} · Depth: {entry['depth']}")
                    preview = entry["response"]
                    if len(preview) > 260:
                        preview = preview[:260] + "…"
                    st.write(preview)
                    st.divider()
