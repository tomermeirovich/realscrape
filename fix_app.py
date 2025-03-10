import re

# Read the original file
with open('app.py', 'r') as f:
    content = f.read()

# Fix the create_temp_file function
new_function = '''def create_temp_file(signal):
    try:
        # Create a temporary file with the signal
        if not hasattr(st.session_state, "comm_file") or not st.session_state.comm_file:
            print("Error: comm_file not set in session state")
            return None
        
        # Write to the existing communication file
        with open(st.session_state.comm_file, "w") as f:
            f.write(signal)
        
        print(f"Created signal '{signal}' in communication file: {st.session_state.comm_file}")
        return st.session_state.comm_file
    except Exception as e:
        print(f"Error creating temporary file: {e}")
        return None'''

# Replace the function
pattern = r'def create_temp_file\(signal\):.*?return None'
content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Add code to store comm_file in session state
pattern = r'comm_file = os\.path\.join\(output_dir, "comm\.txt"\)'
replacement = 'comm_file = os.path.join(output_dir, "comm.txt")\n    st.session_state.comm_file = comm_file'
content = re.sub(pattern, replacement, content)

# Write the modified content back to the file
with open('app.py', 'w') as f:
    f.write(content)

print("Fixed app.py successfully!") 