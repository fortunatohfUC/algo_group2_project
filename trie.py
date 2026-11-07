"""Reusable prefix-search index for the Library Inventory Tracker.

Owner: Person 2 (Aliza Shrestha).

The caller (models.py / inventory.py) is responsible for normalizing text
consistently before insertion, searching, and removal. Each Trie instance
indexes one field (title, author, or category), mapping complete strings to
sets of internal book IDs. The Trie never stores Book records.
"""


class TrieNode:
    """A character node with child nodes and IDs ending at this node."""
    #children is a dict mapping a character to another TrieNode
    def __init__(self):
        self.children = {}  # character -> TrieNode
        self.book_ids = set()  # IDs only for complete indexed strings


class Trie:
    """Index normalized strings for case-consistent prefix retrieval."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, text: str, book_id: str) -> None:
        """Associate book_id with text; O(m) average for m characters.

        Repeated insertion of the same (text, book_id) is harmless. Empty
        indexed strings are rejected to avoid storing records at the root.
        """
        if not isinstance(text, str) or not text:
            raise ValueError("indexed text must be a nonempty string")
        node = self.root
        for char in text:
            node = node.children.setdefault(char, TrieNode())
        node.book_ids.add(book_id)

    def search_prefix(self, prefix: str) -> set:
        """Return all IDs under prefix; O(m + s + k) average.

        m = prefix length; s = visited descendant nodes; k = collected IDs.
        An empty prefix returns an empty set, as specified by the team plan.
        """
        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string") #entry has to be string
        if not prefix: #empty
            print("No prefix entered")
            return set() #returns an empty set

        node = self.root
        for char in prefix:
            node = node.children.get(char)
            if node is None:
                return set()

        result = set()
        stack = [node]
        while stack:
            current = stack.pop()
            result.update(current.book_ids)
            stack.extend(current.children.values())
        return result

    def remove(self, text: str, book_id: str) -> None:
        """Remove an existing association and prune only unused nodes.

        Missing text or book ID is a no-op. Traversal and pruning take O(m)
        average time and preserve prefixes shared with other strings.
        """
        if not isinstance(text, str) or not text:
            raise ValueError("indexed text must be a nonempty string")

        node = self.root
        path = []  # (parent, character, child)
        for char in text:
            child = node.children.get(char)
            if child is None:
                return
            path.append((node, char, child))
            node = child

        if book_id not in node.book_ids:
            return
        node.book_ids.remove(book_id)

        # Walk backward; stop if a node is needed for another word or ID.
        for parent, char, child in reversed(path):
            if child.book_ids or child.children:
                break
            del parent.children[char]
