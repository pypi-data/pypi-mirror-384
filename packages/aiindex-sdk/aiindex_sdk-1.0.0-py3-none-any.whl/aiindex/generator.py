"""
AIIndex document generation with web crawling and metadata extraction.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .types import AIIndexDocument, Entity, EntityType, FAQ, Page, ContentType, Publisher, Contact


class AIIndexGenerator:
    """
    Generator for AIIndex documents with web crawling and content extraction.

    Example:
        >>> generator = AIIndexGenerator("example.com", "example.com")
        >>> generator.crawl("https://example.com", max_pages=10)
        >>> generator.extract_metadata()
        >>> doc = generator.build()
    """

    def __init__(
        self,
        publisher_id: str,
        domain: str,
        user_agent: str = "AIIndexGenerator/1.0"
    ):
        """
        Initialize the generator.

        Args:
            publisher_id: Unique publisher identifier
            domain: Primary domain name
            user_agent: User agent string for HTTP requests
        """
        self.publisher_id = publisher_id
        self.domain = domain
        self.user_agent = user_agent
        self.pages: List[Page] = []
        self.entities: List[Entity] = []
        self.faq: List[FAQ] = []
        self.publisher: Optional[Publisher] = None
        self._visited_urls: Set[str] = set()

    def crawl(
        self,
        start_url: str,
        max_pages: int = 10,
        max_depth: int = 3,
        same_domain_only: bool = True
    ) -> int:
        """
        Crawl a website starting from the given URL.

        Args:
            start_url: Starting URL for crawling
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth of crawling
            same_domain_only: Only crawl pages on the same domain

        Returns:
            Number of pages crawled
        """
        base_domain = urlparse(start_url).netloc
        to_visit = [(start_url, 0)]
        crawled = 0

        while to_visit and crawled < max_pages:
            url, depth = to_visit.pop(0)

            if url in self._visited_urls or depth > max_depth:
                continue

            try:
                page_data = self._fetch_page(url)
                if page_data:
                    self.pages.append(page_data)
                    self._visited_urls.add(url)
                    crawled += 1

                    # Extract links for further crawling
                    if depth < max_depth:
                        links = self._extract_links(url)
                        for link in links:
                            if link not in self._visited_urls:
                                link_domain = urlparse(link).netloc
                                if not same_domain_only or link_domain == base_domain:
                                    to_visit.append((link, depth + 1))

            except Exception as e:
                print(f"Error crawling {url}: {e}")
                continue

        return crawled

    def _fetch_page(self, url: str) -> Optional[Page]:
        """Fetch and parse a single page."""
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract title
            title_tag = soup.find("title")
            title = title_tag.get_text().strip() if title_tag else url

            # Extract description
            description = None
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()

            # Try to determine content type
            content_type = self._infer_content_type(url, soup)

            # Extract dates if available
            published = self._extract_date(soup, "published")
            modified = self._extract_date(soup, "modified")

            # Extract author
            author = self._extract_author(soup)

            # Extract keywords/tags
            tags = self._extract_tags(soup)

            # Create summary from meta description or first paragraph
            summary = description
            if not summary:
                first_p = soup.find("p")
                if first_p:
                    summary = first_p.get_text().strip()[:2000]

            return Page(
                url=url,
                title=title,
                description=description,
                content_type=content_type,
                published=published,
                modified=modified,
                author=author,
                tags=tags,
                summary=summary,
            )

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _extract_links(self, base_url: str) -> List[str]:
        """Extract all valid links from a page."""
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(base_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            links = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(base_url, href)

                # Only include http/https links
                if full_url.startswith(("http://", "https://")):
                    # Remove fragments
                    full_url = full_url.split("#")[0]
                    if full_url not in links:
                        links.append(full_url)

            return links

        except Exception:
            return []

    def _infer_content_type(self, url: str, soup: BeautifulSoup) -> Optional[ContentType]:
        """Infer content type from URL and page structure."""
        url_lower = url.lower()

        if "blog" in url_lower or "article" in url_lower or "post" in url_lower:
            return ContentType.ARTICLE
        elif "product" in url_lower or "shop" in url_lower:
            return ContentType.PRODUCT
        elif "docs" in url_lower or "documentation" in url_lower or "api" in url_lower:
            return ContentType.DOCUMENTATION
        elif "faq" in url_lower or "help" in url_lower:
            return ContentType.FAQ
        elif "about" in url_lower:
            return ContentType.ABOUT

        # Check for article tags
        if soup.find("article"):
            return ContentType.ARTICLE

        return ContentType.PAGE

    def _extract_date(self, soup: BeautifulSoup, date_type: str) -> Optional[datetime]:
        """Extract published or modified date from page."""
        # Try various meta tags
        meta_names = {
            "published": ["article:published_time", "datePublished", "publish_date"],
            "modified": ["article:modified_time", "dateModified", "last_modified"],
        }

        for name in meta_names.get(date_type, []):
            meta = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
            if meta and meta.get("content"):
                try:
                    # Try to parse ISO format
                    return datetime.fromisoformat(meta["content"].replace("Z", "+00:00"))
                except Exception:
                    pass

        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from page."""
        # Try meta tags
        author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", attrs={"property": "article:author"})
        if author_meta and author_meta.get("content"):
            return author_meta["content"].strip()

        # Try author class
        author_elem = soup.find(class_=re.compile("author", re.I))
        if author_elem:
            return author_elem.get_text().strip()

        return None

    def _extract_tags(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract tags/keywords from page."""
        tags = []

        # Try keywords meta tag
        keywords_meta = soup.find("meta", attrs={"name": "keywords"})
        if keywords_meta and keywords_meta.get("content"):
            tags.extend([tag.strip() for tag in keywords_meta["content"].split(",")])

        # Try article tags
        tag_meta = soup.find("meta", attrs={"property": "article:tag"})
        if tag_meta and tag_meta.get("content"):
            tags.append(tag_meta["content"].strip())

        return tags if tags else None

    def extract_metadata(self, url: str) -> Dict:
        """
        Extract metadata from a website's homepage.

        Args:
            url: URL to extract metadata from

        Returns:
            Dictionary with extracted metadata
        """
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract publisher info
            site_name = None
            og_site_name = soup.find("meta", attrs={"property": "og:site_name"})
            if og_site_name and og_site_name.get("content"):
                site_name = og_site_name["content"].strip()

            description = None
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()

            # Extract contact email
            email = None
            email_links = soup.find_all("a", href=re.compile(r"^mailto:"))
            if email_links:
                email = email_links[0]["href"].replace("mailto:", "")

            # Create publisher object
            contact = Contact(email=email) if email else None
            self.publisher = Publisher(
                name=site_name,
                description=description,
                url=url,
                contact=contact,
            )

            return {
                "site_name": site_name,
                "description": description,
                "email": email,
            }

        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the index."""
        self.entities.append(entity)

    def add_faq(self, question: str, answer: str, category: Optional[str] = None) -> None:
        """Add an FAQ entry."""
        self.faq.append(FAQ(question=question, answer=answer, category=category))

    def build(self) -> AIIndexDocument:
        """
        Build the final AIIndex document.

        Returns:
            Complete AIIndexDocument
        """
        return AIIndexDocument(
            version="1.0",
            publisher_id=self.publisher_id,
            domain=self.domain,
            last_updated=datetime.utcnow(),
            publisher=self.publisher,
            entities=self.entities if self.entities else None,
            pages=self.pages if self.pages else None,
            faq=self.faq if self.faq else None,
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        doc = self.build()
        return doc.model_dump(exclude_none=True, mode='json')

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2, default=str)
