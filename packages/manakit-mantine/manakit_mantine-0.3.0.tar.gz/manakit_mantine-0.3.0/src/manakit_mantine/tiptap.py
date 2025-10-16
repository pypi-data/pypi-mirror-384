"""Mantine RichTextEditor (Tiptap) component wrapper for Reflex.

Provides a WYSIWYG rich text editor based on Tiptap with Mantine UI.
Uses external JavaScript wrapper file for React hook management.

Documentation: https://mantine.dev/x/tiptap/
"""

from __future__ import annotations

import enum
from typing import Final, Literal

import reflex as rx
from reflex.assets import asset
from reflex.base import Base
from reflex.components.component import NoSSRComponent
from reflex.event import EventHandler
from reflex.vars.base import Var

from .base import MANTINE_VERSION

TIPTAP_REACT_VERSION: Final[str] = "^2.10.4"
TIPTAP_VERSION: Final[str] = (
    TIPTAP_REACT_VERSION  # Same version for all @tiptap packages
)


class ToolbarControlGroup(list, enum.Enum):
    """Predefined control groups for the toolbar."""

    BASIC_FORMATTING = [
        "bold",
        "italic",
        "underline",
        "strikethrough",
        "clearFormatting",
        "code",
        "highlight",
    ]
    HEADINGS = ["h1", "h2", "h3", "h4"]
    LISTS_AND_BLOCKS = [
        "blockquote",
        "hr",
        "bulletList",
        "orderedList",
        "subscript",
        "superscript",
    ]
    LINKS = ["link", "unlink"]
    ALIGNMENT = ["alignLeft", "alignCenter", "alignRight", "alignJustify"]
    COLORS = ["colorPicker", "unsetColor"]
    HISTORY = ["undo", "redo"]
    MEDIA = ["image"]
    ALL = [
        "bold",
        "italic",
        "underline",
        "strikethrough",
        "clearFormatting",
        "code",
        "highlight",
        "h1",
        "h2",
        "h3",
        "h4",
        "blockquote",
        "hr",
        "bulletList",
        "orderedList",
        "subscript",
        "superscript",
        "link",
        "unlink",
        "alignLeft",
        "alignCenter",
        "alignRight",
        "alignJustify",
        "colorPicker",
        "unsetColor",
        "undo",
        "redo",
        "image",
    ]


class EditorToolbarConfig(Base):
    """Configuration for the RichTextEditor toolbar.

    Use this to customize which controls appear in the toolbar and how they are grouped.

    Example:
        ```python
        from mantine import EditorToolbarConfig, ToolbarControlGroup

        # Use predefined groups
        config = EditorToolbarConfig(
            control_groups=[
                ToolbarControlGroup.BASIC_FORMATTING.value,
                ToolbarControlGroup.HEADINGS.value,
                ToolbarControlGroup.ALIGNMENT.value,
            ]
        )

        # Or define custom groups
        config = EditorToolbarConfig(
            control_groups=[
                ["bold", "italic", "underline"],
                ["h1", "h2"],
                ["link", "unlink"],
            ]
        )

        # Use in component
        mn.rich_text_editor(
            content=State.content,
            toolbar_config=config,
        )
        ```
    """

    # List of control groups (each group is a list of control names)
    control_groups: list[list[str]] | None = None

    # Whether to show the toolbar (default: True)
    show_toolbar: bool | None = None

    # Whether the toolbar should be sticky (default: True)
    sticky: bool | None = None

    # Sticky offset in pixels (default: 0)
    sticky_offset: int | str | None = None


