import asyncio
import streamlit as st
import os
import uuid
import sys
from pathlib import Path

from mcp_agent_ui_utils.config import bot_configs
from mcp_agent_ui_utils.ui_utils import invoke_agent, initialize_mcp_config
import argparse

def initialize_session(mcp_config_file=None):
    """Initialize session state and bot configuration."""
    if 'count' not in st.session_state:
        st.session_state['count'] = 1
        initialize_mcp_config(mcp_config_file)
        # Get bot configuration
        bot_name = os.environ.get('BOT_NAME', 'MCP Agent')
        bot_config = next((config for config in bot_configs if config['bot_name'] == bot_name), None)
        
        if bot_config:
            st.session_state['bot_config'] = bot_config

            # Initialize session ID and message history
            st.session_state['session_id'] = str(uuid.uuid4())
            st.session_state.messages = []

def main():
    """Main application flow."""
    parser = argparse.ArgumentParser(description="MCP Agent UI")
    parser.add_argument("--mcp-config", dest="mcp_config_file", 
                        help="Path to MCP config file", default=None)
    args = parser.parse_args()
    mcp_config_file = args.mcp_config_file

    print(f"Starting with config file: {args.mcp_config_file}")
    
    initialize_session(mcp_config_file)

    # Display chat interface
    st.title(st.session_state['bot_config']['bot_name'])

    # Show message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if 'user_input' not in st.session_state:
        next_prompt = st.session_state['bot_config']['start_prompt']
        user_query = st.chat_input(placeholder=next_prompt, key="user_input")
        st.session_state['bot_config']['start_prompt'] = " "
    elif st.session_state.count > 1:
        user_query = st.session_state['user_input']
        
        if user_query:
            # Display user message
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Get and display assistant response
            response = ""
            with st.chat_message("assistant"):
                try:
                    session_id = st.session_state['session_id']
                    response = st.write(asyncio.run(invoke_agent(
                        user_query, 
                        session_id, 
                    )))
                except Exception as e:
                    print(f"Error: {e}")  # Keep logging for debugging
                    st.error(f"An error occurred: {str(e)}")  # Show error in UI
                    response = "I encountered an error processing your request. Please try again."

            # Update chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Reset input
        user_query = st.chat_input(placeholder=" ", key="user_input")

    # Update session count
    st.session_state['count'] = st.session_state.get('count', 1) + 1

if __name__ == "__main__":
    main()