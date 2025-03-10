# Yad2 Real Estate Analyzer

A Streamlit web application for scraping and analyzing real estate listings from Yad2, an Israeli real estate website.

## Features

- Scrape real estate listings from Yad2 with a simple interface
- Analyze the data with interactive visualizations
- View statistics about prices, rooms, and more
- Download the data as CSV

## How It Works

This application combines:

1. **Node.js with Puppeteer** for web scraping (handles JavaScript-rendered content)
2. **Streamlit** for the user interface and data analysis

The workflow is simple:

1. User enters a Yad2 URL in the Streamlit interface
2. The Node.js scraper extracts the data and saves it as a CSV
3. Streamlit loads the CSV and provides analysis tools
4. The data is stored only for the current session

## Requirements

- Node.js 14+ with npm
- Python 3.8+
- Chrome browser installed

## Installation

1. Clone this repository:

   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install Node.js dependencies:

   ```
   npm install puppeteer csv-writer
   ```

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the Streamlit app:

   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Enter the Yad2 URL you want to analyze and click "Get Data"

4. Explore the data and analysis in the tabs

## Example URL

The default URL is set to:

```
https://www.yad2.co.il/realestate/forsale?propertyGroup=apartments&property=1&rooms=4-4&price=-1-4220000&page=2
```

You can modify the URL parameters to search for different types of properties, price ranges, locations, etc.

## Notes

- Web scraping may be subject to the terms of service of the website. Use responsibly.
- The scraper may break if Yad2 changes their website structure.
- For large datasets, the scraping process may take some time.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
