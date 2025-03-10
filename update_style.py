import re

# Read the original file
with open('app.py', 'r') as f:
    content = f.read()

# Define a simpler color scheme
simple_color_scheme = """
# Define color scheme
COLOR_THEME = {
    "primary": "#4285F4",    # Google Blue
    "secondary": "#34A853",  # Google Green
    "background": "#FFFFFF", # White
    "success": "#34A853",    # Google Green
    "warning": "#FBBC05",    # Google Yellow
    "error": "#EA4335",      # Google Red
    "text": "#202124",       # Dark Gray
    "light_text": "#5F6368"  # Medium Gray
}
"""

# Define simpler CSS
simple_css = """
# Add custom CSS
st.markdown(f'''
<style>
    /* Global styles */
    .main {
        background-color: white;
        padding: 1rem;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #4285F4;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Button styles */
    .stButton > button {
        background-color: #4285F4;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #5c9ce6;
    }
    
    /* Status message styles */
    .success-message {
        color: #34A853;
        font-weight: bold;
    }
    
    .warning-message {
        color: #FBBC05;
        font-weight: bold;
    }
    
    .error-message {
        color: #EA4335;
        font-weight: bold;
    }
</style>
''', unsafe_allow_html=True)
"""

# Replace the color scheme
content = re.sub(r'# Define color scheme.*?}', simple_color_scheme, content, flags=re.DOTALL)

# Replace the CSS
content = re.sub(r'# Add custom CSS.*?unsafe_allow_html=True\)', simple_css, content, flags=re.DOTALL)

# Remove card styling
content = content.replace('<div class="card">', '')
content = content.replace('</div>', '')

# Write the modified content back to the file
with open('app.py', 'w') as f:
    f.write(content)

print("Updated app.py with simpler styling and colors") 