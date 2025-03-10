import re

# Read the original file
with open('app.py', 'r') as f:
    content = f.read()

# Replace the custom header with a simple title
content = re.sub(
    r'# Custom header.*?st.markdown\(""".*?""", unsafe_allow_html=True\)',
    '# Simple title\nst.title("Yad2 Real Estate Scraper")',
    content,
    flags=re.DOTALL
)

# Write the modified content back to the file
with open('app.py', 'w') as f:
    f.write(content)

print("Simplified the header in app.py") 