### Language: 
- [Python](https://www.python.org/)
  
### Flow diagrams:

### Requirements:
- Python 3.x
- Playwright
- Streamlit
- BeautifulSoup 
  
### Modules:
- Playwright for web crawling
- BeautifulSoup for HTML parsing
- FastAPI for API creation
- Uvicorn for running the server



### Troubleshooting:
If an error throws when scraping the actual listing elements, a classname most likely changed.

### Activiate venv
`source /Users/samrussell/Scraper/facebook-marketplace-scraper/venv/bin/activate`

### Start local server using uvicorn
`uvicorn entry:app --host 0.0.0.0 --port 4000`