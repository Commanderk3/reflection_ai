import streamlit as st
import requests

# Configuration
FASTAPI_URL = "https://reflection-ai.onrender.com"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "terminated" not in st.session_state:
    st.session_state.terminated = False
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "analysis" not in st.session_state:
    st.session_state.analysis = ""
if "old_summary" not in st.session_state:
    st.session_state.old_summary = """
Let's summarize what we've discussed so far:
You created a project in Music Blocks and made a cool hip-hop beat. You used the Pitch-Drum Matrix to experiment with different rhythms and patterns, which allowed you to think freely and focus on the creative aspect.
You learned that trying different patterns is not the only thing to focus on when creating a beat, and that splitting a note value can lead to some really cool and unique sounds.
You're planning to create a chord progression that suits your beat and wants to enhance or complement its vibe.
"""

# Page setup
st.title("Reflective Learning")
st.caption("A conversational guide for your MusicBlocks learning journey")

# Sidebar for additional features
with st.sidebar:
    st.header("Additional Options")

    # Generate Summary Button
    if st.button("Generate Summary"):
        try:
            response = requests.get(f"{FASTAPI_URL}/summary/")
            if response.status_code == 200:
                summary = response.json()["new_summary"]
                st.session_state.summary = summary

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"📝 Here's a summary of our conversation:\n\n{summary}"
                })
            else:
                st.error("Failed to generate summary")
        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")

    # Generate Analysis Button (only if summary is generated)
    if st.button("Generate Analysis"):
        if not st.session_state.summary:
            st.warning("⚠️ Please generate a summary first.")
        else:
            try:
                # Send both summaries (old and new) to the backend
                response = requests.get(f"{FASTAPI_URL}/summary/")
                if response.status_code == 200:
                    outcome = response.json()["outcome"]
                    st.session_state.outcome = outcome

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"📈 Learning Outcome:\n\n{outcome}"
                    })
                else:
                    st.error("Failed to generate analysis")
            except Exception as e:
                st.error(f"Error generating analysis: {str(e)}")


# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if not st.session_state.terminated:
    if prompt := st.chat_input("What would you like to discuss about your MusicBlocks project?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{FASTAPI_URL}/chat/",
                    json={"query": prompt}
                )
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        response_content = f"Error: {data['error']}"
                    else:
                        response_content = data["response"]
                        if data.get("terminate", False):
                            st.session_state.terminated = True
                else:
                    response_content = f"API request failed with status {response.status_code}"

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content
                })

                with st.chat_message("assistant"):
                    st.markdown(response_content)

            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Sorry, I'm having trouble connecting to the server. Please try again later."
                })
else:
    st.info("This conversation has ended. Please refresh the page to start a new one.")
