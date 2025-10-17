import gettext
import os
import shutil
from pathlib import Path
from typing import Dict

from pyguiadapterlite import assets

_DEFAULT_LOCALE_DIR = assets.locales_dir()
_DEFAULT_DOMAIN = "pyguiadapterlite"
_DEFAULT_LANGUAGE = "en_US"


class I18N:
    def __init__(
        self,
        domain: str = _DEFAULT_DOMAIN,
        localedir: str = _DEFAULT_LOCALE_DIR,
        language: str = _DEFAULT_LANGUAGE,
    ):
        self._domain = domain
        self._localedir = localedir
        self._current_language = language
        self._translation = None
        self._fallback_translations = {}

        # 确保目录存在
        if not os.path.exists(localedir):
            os.makedirs(os.path.abspath(localedir), exist_ok=True)

    def set_locale_dir(self, localedir: str) -> None:
        if not os.path.exists(localedir):
            os.makedirs(localedir, exist_ok=True)
        self._localedir = localedir

    def get_locale_dir(self) -> str:
        return self._localedir

    def set_language(self, language: str) -> None:
        self._current_language = language
        try:
            self._translation = gettext.translation(
                self._domain,
                localedir=self._localedir,
                languages=[language],
                fallback=True,
            )
            self._translation.install()
        except FileNotFoundError:
            # 如果找不到翻译文件，使用空翻译
            self._translation = gettext.NullTranslations()
            self._translation.install()

    def gettext(self, message: str) -> str:
        if self._translation:
            return self._translation.gettext(message)
        return message

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        if self._translation:
            return self._translation.ngettext(singular, plural, n)
        return singular if n == 1 else plural

    # 简化方法别名
    def _(self, message: str) -> str:
        """gettext 的简写形式"""
        return self.gettext(message)

    def _n(self, singular: str, plural: str, n: int) -> str:
        """ngettext 的简写形式"""
        return self.ngettext(singular, plural, n)


class I18NManager:
    """
    i18n 管理器，支持多个翻译域
    """

    def __init__(self):
        self._domains: Dict[str, I18N] = {}
        self._default_domain = _DEFAULT_DOMAIN

    def add_domain(self, domain: str, localedir: str = _DEFAULT_LOCALE_DIR) -> I18N:
        i18n = I18N(domain, localedir)
        self._domains[domain] = i18n
        return i18n

    def set_language(self, language: str, domain: str = None) -> None:
        if domain:
            if domain in self._domains:
                self._domains[domain].set_language(language)
        else:
            for i18n in self._domains.values():
                i18n.set_language(language)

    def get_domain(self, domain: str = None) -> I18N:
        domain = domain or self._default_domain
        if domain not in self._domains:
            self.add_domain(domain)
        return self._domains[domain]


# 创建全局实例
_manager = I18NManager()
_default_i18n = _manager.add_domain(_DEFAULT_DOMAIN)


# 便捷函数
def set_language(language: str):
    """设置当前语言"""
    _default_i18n.set_language(language)


def set_locale_dir(localedir: str):
    """设置翻译文件目录"""
    _default_i18n.set_locale_dir(localedir)


def tr_(message: str) -> str:
    """翻译字符串"""
    return _default_i18n.gettext(message)


def ntr_(singular: str, plural: str, n: int) -> str:
    """翻译单复数字符串"""
    return _default_i18n.ngettext(singular, plural, n)


def export_locale_dir(target_dir: str, overwrite: bool = False) -> None:
    """导出翻译文件到指定目录"""
    target_dir = Path(target_dir)
    if target_dir.is_dir() and not overwrite:
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(assets.locales_dir(), target_dir, dirs_exist_ok=True)
