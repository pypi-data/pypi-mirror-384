from typing import TYPE_CHECKING, Literal

from konigle.logging import get_logger

if TYPE_CHECKING:
    from konigle.session import AsyncSession, SyncSession


class BaseWebsiteManager:

    site_documents_base_path = "/admin/api/site-documents"
    """The API base path for site documents."""

    business_info_doc_type = "biz_info"
    """Document type for business information."""

    website_info_doc_type = "website_info"
    """Document type for website information."""

    design_system_doc_type = "design_system"
    """Document type for design system."""

    pages_base_path = "/admin/api/pages"
    """The API base path for pages."""


class WebsiteManager(BaseWebsiteManager):
    """Manager for managing website related information and settings"""

    def __init__(self, session: "SyncSession"):
        self._session = session
        self.logger = get_logger()

        self._site_doc_ids: dict[str, str] = {}

    def get_business_info(self) -> str:
        """
        Get the business information content.

        Returns:
            str: The business information content as markdown.
        """
        doc_id = self._get_site_doc_id(self.business_info_doc_type)
        url = f"{self.site_documents_base_path}/{doc_id}"
        response = self._session.get(url)
        response.raise_for_status()
        doc = response.json()
        return doc.get("content", "")

    def set_business_info(self, info: str) -> None:
        """
        Set the business information content.

        Args:
            info (str): The business information content as markdown.
        """
        doc_id = self._get_site_doc_id(self.business_info_doc_type)
        url = f"{self.site_documents_base_path}/{doc_id}"
        params = {"content": info}
        response = self._session.patch(url, data=params)
        response.raise_for_status()

    def get_website_info(self) -> str:
        """
        Get the website information content.

        Returns:
            str: The website information content as markdown.
        """
        doc_id = self._get_site_doc_id(self.website_info_doc_type)
        url = f"{self.site_documents_base_path}/{doc_id}"
        response = self._session.get(url)
        response.raise_for_status()
        doc = response.json()
        return doc.get("content", "")

    def set_website_info(self, info: str) -> None:
        """
        Set the website information content.

        Args:
            info (str): The website information content as markdown.
        """
        doc_id = self._get_site_doc_id(self.website_info_doc_type)

        url = f"{self.site_documents_base_path}/{doc_id}"
        params = {"content": info}
        response = self._session.patch(url, data=params)
        response.raise_for_status()

    def get_design_system(self) -> str:
        """
        Get the design system content.

        Returns:
            str: The design system content as markdown.
        """
        doc_id = self._get_site_doc_id(self.design_system_doc_type)
        url = f"{self.site_documents_base_path}/{doc_id}"
        response = self._session.get(url)
        response.raise_for_status()
        doc = response.json()
        return doc.get("content", "")

    def set_design_system(self, info: str) -> None:
        """
        Set the design system content.

        Args:
            info (str): The design system content as markdown.
        """
        doc_id = self._get_site_doc_id(self.design_system_doc_type)

        url = f"{self.site_documents_base_path}/{doc_id}"
        params = {"content": info}
        response = self._session.patch(url, data=params)
        response.raise_for_status()

    def add_url(
        self, pathname: str, url_type: Literal["page", "folder"] = "page"
    ) -> dict:
        """Add URL to the website.
        This creates nested folders as needed.
        Args:
            pathname (str): The pathname to add.
        Returns:
            dict: Containing type of page and the ID.
        """
        path = f"{self.pages_base_path}/add-url"
        response = self._session.post(
            path, json={"pathname": pathname, "url_type": url_type}
        )
        return response.json()

    def get_url(self, pathname: str, version: str | None = None) -> dict:
        """Get URL details from the website.
        Args:
            pathname (str): The pathname to get.
            version: Page version
        Returns:
            dict: Containing type of page and the ID.
        """
        path = f"{self.pages_base_path}/get-url"
        params = {"pathname": pathname}
        if version:
            params["version"] = version
        response = self._session.get(path, params=params)
        return response.json()

    def _get_site_doc_id(self, type_: str) -> str:
        if type_ in self._site_doc_ids:
            return self._site_doc_ids[type_]

        url = f"{self.site_documents_base_path}/bootstrap"
        response = self._session.post(url, data={"type": type_})
        response.raise_for_status()
        doc = response.json()
        site_doc_id = doc.get("id")
        if site_doc_id:
            self._site_doc_ids[type_] = site_doc_id
        else:
            raise ValueError(f"Site document of type '{type_}' not found")
        return site_doc_id


