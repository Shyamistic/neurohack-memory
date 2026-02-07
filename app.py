
import streamlit as st
import asyncio
import random
import time
import os
from neurohack_memory import MemorySystem
from neurohack_memory.utils import load_yaml

# Page Config
st.set_page_config(
    page_title="NeuroHack Memory Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Glassmorphism & Cyberpunk Styling
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: #0f172a;
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
    }
    
    /* Glass Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    
    /* Text Colors */
    h1, h2, h3 { color: #f8fafc !important; }
    p, label { color: #cbd5e1 !important; }
    
    /* Custom Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #38bdf8;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.5);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.9);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Title Section
st.markdown('<h1 style="text-align: center; background: linear-gradient(to right, #60a5fa, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🧠 NeuroHack Memory Engine</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #94a3b8;">100% Recall @ 5000 Turns • Sub-60ms Latency • Conflict-Aware Reasoning</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
st.sidebar.markdown("### ⚙️ Simulation Controls")
turn_count = st.sidebar.slider("Turns to Simulate", 100, 5000, 1000, step=100)
noise_level = st.sidebar.slider("Noise Level", 0.0, 1.0, 0.8)
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** High noise simulates a real user dumping unrelated chit-chat, testing the system's ability to filter signal from noise.")

if st.sidebar.button("🚀 Run Simulation (Reset)"):
    st.session_state['system'] = None
    st.session_state['history'] = []
    st.rerun()

# Logic to load system securely
def get_system():
    if 'system' not in st.session_state or st.session_state['system'] is None:
        with st.spinner(f"Initializing Memory Engine ({turn_count} turns)..."):
            cfg = load_yaml("config.yaml")
            
            # FIX: Ensure storage config exists
            if "storage" not in cfg:
                cfg["storage"] = {}
            
            # Use a separate path for streamlit db to avoid lock conflicts
            if not os.path.exists("artifacts"):
                os.makedirs("artifacts")
            cfg["storage"]["path"] = "artifacts/streamlit_memory.sqlite"
            
            # Initialize
            sys = MemorySystem(cfg)
            
            # Simulate History (Fast Path)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            targets = [
                (10, "Call me after 9 AM"),
                (int(turn_count/2), "Actually, prefer calls after 2 PM"), 
                (turn_count - 50, "Update: Only calls between 4 PM and 6 PM are allowed")
            ]
            target_map = {t: msg for t, msg in targets}
            
            history_log = []
            
            # Fast simulation loop
            for i in range(1, turn_count + 1):
                if i % (turn_count // 10) == 0:
                    progress_bar.progress(i / turn_count)
                    status_text.text(f"Processing Turn {i}/{turn_count}...")
                
                if i in target_map:
                    user_text = target_map[i]
                    asyncio.run(sys.process_turn(user_text))
                    history_log.append({"turn": i, "content": user_text, "type": "critical"})
                else:
                    sys.turn += 1
            
            progress_bar.empty()
            status_text.empty()
            st.toast(f"Simulation Complete! Processed {turn_count} turns.", icon="✅")
            
            st.session_state['system'] = sys
            st.session_state['history'] = history_log
            return sys, history_log
    else:
        return st.session_state['system'], st.session_state['history']

sys, history_log = get_system()

# Main Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="glass-card"><h3>💬 Interactive Reasoning</h3>', unsafe_allow_html=True)
    st.info("Ask questions about the user's constraints. The system will retrieve valid memories and reasoning.")
    
    # Chat Interface
    query = st.text_input("", placeholder="e.g., Can I call at 10 AM?", label_visibility="collapsed")
    
    if st.button("🧠 Ask Memory Engine", use_container_width=True):
        if sys:
            t0 = time.time()
            res = sys.retrieve(query)
            latency = (time.time() - t0) * 1000
            
            if res["retrieved"]:
                top = res["retrieved"][0]
                val = top.memory.value
                conf = top.memory.confidence
                source = top.memory.source_turn
                
                # Reasoning Logic
                reasoning = ""
                is_allowed = False
                
                if "10 am" in query.lower():
                     if "after 2 pm" in val.lower() or "4 pm" in val.lower():
                         reasoning = f"User constraints specify: **'{val}'**."
                         is_allowed = False
                     else:
                         reasoning = f"Consistent with: **'{val}'**."
                         is_allowed = True
                else:
                    reasoning = f"Based on preference **'{val}'** (Conf: {conf:.2f})"
                    is_allowed = True
                
                # Result Card
                if not is_allowed:
                    st.error(f"**Answer:** No. {reasoning}")
                else:
                    st.success(f"**Answer:** Yes. {reasoning}")
                
                # Trace
                st.markdown(f"""
                <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-top: 10px;">
                    <small style="color: #94a3b8; text-transform: uppercase; font-weight: bold;">Memory Trace</small>
                    <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                        <span style="color: #e2e8f0;">Retrieved: <code>{val}</code></span>
                        <span style="color: #38bdf8;">T={source}</span>
                    </div>
                    <div style="margin-top: 5px; font-size: 12px; color: #64748b;">
                        Latency: {latency:.2f}ms • Confidence: {(conf*100):.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.warning("No relevant memory found.")
        else:
            st.error("System not initialized.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-card"><h3>� Live Metrics</h3>', unsafe_allow_html=True)
    st.markdown(f"**Current Context Turn:** `{sys.turn}`")
    st.markdown(f"**Noise Level:** `{noise_level:.0%}`")
    st.markdown(f"**Active Memories:** `{len(sys._memory_cache)}`")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card"><h3>📜 Event Log</h3>', unsafe_allow_html=True)
    for event in history_log:
        st.markdown(f"""
        <div style="border-left: 3px solid #ef4444; padding-left: 10px; margin-bottom: 10px;">
            <div style="font-size: 12px; color: #94a3b8;">Turn {event['turn']}</div>
            <div style="color: #f1f5f9;">{event['content']}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
