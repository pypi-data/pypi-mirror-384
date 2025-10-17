# DjangoCMS Deleted Pages

This module is designed for the [Django CMS](https://www.django-cms.org/) content management system.
Since CMS 4, the content of pages that users publish has been versioned. This makes it possible to revert changes that users have made.
Unfortunately, this does not apply to deleted pages. Once a page is deleted, all content, including all its versions, is irretrievably gone.
That is why there is this module that creates a copy of the page before deleting it and places it under the Trash page.
This way, it is possible to restore a page that was deleted by mistake.

A page representing the trash can for deleted pages is created automatically when a page is deleted.
The trash can page has a special `slug`, which has the default value `deleted-pages`. This slug can be redefined in settings in the constant `DELETED_PAGES_SLUG`.
It is also possible to redefine the slug in [Constance](https://django-constance.readthedocs.io/), if you have it installed. The name `DELETED_PAGES_SLUG` is also used there.
By redefining the slug, it is possible to store deleted pages in a different page than the current one.

![Pages list](https://gitlab.nic.cz/djangocms-apps/djangocms-deleted-pages/-/raw/main/snapshosts/deleted-pages-are-duplicated-into-trash.gif "Pages list")

## Install

Install the package from pypi.org.

```
pip install djangocms-deleted-pages
```

Add into `INSTALLED_APPS` in your site `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "djangocms_deleted_pages",
]
```

### Extra settings

This value can be defined in both settings and Constance. Constance always takes precedence.

 - `DELETED_PAGES_SLUG` - Slug for Trash bin page. Default is `deleted-pages`.


## License

BSD-3-Clause
