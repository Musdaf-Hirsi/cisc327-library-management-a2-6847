import os
import subprocess
import time
import signal
import random
import string

import requests
from playwright.sync_api import sync_playwright
import pytest


def random_isbn():
    # produce a 13-digit isbn starting with 978
    tail = ''.join(random.choice(string.digits) for _ in range(10))
    return '978' + tail


@pytest.fixture(scope='session')
def server():
    """Start the Flask app in a subprocess for the duration of the tests."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(repo_root, 'library.db')
    # Ensure a fresh DB for the test session
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'

    proc = subprocess.Popen(
        ['python', 'app.py'], cwd=repo_root, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Wait for server to be ready
    url = 'http://127.0.0.1:5000/catalog'
    for _ in range(30):
        try:
            resp = requests.get(url, timeout=1)
            if resp.status_code in (200, 302):
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        out, err = proc.communicate(timeout=1)
        raise RuntimeError('Flask app failed to start:\n' + (err.decode() if err else ''))

    yield

    # Teardown
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def test_add_book_and_borrow_flow(server):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    base = 'http://127.0.0.1:5000'

    title = 'E2E Test Book'
    author = 'E2E Author'
    isbn = random_isbn()
    copies = '1'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1) Navigate to add book page and submit form
        page.goto(f'{base}/add_book')
        page.fill('#title', title)
        page.fill('#author', author)
        page.fill('#isbn', isbn)
        page.fill('#total_copies', copies)
        page.click("text=Add Book to Catalog")

        # After submit should be redirected to catalog; verify the book appears
        page.wait_for_url(f'{base}/catalog')
        assert page.locator(f"text={title}").count() >= 1
        # Availability should match the copies we entered
        assert page.locator(f"text=1/1 Available").count() >= 1

        # 2) Borrow the book using a patron ID
        patron_id = '654321'
        # Locate the row that contains our book then fill patron id and click Borrow
        row = page.locator(f"tr:has-text('{title}')")
        assert row.count() >= 1
        # fill patron id input in that row
        row.locator("input[name=patron_id]").fill(patron_id)
        # click the Borrow button in that row
        row.locator("button:has-text('Borrow')").click()

        # After borrow, there should be a success flash message
        page.wait_for_selector('.flash-success')
        flash = page.locator('.flash-success').inner_text()
        assert 'Successfully borrowed' in flash
        # Book should no longer be available
        row = page.locator(f"tr:has-text('{title}')")
        assert row.locator("text=Not Available").count() >= 1

        browser.close()


def test_search_and_borrow_existing_book(server):
    """Add a book, find it via search, and borrow it from the search results table."""
    base = 'http://127.0.0.1:5000'
    patron_id = '123999'
    title = 'Searchable Playwright Book'
    author = 'Search Author'
    isbn = random_isbn()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # First, add a book to guarantee a search hit
        page.goto(f'{base}/add_book')
        page.fill('#title', title)
        page.fill('#author', author)
        page.fill('#isbn', isbn)
        page.fill('#total_copies', '2')
        page.click("text=Add Book to Catalog")
        page.wait_for_url(f'{base}/catalog')

        # Navigate to search page and search for a seed book title
        page.goto(f'{base}/search')
        page.fill('#q', 'Searchable')
        # Submit the form by pressing Enter or clicking the submit button
        page.press('#q', 'Enter')
        # Wait for the search results to load (the table should appear)
        page.wait_for_selector('table tbody tr', timeout=10000)

        # Verify results table contains the newly added book
        row = page.locator(f"tr:has-text('{title}')")
        assert row.count() >= 1
        assert row.locator("text=Available").count() >= 1

        # Borrow the book from the search results row
        row.locator("input[name=patron_id]").fill(patron_id)
        row.locator("button:has-text('Borrow')").click()

        # Wait for flash message
        page.wait_for_selector('.flash-success', timeout=10000)
        flash = page.locator('.flash-success').inner_text()
        assert 'Successfully borrowed' in flash

        browser.close()
