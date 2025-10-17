from cms.api import create_page, create_page_content
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page
from cms.utils.page import get_page_from_request
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest

try:
    from constance import config as constance_config
except ModuleNotFoundError:
    constance_config = None

from .constants import TRASH_BIN_PAGE_TITLES


def get_or_create_page_trash_bin(request: HttpRequest, path: str) -> Page:
    """Get or create page trash bin."""
    page = get_page_from_request(request, use_path=path)
    if page is None:
        title = TRASH_BIN_PAGE_TITLES.get(request.LANGUAGE_CODE, TRASH_BIN_PAGE_TITLES["en"])
        current_site = get_current_site(request)
        page = create_page(
            title,
            TEMPLATE_INHERITANCE_MAGIC,
            request.LANGUAGE_CODE,
            slug=path,
            created_by=request.user,
            site=current_site,
        )
        for language, _ in settings.LANGUAGES:
            if language != request.LANGUAGE_CODE:
                title = TRASH_BIN_PAGE_TITLES.get(language, TRASH_BIN_PAGE_TITLES["en"])
                create_page_content(language, title, page, created_by=request.user)
    return page


def get_page_slug() -> str:
    """Get page slug."""
    slug = getattr(settings, "DELETED_PAGES_SLUG", "deleted-pages")
    if constance_config is not None:
        slug = getattr(constance_config, "DELETED_PAGES_SLUG", slug)
    return slug
