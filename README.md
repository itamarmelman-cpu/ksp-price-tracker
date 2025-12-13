# KSP Price Tracker: Web Scraping and Streamlit Dashboard

## Project Overview

This project implements a full-stack solution for monitoring hardware prices in real-time from K.S.P, a leading Israeli retail website. It combines robust **Web Scraping** with **Data Visualization** to deliver actionable market insights.

The primary goal is to provide a comprehensive tool for tracking historical price fluctuations, identifying purchasing opportunities, and analyzing market trends within the consumer electronics sector.

## Core Technologies

The system is built using the following technologies:

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Data Acquisition** | Python, Selenium | Dynamic web scraping and data extraction from JavaScript-rendered pages. |
| **Data Storage** | SQLite | Persistent, local storage for historical price data and product metadata. |
| **Scheduling** | schedule (Python library) | Automated, time-based execution of the scraping script (similar to a Cron job). |
| **Presentation** | Streamlit | Creation of an interactive, browser-based dashboard for data analysis. |

## System Architecture

The workflow is divided into two primary modules:

1.  **Scraping Module (`main.py`, `market_pulse.py`):**
    * Responsible for connecting to the website and executing the data extraction logic.
    * Automatically triggered by a scheduler at predefined intervals.
    * Stores structured data records in the SQLite database.

2.  **Dashboard Module (`dashboard.py`):**
    * Loads and processes the data from the database.
    * Presents visualizations (line charts, tables) showing price movement over time.
    * Provides controls for users to filter products and examine key metrics (e.g., Min/Max Price, Average Price).

## Local Setup and Execution

Follow these steps to set up and run the KSP Price Tracker locally:

### Prerequisites

* Python 3.8+
* Google Chrome or Chromium (required for Selenium WebDriver)

### 1. Clone the Repository

```bash
git clone [https://github.com/itamarmelman-cpu/ksp-price-tracker.git](https://github.com/itamarmelman-cpu/ksp-price-tracker.git)
cd ksp-price-tracker


2. Install Dependencies

It is highly recommended to use a virtual environment (.venv).
pip install -r requirements.txt


3. Initialize the Database (Scraping)

Run the main script to perform the initial data collection and populate the database (ksp_prices.db):
python main.py

4. Run the Streamlit Dashboard

Start the interactive dashboard, which will open automatically in your default web browser:
streamlit run dashboard.py
