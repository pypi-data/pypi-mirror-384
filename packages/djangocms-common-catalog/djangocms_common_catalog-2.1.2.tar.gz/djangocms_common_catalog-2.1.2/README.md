# Common Catalog

Common catalog for various uses.

The program is built on the  [Django CMS](https://www.django-cms.org/) framework.

The program itself does not contain any cascading styles or javascript code.

## Install

Install the package from pypi.org.

```
pip install djangocms-common-catalog
```

Add into `INSTALLED_APPS` in your site `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'common_catalog',
]
```

### Extra settings

 - ``COMMON_CATALOG_TEMPLATE_LIST`` - custom template for the list of items.
 - ``COMMON_CATALOG_TEMPLATE_DETAIL`` - custom template the Item detail.
 - ``COMMON_CATALOG_LOCATIONS`` - Custom filter location names.
 - ``COMMON_CATALOG_FILTER_QUERY_NAME`` - URL query name. Default is `cocaf`.
 - ``COMMON_CATALOG_DETAIL_PARENT_TEMPLATE`` - Name of parent template on Item detail page.


## Temporary fix

There was a problem with editing items when switching to CMS 4. An exception AttributeError occurs: type object 'Meta' has no attribute 'model'.
Until the problem is resolved, you can apply a patch on github.com.

``django-parler @ git+https://github.com/zbohm/django-parler.git@d448685ba3a2614aeb8f4df9e422a924a3c34ec2``

## License

GPLv3+
