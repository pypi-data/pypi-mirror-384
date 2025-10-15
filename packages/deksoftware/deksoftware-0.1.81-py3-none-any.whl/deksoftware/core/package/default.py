from .base import PackageBase, register_package


@register_package('default')
class DefaultPackage(PackageBase):
    pass
