import streamlit as st
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import datetime
import time

# -----------------------------------------------------------
# Selenium Setup Function
# -----------------------------------------------------------
def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# -----------------------------------------------------------
# Ticket Details Extraction Function
# -----------------------------------------------------------
def get_ticket_details(barcode_value):
    # Extract only the numeric part from the barcode (e.g., "RST-93113342" -> "93113342")
    ticket_id = barcode_value.split("-")[-1]
    url = f"https://cellmechanic.repairshopr.com/tickets/{ticket_id}"
    
    driver = setup_selenium()
    try:
        driver.get(url)
        # Wait explicitly for the ticket number element to appear (up to 10 seconds)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-md-4 h1"))
            )
        except Exception as e:
            st.error("Timed out waiting for page to load.")
            return {'ticket_number': "Not Found", 'school_name': "Not Found", 'device_model': ""}
        
        # Use BeautifulSoup to parse the page source
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract the ticket number from the <div class="col-md-4"> element
        ticket_number_div = soup.find('div', class_='col-md-4')
        ticket_number = ticket_number_div.find('h1').text.strip() if ticket_number_div else "Not Found"
        
        # Extract the school name and device model from the <div class="col-sm-12"> element
        school_div = soup.find('div', class_='col-sm-12')
        school_text = school_div.find('h3', class_='large').text.strip() if school_div else "Not Found"
        
        # Expecting a format like "North Pocono School District / Acer CP514"
        school_name = school_text.split("/")[0].strip() if "/" in school_text else school_text
        device_model = school_text.split("/")[-1].strip() if "/" in school_text else ""
        
        return {
            'ticket_number': ticket_number.replace("#", ""),
            'school_name': school_name,
            'device_model': device_model
        }
    finally:
        driver.quit()

# -----------------------------------------------------------
# Streamlit Barcode Scan Page
# -----------------------------------------------------------
def barcode_scan_page():
    st.title("Barcode Scanner Integration")
    
    # Input field for scanning barcode (e.g., "RST-93113342")
    barcode_value = st.text_input("Scan Barcode (RST-XXXXXXX format)")
    
    if barcode_value:
        if not barcode_value.startswith("RST-"):
            st.error("Invalid barcode format. Barcode must start with 'RST-'.")
            return
        
        with st.spinner("Fetching ticket details..."):
            ticket_details = get_ticket_details(barcode_value)
        
        if ticket_details['ticket_number'] == "Not Found":
            st.error("Ticket not found in RepairShopr.")
            return
        
        st.success("Ticket details retrieved successfully!")
        st.subheader("Ticket Information")
        st.write(f"**Ticket Number:** {ticket_details['ticket_number']}")
        st.write(f"**School Name:** {ticket_details['school_name']}")
        st.write(f"**Device Model:** {ticket_details['device_model']}")
        
        # This example simply displays the result.
        # If you have a database integration, you can add the ticket details to your system here.
        if st.button("Add to Ticket System"):
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Replace the following with your database insertion logic
            st.write(f"Ticket added to system at {current_time}!")
            st.success("Ticket added to system!")

# -----------------------------------------------------------
# Main App Function
# -----------------------------------------------------------
def main():
    # For demonstration, use a simple page selector
    page = st.selectbox("Select Page", ["Barcode Scan"])
    if page == "Barcode Scan":
        barcode_scan_page()

if __name__ == "__main__":
    main()