class AsyncWebsiteManager(BaseWebsiteManager):
    """Async Manager for managing website related information and settings"""

    def __init__(self, session: "AsyncSession"):
        self._session = session
        self.logger = get_logger()

        self._site_doc_ids: dict[str, str] = {}

    async def get_business_info(self) -> str:
        """
        Get the business information content.

        Returns:
            str: The business information content as markdown.
        """
        doc_id = await self._get_site_doc_id(self.business_info_doc_type)
        url = f"{self.site_documents_base_path}/{doc_id}"
        response = await self._session.get(url)
        response.raise_for_status()
        doc = response.json()
        return doc.get("content", "")

    async def set_business_info(self, info: str) -> None:
        """
        Set the business information content.

        Args:
            info (str): The business information content as markdown.
        """
        doc_id = await self._get_site_doc_id(self.business_info_doc_type)
        url = f"{self.site_documents_base_path}/{doc_id}"
        params = {"content": info}
        response = await self._session.patch(url, data=params)
        response.raise_for_status()

    async def get_website_info(self) -> str:
        """
        Get the website information content.

        Returns:
            str: The website information content as markdown.
        """
        doc_id = await self._get_site_doc_id(self.website_info_doc_type)
        url = f"{self.site_documents_base_path}/{doc_id}"
        response = await self._session.get(url)
        response.raise_for_status()
        doc = response.json()
        return doc.get("content", "")

    async def set_website_info(self, info: str) -> None:
        """
        Set the website information content.

        Args:
            info (str): The website information content as markdown.
        """
        doc_id = await self._get_site_doc_id(self.website_info_doc_type)

        url = f"{self.site_documents_base_path}/{doc_id}"
        params = {"content": info}
        response = await self._session.patch(url, data=params)
        response.raise_for_status()

    async def get_design_system(self) -> str:
        """
        Get the design system content.

        Returns:
            str: The design system content as markdown.
        """
        doc_id = await self._get_site_doc_id(self.design_system_doc_type)
        url = f"{self.site_documents_base_path}/{doc_id}"
        response = await self._session.get(url)
        response.raise_for_status()
        doc = response.json()
        return doc.get("content", "")

    async def set_design_system(self, info: str) -> None:
        """
        Set the design system content.

        Args:
            info (str): The design system content as markdown.
        """
        doc_id = await self._get_site_doc_id(self.design_system_doc_type)

        url = f"{self.site_documents_base_path}/{doc_id}"
        params = {"content": info}
        response = await self._session.patch(url, data=params)
        response.raise_for_status()

    async def add_url(
        self, pathname: str, url_type: Literal["page", "folder"] = "page"
    ) -> dict:
        """Add URL to the website.
        This creates nested folders as needed.
        Args:
            pathname (str): The pathname to add.
        Returns:
            dict: Containing type of page and the ID.
        """
        path = f"{self.pages_base_path}/add-url"
        response = await self._session.post(
            path, json={"pathname": pathname, "url_type": url_type}
        )
        return response.json()

    async def get_url(self, pathname: str, version: str | None = None) -> dict:
        """Get URL details from the website.
        Args:
            pathname (str): The pathname to get.
            version: Page version
        Returns:
            dict: Containing type of page and the ID.
        """
        path = f"{self.pages_base_path}/get-url"
        params = {"pathname": pathname}
        if version:
            params["version"] = version
        response = await self._session.get(path, params=params)
        return response.json()

    async def _get_site_doc_id(self, type_: str) -> str:
        if type_ in self._site_doc_ids:
            return self._site_doc_ids[type_]

        url = f"{self.site_documents_base_path}/bootstrap"
        response = await self._session.post(url, data={"type": type_})
        response.raise_for_status()
        doc = response.json()
        site_doc_id = doc.get("id")
        if site_doc_id:
            self._site_doc_ids[type_] = site_doc_id
        else:
            raise ValueError(f"Site document of type '{type_}' not found")
        return site_doc_id
