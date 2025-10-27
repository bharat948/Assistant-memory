import streamlit as st
import requests
import json

st.title("Register Agent Form")

st.write("Fill the details below to register a new agent.")

with st.form("register_agent_form"):
    agent_id = st.text_input("Agent ID", "")
    name = st.text_input("Name", "")
    agent_type = st.text_input("Agent Type", "")
    description = st.text_area("Description", "")
    system_prompt_template = st.text_area("System Prompt Template", "")
    allowed_tool_ids = st.text_input("Allowed Tool IDs (comma separated)", "")
    allowed_roles = st.text_input("Allowed Roles (comma separated)", "")
    created_by = st.text_input("Created By", "api")
    submit_btn = st.form_submit_button("Register Agent")

if submit_btn:
    data = {
        "agent_id": agent_id,
        "name": name,
        "agent_type": agent_type,
        "description": description,
        "system_prompt_template": system_prompt_template,
        "allowed_tool_ids": [x.strip() for x in allowed_tool_ids.split(",") if x.strip()],
        "allowed_roles": [x.strip() for x in allowed_roles.split(",") if x.strip()],
        "created_by": created_by,
    }

    url = "http://127.0.0.1:8000/agents/register"
    try:
        response = requests.post(
            url,
            headers={"accept": "application/json", "Content-Type": "application/json"},
            data=json.dumps(data)
        )
        if response.status_code == 200:
            st.success("Agent registered successfully!")
            st.json(response.json())
        else:
            st.error(f"Error {response.status_code} - {response.reason}")
            st.text(response.text)
    except Exception as e:
        st.error(f"Exception occurred: {e}")
