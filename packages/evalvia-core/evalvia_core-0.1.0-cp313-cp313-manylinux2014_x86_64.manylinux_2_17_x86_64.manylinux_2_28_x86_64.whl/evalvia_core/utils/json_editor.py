import streamlit as st
import json

def render_json_editor(data, prefix="", path=""):
    """Recursively render JSON editor with key-value inputs"""
    if isinstance(data, dict):
        new_data = {}
        keys_to_delete = []
        
        for key, value in data.items():
            col1, col2, col3 = st.columns([2, 4, 1])
            
            with col1:
                new_key = st.text_input("Key", value=key, key=f"key_{prefix}_{key}")
            
            with col3:
                if st.button("🗑️", key=f"del_{prefix}_{key}", help="Delete this key"):
                    keys_to_delete.append(key)
                    continue
            
            with col2:
                if isinstance(value, dict):
                    with st.expander(f"📁 {new_key} (Object)"):
                        new_value = render_json_editor(value, f"{prefix}_{new_key}", f"{path}.{new_key}")
                elif isinstance(value, list):
                    with st.expander(f"📋 {new_key} (Array)"):
                        new_value = render_json_editor(value, f"{prefix}_{new_key}", f"{path}.{new_key}")
                else:
                    # Determine value type and render appropriate input
                    if isinstance(value, bool):
                        new_value = st.checkbox("Value", value=value, key=f"value_{prefix}_{key}")
                    elif isinstance(value, (int, float)):
                        new_value = st.number_input("Value", value=value, key=f"value_{prefix}_{key}")
                    else:
                        new_value = st.text_input("Value", value=str(value), key=f"value_{prefix}_{key}")
                        # Try to parse as number or boolean
                        if new_value.lower() in ['true', 'false']:
                            new_value = new_value.lower() == 'true'
                        else:
                            try:
                                if '.' in new_value:
                                    new_value = float(new_value)
                                else:
                                    new_value = int(new_value)
                            except ValueError:
                                pass  # Keep as string
            
            new_data[new_key] = new_value
        
        # Remove deleted keys
        for key in keys_to_delete:
            if key in new_data:
                del new_data[key]
        
        # Add new key button
        if st.button(f"➕ Add Key", key=f"add_key_{prefix}"):
            new_data["new_key"] = "new_value"
        
        return new_data
    
    elif isinstance(data, list):
        new_list = []
        items_to_delete = []
        
        for i, item in enumerate(data):
            col1, col2 = st.columns([4, 1])
            
            with col2:
                if st.button("🗑️", key=f"del_item_{prefix}_{i}", help="Delete this item"):
                    items_to_delete.append(i)
                    continue
            
            with col1:
                if isinstance(item, dict):
                    with st.expander(f"📁 Item {i} (Object)"):
                        new_item = render_json_editor(item, f"{prefix}_item_{i}", f"{path}[{i}]")
                elif isinstance(item, list):
                    with st.expander(f"📋 Item {i} (Array)"):
                        new_item = render_json_editor(item, f"{prefix}_item_{i}", f"{path}[{i}]")
                else:
                    if isinstance(item, bool):
                        new_item = st.checkbox(f"Item {i}", value=item, key=f"item_{prefix}_{i}")
                    elif isinstance(item, (int, float)):
                        new_item = st.number_input(f"Item {i}", value=item, key=f"item_{prefix}_{i}")
                    else:
                        new_item = st.text_input(f"Item {i}", value=str(item), key=f"item_{prefix}_{i}")
                        if new_item.lower() in ['true', 'false']:
                            new_item = new_item.lower() == 'true'
                        else:
                            try:
                                if '.' in new_item:
                                    new_item = float(new_item)
                                else:
                                    new_item = int(new_item)
                            except ValueError:
                                pass
            
            new_list.append(new_item)
        
        # Remove deleted items (in reverse order to maintain indices)
        for i in sorted(items_to_delete, reverse=True):
            if i < len(new_list):
                new_list.pop(i)
        
        # Add new item button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("➕ Add String", key=f"add_str_{prefix}"):
                new_list.append("new_item")
        with col2:
            if st.button("➕ Add Object", key=f"add_obj_{prefix}"):
                new_list.append({})
        with col3:
            if st.button("➕ Add Array", key=f"add_arr_{prefix}"):
                new_list.append([])
        
        return new_list
    
    else:
        # Primitive value
        if isinstance(data, bool):
            return st.checkbox("Value", value=data, key=f"root_value_{prefix}")
        elif isinstance(data, (int, float)):
            return st.number_input("Value", value=data, key=f"root_value_{prefix}")
        else:
            val = st.text_input("Value", value=str(data), key=f"root_value_{prefix}")
            if val.lower() in ['true', 'false']:
                return val.lower() == 'true'
            try:
                if '.' in val:
                    return float(val)
                else:
                    return int(val)
            except ValueError:
                return val