class RichTextEditor(NoSSRComponent):
    """Mantine RichTextEditor - WYSIWYG editor with automatic hook management.

    Based on: https://mantine.dev/x/tiptap/

    This component uses a custom JavaScript wrapper that handles the useEditor
    React hook internally. The wrapper is located in assets/external/mantine/tiptap/

    Props:
        content: HTML content for the editor
        on_update: Callback when content changes (receives HTML string)
        editable: Whether the editor is editable (default: True)
        placeholder: Placeholder text when editor is empty
        variant: Visual style - "default" or "subtle"
        with_typography_styles: Apply typography styles (default: True)
        labels: Localization labels
    """

    tag = "RichTextEditorWrapper"

    # Point to our custom wrapper component (same directory as this module)
    library = "$/public/" + asset(
        path="tiptap_wrapper.js",
        shared=True,
    )
    is_default = False

    lib_dependencies: list[str] = [
        f"@mantine/tiptap@{MANTINE_VERSION}",
        f"@mantine/core@{MANTINE_VERSION}",
        f"@tiptap/react@{TIPTAP_VERSION}",
        f"@tiptap/pm@{TIPTAP_VERSION}",
        f"@tiptap/extension-link@{TIPTAP_VERSION}",
        f"@tiptap/starter-kit@{TIPTAP_VERSION}",
        f"@tiptap/extension-color@{TIPTAP_VERSION}",
        f"@tiptap/extension-highlight@{TIPTAP_VERSION}",
        f"@tiptap/extension-image@{TIPTAP_VERSION}",
        f"@tiptap/extension-placeholder@{TIPTAP_VERSION}",
        f"@tiptap/extension-subscript@{TIPTAP_VERSION}",
        f"@tiptap/extension-superscript@{TIPTAP_VERSION}",
        f"@tiptap/extension-text-align@{TIPTAP_VERSION}",
        f"@tiptap/extension-text-style@{TIPTAP_VERSION}",
    ]

    # Content management
    content: Var[str] = None
    """HTML content for the editor."""

    on_update: EventHandler[lambda html: [html]] = None
    """Callback when content changes (receives HTML string)."""

    # Editor state
    editable: Var[bool] = None
    """Whether the editor is editable. Default: True."""

    placeholder: Var[str] = None
    """Placeholder text when editor is empty."""

    # Visual props
    variant: Var[Literal["default", "subtle"]] = None
    """Visual style: default (with borders) or subtle (borderless)."""

    with_typography_styles: Var[bool] = None
    """Apply typography styles to content. Default: True."""

    # Localization
    labels: Var[dict] = None
    """Localization labels for controls."""

    # Toolbar configuration - individual props instead of dict
    control_groups: Var[list] = None
    """List of control groups for the toolbar. Each group is a list of control names."""

    show_toolbar: Var[bool] = None
    """Whether to show the toolbar. Default: True."""

    sticky: Var[bool] = None
    """Whether the toolbar should be sticky. Default: True."""

    sticky_offset: Var[str | int] = None
    """Sticky offset in pixels. Default: '0px'."""

    @classmethod
    def create(
        cls, toolbar_config: EditorToolbarConfig | None = None, **props
    ) -> rx.Component:
        """Create an instance of RichTextEditor.

        Args:
            toolbar_config: Optional toolbar configuration to customize controls.
            **props: Any properties to be passed to the RichTextEditor

        Returns:
            A RichTextEditor instance.

        Raises:
            ValueError: If toolbar_config is a state Var.

        Example:
            ```python
            from mantine import (
                rich_text_editor,
                EditorToolbarConfig,
                ToolbarControlGroup,
            )

            # With default toolbar
            rich_text_editor(content=State.content, on_update=State.update)

            # With custom toolbar using config
            config = EditorToolbarConfig(
                control_groups=[
                    ToolbarControlGroup.BASIC_FORMATTING.value,
                    ToolbarControlGroup.HEADINGS.value,
                ]
            )
            rich_text_editor(content=State.content, toolbar_config=config)
            ```
        """
        if toolbar_config is not None:
            if isinstance(toolbar_config, Var):
                msg = "EditorToolbarConfig cannot be a state Var"
                raise ValueError(msg)
            # Extract individual props from config
            config_dict = toolbar_config.dict()
            if config_dict.get("control_groups") is not None:
                props["control_groups"] = config_dict["control_groups"]
            if config_dict.get("show_toolbar") is not None:
                props["show_toolbar"] = config_dict["show_toolbar"]
            if config_dict.get("sticky") is not None:
                props["sticky"] = config_dict["sticky"]
            if config_dict.get("sticky_offset") is not None:
                props["sticky_offset"] = config_dict["sticky_offset"]
        return super().create(**props)


# Namespace
class RichTextEditorNamespace(rx.ComponentNamespace):
    """Namespace for RichTextEditor component."""

    __call__ = staticmethod(RichTextEditor.create)


rich_text_editor = RichTextEditorNamespace()
