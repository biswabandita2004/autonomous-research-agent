import requests
import streamlit as st

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Autonomous Research Agent",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Custom CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #6b7280;
        margin-bottom: 30px;
    }

    .metric-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        background-color: #ffffff;
    }

    .section-title {
        font-size: 24px;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

API_URL = "http://127.0.0.1:8001"

# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🔎 Autonomous Research Agent</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">AI-powered research, source discovery, analysis, and structured insights.</div>',
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.header("⚙️ Research Settings")

    export_format = st.selectbox(
        "Export Format",
        ["none", "markdown", "pdf"],
    )

    st.divider()

    st.markdown("### Agent Pipeline")

    st.markdown(
        """
        🔍 Source Selection  
        ↓  
        🌐 Web + arXiv Search  
        ↓  
        ⚡ Parallel Research  
        ↓  
        🧹 Deduplication  
        ↓  
        🤖 LLM Analysis  
        ↓  
        📊 Structured Insights
        """
    )

# --------------------------------------------------
# Research Input
# --------------------------------------------------

st.markdown(
    '<div class="section-title">Research Topic</div>',
    unsafe_allow_html=True,
)

query = st.text_area(
    "Enter your research question",
    placeholder="Example: What are the latest trends in Generative AI in 2026?",
    height=120,
)

research_button = st.button(
    "🚀 Start Autonomous Research",
    type="primary",
    use_container_width=True,
)

# --------------------------------------------------
# Research Execution
# --------------------------------------------------

if research_button:

    if not query.strip():
        st.warning("Please enter a research question.")
        st.stop()

    payload = {
        "query": query.strip(),
        "export_format": None if export_format == "none" else export_format,
    }

    with st.spinner("🤖 Agent is researching your topic..."):

        try:
            response = requests.post(
                f"{API_URL}/research",
                json=payload,
                timeout=180,
            )

            if response.status_code != 200:
                st.error(
                    f"Research failed: {response.status_code}"
                )
                st.code(response.text)
                st.stop()

            result = response.json()

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to FastAPI. "
                "Make sure the FastAPI server is running on port 8001."
            )
            st.stop()

        except requests.exceptions.Timeout:
            st.error("The research request timed out.")
            st.stop()

        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.stop()

    # --------------------------------------------------
    # Research Overview
    # --------------------------------------------------

    st.success("Research completed successfully! ✅")

    st.markdown(
        '<div class="section-title">Research Overview</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Sources Selected",
            len(result.get("sources_selected", [])),
        )

    with col2:
        st.metric(
            "Sources Queried",
            len(result.get("sources_queried", [])),
        )

    with col3:
        st.metric(
            "Raw Results",
            result.get("raw_results_count", 0),
        )

    with col4:
        st.metric(
            "After Deduplication",
            result.get("deduplicated_results_count", 0),
        )

    # --------------------------------------------------
    # Sources
    # --------------------------------------------------

    st.markdown(
        '<div class="section-title">🔍 Sources Used</div>',
        unsafe_allow_html=True,
    )

    sources = result.get("sources_queried", [])

    if sources:
        for source in sources:
            st.write(f"• {source}")

    # --------------------------------------------------
    # Key Points
    # --------------------------------------------------

    st.markdown(
        '<div class="section-title">📌 Key Points</div>',
        unsafe_allow_html=True,
    )

    for point in result.get("key_points", []):
        st.markdown(f"- {point}")

    # --------------------------------------------------
    # Important Findings
    # --------------------------------------------------

    st.markdown(
        '<div class="section-title">💡 Important Findings</div>',
        unsafe_allow_html=True,
    )

    for finding in result.get("important_findings", []):
        st.markdown(f"- {finding}")

    # --------------------------------------------------
    # Actionable Insights
    # --------------------------------------------------

    st.markdown(
        '<div class="section-title">🎯 Actionable Insights</div>',
        unsafe_allow_html=True,
    )

    for insight in result.get("actionable_insights", []):
        st.markdown(f"- {insight}")

    # --------------------------------------------------
    # References
    # --------------------------------------------------

    st.markdown(
        '<div class="section-title">📚 References</div>',
        unsafe_allow_html=True,
    )

    references = result.get("references", [])

    if references:
        for reference in references:
            st.write(f"• {reference}")

    # --------------------------------------------------
    # Export
    # --------------------------------------------------

    export_path = result.get("export_path")

    if export_path:
        st.divider()

        st.markdown(
            '<div class="section-title">📄 Export</div>',
            unsafe_allow_html=True,
        )

        st.info(f"Research report generated: {export_path}")

    # --------------------------------------------------
    # History ID
    # --------------------------------------------------

    history_id = result.get("history_id")

    if history_id:
        st.caption(f"Research History ID: {history_id}")
        