"""Knowledge base loader."""

import os
from typing import List


class KnowledgeBase:
    """Load knowledge from markdown and text files."""

    def __init__(self, knowledge_path: str):
        self.knowledge_path = knowledge_path
        self.content = ""
        self._load()

    def _load(self):
        """Load all knowledge files."""
        if not os.path.exists(self.knowledge_path):
            print(f"Warning: Knowledge path does not exist: {self.knowledge_path}")
            return

        documents = []

        # Walk through all subdirectories
        for root, dirs, files in os.walk(self.knowledge_path):
            for filename in files:
                if filename.endswith((".md", ".txt")):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Add file header
                            rel_path = os.path.relpath(file_path, self.knowledge_path)
                            documents.append(f"=== {rel_path} ===\n\n{content}")
                    except Exception as e:
                        print(f"Warning: Failed to load {file_path}: {e}")

        if documents:
            self.content = "\n\n---\n\n".join(documents)
            print(f"Loaded {len(documents)} knowledge documents")
        else:
            print("No knowledge documents found")

    def get_content(self) -> str:
        """Get all knowledge content."""
        return self.content

    def reload(self):
        """Reload knowledge base."""
        self._load()