st.set_page_config(page_title="JSON Editor", layout="wide")
st.title("JSON Editor")

# Initialize session state
if 'recent_files' not in st.session_state:
    st.session_state.recent_files = []  # list of dicts: {'name': str, 'content': str, 'path': str}

if 'current_data' not in st.session_state:
    st.session_state.current_data = {}

if 'current_name' not in st.session_state:
    st.session_state.current_name = "Untitled"

if 'current_path' not in st.session_state:
    st.session_state.current_path = None

if 'selected_file' not in st.session_state:
    st.session_state.selected_file = ""

# Sidebar for recent files
with st.sidebar:
    st.header("Recent Files")
    
    file_options = [""] + [f['name'] for f in st.session_state.recent_files]
    selected_file = st.selectbox("Select a file", file_options, key="file_selector")
    
    if selected_file and selected_file != st.session_state.selected_file:
        st.session_state.selected_file = selected_file
        if selected_file != "":
            # Find the file in recent files
            for file_info in st.session_state.recent_files:
                if file_info['name'] == selected_file:
                    st.session_state.current_data = json.loads(file_info['content'])
                    st.session_state.current_name = selected_file
                    st.session_state.current_path = file_info.get('path')
                    st.success(f"Loaded: {selected_file}")
    
    # Display file paths on hover (approximation)
    if st.session_state.recent_files:
        st.subheader("File Paths:")
        for file_info in st.session_state.recent_files:
            st.text(f"{file_info['name']}")
            st.caption(f"Path: {file_info.get('path', 'Unknown')}")

# File upload
uploaded_file = st.file_uploader("Choose a JSON file to load", type="json")
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        name = uploaded_file.name
        
        # Add to recent files if not already there
        if not any(f['name'] == name for f in st.session_state.recent_files):
            st.session_state.recent_files.append({
                'name': name, 
                'content': json.dumps(data, indent=4),
                'path': f"Uploaded: {name}"
            })
        
        st.session_state.current_data = data
        st.session_state.current_name = name
        st.session_state.current_path = f"Uploaded: {name}"
        st.success(f"File loaded: {name}")
    except Exception as e:
        st.error(f"Failed to load JSON: {e}")

# Main editor area
st.header(f"Editing: {st.session_state.current_name}")

# Buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🆕 Create New"):
        st.session_state.current_data = {}
        st.session_state.current_name = "Untitled"
        st.session_state.current_path = None
        st.session_state.selected_file = ""
        st.success("New file created!")

with col2:
    if st.button("✅ Validate JSON"):
        try:
            json.dumps(st.session_state.current_data)
            st.success("JSON is valid!")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

with col3:
    # Save functionality
    current_json = json.dumps(st.session_state.current_data, indent=4)
    
    if st.session_state.current_name == "Untitled":
        filename = st.text_input("Filename for new file", value="new_file.json", key="save_filename")
        st.download_button(
            label="💾 Save File",
            data=current_json,
            file_name=filename,
            mime="application/json",
            help="Save as new file"
        )
    else:
        st.download_button(
            label="💾 Save File",
            data=current_json,
            file_name=st.session_state.current_name,
            mime="application/json",
            help=f"Save {st.session_state.current_name}"
        )

# JSON Editor
st.subheader("JSON Structure")
if st.session_state.current_data is not None:
    try:
        new_data = render_json_editor(st.session_state.current_data, "root")
        # Update the session state with the new data
        if new_data != st.session_state.current_data:
            st.session_state.current_data = new_data
    except Exception as e:
        st.error(f"Error rendering JSON: {e}")
        st.json(st.session_state.current_data)

# Display raw JSON (read-only)
with st.expander("📄 View Raw JSON"):
    st.code(json.dumps(st.session_state.current_data, indent=2), language="json")
