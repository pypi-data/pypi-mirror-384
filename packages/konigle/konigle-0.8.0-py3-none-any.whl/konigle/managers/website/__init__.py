"""
Website managers for the Konigle SDK.

This module provides managers for website-related resources like folders,
pages, blog posts, and glossary terms.
"""

from .author import AsyncAuthorManager, AuthorManager
from .blog import AsyncBlogManager, BlogManager
from .component import AsyncComponentManager, ComponentManager
from .design import AsyncStylesheetManager, StylesheetManager
from .folder import AsyncFolderManager, FolderManager
from .glossary import AsyncGlossaryTermManager, GlossaryTermManager
from .page import AsyncPageManager, PageManager
from .site import AsyncWebsiteManager, WebsiteManager
from .template import AsyncTemplateManager, TemplateManager

__all__ = [
    "FolderManager",
    "AsyncFolderManager",
    "AuthorManager",
    "AsyncAuthorManager",
    "PageManager",
    "AsyncPageManager",
    "BlogManager",
    "AsyncBlogManager",
    "GlossaryTermManager",
    "AsyncGlossaryTermManager",
    "ComponentManager",
    "AsyncComponentManager",
    "TemplateManager",
    "AsyncTemplateManager",
    "StylesheetManager",
    "AsyncStylesheetManager",
    "WebsiteManager",
    "AsyncWebsiteManager",
]
