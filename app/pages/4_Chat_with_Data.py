# app/pages/4_Chat_with_Data.py
"""
Enhanced Chat with Data - Natural Conversational Interface
- Context-aware conversations
- Intent classification
- Natural language responses
- Maintains conversation history
"""

import streamlit as st
import pandas as pd
import os

# Import functions from core_logic modules
from core_logic.data_loader import load_all_data_sources, get_selected_dfs
from core_logic.llm_config import configure_llm_backend
from core_logic.enhanced_chat_handler import EnhancedChatHandler
from assets.streamlit_styles import apply_professional_styling, create_nav_header

# --- Page Configuration ---
st.set_page_config(
    page_title="Chat with Data",
    page_icon="💬",
    layout="wide"
)

apply_professional_styling()

# --- Navigation Header ---
create_nav_header("💬 Conversational Data Analysis", "Have natural conversations with your data using AI")

# Enhanced CSS for chat interface
st.markdown("""
<style>
    .chat-container {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0 0.5rem auto;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: white;
        border: 1px solid #e0e0e0;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem auto 0.5rem 0;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .intent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .intent-data-query {
        background: #e3f2fd;
        color: #1976d2;
    }
    
    .intent-follow-up {
        background: #f3e5f5;
        color: #7b1fa2;
    }
    
    .intent-greeting {
        background: #e8f5e9;
        color: #388e3c;
    }
    
    .intent-help {
        background: #fff3e0;
        color: #f57c00;
    }
    
    .chat-input-container {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 1rem;
        border-top: 2px solid #f0f0f0;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
    }
    
    .suggestion-chip {
        display: inline-block;
        background: #f5f5f5;
        border: 1px solid #e0e0e0;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.9rem;
    }
    
    .suggestion-chip:hover {
        background: #667eea;
        color: white;
        border-color: #667eea;
    }
    
    .context-indicator {
        background: #fff9c4;
        border-left: 4px solid #fbc02d;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize enhanced chat handler
if 'enhanced_chat_handler' not in st.session_state:
    st.session_state.enhanced_chat_handler = EnhancedChatHandler()

chat_handler = st.session_state.enhanced_chat_handler

# Initialize display history (separate from internal conversation manager)
if 'display_messages' not in st.session_state:
    st.session_state.display_messages = []

# --- Load and Select Data ---
data_sources = load_all_data_sources()

if not data_sources:
    st.warning("📂 No data sources found. Please upload a CSV or connect to a database in the 'Load Data' page first.")
    st.info("💡 Once you load data, you can have natural conversations to analyze it!")
    st.stop()

# Sidebar for configuration
with st.sidebar:
    st.markdown("### 🎛️ Chat Configuration")
    
    st.markdown("#### 📊 Select Data Sources")
    selected_keys = st.multiselect(
        "Choose datasets to chat with:",
        list(data_sources.keys()),
        default=list(data_sources.keys())[:2] if len(data_sources) >= 2 else list(data_sources.keys()),
        help="Select up to 3 datasets for your conversation"
    )
    
    if not selected_keys:
        st.warning("Please select at least one dataset")
        st.stop()
    
    # Display selected data info
    st.markdown("#### 📋 Selected Data Summary")
    for key in selected_keys:
        df = data_sources[key]
        with st.expander(f"📄 {key}", expanded=False):
            st.metric("Rows", f"{len(df):,}")
            st.metric("Columns", len(df.columns))
            st.text("Columns: " + ", ".join(df.columns[:5].tolist()))
            if len(df.columns) > 5:
                st.text(f"... and {len(df.columns) - 5} more")
    
    st.markdown("---")
    
    # Conversation controls
    st.markdown("#### 🔧 Conversation Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            chat_handler.clear_conversation()
            st.session_state.display_messages = []
            st.rerun()
    
    with col2:
        show_intent = st.checkbox("Show Intent", value=True, help="Display detected intent for each message")
    
    # Conversation stats
    st.markdown("#### 📊 Conversation Stats")
    message_count = len(st.session_state.display_messages)
    st.metric("Messages", message_count)
    
    if message_count > 0:
        data_queries = sum(1 for msg in st.session_state.display_messages 
                          if msg.get('intent', {}).get('requires_data_access', False))
        st.metric("Data Queries", data_queries)

# Get selected dataframes
dfs = get_selected_dfs(data_sources, selected_keys)

# Main chat area
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# --- LLM Configuration ---
with st.expander("⚙️ LLM Configuration", expanded=False):
    llm_backend, model_backend, model_name, user_token = configure_llm_backend()

# If no configuration done, use defaults
if 'llm_backend' not in locals():
    llm_backend = "pandasai"
    model_backend = "ollama"
    model_name = "mistral"
    user_token = ""

# Welcome message
if not st.session_state.display_messages:
    st.markdown("""
    <div class="assistant-message">
        <strong>👋 Hello! I'm your data analysis assistant.</strong>
        <p>I can help you explore and understand your data through natural conversation. Just ask me anything!</p>
        <p style="font-size: 0.9rem; color: #666; margin-top: 1rem;">
        💡 Try asking questions like:<br>
        • "What's in my data?"<br>
        • "Show me the top 10 customers by revenue"<br>
        • "Compare sales across different regions"<br>
        • "Create a chart of monthly trends"
        </p>
    </div>
    """, unsafe_allow_html=True)

# Display conversation history
for msg in st.session_state.display_messages:
    if msg['role'] == 'user':
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong> {msg['content']}
        </div>
        """, unsafe_allow_html=True)
    
    elif msg['role'] == 'assistant':
        # Show natural response
        intent_class = f"intent-{msg.get('intent', {}).get('intent', 'data-query').replace('_', '-')}"
        intent_label = msg.get('intent', {}).get('intent', 'response').replace('_', ' ').title()
        
        response_html = f"""
        <div class="assistant-message">
            <strong>🤖 Assistant:</strong>
            <div style="margin-top: 0.5rem;">{msg['content']}</div>
        """
        
        if show_intent:
            confidence = msg.get('intent', {}).get('confidence', 0) * 100
            response_html += f"""
            <div class="intent-badge {intent_class}">
                {intent_label} ({confidence:.0f}% confidence)
            </div>
            """
        
        response_html += "</div>"
        
        st.markdown(response_html, unsafe_allow_html=True)
        
        # Show data results if available
        if 'data_results' in msg and msg['data_results']:
            data_results = msg['data_results']
            result_type = data_results.get('type', 'unknown')
            
            if result_type == 'dataframe':
                with st.expander("📊 View Data Results", expanded=False):
                    df_result = data_results['content']
                    st.dataframe(df_result, use_container_width=True)
                    
                    # Quick stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows", len(df_result))
                    with col2:
                        st.metric("Columns", len(df_result.columns))
                    with col3:
                        if len(df_result) > 0:
                            st.metric("First Value", df_result.iloc[0, 0])
            
            elif result_type == 'image':
                image_path = data_results['content']
                if os.path.exists(image_path):
                    st.image(image_path, caption="Generated Visualization", use_column_width=True)
            
            elif result_type == 'error':
                st.error(f"❌ {data_results['content']}")

