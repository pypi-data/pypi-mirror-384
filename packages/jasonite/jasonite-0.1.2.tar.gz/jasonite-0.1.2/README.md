# Jasonite

**Jasonite** is a simple and fast JSON database for Python.  
It stores data in a JSON file and keeps it in memory while you work.  
When you save, it writes the data safely to disk (atomic file writes).  

Jasonite is great for small projects, prototypes, and scripts.

---

## 🌱 Install

```bash
pip install jasonite
```

Or install from source:

```bash
git clone https://github.com/guelfoweb/jasonite.git
cd jasonite
pip install .
```

---

## ⚡ Quick Start

```python
from jasonite import Jasonite

# Create or open a database file
db = Jasonite("mydb.json", autosave=True)

# Create a collection if it does not exist
db.create_collection("users")

# Insert data
db.insert("users", {"id": "u1", "name": "Alice", "age": 30})
db.insert("users", {"id": "u2", "name": "Bob", "age": 25})

# Find one document
user = db.find_one("users", {"id": "u1"})
print(user)

# Update a document
db.update("users", {"id": "u1"}, {"age": 31})

# Delete a document
db.remove("users", {"id": "u2"})

# Save changes (if autosave=False)
db.flush()
```

---

## 🧠 How it works

- **In-memory cache**: Jasonite loads all JSON data in memory for speed.  
- **Atomic writes**: When saving, Jasonite writes to a temporary file first, then replaces the original file. This avoids data loss.  
- **Thread-safe**: Safe to use in simple multi-threaded scripts.  

---

## 📚 Main Functions

### `create_collection(name)`
Create a new collection (like a table).

```python
db.create_collection("books")
```

---

### `insert(collection, data)`
Add one or more documents to a collection.

```python
db.insert("books", {"id": "b1", "title": "1984", "author": "Orwell"})
```

If the collection does not exist, Jasonite will create it automatically.

---

### `find(collection, query)`
Find documents that match a query.

```python
db.find("books", {"author": "Orwell"})
```

Example with operators:

```python
db.find("users", {"age": {"$gt": 18}})
```

---

### `find_one(collection, query)`
Return the first document that matches a query.

```python
user = db.find_one("users", {"id": "u1"})
```

---

### `find_all(collection)`
Return all documents in a collection.

```python
all_users = db.find_all("users")
```

---

### `update(collection, query, new_data)`
Update all documents that match a query.

```python
db.update("users", {"name": "Alice"}, {"age": 32})
```

---

### `upsert(collection, document)`
Insert a new document, or update it if it already exists.

```python
db.upsert("users", {"id": "u1", "name": "Alice", "age": 33})
```

---

### `remove(collection, query)`
Remove documents that match a query.

```python
db.remove("users", {"age": {"$lt": 18}})
```

---

### `flush()`
Save all data to the JSON file.

```python
db.flush()
```

---

## 🔍 Query Operators

Jasonite supports many simple query operators.  
You can use them inside a query dictionary.

| Operator | Meaning | Example |
|-----------|----------|----------|
| `$eq` | equal | `{"age": {"$eq": 25}}` |
| `$ne` | not equal | `{"age": {"$ne": 30}}` |
| `$gt` | greater than | `{"age": {"$gt": 18}}` |
| `$gte` | greater or equal | `{"age": {"$gte": 18}}` |
| `$lt` | less than | `{"age": {"$lt": 60}}` |
| `$lte` | less or equal | `{"age": {"$lte": 60}}` |
| `$in` | value in list | `{"name": {"$in": ["Alice", "Bob"]}}` |
| `$nin` | value not in list | `{"name": {"$nin": ["Tom"]}}` |
| `$exists` | field exists | `{"age": {"$exists": True}}` |
| `$contains` | substring or element in list | `{"Authors": {"$contains": "John"}}` |
| `$regex` | regex match (case-insensitive) | `{"Title": {"$regex": "learning"}}` |

---

## 🧩 Examples of `$contains` and `$regex`

### `$contains`
Works on **strings** and **lists**.

```python
# string field
db.find("papers", {"Summary": {"$contains": "AI"}})

# list field
db.find("papers", {"Authors": {"$contains": "Alice"}})
```

### `$regex`
Supports complex text search (case-insensitive).  
Jasonite caches regex patterns for faster queries.

```python
# Find documents where title contains "Deep"
db.find("papers", {"Title": {"$regex": "deep"}})

# Find titles that start with "Neural"
db.find("papers", {"Title": {"$regex": "^Neural"}})
```

---

## 💾 Example JSON structure

Jasonite works directly with JSON files like this:

```json
{
  "users": [
    {"id": "u1", "name": "Alice", "age": 30},
    {"id": "u2", "name": "Bob", "age": 25}
  ]
}
```

---

## 📘 Example: Books Database

You can use a public JSON file with 100 classic books.

**Download the file:**
[https://raw.githubusercontent.com/benoitvallon/100-best-books/master/books.json](https://raw.githubusercontent.com/benoitvallon/100-best-books/master/books.json)

This file contains a list of books with fields like:
```json
{
  "author": "Chinua Achebe",
  "country": "Nigeria",
  "language": "English",
  "link": "https://en.wikipedia.org/wiki/Things_Fall_Apart",
  "pages": 209,
  "title": "Things Fall Apart",
  "year": 1958
}
```

### Import data into Jasonite

```python
from jasonite import Jasonite
import json

db = Jasonite("books_db.json", autosave=True)
db.create_collection("books")

with open("books.json") as f:
    books = json.load(f)
    for i, book in enumerate(books, start=1):
        book["id"] = f"b{i}"  # add a simple id like "b1", "b2", ...
        db.insert("books", book)

print("Books imported:", len(books))
```

### Find documents

#### Find all books written in English:

```python
english_books = db.find("books", {"language": {"$eq": "English"}})
```

#### Find all books by "Jane Austen":

```python
austen_books = db.find("books", {"author": {"$contains": "Jane Austen"}})
```

### Sort by year

```python
sorted_books = sorted(
    db.find_all("books"),
    key=lambda x: x["year"],
    reverse=False
)
```

### Search by title (using `$regex`)

#### Find books that contain the word "love" in the title (case-insensitive):

```python
love_books = db.find("books", {"title": {"$regex": "love"}})
```

### Update and save

#### Update all books by Jane Austen to mark them as "classic":

```python
db.update("books", {"author": {"$contains": "Jane Austen"}}, {"tag": "classic"})
db.flush()
```

### Remove and upsert examples

#### Remove books with less than 100 pages:

```python
db.remove("books", {"pages": {"$lt": 100}})
```

#### Insert a new book or update if it exists:

```python
db.upsert("books", {
    "title": "New Book",
    "author": "John Writer",
    "language": "English",
    "year": 2025,
    "pages": 120
})
```

---

**Jasonite** is developed by [@guelfoweb](https://github.com/guelfoweb)  
Open source under the MIT license.
