"""Trie-backed dictionary loader for Boggle lexicons."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator

RESOURCES_DIR = Path(__file__).resolve().parent / "resources" / "dictionaries"


class TrieNode:
    """Node in a trie representing dictionary entries."""

    __slots__ = ("children", "is_word")

    def __init__(self) -> None:
        self.children: Dict[str, TrieNode] = {}
        self.is_word = False


class Trie:
    """Simple trie implementation supporting prefix lookups."""

    def __init__(self) -> None:
        self._root = TrieNode()

    def insert(self, word: str) -> None:
        """Insert a word into the trie.

        Args:
            word: Word to insert into the trie.
        """
        node = self._root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_word = True

    def contains(self, word: str) -> bool:
        """Determine whether ``word`` exists within the trie.

        Args:
            word: Word to check for membership.

        Returns:
            True if the trie stores the word, otherwise False.
        """
        node = self._root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_word

    def has_prefix(self, prefix: str) -> bool:
        """Determine whether any stored word begins with ``prefix``.

        Args:
            prefix: Prefix to test.

        Returns:
            True if the prefix is present, False otherwise.
        """
        node = self._root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

    def __contains__(self, word: str) -> bool:
        """Return True when ``word`` exists within the trie."""

        return self.contains(word)


@dataclass(frozen=True)
class DictionaryMetadata:
    """Metadata describing a lexicon stored on disk."""

    language: str
    lexicon: str
    path: Path


class BoggleDictionary:
    """Trie-backed dictionary for validating Boggle submissions."""

    def __init__(self, language: str = "en", lexicon: str = "enable") -> None:
        self.language = language
        self.lexicon = lexicon
        self._trie = Trie()
        self._words_loaded = False
        self._load_default()

    def _load_default(self) -> None:
        path = self._get_default_path()
        self.load_from_path(path)

    def _get_default_path(self) -> Path:
        """Return the filesystem path to the packaged dictionary."""

        path = RESOURCES_DIR / self.language / f"{self.lexicon}.txt"
        if not path.exists():
            raise FileNotFoundError(f"Dictionary for language '{self.language}' and lexicon '{self.lexicon}' not found at {path}.")
        return path

    @classmethod
    def available_dictionaries(cls) -> Iterator[DictionaryMetadata]:
        """Yield metadata for bundled dictionaries.

        Returns:
            Iterator over metadata describing each available language and lexicon.
        """
        for language_dir in RESOURCES_DIR.iterdir():
            if not language_dir.is_dir():
                continue
            language = language_dir.name
            for lexicon_path in language_dir.glob("*.txt"):
                yield DictionaryMetadata(language=language, lexicon=lexicon_path.stem, path=lexicon_path)

    def load_from_path(self, path: Path) -> None:
        """Load lexicon entries from ``path``.

        Args:
            path: File containing newline separated words.
        """
        words = path.read_text(encoding="utf-8").splitlines()
        self.load_words(words)

    def load_words(self, words: Iterable[str]) -> None:
        """Populate the trie with words from ``words``.

        Args:
            words: Iterable providing candidate words.
        """
        self._trie = Trie()
        for word in words:
            normalized = self._normalize_word(word)
            if not normalized:
                continue
            self._trie.insert(normalized)
        self._words_loaded = True

    def contains(self, word: str) -> bool:
        """Determine whether ``word`` is present in the dictionary.

        Args:
            word: Word to check.

        Returns:
            True if the dictionary contains the word, otherwise False.
        """
        self._ensure_loaded()
        return self._trie.contains(self._normalize_word(word))

    def has_prefix(self, prefix: str) -> bool:
        """Determine whether any entry begins with ``prefix``.

        Args:
            prefix: Prefix to test.

        Returns:
            True if at least one dictionary word starts with the prefix, otherwise False.
        """
        self._ensure_loaded()
        return self._trie.has_prefix(self._normalize_word(prefix))

    def _ensure_loaded(self) -> None:
        """Load the default dictionary if it has not been read yet."""

        if not self._words_loaded:
            self._load_default()

    @staticmethod
    def _normalize_word(word: str) -> str:
        """Normalise ``word`` to uppercase alphabetical characters."""

        cleaned = "".join(char for char in word.strip() if char.isalpha())
        return cleaned.upper()

    def __contains__(self, word: str) -> bool:
        """Return True when ``word`` is in the dictionary."""

        return self.contains(word)

    def __iter__(self) -> Iterator[str]:
        """Iterate over all stored words.

        Returns:
            Iterator yielding each stored word in alphabetical traversal order.
        """
        self._ensure_loaded()
        yield from self._iterate_trie(self._trie._root, prefix="")

    def _iterate_trie(self, node: TrieNode, prefix: str) -> Iterator[str]:
        """Yield words stored in ``node`` prefixed by ``prefix``.

        Args:
            node: Current trie node.
            prefix: Prefix accumulated for the node.

        Returns:
            Iterator yielding words encountered beneath the node.
        """

        if node.is_word:
            yield prefix
        for char, child in node.children.items():
            yield from self._iterate_trie(child, prefix + char)
