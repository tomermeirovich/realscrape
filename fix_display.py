import re

# Read the original file
with open('app.py', 'r') as f:
    content = f.read()

# Add debug print before displaying dataframe
content = content.replace(
    '# Display the dataframe\n                results_card.dataframe(df)',
    '# Display the dataframe\n                print("Debug: About to display dataframe with", len(df), "rows")\n                st.dataframe(df)'
)

# Write the modified content back to the file
with open('app.py', 'w') as f:
    f.write(content)

print("Fixed app.py to use st.dataframe() instead of results_card.dataframe()") 