# Suggestion chips (contextual)
if not st.session_state.display_messages or len(st.session_state.display_messages) < 2:
    st.markdown("### 💡 Try asking:")
    suggestions = [
        "What data do I have?",
        "Show me a summary",
        "What are the column names?",
        "How many rows are there?"
    ]
else:
    # Context-aware suggestions
    last_intent = st.session_state.display_messages[-1].get('intent', {}).get('intent', '')
    
    if last_intent == 'data_query':
        suggestions = [
            "Show me more details",
            "Create a visualization",
            "What patterns do you see?",
            "Compare these results with another column"
        ]
    elif last_intent == 'visualization':
        suggestions = [
            "Show different type of chart",
            "What insights can we draw?",
            "Analyze the trends",
        ]
    else:
        suggestions = [
            "Tell me more",
            "Show me an example",
            "What else can you do?"
        ]

# Display suggestions
suggestion_cols = st.columns(len(suggestions))
for i, suggestion in enumerate(suggestions):
    with suggestion_cols[i]:
        if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
            # Trigger input with suggestion
            st.session_state.suggestion_input = suggestion
            st.rerun()

# Chat input
st.markdown("---")

# Use suggestion if available
default_input = st.session_state.pop('suggestion_input', '')

with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_question = st.text_input(
            "Your message:",
            value=default_input,
            placeholder="Ask me anything about your data...",
            label_visibility="collapsed",
            key="user_input"
        )
    
    with col2:
        submit_button = st.form_submit_button("Send 📤", type="primary", use_container_width=True)

