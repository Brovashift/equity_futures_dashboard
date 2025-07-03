import streamlit as st
import traceback
import subprocess
subprocess.run(["playwright", "install"], check=True)

from playwright.sync_api import sync_playwright
from streamlit_autorefresh import st_autorefresh

@st.cache_data(ttl=30)  # cache for 30 seconds
def get_vix_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # show browser for debug
        page = browser.new_page()

        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        })

        # Scrape VIX Spot
        page.goto("https://uk.investing.com/indices/cboe-vix-volatility")
        page.wait_for_selector("div[data-test='instrument-price-last']")
        page.wait_for_timeout(3000)  # wait 3 sec to be sure
        vix_spot_text = page.locator("div[data-test='instrument-price-last']").inner_text()
        vix_spot = float(vix_spot_text.replace(',', ''))

        # Scrape VIX Futures
        page.goto("https://uk.investing.com/indices/us-spx-vix-futures")
        page.wait_for_selector("div[data-test='instrument-price-last']")
        page.wait_for_timeout(3000)  # wait 3 sec
        vix_fut_text = page.locator("div[data-test='instrument-price-last']").inner_text()
        vix_fut = float(vix_fut_text.replace(',', ''))

        browser.close()

    return vix_spot, vix_fut


# Auto refresh every 30 seconds
count = st_autorefresh(interval=30 * 1000, limit=None, key="vix_refresh")

st.title("📊 Real-Time VIX Dashboard")

try:
    vix_spot, vix_fut = get_vix_data()
    spread = vix_fut - vix_spot

    col1, col2, col3 = st.columns(3)
    col1.metric("VIX Spot", f"{vix_spot:.2f}")
    col2.metric("VIX Futures", f"{vix_fut:.2f}")
    col3.metric("Spread", f"{spread:.2f}", "Contango" if spread > 0 else "Backwardation")

    st.caption("Data scraped live from Investing.com using Playwright. Updates every 30 seconds.")

except Exception as e:
    st.error(f"Error fetching VIX data: {e}")
    st.text(traceback.format_exc())

