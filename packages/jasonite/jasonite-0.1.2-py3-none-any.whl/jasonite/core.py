import json
import os
import re
import threading
import copy
from typing import Any, Dict, List, Optional, Tuple, Union

DictLike = Dict[str, Any]
Query = Dict[str, Any]
SortSpec = Optional[Union[str, Tuple[str, bool], List[Tuple[str, bool]]]]


class Jasonite:
    """
    Jasonite: a tiny JSON-backed document store.
    """

    def __init__(self, filename: str, id_field: str = "id", autosave: bool = True):
        """
        Initialize the database.

        Example:
        >>> db = Jasonite("mydb.json")
        """
        self.filename = filename
        self.id_field = id_field
        self.autosave = autosave

        self._lock = threading.RLock()
        self._data: Dict[str, List[DictLike]] = {}

        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            self._atomic_save({})
        self._data = self._load()

    # ---------- Persistence ----------

    def _load(self) -> Dict[str, Any]:
        with self._lock:
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)

    def _atomic_save(self, data: Dict[str, Any]):
        """Save data atomically to disk (tmp + replace)."""
        with self._lock:
            tmp = self.filename + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.filename)

    def _maybe_flush(self):
        if self.autosave:
            self.flush()

    def flush(self):
        """Save in-memory data to disk atomically."""
        with self._lock:
            self._atomic_save(self._data)

    # ---------- Collections ----------

    def create_collection(self, name: str):
        """Create a collection if it does not exist."""
        with self._lock:
            if name not in self._data:
                self._data[name] = []
            self._maybe_flush()

    def drop_collection(self, name: str):
        """Delete an entire collection."""
        with self._lock:
            self._data.pop(name, None)
            self._maybe_flush()

    def _ensure_collection(self, name: str):
        if name not in self._data:
            raise KeyError(f"Collection '{name}' not found")

    def _deepcopy(self, obj: Any) -> Any:
        return copy.deepcopy(obj)

    # ---------- CRUD ----------

    def insert(self, collection: str, doc: DictLike):
        """Insert a new document. Fails if id already exists."""
        with self._lock:
            self._ensure_collection(collection)
            col = self._data[collection]
            _id = doc.get(self.id_field)
            if _id is None:
                raise ValueError(f"Missing primary key field '{self.id_field}'")
            if any(d.get(self.id_field) == _id for d in col):
                raise ValueError("Duplicate primary key")
            col.append(self._deepcopy(doc))
            self._maybe_flush()

    def save(self, collection: str, doc: DictLike):
        """Insert or replace a document."""
        with self._lock:
            self._ensure_collection(collection)
            col = self._data[collection]
            _id = doc.get(self.id_field)
            if _id is None:
                raise ValueError(f"Missing primary key field '{self.id_field}'")
            idx = next((i for i, d in enumerate(col) if d.get(self.id_field) == _id), -1)
            if idx >= 0:
                col[idx] = self._deepcopy(doc)
            else:
                col.append(self._deepcopy(doc))
            self._maybe_flush()

    def upsert(self, collection: str, doc: DictLike):
        """Alias of save()."""
        self.save(collection, doc)

    def remove(self, collection: str, doc_or_id: Union[DictLike, Any]) -> int:
        """Remove a document by id. Returns 1 if removed, else 0."""
        with self._lock:
            self._ensure_collection(collection)
            col = self._data[collection]
            _id = doc_or_id if not isinstance(doc_or_id, dict) else doc_or_id.get(self.id_field)
            if _id is None:
                raise ValueError(f"Missing '{self.id_field}'")
            before = len(col)
            self._data[collection] = [d for d in col if d.get(self.id_field) != _id]
            removed = before - len(self._data[collection])
            if removed:
                self._maybe_flush()
            return removed

    def find_by_id(self, collection: str, _id: Any) -> Optional[DictLike]:
        """Return a document by id, or None if not found."""
        with self._lock:
            self._ensure_collection(collection)
            for d in self._data[collection]:
                if d.get(self.id_field) == _id:
                    return self._deepcopy(d)
            return None

    # ---------- Query ----------

    def find(self, collection: str, query: Optional[Query] = None,
             sort: SortSpec = None, slice_str: Optional[str] = None) -> List[DictLike]:
        """
        Query documents with optional sort and slice.
        Example:
        >>> db.find("users", {"age": {"$gte": 18}}, sort="age", slice_str="0:5")
        """
        with self._lock:
            self._ensure_collection(collection)
            col = self._data[collection]

            # filter
            if query:
                filtered = [d for d in col if self._match(d, query)]
            else:
                filtered = list(col)

            # sort
            if sort:
                if isinstance(sort, str):
                    sort_specs = [(sort, False)]
                elif isinstance(sort, tuple):
                    fld, desc = sort
                    sort_specs = [(fld, bool(desc))]
                else:
                    sort_specs = [(fld, bool(desc)) for (fld, desc) in sort]
                for fld, desc in reversed(sort_specs):
                    filtered.sort(key=lambda d, f=fld: self._get_by_path(d, f), reverse=desc)

            # slice
            if slice_str:
                i, j, k = self._parse_slice(slice_str)
                filtered = filtered[i:j:k]

            return [self._deepcopy(d) for d in filtered]

    def find_all(self, collection: str, sort: SortSpec = None, slice_str: Optional[str] = None) -> List[DictLike]:
        """Return all documents, optionally sorted and sliced."""
        return self.find(collection, query=None, sort=sort, slice_str=slice_str)

    def find_and_remove(self, collection: str, query: Query) -> Optional[DictLike]:
        """Find the first matching doc and remove it."""
        with self._lock:
            res = self.find(collection, query=query)
            if not res:
                return None
            to_remove = res[0][self.id_field]
            removed = self.remove(collection, to_remove)
            return res[0] if removed else None

    def find_and_modify(self, collection: str, query: Query, update: DictLike) -> Optional[DictLike]:
        """Find the first matching doc and apply an update."""
        with self._lock:
            self._ensure_collection(collection)
            for idx, d in enumerate(self._data[collection]):
                if self._match(d, query):
                    newd = self._apply_update(copy.deepcopy(d), update)
                    self._data[collection][idx] = newd
                    self._maybe_flush()
                    return self._deepcopy(newd)
            return None

    def count(self, collection: str) -> int:
        """Return number of documents in a collection."""
        with self._lock:
            self._ensure_collection(collection)
            return len(self._data[collection])

    # ---------- Query engine ----------

    def _match(self, doc: DictLike, query: Query) -> bool:
        """
        Check if a document matches a query.
        Supports: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $exists, $contains, $regex
        """
        for key, cond in query.items():
            val = self._get_by_path(doc, key) if not key.startswith("$") else None

            if isinstance(cond, dict):
                for op, rhs in cond.items():
                    if op == "$eq":
                        if val != rhs:
                            return False
                    elif op == "$ne":
                        if val == rhs:
                            return False
                    elif op == "$gt":
                        if not (val is not None and val > rhs):
                            return False
                    elif op == "$gte":
                        if not (val is not None and val >= rhs):
                            return False
                    elif op == "$lt":
                        if not (val is not None and val < rhs):
                            return False
                    elif op == "$lte":
                        if not (val is not None and val <= rhs):
                            return False
                    elif op == "$in":
                        if val not in rhs:
                            return False
                    elif op == "$nin":
                        if val in rhs:
                            return False
                    elif op == "$exists":
                        exists = val is not None
                        if bool(rhs) != exists:
                            return False
                    elif op == "$contains":
                        # Works for list or string
                        if isinstance(val, list):
                            if rhs not in val:
                                return False
                        elif isinstance(val, str):
                            if rhs not in val:
                                return False
                        else:
                            return False
                    elif op == "$regex":
                        """
                        Regex-based text search (case-insensitive).

                        The pattern is compiled only once and stored in a cache
                        to improve performance for repeated queries using the same regex.

                        Example:
                            Query: {"Title": {"$regex": "deep learning"}}
                            Matches: any document where Title contains "deep learning"
                                     (case-insensitive, partial match).
                        """
                        if not isinstance(val, str):
                            return False

                        # Initialize regex cache on first use
                        if not hasattr(self, "_regex_cache"):
                            self._regex_cache = {}

                        # Compile the regex only once and reuse it from cache
                        if rhs not in self._regex_cache:
                            try:
                                self._regex_cache[rhs] = re.compile(rhs, re.IGNORECASE)
                            except re.error:
                                raise ValueError(f"Invalid regex pattern: {rhs}")

                        pattern = self._regex_cache[rhs]

                        # Perform case-insensitive match
                        if not pattern.search(val):
                            return False

                    else:
                        raise ValueError(f"Unsupported operator: {op}")
            else:
                if val != cond:
                    return False
        return True

    def _get_by_path(self, doc: DictLike, dotted: str) -> Any:
        cur: Any = doc
        for part in dotted.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    def _parse_slice(self, s: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        parts = s.split(":")
        if not 1 <= len(parts) <= 3:
            raise ValueError("Slice must look like 'i:j[:k]'")
        def conv(x):
            return None if x == "" else int(x)
        parts += [""] * (3 - len(parts))
        return tuple(conv(p) for p in parts)  # type: ignore

    # ---------- Update operators ----------

    def _apply_update(self, doc: DictLike, update: DictLike) -> DictLike:
        sets = update.get("$set", {})
        unsets = update.get("$unset", {})
        incs = update.get("$inc", {})

        for path, value in sets.items():
            self._set_by_path(doc, path, value)
        for path, flag in unsets.items():
            if flag:
                self._unset_by_path(doc, path)
        for path, delta in incs.items():
            cur = self._get_by_path(doc, path)
            if cur is None:
                self._set_by_path(doc, path, delta)
            else:
                self._set_by_path(doc, path, cur + delta)
        return doc

    def _set_by_path(self, doc: DictLike, dotted: str, value: Any):
        parts = dotted.split(".")
        cur: Any = doc
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = value

    def _unset_by_path(self, doc: DictLike, dotted: str):
        parts = dotted.split(".")
        cur: Any = doc
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                return
            cur = cur[p]
        cur.pop(parts[-1], None)
