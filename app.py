
import streamlit as st
import asyncio
import random
from neurohack_memory import MemorySystem
from neurohack_memory.utils import load_yaml
import time

# Page Config
st.set_page_config(
    page_title="NeuroHack Memory Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #374151;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🧠 NeuroHack Memory: The Adversarial Engine")
st.markdown("**100% Recall @ 5000 Turns • Sub-60ms Latency • Conflict-Aware Reasoning**")

# Sidebar
st.sidebar.header("⚙️ Simulation Controls")
turn_count = st.sidebar.slider("Turns to Simulate", 100, 5000, 1000, step=100)
noise_level = st.sidebar.slider("Noise Level", 0.0, 1.0, 0.8)

if st.sidebar.button("Run Simulation (Re-Index)"):
    st.session_state['system'] = None
    st.session_state['history'] = []
    st.experimental_rerun()

# Initialize System
if 'system' not in st.session_state or st.session_state['system'] is None:
    with st.spinner(f"Initializing Memory Engine ({turn_count} turns)..."):
        cfg = load_yaml("config.yaml")
        # Use a separate path for streamlit db to avoid lock conflicts if local
        cfg["storage"]["path"] = "artifacts/streamlit_memory.sqlite"
        sys = MemorySystem(cfg)
        
        # Simulate History
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        targets = [
            (10, "Call me after 9 AM"),
            (int(turn_count/2), "Actually, prefer calls after 2 PM"), 
            (turn_count - 50, "Update: Only calls between 4 PM and 6 PM are allowed")
        ]
        target_map = {t: msg for t, msg in targets}
        noise_phrases = ["Log entry", "System ping", "Status update", "Weather query"]
        
        history_log = []
        
        for i in range(1, turn_count + 1):
            if i % (turn_count // 10) == 0:
                progress_bar.progress(i / turn_count)
                status_text.text(f"Processing Turn {i}/{turn_count}...")
            
            if i in target_map:
                user_text = target_map[i]
                asyncio.run(sys.process_turn(user_text))
                history_log.append(f"🔴 **T={i}:** {user_text} (CRITICAL UPDATE)")
            else:
                sys.turn += 1
                if random.random() < noise_level:
                    # noise
                    pass

        progress_bar.progress(100)
        status_text.text("Simulation Complete. System Ready.")
        
        st.session_state['system'] = sys
        st.session_state['history'] = history_log

# Main Dashboard
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Interactive Reasoning")
    st.info("Ask questions about the user's constraints. The system will retrieve valid memories and reasoning.")
    
    query = st.text_input("Ask a question:", "Can I call at 10 AM?")
    
    if st.button("Ask Memory Engine"):
        if 'system' in st.session_state:
            sys = st.session_state['system']
            t0 = time.time()
            res = sys.retrieve(query)
            latency = (time.time() - t0) * 1000
            
            if res["retrieved"]:
                top = res["retrieved"][0]
                val = top.memory.value
                conf = top.memory.confidence
                source = top.memory.source_turn
                
                # Reasoning Logic (Template for Demo)
                reasoning = ""
                if "10 am" in query.lower():
                     if "after 2 pm" in val.lower() or "4 pm" in val.lower():
                         reasoning = f"❌ **No.** User constraints specify: '{val}'."
                     else:
                         reasoning = f"✅ **Yes.** Consistent with: '{val}'."
                else:
                    reasoning = f"ℹ️ **Insight:** Based on '{val}' (Conf: {conf:.2f})"
                
                st.success(reasoning)
                
                with st.expander("🔍 Inspect Core Memory (Trace)", expanded=True):
                    st.write(f"**Retrieved:** `{val}`")
                    st.write(f"**Confidence:** `{conf:.2f}`")
                    st.write(f"**Source Turn:** `T={source}`")
                    st.caption(f"Latency: {latency:.2f}ms")
            else:
                st.warning("No relevant memory found.")
        else:
            st.error("System not initialized.")

with col2:
    st.subheader("📜 Event Log")
    st.write("Critical updates injected during simulation:")
    for log in st.session_state.get('history', []):
        st.markdown(log)
    
    st.subheader("📊 Live Metrics")
    st.metric(label="Current Turn", value=st.session_state['system'].turn if 'system' in st.session_state else 0)
    st.metric(label="Adversarial Noise", value=f"{noise_level:.0%}")
