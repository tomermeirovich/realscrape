const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");
const createCsvWriter = require("csv-writer").createObjectCsvWriter;

// Command line arguments
const args = process.argv.slice(2);
const url = args[0] || "https://www.yad2.co.il/realestate/forsale?propertyGroup=apartments&property=1&rooms=4-4&price=-1-4220000&page=2";
const outputFilename = args[1] || path.join("exports", "yad2_listings.csv");
const commFilename = args[2]; // File for communication with Streamlit
const maxPages = args[3] ? parseInt(args[3]) : 3; // Maximum number of pages to scrape, default is 3

// Global variables
let browser;
let page;
let data = [];
let currentPage = 1;

// Function to wait for a signal from Streamlit
async function waitForSignal(signal) {
    console.log(`Waiting for ${signal} signal from Streamlit...`);
    console.log(`Communication file: ${commFilename}`);

    return new Promise((resolve) => {
        if (!commFilename) {
            console.log("No communication file provided, resolving immediately");
            resolve();
            return;
        }

        // Check if the file exists initially
        if (fs.existsSync(commFilename)) {
            const content = fs.readFileSync(commFilename, 'utf8');
            console.log(`Initial file content: "${content}"`);
            if (content.includes(signal)) {
                console.log(`Signal ${signal} already received`);
                // Delete the file to reset the signal
                fs.unlinkSync(commFilename);
                resolve();
                return;
            }
        } else {
            console.log(`Communication file does not exist yet: ${commFilename}`);
        }

        console.log(`Setting up file watcher for ${commFilename}`);
        // Set up a file watcher
        const checkInterval = setInterval(() => {
            try {
                if (fs.existsSync(commFilename)) {
                    const content = fs.readFileSync(commFilename, 'utf8');
                    console.log(`File check: "${content}"`);
                    if (content.includes(signal)) {
                        console.log(`Signal ${signal} received`);
                        clearInterval(checkInterval);
                        // Delete the file to reset the signal
                        fs.unlinkSync(commFilename);
                        resolve();
                    }
                }
            } catch (error) {
                console.error(`Error checking signal file: ${error.message}`);
            }
        }, 500); // Check every 500ms
    });
}

// Main scraper function
async function scrapeYad2() {
    try {
        console.log("Starting Interactive Yad2 scraper...");

        // Launch browser in visible mode
        browser = await puppeteer.launch({
            headless: false, // Visible browser so user can interact
            args: [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--window-size=1920,1080",
            ],
            defaultViewport: {
                width: 1920,
                height: 1080,
            },
        });

        // Create new page
        page = await browser.newPage();

        // Set user agent
        await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');

        // Navigate to URL
        console.log(`Navigating to ${url}...`);
        await page.goto(url, {
            waitUntil: "networkidle2",
            timeout: 60000,
        });

        console.log("Page loaded successfully");

        // Take screenshot
        const screenshotPath = path.join(path.dirname(outputFilename), "page_loaded.png");
        await page.screenshot({ path: screenshotPath, fullPage: true });

        // Check for captcha
        await handleCaptcha();

        // We'll use the specific class name from the provided element
        const listingSelector = "div.item-data-content_itemDataContentBox__gvAC2";
        console.log(`Using selector: ${listingSelector}`);

        // Extract listings from all pages
        let allListings = [];
        let hasNextPage = true;

        while (hasNextPage && currentPage <= maxPages) {
            console.log(`Scraping page ${currentPage}...`);

            // Wait for listings to load
            await page.waitForSelector(listingSelector, { timeout: 10000 })
                .catch(e => console.log(`No listings found on page ${currentPage}: ${e.message}`));

            // Extract listings from current page
            const pageListings = await extractListings(listingSelector);
            console.log(`Extracted ${pageListings.length} listings from page ${currentPage}`);

            // Add to all listings
            allListings = allListings.concat(pageListings);

            // Check if there's a next page
            hasNextPage = await goToNextPage();
            if (hasNextPage) {
                currentPage++;
                // Wait for page to load
                await page.waitForNavigation({ waitUntil: "networkidle2", timeout: 30000 })
                    .catch(e => console.log(`Error waiting for navigation: ${e.message}`));

                // Check for captcha again
                await handleCaptcha();
            }
        }

        if (allListings.length > 0) {
            // Save to CSV
            await saveToCSV(allListings);
            console.log(`Successfully scraped ${allListings.length} listings to ${outputFilename}`);
            console.log(JSON.stringify({
                success: true,
                path: outputFilename,
                count: allListings.length
            }));
        } else {
            console.log("No listings found");
            console.log(JSON.stringify({
                success: false,
                error: "No listings found"
            }));
        }

    } catch (error) {
        console.error("Error during scraping:", error);
        console.log(JSON.stringify({
            success: false,
            error: error.message
        }));
    } finally {
        // Close browser
        if (browser) await browser.close();
    }
}

