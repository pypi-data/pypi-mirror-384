from cms.operations import DELETE_PAGE
from django.apps import AppConfig


def pre_obj_operation_handler(sender, operation=None, request=None, token=None, obj=None, **kwargs):
    """Copy the page to the trash before deleting it."""
    from .utils import get_or_create_page_trash_bin, get_page_slug

    if operation == DELETE_PAGE:
        page = obj
        deleted_page_slug = get_page_slug()
        root = page.get_root()
        slug = root.get_slug(request.LANGUAGE_CODE)
        if slug != deleted_page_slug:
            trash = get_or_create_page_trash_bin(request, deleted_page_slug)
            page.copy_with_descendants(trash.node, position="last-child", user=request.user)


class DeletedPagesConfig(AppConfig):
    name = "djangocms_deleted_pages"

    def ready(self):
        from cms.signals import pre_obj_operation

        pre_obj_operation.connect(pre_obj_operation_handler)
