from typing import Any

from rich.console import RenderableType
from rich.tree import Tree as RichTree

from ..core.console import get_console
from ..core.theme import get_theme


class Tree:
    """Themed tree view for hierarchical data."""

    def __init__(
        self,
        label: str,
        guide_style: str | None = None,
        expanded: bool = True,
    ):
        """Create a tree view."""
        self.theme = get_theme()
        self.console = get_console()

        # Apply theme to guide style
        style = guide_style or self.theme.get_style("muted")

        # Create Rich tree with themed styling
        self._tree = RichTree(
            label,
            guide_style=style,
            expanded=expanded,
        )

    def add(
        self,
        label: str,
        style: str | None = None,
        guide_style: str | None = None,
        expanded: bool = True,
    ) -> "Tree":
        """Add a branch to the tree."""
        # Apply themed styling
        branch_guide_style = guide_style or self.theme.get_style("muted")

        # Add branch to Rich tree
        rich_branch = self._tree.add(
            label,
            style=style,
            guide_style=branch_guide_style,
            expanded=expanded,
        )

        # Wrap in ChalkBox Tree
        branch_tree = Tree.__new__(Tree)
        branch_tree.theme = self.theme
        branch_tree.console = self.console
        branch_tree._tree = rich_branch

        return branch_tree

    def add_branch(
        self,
        label: str,
        items: list[str] | dict[str, Any],
        style: str | None = None,
    ) -> "Tree":
        """Add a branch with multiple items."""
        branch = self.add(label, style=style)

        if isinstance(items, dict):
            for key, value in items.items():
                if isinstance(value, list | dict):
                    # Recursively add nested structures
                    branch.add_branch(str(key), value)
                else:
                    branch.add(f"{key}: {value}")
        elif isinstance(items, list):
            for item in items:
                if isinstance(item, list | dict):
                    # Handle nested structures
                    branch.add_branch("item", item)
                else:
                    branch.add(str(item))

        return branch

    def __rich__(self) -> RenderableType:
        """Render the tree as a Rich renderable."""
        return self._tree

    def print(self) -> None:
        """Print the tree to console."""
        self.console.print(self.__rich__())

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        root_label: str = "Root",
        **kwargs: Any,
    ) -> "Tree":
        """Create a tree from a dictionary."""
        tree = cls(root_label, **kwargs)

        def add_dict_items(parent: Tree, items: dict[str, Any]) -> None:
            """Recursively add dictionary items to tree."""
            for key, value in items.items():
                if isinstance(value, dict):
                    branch = parent.add(str(key))
                    add_dict_items(branch, value)
                elif isinstance(value, list):
                    branch = parent.add(str(key))
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            item_branch = branch.add(f"[{i}]")
                            add_dict_items(item_branch, item)
                        else:
                            branch.add(str(item))
                else:
                    parent.add(f"{key}: {value}")

        add_dict_items(tree, data)
        return tree

    @classmethod
    def from_filesystem(
        cls,
        path: str,
        max_depth: int = 3,
        show_hidden: bool = False,
        **kwargs: Any,
    ) -> "Tree":
        """Create a tree from a filesystem path."""
        from pathlib import Path

        root_path = Path(path)
        if not root_path.exists():
            # Fail-safe: return empty tree
            return cls("Path not found", **kwargs)

        tree = cls(str(root_path.name or root_path), **kwargs)

        def add_directory(parent: Tree, dir_path: Path, depth: int) -> None:
            """Recursively add directory contents to tree."""
            if depth >= max_depth:
                return

            try:
                items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name))

                for item in items:
                    # Skip hidden files if configured
                    if not show_hidden and item.name.startswith("."):
                        continue

                    if item.is_dir():
                        branch = parent.add(
                            f"📁 {item.name}",
                            style=parent.theme.get_style("primary"),
                        )
                        add_directory(branch, item, depth + 1)
                    else:
                        parent.add(
                            f"📄 {item.name}",
                            style=parent.theme.get_style("muted"),
                        )
            except PermissionError:
                # Fail-safe: skip inaccessible directories
                parent.add("(permission denied)", style=parent.theme.get_style("error"))

        if root_path.is_dir():
            add_directory(tree, root_path, 0)
        else:
            tree.add(f"📄 {root_path.name}")

        return tree

    @classmethod
    def simple(cls, label: str, items: list[str], **kwargs: Any) -> "Tree":
        """Create a simple tree with a list of items."""
        tree = cls(label, **kwargs)
        for item in items:
            tree.add(item)
        return tree
