import os, json
from flask import Blueprint, request, jsonify

def register(app, app_id):
    bp = Blueprint(app_id, __name__)
    DATA_FILE = os.path.join('data', 'library.json')

    def load_books():
        if not os.path.exists(DATA_FILE): return []
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except: return []

    @bp.route('/api/books', methods=['GET', 'POST'])
    def handle_books():
        books = load_books()
        if request.method == 'POST':
            book = request.json
            books.append(book)
            os.makedirs('data', exist_ok=True)
            with open(DATA_FILE, 'w') as f: json.dump(books, f)
            return jsonify({"status": "success", "book": book})
        return jsonify(books)

    @bp.route('/api/books/<int:idx>', methods=['DELETE'])
    def delete_book(idx):
        books = load_books()
        if 0 <= idx < len(books):
            books.pop(idx)
            with open(DATA_FILE, 'w') as f: json.dump(books, f)
            return jsonify({"status": "success"})
        return jsonify({"error": "Index out of range"}), 400

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
