import streamlit as st
from main import get_db_answer

# Set page configuration
st.set_page_config(
    page_title="DB Chat Assistant",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS with improved styling
st.markdown("""
<style>
    /* Modern chat container styling */
    .stChatMessage {
        background-color: #2d3748;  /* Dark background */
        border-radius: 15px;
        padding: 15px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* User message styling */
    .stChatMessage[data-testid="user-message"] {
        background-color: #3b82f6;  /* Blue background */
    }
    
    /* Assistant message styling */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #4b5563;  /* Gray background */
    }
    
    /* Improve button styling */
    .stButton button {
        border-radius: 20px;
        padding: 10px 25px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }

    /* Chat message text color */
    .stChatMessage p {
        color: white !important;
    }

    /* Chat input styling */
    .stChatInputContainer textarea {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'conversation_key' not in st.session_state:
        st.session_state.conversation_key = 0

def display_chat_history():
    """Display all messages in the chat history"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

def main():
    # Sidebar configuration
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # Clear chat button with confirmation
        if st.button("Clear Chat History", key="clear_chat"):
            if st.session_state.messages:  # Only show confirmation if there are messages
                if st.button("Confirm Clear?", key="confirm_clear"):
                    st.session_state.messages = []
                    st.session_state.conversation_key += 1  # Force re-render
                    st.rerun()
        
        # Add any additional settings here
        st.divider()
        st.markdown("### About")
        st.markdown("""
        This chat interface allows you to query your database using natural language.
        Built with Streamlit and CrewAI.
        """)

    # Main chat interface
    st.title("💬 Database Chat Assistant")
    
    # Initialize session state
    initialize_session_state()

    # Welcome message container
    with st.container():
        if not st.session_state.messages:  # Only show if no messages
            st.markdown("""
            👋 Welcome! I can help you query your database in natural language.
            
            Try asking questions like:
            - How many customers do we have?
            - What was the total sales last month?
            - Who are our top 5 customers?
            """)

    # Display chat history
    display_chat_history()

    # Chat input
    if prompt := st.chat_input("Ask me about your database...", key=f"chat_input_{st.session_state.conversation_key}"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # Get response from database
        with st.chat_message("assistant", avatar="🤖"):
            try:
                with st.spinner("Querying database..."):
                    response = get_db_answer(prompt)
                    st.markdown(response)
                    
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_message = f"❌ Sorry, I encountered an error: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main() 