import streamlit as st
import pandas as pd
import os
import subprocess
import json
import tempfile
import time
import threading
import signal
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Yad2 Real Estate Scraper",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color scheme
COLOR_THEME = {
    "primary": "#1E88E5",
    "secondary": "#FFC107",
    "background": "#F8F9FA",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#F44336",
    "text": "#212121",
    "light_text": "#757575"
}

# Add custom CSS
st.markdown(f"""
<style>
    /* Global styles */
    .main {{
        background-color: {COLOR_THEME["background"]};
        padding: 2rem;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOR_THEME["primary"]};
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* Card styles */
    .card {{
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }}
    
    /* Button styles */
    .stButton > button {{
        background-color: {COLOR_THEME["primary"]};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {COLOR_THEME["secondary"]};
        color: {COLOR_THEME["text"]};
    }}
    
    /* Status message styles */
    .success-message {{
        background-color: {COLOR_THEME["success"]};
        color: white;
        padding: 1rem;
        border-radius: 5px;
        font-weight: bold;
    }}
    
    .warning-message {{
        background-color: {COLOR_THEME["warning"]};
        color: white;
        padding: 1rem;
        border-radius: 5px;
        font-weight: bold;
    }}
    
    .error-message {{
        background-color: {COLOR_THEME["error"]};
        color: white;
        padding: 1rem;
        border-radius: 5px;
        font-weight: bold;
    }}
    
    /* Sidebar styles */
    .sidebar .sidebar-content {{
        background-color: white;
    }}
    
    /* Dataframe styles */
    .dataframe {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* Custom header */
    .app-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem;
        background-color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .app-header-title {{
        display: flex;
        align-items: center;
        gap: 1rem;
    }}
    
    .app-header-title h1 {{
        margin: 0;
        font-size: 2rem;
    }}
    
    .app-header-actions {{
        display: flex;
        gap: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state for storing data
if 'data' not in st.session_state:
    st.session_state.data = None
if 'csv_path' not in st.session_state:
    st.session_state.csv_path = None
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = None
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'scraper_process' not in st.session_state:
    st.session_state.scraper_process = None
if 'captcha_detected' not in st.session_state:
    st.session_state.captcha_detected = False
if 'element_selection_mode' not in st.session_state:
    st.session_state.element_selection_mode = False
if 'captcha_solved' not in st.session_state:
    st.session_state.captcha_solved = False
if 'element_selected' not in st.session_state:
    st.session_state.element_selected = False
if 'temp_file' not in st.session_state:
    st.session_state.temp_file = None
if "scraper_running" not in st.session_state:
    st.session_state.scraper_running = False
if "last_scrape_results" not in st.session_state:
    st.session_state.last_scrape_results = None
if "all_scrape_results" not in st.session_state:
    st.session_state.all_scrape_results = []
if "scrape_history" not in st.session_state:
    st.session_state.scrape_history = []

# App title
st.markdown("""
<div class="app-header">
    <div class="app-header-title">
        <h1>🏠 Yad2 Real Estate Scraper</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    This app scrapes real estate listings from Yad2.co.il.
    
    **How it works:**
    1. Enter a Yad2 URL
    2. The app will open a browser window
    3. Solve any CAPTCHA if presented
    4. Wait for the listings to be scraped
    5. Download the results as CSV
    
    **Note:** This app requires user interaction to solve CAPTCHAs.
    """)
    
    st.header("Settings")
    max_pages = st.number_input("Maximum pages to scrape", min_value=1, max_value=20, value=3)
    
    st.header("Debug Info")
    if st.button("Show Debug Info"):
        st.json(st.session_state.debug_info)

# Main content
st.header("Enter Yad2 URL")
url = st.text_input(
    "Enter a Yad2 real estate URL",
    value="https://www.yad2.co.il/realestate/forsale",
    help="Enter a URL from Yad2's real estate section"
)

# Settings in a collapsible section
with st.expander("Scraper Settings", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        max_pages = st.number_input("Maximum pages to scrape", min_value=1, max_value=20, value=3)
    with col2:
        save_to_history = st.checkbox("Save results to history", value=True, 
                                     help="Save the results to history for later analysis")

# Start scraping button
start_button = st.button(
    "Start Scraping",
    disabled=st.session_state.scraper_running,
    help="Click to start scraping the provided URL"
)

# Create placeholders for dynamic content
status_card = st.empty()
interactive_card = st.empty()
results_card = st.empty()

# Function to create a temporary file for communication
def create_temp_file(signal):
    try:
        # Create a temporary file with the signal
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt')
        temp_file.write(signal)
        temp_file.close()
        print(f"Created temporary file for signal '{signal}' at {temp_file.name}")
        return temp_file.name
    except Exception as e:
        print(f"Error creating temporary file: {e}")
        return None

# Function to handle captcha solved button
def on_captcha_solved():
    try:
        # Create a temporary file to signal that captcha is solved
        temp_file = create_temp_file("captcha_solved")
        if temp_file:
            st.session_state.captcha_comm_file = temp_file
            st.session_state.captcha_solved = True
            print(f"Created captcha solved signal file: {temp_file}")
        else:
            print("Failed to create captcha solved signal file")
    except Exception as e:
        print(f"Error in on_captcha_solved: {e}")

# Function to handle element selected button
def on_element_selected():
    try:
        # Create a temporary file to signal that element is selected
        temp_file = create_temp_file("element_selected")
        if temp_file:
            st.session_state.element_comm_file = temp_file
            st.session_state.element_selected = True
            print(f"Created element selected signal file: {temp_file}")
        else:
            print("Failed to create element selected signal file")
    except Exception as e:
        print(f"Error in on_element_selected: {e}")

# Function to run the scraper
def run_scraper(url, max_pages=3):
    # Create a temporary file for the output
    output_dir = tempfile.mkdtemp()
    output_path = os.path.join(output_dir, "yad2_listings.csv")
    
    # Create a temporary file for communication
    comm_file = os.path.join(output_dir, "comm.txt")
    
    # Get the path to the interactive scraper
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scraper_path = os.path.join(script_dir, "interactive_scraper.js")
    
    # Check if the scraper exists
    if not os.path.exists(scraper_path):
        st.error(f"Scraper not found at {scraper_path}")
        return None, None
    
    # Run the scraper
    cmd = ["node", scraper_path, url, output_path, comm_file, str(max_pages)]
    
    # Print the command for debugging
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the command
    result = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    return result, output_path

# Handle start button click
if start_button:
    st.session_state.scraper_running = True
    st.session_state.captcha_solved = False
    st.session_state.element_selection_mode = False
    st.session_state.debug_info = {"stdout": [], "stderr": []}
    
    # Create status card
    status_card.markdown('<div class="card">', unsafe_allow_html=True)
    status_placeholder = status_card.empty()
    status_placeholder.info("Starting the scraper...")
    
    # Run the scraper
    result, output_path = run_scraper(url, max_pages)
    
    if not result:
        status_placeholder.error("Failed to start the scraper")
        st.session_state.scraper_running = False
        status_card.markdown('</div>', unsafe_allow_html=True)
    else:
        status_placeholder.info("Scraper started. Browser window should open shortly...")
        
        # Create interactive card
        interactive_card.markdown('<div class="card">', unsafe_allow_html=True)
        interactive_placeholder = interactive_card.empty()
        
        # Process stdout
        for line in iter(result.stdout.readline, ''):
            st.session_state.debug_info["stdout"].append(line)
            
            # Check for captcha
            if "CAPTCHA detected" in line:
                st.session_state.captcha_solved = False
                interactive_placeholder.warning("CAPTCHA detected! Please solve it in the browser window.")
                
                # Add a button for the user to indicate they've solved the captcha
                captcha_button = interactive_placeholder.button(
                    "I've Solved the CAPTCHA",
                    key="captcha_button",
                    help="Click this button after solving the CAPTCHA in the browser window"
                )
                
                if captcha_button:
                    on_captcha_solved()
                    
                status_placeholder.warning("Waiting for you to solve the CAPTCHA...")
            
            # Check for captcha solved
            if "Captcha solved successfully" in line:
                st.session_state.captcha_solved = True
                interactive_placeholder.empty()
                status_placeholder.success("CAPTCHA solved! Proceeding with scraping...")
            
            # Check for element selection mode
            if "INTERACTIVE ELEMENT SELECTION" in line:
                st.session_state.element_selection_mode = True
                interactive_placeholder.warning("Please select a listing element in the browser window.")
                
                # Add a button for the user to indicate they've selected an element
                element_button = interactive_placeholder.button(
                    "I've Selected an Element",
                    key="element_button",
                    help="Click this button after selecting a listing element in the browser window"
                )
                
                if element_button:
                    on_element_selected()
                    
                status_placeholder.warning("Waiting for you to select a listing element...")
            
            # Check for element selected
            if "Selected element information:" in line:
                st.session_state.element_selection_mode = False
                interactive_placeholder.empty()
                status_placeholder.success("Element selected! Extracting listings...")
            
            # Update status for other important messages
            if "Extracting listings" in line:
                status_placeholder.info("Extracting listings from the page...")
            
            if "Successfully scraped" in line and "listings" in line:
                status_placeholder.success("Scraping completed successfully!")
            
            # Check for page navigation
            if "Scraping page" in line:
                page_num = line.split("page")[1].split("...")[0].strip()
                status_placeholder.info(f"Scraping page {page_num}...")
            
            if "Next page found" in line:
                status_placeholder.info("Moving to next page...")
        
        # Process stderr
        for line in iter(result.stderr.readline, ''):
            st.session_state.debug_info["stderr"].append(line)
        
        # Wait for process to complete
        result.wait()
        
        # Close interactive card
        interactive_card.markdown('</div>', unsafe_allow_html=True)
        
        # Check for debug files
        debug_dir = os.path.dirname(output_path)
        
        # Look for screenshots
        for filename in os.listdir(debug_dir):
            if filename.endswith('.png') and (
                filename.startswith('page_loaded') or 
                filename.startswith('captcha') or 
                filename.startswith('after_captcha') or
                filename.startswith('selected_element')
            ):
                st.session_state.debug_info[filename] = os.path.join(debug_dir, filename)
        
        # Check if the output file exists
        if os.path.exists(output_path):
            try:
                # Read the CSV file
                df = pd.read_csv(output_path)
                
                # Add timestamp and URL to the dataframe
                df['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df['source_url'] = url
                
                # Store in session state
                st.session_state.last_scrape_results = df
                
                # Add to history if enabled
                if save_to_history:
                    st.session_state.all_scrape_results.append(df)
                    
                    # Add to scrape history
                    history_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "url": url,
                        "count": len(df),
                        "max_pages": max_pages,
                        "output_path": output_path
                    }
                    st.session_state.scrape_history.append(history_entry)
                
                # Create results card
                results_card.markdown('<div class="card">', unsafe_allow_html=True)
                
                # Display the results
                results_card.success(f"Successfully scraped {len(df)} listings!")
                
                # Quick stats
                col1, col2, col3 = results_card.columns(3)
                
                # Clean price data for analysis
                df['price_numeric'] = df['Price'].str.extract(r'([\d,]+)').replace(',', '', regex=True).astype(float)
                
                with col1:
                    avg_price = df['price_numeric'].mean()
                    st.metric("Average Price", f"₪{avg_price:,.0f}")
                
                with col2:
                    if 'Rooms' in df.columns:
                        # Extract numeric rooms value
                        df['rooms_numeric'] = df['Rooms'].str.extract(r'([\d\.]+)').astype(float)
                        avg_rooms = df['rooms_numeric'].mean()
                        st.metric("Average Rooms", f"{avg_rooms:.1f}")
                
                with col3:
                    if 'Size' in df.columns:
                        # Extract numeric size value
                        df['size_numeric'] = df['Size'].str.extract(r'([\d\.]+)').astype(float)
                        avg_size = df['size_numeric'].mean()
                        st.metric("Average Size", f"{avg_size:.1f} m²")
                
                # Display the dataframe
                results_card.dataframe(df)
                
                # Download button
                csv = df.to_csv(index=False)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                results_card.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"yad2_listings_{timestamp}.csv",
                    mime="text/csv"
                )
                
                # Close results card
                results_card.markdown('</div>', unsafe_allow_html=True)
                
                # Show a message to navigate to analytics
                st.info("Navigate to the Analytics page to see more insights from your data!")
                
            except Exception as e:
                results_card.error(f"Error reading results: {e}")
        else:
            results_card.error("No results found. The scraper may have failed.")
        
        # Close status card
        status_card.markdown('</div>', unsafe_allow_html=True)
        
        # Reset the scraper running state
        st.session_state.scraper_running = False

# Show recent history if available
if st.session_state.scrape_history and len(st.session_state.scrape_history) > 0:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Recent Scraping History")
    
    # Create a dataframe from history
    history_df = pd.DataFrame(st.session_state.scrape_history)
    
    # Display the history
    st.dataframe(history_df[["timestamp", "url", "count", "max_pages"]])
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #757575; font-size: 0.8rem;">
    © 2023 Yad2 Real Estate Scraper | Not affiliated with Yad2.co.il
</div>
""", unsafe_allow_html=True) 