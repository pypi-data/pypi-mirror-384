"""Trie-backed dictionary loader and manager for Boggle lexicons.

This module provides the necessary tools for loading and querying Boggle
dictionaries, which are essential for word validation. It uses a Trie data
structure for efficient storage and prefix-based lookups, which is ideal
for the Boggle game's word-finding mechanics.

Classes:
    TrieNode: Represents a single node in the Trie.
    Trie: A simple Trie implementation for storing and searching words.
    DictionaryMetadata: A dataclass for holding metadata about a dictionary.
    BoggleDictionary: The main class for loading, managing, and querying a
                      Boggle dictionary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator

# Define the directory where dictionary resources are stored.
RESOURCES_DIR = Path(__file__).resolve().parent / "resources" / "dictionaries"


class TrieNode:
    """Represents a single node in a Trie data structure.

    Each node has a dictionary of children, mapping a character to another
    `TrieNode`, and a boolean flag indicating if it marks the end of a word.
    """

    __slots__ = ("children", "is_word")

    def __init__(self) -> None:
        self.children: Dict[str, TrieNode] = {}
        self.is_word = False


class Trie:
    """A simple Trie implementation optimized for prefix-based lookups.

    This data structure is used to store the dictionary of valid words for
    the Boggle game, allowing for efficient checking of both full words and
    prefixes.
    """

    def __init__(self) -> None:
        self._root = TrieNode()

    def insert(self, word: str) -> None:
        """Inserts a word into the Trie.

        Args:
            word (str): The word to insert.
        """
        node = self._root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_word = True

    def contains(self, word: str) -> bool:
        """Checks if a complete word exists in the Trie.

        Args:
            word (str): The word to check for membership.

        Returns:
            bool: True if the word is in the Trie, False otherwise.
        """
        node = self._root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_word

    def has_prefix(self, prefix: str) -> bool:
        """Checks if any stored word begins with the given prefix.

        Args:
            prefix (str): The prefix to test.

        Returns:
            bool: True if the prefix exists, False otherwise.
        """
        node = self._root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

    def __contains__(self, word: str) -> bool:
        """Allows for using the 'in' operator to check for a word's existence."""
        return self.contains(word)


@dataclass(frozen=True)
class DictionaryMetadata:
    """A dataclass for storing metadata about a dictionary lexicon.

    Attributes:
        language (str): The language of the dictionary (e.g., "en").
        lexicon (str): The name of the lexicon (e.g., "enable").
        path (Path): The file path to the dictionary.
    """

    language: str
    lexicon: str
    path: Path


class BoggleDictionary:
    """A Trie-backed dictionary for validating Boggle word submissions.

    This class handles the loading of word lists from files, storing them in
    a Trie, and providing an interface for checking the validity of words and
    prefixes.
    """

    def __init__(self, language: str = "en", lexicon: str = "enable") -> None:
        self.language = language
        self.lexicon = lexicon
        self._trie = Trie()
        self._words_loaded = False
        self._load_default()

    def _load_default(self) -> None:
        """Loads the default dictionary based on the instance's language and lexicon."""
        path = self._get_default_path()
        self.load_from_path(path)

    def _get_default_path(self) -> Path:
        """Constructs and returns the file path to the default dictionary.

        Returns:
            Path: The path to the dictionary file.

        Raises:
            FileNotFoundError: If the dictionary file does not exist.
        """
        path = RESOURCES_DIR / self.language / f"{self.lexicon}.txt"
        if not path.exists():
            raise FileNotFoundError(f"Dictionary for language '{self.language}' and lexicon '{self.lexicon}' not found at {path}.")
        return path

    @classmethod
    def available_dictionaries(cls) -> Iterator[DictionaryMetadata]:
        """Yields metadata for all bundled dictionaries.

        Returns:
            Iterator[DictionaryMetadata]: An iterator over metadata for each
                                          available language and lexicon.
        """
        for language_dir in RESOURCES_DIR.iterdir():
            if not language_dir.is_dir():
                continue
            language = language_dir.name
            for lexicon_path in language_dir.glob("*.txt"):
                yield DictionaryMetadata(language=language, lexicon=lexicon_path.stem, path=lexicon_path)

    def load_from_path(self, path: Path) -> None:
        """Loads lexicon entries from a specified file path.

        Args:
            path (Path): The path to the file containing newline-separated words.
        """
        words = path.read_text(encoding="utf-8").splitlines()
        self.load_words(words)

    def load_words(self, words: Iterable[str]) -> None:
        """Populates the Trie with words from an iterable.

        Args:
            words (Iterable[str]): An iterable providing the words to load.
        """
        self._trie = Trie()
        for word in words:
            normalized = self._normalize_word(word)
            if not normalized:
                continue
            self._trie.insert(normalized)
        self._words_loaded = True

    def contains(self, word: str) -> bool:
        """Checks if a word is present in the dictionary.

        Args:
            word (str): The word to check.

        Returns:
            bool: True if the dictionary contains the word, False otherwise.
        """
        self._ensure_loaded()
        return self._trie.contains(self._normalize_word(word))

    def has_prefix(self, prefix: str) -> bool:
        """Checks if any word in the dictionary begins with the given prefix.

        Args:
            prefix (str): The prefix to test.

        Returns:
            bool: True if at least one word starts with the prefix, False otherwise.
        """
        self._ensure_loaded()
        return self._trie.has_prefix(self._normalize_word(prefix))

    def _ensure_loaded(self) -> None:
        """Loads the default dictionary if it has not been loaded yet."""
        if not self._words_loaded:
            self._load_default()

    @staticmethod
    def _normalize_word(word: str) -> str:
        """Normalizes a word to uppercase and removes non-alphabetic characters.

        Args:
            word (str): The word to normalize.

        Returns:
            str: The normalized word.
        """
        cleaned = "".join(char for char in word.strip() if char.isalpha())
        return cleaned.upper()

    def __contains__(self, word: str) -> bool:
        """Allows for using the 'in' operator to check if a word is in the dictionary."""
        return self.contains(word)

    def __iter__(self) -> Iterator[str]:
        """Iterates over all words stored in the dictionary.

        Returns:
            Iterator[str]: An iterator that yields each stored word in
                           alphabetical order.
        """
        self._ensure_loaded()
        yield from self._iterate_trie(self._trie._root, prefix="")

    def _iterate_trie(self, node: TrieNode, prefix: str) -> Iterator[str]:
        """Recursively yields words stored in the Trie.

        Args:
            node (TrieNode): The current node in the Trie.
            prefix (str): The prefix accumulated for the current node.

        Returns:
            Iterator[str]: An iterator that yields words found beneath the node.
        """
        if node.is_word:
            yield prefix
        for char, child in sorted(node.children.items()):
            yield from self._iterate_trie(child, prefix + char)
