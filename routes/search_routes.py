"""
Search Routes - Book search functionality
"""

from flask import Blueprint, render_template, request
from library_service import search_books_in_catalog

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
def search_books():
    """
    Search for books in the catalog (R5)
    - Title: partial match (case-insensitive)
    - Author: partial match (case-insensitive)
    - ISBN: exact match
    """
    search_term = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'title')
    books = []

    if search_term:
        books = search_books_in_catalog(search_term, search_type)

    return render_template(
        'search.html',
        books=books,
        search_term=search_term,
        search_type=search_type
    )
