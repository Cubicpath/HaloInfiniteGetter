###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module containing code related to translation and language files."""

__all__ = (
    'format_value',
    'LANG_PATH',
    'Language',
    'Translator',
)

import json
import re
from contextlib import AbstractContextManager
from contextlib import contextmanager
from pathlib import Path
from string import ascii_letters
from string import digits
from typing import Annotated
from typing import Any
from typing import Final

from .constants import *

LANG_PATH: Final[Path] = HI_RESOURCE_PATH / 'lang'
"""Directory containing language JSON data."""


def format_value(value: str, *args, _language: 'Language' = None) -> str:
    """Format a str with positional arguments.

    You can use {0} notation to refer to a specific positional argument.
    If the notation chars are replaced with the argument, you can no longer use it as a normal positional argument.

    JSON strings ex::

        {
            "a": "{0} is the same as {0} using only one argument.",
            "b": "{0} %s will not work and require 2 arguments",
            "c": "%s {0} is the same as above, where \"%s\" is now the 2nd argument since the 1st is used by \"{0}\""
        }
    """
    list_args:     list = list(args)
    replaced:      set[str] = set()
    pos_param_ref: re.Pattern = re.compile(r'{([1-9]\d*|0)}')
    key_ref:       re.Pattern = re.compile(r'{[\w\d\-.]*}')

    for match in pos_param_ref.finditer(value):
        match = match[0]
        arg_val = args[int(match.strip('{}'))]
        if match not in replaced:
            replaced.add(match)
            value = value.replace(match, arg_val)
            list_args.remove(arg_val)

    value = value % tuple(list_args)

    replaced.clear()
    if _language is not None:
        for match in key_ref.finditer(value):
            match = match[0]
            if match not in replaced:
                replaced.add(match)
                value = value.replace(match, _language.get_raw(match.strip('{}')))

    return value