// Function to check for and handle captcha
async function handleCaptcha() {
    // Check for common captcha indicators
    const hasCaptcha = await page.evaluate(() => {
        const bodyText = document.body.textContent.toLowerCase();
        return bodyText.includes('captcha') ||
            bodyText.includes('robot') ||
            bodyText.includes('human verification') ||
            bodyText.includes('security check') ||
            document.querySelector('.security-error') !== null ||
            document.querySelector('.captcha') !== null ||
            document.querySelector('.recaptcha') !== null;
    });

    if (hasCaptcha) {
        console.log("CAPTCHA detected! Please solve it in the browser window.");

        // Take screenshot of captcha
        const captchaScreenshotPath = path.join(path.dirname(outputFilename), "captcha.png");
        await page.screenshot({ path: captchaScreenshotPath, fullPage: false });
        console.log(`Captcha screenshot saved to: ${captchaScreenshotPath}`);

        // Wait for user to solve captcha (via Streamlit button)
        await waitForSignal('captcha_solved');

        // Wait a bit for any redirects after captcha
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Check if we're still on a captcha page
        const stillHasCaptcha = await page.evaluate(() => {
            const bodyText = document.body.textContent.toLowerCase();
            return bodyText.includes('captcha') ||
                bodyText.includes('robot') ||
                bodyText.includes('human verification') ||
                bodyText.includes('security check') ||
                document.querySelector('.security-error') !== null ||
                document.querySelector('.captcha') !== null ||
                document.querySelector('.recaptcha') !== null;
        });

        if (stillHasCaptcha) {
            console.log("Captcha still detected. Trying again...");
            await handleCaptcha(); // Recursive call to handle captcha again
        } else {
            console.log("Captcha solved successfully!");

            // Take screenshot after captcha
            const afterCaptchaPath = path.join(path.dirname(outputFilename), "after_captcha.png");
            await page.screenshot({ path: afterCaptchaPath, fullPage: true });
        }
    } else {
        console.log("No captcha detected, proceeding with scraping");
    }
}

// Function to extract listings using the provided selector
async function extractListings(selector) {
    console.log(`Extracting listings using selector: ${selector}`);

    // Extract data using the selected selector
    const listings = await page.evaluate((selector) => {
        const items = [];

        // Find all elements matching the selector
        const elements = document.querySelectorAll(selector);
        console.log(`Found ${elements.length} elements matching the selector`);

        // Process each element
        elements.forEach((element) => {
            try {
                // Extract price
                let price = "N/A";
                const priceElement = element.querySelector('span[data-testid="price"]');
                if (priceElement) {
                    price = priceElement.textContent.trim();
                }

                // Extract address
                let address = "N/A";
                const addressElement = element.querySelector('.item-data-content_itemInfoLine__AeoPP.item-data-content_first__oi7xM');
                if (addressElement) {
                    address = addressElement.textContent.trim();
                }

                // Extract rooms, floor, size
                let roomsFloorSize = "N/A";
                const detailsElement = element.querySelector('.item-data-content_itemInfoLine__AeoPP:not(.item-data-content_first__oi7xM)');
                if (detailsElement) {
                    roomsFloorSize = detailsElement.textContent.trim();
                }

                // Parse rooms, floor, size
                let rooms = "N/A";
                let floor = "N/A";
                let size = "N/A";

                if (roomsFloorSize !== "N/A") {
                    const parts = roomsFloorSize.split('•').map(part => part.trim());
                    if (parts.length >= 1) rooms = parts[0];
                    if (parts.length >= 2) floor = parts[1];
                    if (parts.length >= 3) size = parts[2];
                }

                // Extract heading/title
                let title = "N/A";
                const titleElement = element.querySelector('.item-data-content_heading__tphH4');
                if (titleElement) {
                    title = titleElement.textContent.trim();
                }

                // Try to get URL
                let url = "N/A";
                // Go up to find the closest link
                let parent = element;
                for (let i = 0; i < 5; i++) { // Check up to 5 levels up
                    if (!parent) break;

                    // Check if this element is a link or contains a link
                    if (parent.tagName === 'A' && parent.href) {
                        url = parent.href;
                        break;
                    }

                    const linkElement = parent.querySelector('a');
                    if (linkElement && linkElement.href) {
                        url = linkElement.href;
                        break;
                    }

                    parent = parent.parentElement;
                }

                items.push({
                    title,
                    price,
                    address,
                    rooms,
                    floor,
                    size,
                    url
                });
            } catch (error) {
                console.error("Error extracting data from element:", error);
            }
        });

        return items;
    }, selector);

    console.log(`Extracted ${listings.length} listings`);

    return listings;
}

// Function to go to the next page
async function goToNextPage() {
    console.log("Checking for next page...");

    // Check if there's a next page button
    const hasNextPage = await page.evaluate(() => {
        // Look for next page button
        const nextButton = document.querySelector('a[aria-label="עבור לעמוד הבא"]');
        return !!nextButton;
    });

    if (hasNextPage) {
        console.log("Next page found, clicking...");

        // Click the next page button
        await page.click('a[aria-label="עבור לעמוד הבא"]')
            .catch(e => console.log(`Error clicking next page button: ${e.message}`));

        return true;
    } else {
        console.log("No next page found");
        return false;
    }
}

// Function to save listings to CSV
async function saveToCSV(listings) {
    // Create exports directory if it doesn't exist
    const outputDir = path.dirname(outputFilename);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    // Save to CSV
    const csvWriter = createCsvWriter({
        path: outputFilename,
        header: [
            { id: "title", title: "Title" },
            { id: "price", title: "Price" },
            { id: "address", title: "Address" },
            { id: "rooms", title: "Rooms" },
            { id: "floor", title: "Floor" },
            { id: "size", title: "Size" },
            { id: "url", title: "URL" },
        ],
    });

    await csvWriter.writeRecords(listings);
}

// Run the scraper
scrapeYad2().catch(error => {
    console.error("Unhandled error:", error);
    process.exit(1);
});