# Handle message submission
if submit_button and user_question:
    
    # Add user message to display
    st.session_state.display_messages.append({
        'role': 'user',
        'content': user_question
    })
    
    with st.spinner("🤔 Thinking..."):
        try:
            # Handle with enhanced chat handler
            response = chat_handler.handle_message(
                user_question,
                dfs,
                llm_backend,
                model_backend,
                model_name,
                user_token
            )
            
            # Process response
            if response['type'] == 'enhanced':
                # Enhanced response with both natural language and data
                display_msg = {
                    'role': 'assistant',
                    'content': response['natural_response'],
                    'intent': response['intent'],
                    'data_results': response.get('data_results')
                }
            else:
                # Simple text response
                display_msg = {
                    'role': 'assistant',
                    'content': response['content'],
                    'intent': response.get('intent', {})
                }
            
            st.session_state.display_messages.append(display_msg)
            
            # Rerun to display new messages
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing your message: {str(e)}")
            st.info("💡 Try rephrasing your question or check your LLM configuration.")

# Footer
st.markdown("---")

with st.expander("ℹ️ How to Chat Effectively", expanded=False):
    st.markdown("""
    ### 💬 Conversation Tips
    
    **Natural Conversations:**
    - I remember our conversation context, so you can ask follow-up questions!
    - Use pronouns like "it", "that", "those" to refer to previous results
    - Example: "Show me sales data" → "What's the average?" → "Plot it"
    
    **Types of Questions I Understand:**
    - 📊 Data queries: "What's the total revenue?"
    - 📈 Visualizations: "Create a bar chart of top products"
    - 🔍 Comparisons: "Compare region A vs region B"
    - 📋 Summaries: "Summarize the customer data"
    - ❓ Follow-ups: "Show me more", "What about category X?"
    
    **Best Practices:**
    - Be specific about what you want to see
    - Ask one question at a time for clearer results
    - Use the suggestion chips for inspiration
    - Check the intent badge to see how I understood your message
    
    **Current Capabilities:**
    - ✅ Natural language understanding
    - ✅ Context-aware conversations
    - ✅ Intent classification
    - ✅ Data querying with PandasAI/Lotus
    - ✅ Visualization generation
    - ✅ Follow-up question handling
    """)

with st.expander("🐛 Debug Information", expanded=False):
    st.markdown("### Conversation State")
    st.json({
        "total_messages": len(st.session_state.display_messages),
        "selected_datasets": selected_keys,
        "llm_backend": llm_backend,
        "model": f"{model_backend}/{model_name}",
        "last_intent": st.session_state.display_messages[-1].get('intent', {}) if st.session_state.display_messages else {}
    })

st.markdown('</div>', unsafe_allow_html=True)

# Performance info
if len(dfs) > 0:
    total_rows = sum(len(df) for _, df in dfs)
    if total_rows > 50000:
        st.warning(f"""
        ⚠️ **Large Dataset Notice**: Working with {total_rows:,} rows. 
        For better performance, ask specific questions to reduce processing time.
        """)