class Language:
    """Object containing language data. Retrieves stored data with associated RFC 5646 language tags."""

    def __init__(self, primary: Annotated[str, 2] | None = None, region: Annotated[str, 2] | None = None, **kwargs) -> None:
        """Build a new Language object using given sub-tags.

        For more information on RFC 5646, visit https://datatracker.ietf.org/doc/html/rfc5646

        :param primary: The first part of the language code. i.e. [en]-US | Section 2.2.1
        :param region: The (commonly) second part of the language code. i.e. en-[US] | Section 2.2.4

        :keyword ext_lang: Extension to primary subtag | Section 2.2.2
        :keyword script: Script used to write the language | Section 2.2.3
        :keyword variants: A variant of the given language subtag | Section 2.2.5
        :keyword extensions: Extension to the given language, prefixed with a singleton | Section 2.2.6
        :keyword private_use: Any subtag that is not publicly defined | Section 2.2.7
        :type ext_lang: Annotated[str, 3] | None
        :type script: Annotated[str, 4] | None = None
        :type variants: Sequence[str] | None
        :type extensions: Sequence[tuple[Annotated[str, 1], str]] | None
        :type private_use: Sequence[str] | None

        :raises ValueError: If a given subtag is invalid.
        """

        (ext_lang, script, variants, extensions, private_use) = (
            kwargs.pop('ext_lang', None),
            kwargs.pop('script', None),
            kwargs.pop('variants', None),
            kwargs.pop('extensions', None),
            kwargs.pop('private_use', None),
        )

        self._data: dict[str, str] = {}
        self.tag:  str = ''

        sub_tags:  list[str] = []
        err: Exception | None = None

        if primary is None and ext_lang is None and private_use is None:
            err = ValueError('The primary and/or ext_lang and/or private_use subtag must be filled out.')

        if primary is not None:
            primary = primary.lower()

            # RFC 5646 section 2.2.1.1 and 2.2.1.2
            if not primary.isalpha() or not 3 >= len(primary) >= 2:
                err = ValueError(f'Primary language subtag "{primary}" is not valid.')

            sub_tags.append(primary)

        if ext_lang is not None:
            ext_lang = ext_lang.lower()

            # RFC 5646 section 2.2.2.1
            if not ext_lang.isalpha() or not len(ext_lang) == 3:
                err = ValueError(f'Extended language subtag "{ext_lang}" is not valid.')

            sub_tags.append(ext_lang)

        if script is not None:
            script = script.title()

            # RFC 5646 section 2.2.3.2
            if not script.isalpha() or not len(script) == 4:
                err = ValueError(f'Script subtag "{script}" is not valid.')

            sub_tags.append(script)

        if region is not None:
            region = region.upper()

            # ISO 3166-1 or UN M.49
            if not (len(region) == 2 and region.isalpha()) and not (len(region) == 5 and region[:2].isalpha() and region[2:].isnumeric()):
                err = ValueError(f'Region subtag "{region}" is not valid.')

            sub_tags.append(region)

        if variants is not None:
            checked = []
            for variant in variants:

                # RFC 5646 section 2.2.5.4
                if not (variant[0] in ascii_letters and 8 >= len(variant) >= 5) or not (variant[0] in digits and 8 >= len(variant) >= 4):
                    err = ValueError(f'Variant subtag "{variant}" is not valid.')

                # RFC 5646 section 2.2.5.5
                if variant in checked:
                    err = ValueError(f'Variant subtag "{variant}" is repeated.')

                checked.append(variant)
                sub_tags.append(variant)

        if extensions is not None:
            checked = []
            for singleton, extension in extensions:
                extension = extension.lower()

                if not (len(singleton) == 1 and (singleton in digits or singleton in ascii_letters)):
                    err = ValueError(f'Singleton subtag "{singleton}" is not valid.')

                # RFC 5646 section 2.2.6.3
                if singleton in checked:
                    err = ValueError(f'Singleton subtag "{singleton}" is repeated.')

                # RFC 5646 section 2.2.6.5
                if not (extension.isalnum() and 8 >= len(extension) >= 2):
                    err = ValueError(f'Extension subtag "{extension}" is not valid.')

                checked.append(singleton)
                sub_tags.extend((singleton, extension))

        if private_use is not None:
            sub_tags.append('x')
            for i, private_sub_tag in enumerate(private_use):
                private_sub_tag = private_sub_tag.lower()

                # If previous subtag was not a singleton
                if i != 0 and len(private_use[i - 1]) != 1:
                    if len(private_sub_tag) == 4:
                        private_sub_tag = private_sub_tag.title()
                    elif len(private_sub_tag) == 2:
                        private_sub_tag = private_sub_tag.upper()

                if not (private_sub_tag.isalnum() and 8 >= len(private_sub_tag) >= 1):
                    err = ValueError(f'The private subtag "{private_sub_tag}" is not valid.')

                sub_tags.append(private_sub_tag)

        self.tag = '-'.join(sub_tags)

        if err is not None:
            raise ValueError(str(err)[:-1] + f' in language tag "{self.tag}".') from err

        for lang_file in LANG_PATH.iterdir():
            if lang_file.suffix == '.json' and lang_file.with_suffix('').name.lower() == self.tag.replace('-', '_').lower():
                # TODO: Find closest related language file. Ex: en-EN would find en_us.json if en_en.json does not exist.
                new_data = json.loads(lang_file.read_text(encoding='utf8'))
                self._data.update(new_data)
                break

    def __repr__(self) -> str:
        return f'<Language data for {self.tag}>'

    def __getitem__(self, key) -> str:
        return self.get_raw(key)

    @classmethod
    def from_tag(cls, tag: str) -> 'Language':
        """Build a :py:class:`Language` object using a plain string tag.

        Breaks tag into sub-tags and verifies compliance with RFC 5646.
        """
        # TODO: Add functionality

    def get(self, key: str, *args: Any, default: str | None = None) -> str:
        """Get a translation key and format with the given arguments if required.

        :param key: Key to get in JSON data.
        :param args: Formatting arguments; packed into tuple and used with str modulus.
        :param default: Default string if key doesn't exist. (Is not formatted)
        """
        # Default value is key if not overridden
        default = default if default is not None else key
        result: str = self._data.get(key, default)

        if result is not default:
            return format_value(result, *args, _language=self)
        else:
            # Dont format default value
            quote = '"'
            for arg in (f'%{str(arg) if not isinstance(arg, str) else quote + arg + quote}%' for arg in args):
                result += arg

        return result

    def get_raw(self, key: str) -> str:
        """Get raw result, no formatting or defaults.

        :raises KeyError: If key is not in JSON data.
        """
        return self._data[key]


class Translator:
    """Simple class meant to abstract key translation into a function-like state.

    Usage::
        translate = Translator('en-US')
        translate('a.translation.key') -> american value
        translate.language = 'de-GER'
        translate('a.translation.key') -> german value
    """

    def __init__(self, language: Language | str) -> None:
        self._language = self._lang_to_lang(language)

    def __bool__(self) -> bool:
        """Return whether the Translator is available."""
        return True

    def __call__(self, key: str, *args: Any, **kwargs) -> str:
        """Syntax sugar for get_translation."""
        return self.get_translation(key, *args, **kwargs)

    @property
    def language(self) -> Language:
        """Current :py:class:`Language` for this translator."""
        return self._language

    @language.setter
    def language(self, value: Language | str) -> None:
        self._language = self._lang_to_lang(value)

    def get_translation(self, key: str, *args: Any, default: str | None = None) -> str:
        """Get a translation key's value for the current language."""
        return self.language.get(key, *args, default=default)

    @contextmanager
    def as_language(self, language: Language | str) -> AbstractContextManager[None]:
        """Temporarily translate for a specific language using a context manager."""
        # __enter__
        old_lang = self._language
        self.language = language
        yield

        # __exit__
        self._language = old_lang

    @staticmethod
    def _lang_to_lang(language: Language | str) -> Language:
        """Assert that a given value is a :py:class:`Language`."""
        if not isinstance(language, Language):
            language = str(language)  # Stringify non-language object

        if isinstance(language, str):
            # TODO: Move this to Language.from_tag
            language = language.replace(' ', '-').replace('_', '-').strip()
            language = Language(*language.split('-'))  # For basic primary and region subtag compilation (ex: 'en-US' -> primary: 'en', region: 'US')
        return language
