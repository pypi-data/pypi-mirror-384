import base64
import hashlib
import html
import json
import os
import re
import unicodedata
import urllib.parse
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

class Stringable(str):

    def after(self, search: str) -> "Stringable":
        """
        Return the substring after the first occurrence of a given value.

        Searches for the first occurrence of the specified substring and returns everything that comes after it. If the substring is not found, returns the original string unchanged.

        Parameters
        ----------
        search : str
            Substring to search for within the current string.

        Returns
        -------
        Stringable
            New Stringable instance containing the substring after the first occurrence of the search string, or the original string if not found.
        """

        # Find the index of the first occurrence of the search string
        idx = self.find(search)

        # If found, return substring after the search string
        # Otherwise, return the original string
        return Stringable(self[idx + len(search):]) if idx != -1 else Stringable(self)

    def afterLast(self, search: str) -> "Stringable":
        """
        Return the substring after the last occurrence of a given value.

        Searches for the last occurrence of the specified substring and returns everything that comes after it. If the substring is not found, returns the original string unchanged.

        Parameters
        ----------
        search : str
            Substring to search for within the current string.

        Returns
        -------
        Stringable
            New Stringable instance containing the substring after the last occurrence of the search string, or the original string if not found.
        """

        # Find the index of the last occurrence of the search string
        idx = self.rfind(search)

        # If found, return substring after the search string
        # Otherwise, return the original string
        return Stringable(self[idx + len(search):]) if idx != -1 else Stringable(self)

    def append(self, *values: str) -> "Stringable":
        """
        Append one or more values to the end of the string.

        Concatenates the provided string values to the end of the current string, returning a new Stringable instance.

        Parameters
        ----------
        *values : str
            One or more string values to append.

        Returns
        -------
        Stringable
            New Stringable instance with all provided values appended to the end.
        """

        # Join all provided values and append them to the current string
        return Stringable(self + "".join(values))

    def newLine(self, count: int = 1) -> "Stringable":
        """
        Append one or more newline characters to the string.

        Appends the specified number of newline characters (\n) to the end of the current string.

        Parameters
        ----------
        count : int, optional
            Number of newline characters to append. Default is 1.

        Returns
        -------
        Stringable
            New Stringable instance with the specified number of newline characters appended.
        """

        # Append the specified number of newline characters to the current string
        return Stringable(str(self) + "\n" * count)

    def before(self, search: str) -> "Stringable":
        """
        Return the substring before the first occurrence of a given value.

        Searches for the first occurrence of the specified substring and returns everything before it. If the substring is not found, returns the original string unchanged.

        Parameters
        ----------
        search : str
            Substring to search for within the current string.

        Returns
        -------
        Stringable
            New Stringable instance containing the substring before the first occurrence of the search string, or the original string if not found.
        """

        # Find the index of the first occurrence of the search string
        idx = self.find(search)

        # If found, return substring before the search string
        # Otherwise, return the original string
        return Stringable(self[:idx]) if idx != -1 else Stringable(self)

    def beforeLast(self, search: str) -> "Stringable":
        """
        Return the substring before the last occurrence of a given value.

        Searches for the last occurrence of the specified substring and returns everything before it. If the substring is not found, returns the original string unchanged.

        Parameters
        ----------
        search : str
            Substring to search for within the current string.

        Returns
        -------
        Stringable
            New Stringable instance containing the substring before the last occurrence of the search string, or the original string if not found.
        """

        # Find the index of the last occurrence of the search string
        idx = self.rfind(search)

        # If found, return substring before the search string
        # Otherwise, return the original string
        return Stringable(self[:idx]) if idx != -1 else Stringable(self)

    def contains(self, needles: Union[str, Iterable[str]], ignore_case: bool = False) -> bool:
        """
        Check if the string contains any of the given values.

        Determines whether the string contains any of the specified needle values. The search can be performed case-sensitively or case-insensitively.

        Parameters
        ----------
        needles : str or Iterable[str]
            Value or values to search for within the string.
        ignore_case : bool, optional
            If True, perform case-insensitive search. Default is False.

        Returns
        -------
        bool
            True if the string contains any of the needle values, False otherwise.
        """

        # Normalize needles to a list for consistent processing
        if isinstance(needles, str):
            needles = [needles]

        # Convert to lowercase for case-insensitive comparison if requested
        s = str(self).lower() if ignore_case else str(self)

        # Check if any needle is found in the string
        return any((needle.lower() if ignore_case else needle) in s for needle in needles)

    def endsWith(self, needles: Union[str, Iterable[str]]) -> bool:
        """
        Check if the string ends with any of the given substrings.

        Determines whether the string ends with any of the specified needle values.

        Parameters
        ----------
        needles : str or Iterable[str]
            Substring or substrings to check at the end of the string.

        Returns
        -------
        bool
            True if the string ends with any of the needle values, False otherwise.
        """

        # Normalize needles to a list for consistent processing
        if isinstance(needles, str):
            needles = [needles]

        # Check if string ends with any of the provided needles
        return any(str(self).endswith(needle) for needle in needles)

    def exactly(self, value: Any) -> bool:
        """
        Check if the string is exactly equal to a given value.

        Performs a strict equality comparison between the string and the provided value after converting both to string representations.

        Parameters
        ----------
        value : Any
            Value to compare against the current string.

        Returns
        -------
        bool
            True if the string exactly matches the given value, False otherwise.
        """

        # Convert both values to strings and compare for exact equality
        return str(self) == str(value)

    def isEmpty(self) -> bool:
        """
        Check if the string is empty.

        Determines if the string has zero length, meaning it contains no characters.

        Returns
        -------
        bool
            True if the string is empty, False otherwise.
        """

        # Return True if the string has zero length
        return len(self) == 0

    def isNotEmpty(self) -> bool:
        """
        Check if the string is not empty.

        Determines if the string has one or more characters, meaning it contains some content.

        Returns
        -------
        bool
            True if the string is not empty, False otherwise.
        """

        # Return True if the string has one or more characters
        return not self.isEmpty()

    def lower(self) -> "Stringable":
        """
        Convert the string to lowercase.

        Returns
        -------
        Stringable
            New Stringable instance with all characters converted to lowercase.
        """

        # Convert all characters to lowercase using the built-in method
        return Stringable(super().lower())

    def upper(self) -> "Stringable":
        """
        Convert the string to uppercase.

        Returns
        -------
        Stringable
            New Stringable instance with all characters converted to uppercase.
        """

        # Convert all characters to uppercase using the built-in method
        return Stringable(super().upper())

    def reverse(self) -> "Stringable":
        """
        Reverse the string.

        Returns
        -------
        Stringable
            New Stringable instance with characters in reverse order.
        """

        # Reverse the string using slicing
        return Stringable(self[::-1])

    def repeat(self, times: int) -> "Stringable":
        """
        Repeat the string a specified number of times.

        Parameters
        ----------
        times : int
            Number of times to repeat the string.

        Returns
        -------
        Stringable
            New Stringable instance with the string repeated the specified number of times.
        """

        # Repeat the string using multiplication
        return Stringable(self * times)

    def replace(self, search: Union[str, Iterable[str]], replace: Union[str, Iterable[str]], case_sensitive: bool = True) -> "Stringable":
        """
        Replace occurrences of specified substrings with corresponding replacements.

        Replaces each substring in `search` with the corresponding value in `replace`. If `search` or `replace` is a single string, it is converted to a list for uniform processing. The replacement can be performed case-sensitively or case-insensitively.

        Parameters
        ----------
        search : str or Iterable[str]
            Substring(s) to search for in the string.
        replace : str or Iterable[str]
            Replacement string(s) for each search substring.
        case_sensitive : bool, optional
            If True, perform case-sensitive replacement. Default is True.

        Returns
        -------
        Stringable
            New Stringable instance with the specified replacements applied.
        """

        # Convert search and replace to lists for consistent processing
        s = self
        if isinstance(search, str):
            search = [search]
        if isinstance(replace, str):
            replace = [replace] * len(search)

        # Iterate through each search-replace pair and apply replacement
        for src, rep in zip(search, replace):

            # Case-sensitive replacement using str.replace
            if case_sensitive:
                s = str(s).replace(src, rep)
            # Case-insensitive replacement using re.sub with IGNORECASE
            else:
                s = re.sub(re.escape(src), rep, str(s), flags=re.IGNORECASE)

        # Return a new Stringable instance with replacements
        return Stringable(s)

    def stripTags(self, allowed_tags: Optional[str] = None) -> "Stringable":
        """
        Remove HTML and PHP tags from the string.

        Parameters
        ----------
        allowed_tags : str, optional
            Tags that should not be stripped. Default is None.

        Returns
        -------
        Stringable
            New Stringable with tags removed.
        """

        # If allowed_tags is specified, use a simple unescape (not full PHP compatibility)
        if allowed_tags:
            return Stringable(html.unescape(str(self)))
        # Otherwise, remove all tags using regex
        else:
            return Stringable(re.sub(r'<[^>]*>', '', str(self)))

    def toBase64(self) -> "Stringable":
        """
        Encode the string to Base64.

        Returns
        -------
        Stringable
            New Stringable with Base64 encoded content.
        """

        # Encode the string to Base64
        return Stringable(base64.b64encode(str(self).encode()).decode())

    def fromBase64(self, strict: bool = False) -> "Stringable":
        """
        Decode the string from Base64.

        Parameters
        ----------
        strict : bool, optional
            If True, raise exception on decode errors. Default is False.

        Returns
        -------
        Stringable
            New Stringable with Base64 decoded content, or empty string if decoding fails and strict is False.
        """

        # Try to decode the string from Base64
        try:
            return Stringable(base64.b64decode(str(self).encode()).decode())
        except Exception:
            if strict:
                raise
            # Return empty string if decoding fails and strict is False
            return Stringable("")

    def md5(self) -> str:
        """
        Generate MD5 hash of the string.

        Returns
        -------
        str
            MD5 hash of the string.
        """

        # Generate MD5 hash using hashlib
        return hashlib.md5(str(self).encode()).hexdigest()

    def sha1(self) -> str:
        """
        Generate SHA1 hash of the string.

        Returns
        -------
        str
            SHA1 hash of the string.
        """

        # Generate SHA1 hash using hashlib
        return hashlib.sha1(str(self).encode()).hexdigest()

    def sha256(self) -> str:
        """
        Generate SHA256 hash of the string.

        Returns
        -------
        str
            SHA256 hash of the string.
        """

        # Generate SHA256 hash using hashlib
        return hashlib.sha256(str(self).encode()).hexdigest()

    def length(self) -> int:
        """
        Get the length of the string.

        Returns
        -------
        int
            Number of characters in the string.
        """

        # Return the length of the string
        return len(self)

    def value(self) -> str:
        """
        Get the string value.

        Returns
        -------
        str
            String representation of the current instance.
        """

        # Return the string representation
        return str(self)

    def toString(self) -> str:
        """
        Convert the Stringable to a string.

        Returns
        -------
        str
            String representation of the current instance.
        """

        # Return the string representation
        return str(self)

    def toInteger(self, base: int = 10) -> int:
        """
        Convert the string to an integer.

        Parameters
        ----------
        base : int, optional
            Base for conversion. Default is 10.

        Returns
        -------
        int
            Integer representation of the string.
        """

        # Convert the string to integer using the specified base
        return int(self, base)

    def toFloat(self) -> float:
        """
        Convert the string to a float.

        Returns
        -------
        float
            Float representation of the string.
        """

        # Convert the string to float
        return float(self)

    def toBoolean(self) -> bool:
        """
        Convert the string to a boolean.

        The string is considered True if it matches common truthy values like "1", "true", "on", or "yes" (case-insensitive).

        Returns
        -------
        bool
            Boolean representation of the string.
        """

        # Check for common truthy values
        return str(self).strip().lower() in ("1", "true", "on", "yes")

    def __getitem__(self, key):
        """
        Get item by index or slice.

        Parameters
        ----------
        key : int or slice
            Index or slice to retrieve.

        Returns
        -------
        Stringable
            New Stringable instance for the selected item(s).
        """

        # Return a Stringable for the selected item(s)
        return Stringable(super().__getitem__(key))

    def __str__(self):
        """
        Get the string representation.

        Returns
        -------
        str
            String representation of the object.
        """

        # Return the string representation
        return super().__str__()

    def isAlnum(self) -> bool:
        """
        Check if all characters in the string are alphanumeric.

        Returns
        -------
        bool
            True if all characters are alphanumeric, False otherwise.
        """

        # Check if all characters are alphanumeric
        return str(self).isalnum()

    def isAlpha(self) -> bool:
        """
        Check if all characters in the string are alphabetic.

        Returns
        -------
        bool
            True if all characters are alphabetic, False otherwise.
        """

        # Check if all characters are alphabetic
        return str(self).isalpha()

    def isDecimal(self) -> bool:
        """
        Check if all characters in the string are decimal characters.

        Returns
        -------
        bool
            True if all characters are decimal, False otherwise.
        """

        # Check if all characters are decimal
        return str(self).isdecimal()

    def isDigit(self) -> bool:
        """
        Check if all characters in the string are digits.

        Returns
        -------
        bool
            True if all characters are digits, False otherwise.
        """

        # Check if all characters are digits
        return str(self).isdigit()

    def isIdentifier(self) -> bool:
        """
        Check if the string is a valid identifier according to Python language definition.

        Returns
        -------
        bool
            True if string is a valid identifier, False otherwise.
        """

        # Check if the string is a valid identifier
        return str(self).isidentifier()

    def isLower(self) -> bool:
        """
        Check if all cased characters in the string are lowercase.

        Returns
        -------
        bool
            True if all cased characters are lowercase, False otherwise.
        """

        # Check if all cased characters are lowercase
        return str(self).islower()

    def isNumeric(self) -> bool:
        """
        Check if all characters in the string are numeric characters.

        Returns
        -------
        bool
            True if all characters are numeric, False otherwise.
        """

        # Check if all characters are numeric
        return str(self).isnumeric()

    def isPrintable(self) -> bool:
        """
        Check if all characters in the string are printable.

        Returns
        -------
        bool
            True if all characters are printable, False otherwise.
        """

        # Check if all characters are printable
        return str(self).isprintable()

    def isSpace(self) -> bool:
        """
        Check if there are only whitespace characters in the string.

        Returns
        -------
        bool
            True if string contains only whitespace, False otherwise.
        """

        # Check if the string contains only whitespace
        return str(self).isspace()

    def isTitle(self) -> bool:
        """
        Check if the string is a titlecased string.

        Returns
        -------
        bool
            True if string is titlecased, False otherwise.
        """

        # Check if the string is titlecased
        return str(self).istitle()

    def isUpper(self) -> bool:
        """
        Check if all cased characters in the string are uppercase.

        Returns
        -------
        bool
            True if all cased characters are uppercase, False otherwise.
        """

        # Check if all cased characters are uppercase
        return str(self).isupper()

    def lStrip(self, chars: Optional[str] = None) -> "Stringable":
        """
        Return a copy of the string with leading characters removed.

        Removes leading characters from the left side of the string. If no characters
        are specified, whitespace characters are removed by default.

        Parameters
        ----------
        chars : str, optional
            Characters to remove from the beginning, by default None (whitespace).

        Returns
        -------
        Stringable
            A new Stringable instance with leading characters removed.
        """

        # Use Python's built-in lstrip to remove leading characters
        return Stringable(str(self).lstrip(chars))

    def rStrip(self, chars: Optional[str] = None) -> "Stringable":
        """
        Return a copy of the string with trailing characters removed.

        Removes trailing characters from the right side of the string. If no characters
        are specified, whitespace characters are removed by default.

        Parameters
        ----------
        chars : str, optional
            Characters to remove from the end, by default None (whitespace).

        Returns
        -------
        Stringable
            A new Stringable instance with trailing characters removed.
        """

        # Use Python's built-in rstrip to remove trailing characters
        return Stringable(str(self).rstrip(chars))

    def swapCase(self) -> "Stringable":
        """
        Return a copy of the string with uppercase characters converted to lowercase and vice versa.

        Converts each uppercase character to lowercase and each lowercase character 
        to uppercase, leaving other characters unchanged.

        Returns
        -------
        Stringable
            A new Stringable instance with all character cases swapped.
        """

        # Use Python's built-in swapcase to invert the case of all characters
        return Stringable(str(self).swapcase())

    def zFill(self, width: int) -> "Stringable":
        """
        Pad a numeric string with zeros on the left.

        Fills the string with leading zeros to reach the specified width. The sign 
        of the number (if any) is handled properly by being placed before the zeros.

        Parameters
        ----------
        width : int
            Total width of the resulting string.

        Returns
        -------
        Stringable
            A new Stringable instance padded with leading zeros to the specified width.
        """

        # Use Python's built-in zfill to pad with zeros while preserving sign
        return Stringable(str(self).zfill(width))

    def ascii(self, language: str = 'en') -> "Stringable":
        """
        Transliterate a UTF-8 value to ASCII.

        Parameters
        ----------
        language : str, optional
            The language for transliteration, by default 'en'

        Returns
        -------
        Stringable
            A new Stringable with ASCII characters
        """
        # Use unicodedata to normalize and transliterate
        normalized = unicodedata.normalize('NFKD', self)
        ascii_str = ''.join(c for c in normalized if ord(c) < 128)
        return Stringable(ascii_str)

    def camel(self) -> "Stringable":
        """
        Convert a value to camel case.

        Returns
        -------
        Stringable
            A new Stringable in camelCase
        """
        # Split by common separators and normalize
        words = re.sub(r'[_\-\s]+', ' ', str(self)).split()
        if not words:
            return Stringable("")

        # First word lowercase, rest title case
        camel_str = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
        return Stringable(camel_str)

    def kebab(self) -> "Stringable":
        """
        Convert a string to kebab case.

        Returns
        -------
        Stringable
            A new Stringable in kebab-case
        """
        # Handle camelCase and PascalCase
        s = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', str(self))
        # Replace spaces, underscores, and multiple dashes with single dash
        s = re.sub(r'[_\s]+', '-', s)
        s = re.sub(r'-+', '-', s)
        return Stringable(s.lower().strip('-'))

    def snake(self, delimiter: str = '_') -> "Stringable":
        """
        Convert a string to snake case.

        Parameters
        ----------
        delimiter : str, optional
            The delimiter to use, by default '_'

        Returns
        -------
        Stringable
            A new Stringable in snake_case
        """
        # Handle camelCase and PascalCase
        s = re.sub(r'([a-z0-9])([A-Z])', rf'\1{delimiter}\2', str(self))
        # Replace spaces and dashes with delimiter
        s = re.sub(r'[\s\-]+', delimiter, s)
        # Replace multiple delimiters with single
        s = re.sub(rf'{re.escape(delimiter)}+', delimiter, s)
        return Stringable(s.lower().strip(delimiter))

    def studly(self) -> "Stringable":
        """
        Convert a value to studly caps case (PascalCase).

        Returns
        -------
        Stringable
            A new Stringable in StudlyCase/PascalCase
        """
        words = re.sub(r'[_\-\s]+', ' ', str(self)).split()
        studly_str = ''.join(word.capitalize() for word in words)
        return Stringable(studly_str)

    def pascal(self) -> "Stringable":
        """
        Convert the string to Pascal case.

        Returns
        -------
        Stringable
            A new Stringable in PascalCase
        """
        return self.studly()

    def slug(self, separator: str = '-', dictionary: Optional[Dict[str, str]] = None) -> "Stringable":
        """
        Generate a URL friendly "slug" from a given string.

        Parameters
        ----------
        separator : str, optional
            The separator to use, by default '-'
        dictionary : dict, optional
            Dictionary for character replacements, by default {'@': 'at'}

        Returns
        -------
        Stringable
            A new Stringable as a URL-friendly slug
        """
        if dictionary is None:
            dictionary = {'@': 'at'}

        s = str(self)

        # Apply dictionary replacements
        for key, value in dictionary.items():
            s = s.replace(key, value)

        # Convert to ASCII
        s = self.__class__(s).ascii().value()

        # Remove all non-alphanumeric characters except spaces and separators
        s = re.sub(r'[^\w\s-]', '', s)

        # Replace spaces and underscores with separator
        s = re.sub(r'[\s_]+', separator, s)

        # Replace multiple separators with single
        s = re.sub(rf'{re.escape(separator)}+', separator, s)

        return Stringable(s.lower().strip(separator))

    def title(self) -> "Stringable":
        """
        Convert the given string to proper case.

        Returns
        -------
        Stringable
            A new Stringable in Title Case
        """
        return Stringable(str(self).title())

    def headline(self) -> "Stringable":
        """
        Convert the given string to proper case for each word.

        Returns
        -------
        Stringable
            A new Stringable as a headline
        """
        # Split by common word boundaries
        words = re.findall(r'\b\w+\b', str(self))
        headline_str = ' '.join(word.capitalize() for word in words)
        return Stringable(headline_str)

    def apa(self) -> "Stringable":
        """
        Convert the given string to APA-style title case.

        Returns
        -------
        Stringable
            A new Stringable in APA title case
        """
        # Words that should not be capitalized in APA style (except at beginning)
        lowercase_words = {
            'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in',
            'nor', 'of', 'on', 'or', 'so', 'the', 'to', 'up', 'yet'
        }

        words = str(self).split()
        apa_words = []

        for i, word in enumerate(words):
            # Always capitalize first and last word
            if i == 0 or i == len(words) - 1:
                apa_words.append(word.capitalize())
            # Capitalize words with 4+ letters or not in lowercase set
            elif len(word) >= 4 or word.lower() not in lowercase_words:
                apa_words.append(word.capitalize())
            else:
                apa_words.append(word.lower())

        return Stringable(' '.join(apa_words))

    def ucfirst(self) -> "Stringable":
        """
        Make a string's first character uppercase.

        Returns
        -------
        Stringable
            A new Stringable with first character uppercase
        """
        if not self:
            return Stringable(self)
        return Stringable(self[0].upper() + self[1:])

    def lcfirst(self) -> "Stringable":
        """
        Make a string's first character lowercase.

        Returns
        -------
        Stringable
            A new Stringable with first character lowercase
        """
        if not self:
            return Stringable(self)
        return Stringable(self[0].lower() + self[1:])

    def isAscii(self) -> bool:
        """
        Determine if a given string is 7 bit ASCII.

        Returns
        -------
        bool
            True if string is ASCII, False otherwise
        """
        try:
            self.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    def isJson(self) -> bool:
        """
        Determine if a given string is valid JSON.

        Returns
        -------
        bool
            True if string is valid JSON, False otherwise
        """
        try:
            json.loads(str(self))
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    def isUrl(self, protocols: Optional[List[str]] = None) -> bool:
        """
        Determine if a given value is a valid URL.

        Parameters
        ----------
        protocols : list, optional
            List of valid protocols, by default ['http', 'https']

        Returns
        -------
        bool
            True if string is a valid URL, False otherwise
        """
        if protocols is None:
            protocols = ['http', 'https']

        try:
            result = urllib.parse.urlparse(str(self))
            return (
                all([result.scheme, result.netloc]) and
                result.scheme in protocols
            )
        except Exception:
            return False

    def isUuid(self, version: Optional[Union[int, str]] = None) -> bool:
        """
        Determine if a given string is a valid UUID.

        Parameters
        ----------
        version : int or str, optional
            UUID version to validate (1-8), by default None (any version)

        Returns
        -------
        bool
            True if string is a valid UUID, False otherwise
        """
        try:
            uuid_obj = uuid.UUID(str(self))
            if version is not None:
                if version == 'max':
                    return uuid_obj.version <= 8
                else:
                    return uuid_obj.version == int(version)
            return True
        except (ValueError, TypeError):
            return False

    def isUlid(self) -> bool:
        """
        Determine if a given string is a valid ULID.

        Returns
        -------
        bool
            True if string is a valid ULID, False otherwise
        """
        # ULID is 26 characters, base32 encoded
        ulid_pattern = r'^[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}$'
        return bool(re.match(ulid_pattern, str(self).upper()))

    def chopStart(self, needle: Union[str, List[str]]) -> "Stringable":
        """
        Remove the given string if it exists at the start of the current string.

        Parameters
        ----------
        needle : str or list
            The string(s) to remove from the start

        Returns
        -------
        Stringable
            A new Stringable with the needle removed from start
        """
        s = str(self)
        if isinstance(needle, str):
            needle = [needle]

        for n in needle:
            if s.startswith(n):
                s = s[len(n):]
                break

        return Stringable(s)

    def chopEnd(self, needle: Union[str, List[str]]) -> "Stringable":
        """
        Remove the given string if it exists at the end of the current string.

        Parameters
        ----------
        needle : str or list
            The string(s) to remove from the end

        Returns
        -------
        Stringable
            A new Stringable with the needle removed from end
        """
        s = str(self)
        if isinstance(needle, str):
            needle = [needle]

        for n in needle:
            if s.endswith(n):
                s = s[:-len(n)]
                break

        return Stringable(s)

    def deduplicate(self, character: str = ' ') -> "Stringable":
        """
        Replace consecutive instances of a given character with a single character.

        Parameters
        ----------
        character : str, optional
            The character to deduplicate, by default ' '

        Returns
        -------
        Stringable
            A new Stringable with deduplicated characters
        """
        pattern = re.escape(character) + '+'
        return Stringable(re.sub(pattern, character, str(self)))

    def mask(self, character: str, index: int, length: Optional[int] = None) -> "Stringable":
        """
        Masks a portion of a string with a repeated character.

        Parameters
        ----------
        character : str
            The character to use for masking
        index : int
            Starting index for masking
        length : int, optional
            Length to mask, by default None (to end of string)

        Returns
        -------
        Stringable
            A new Stringable with masked portion
        """
        s = str(self)

        if index < 0:
            index = max(0, len(s) + index)

        if length is None:
            length = len(s) - index
        elif length < 0:
            length = max(0, len(s) + length - index)

        end_index = min(len(s), index + length)
        mask_str = character * (end_index - index)

        return Stringable(s[:index] + mask_str + s[end_index:])

    def limit(self, limit: int = 100, end: str = '...', preserve_words: bool = False) -> "Stringable":
        """
        Limit the number of characters in a string.

        Parameters
        ----------
        limit : int, optional
            Maximum number of characters, by default 100
        end : str, optional
            String to append if truncated, by default '...'
        preserve_words : bool, optional
            Whether to preserve word boundaries, by default False

        Returns
        -------
        Stringable
            A new Stringable with limited length
        """
        s = str(self)

        if len(s) <= limit:
            return Stringable(s)

        if preserve_words:
            # Find the last space before the limit
            truncated = s[:limit]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
        else:
            truncated = s[:limit]

        return Stringable(truncated + end)

    def padBoth(self, length: int, pad: str = ' ') -> "Stringable":
        """
        Pad both sides of the string with another.

        Parameters
        ----------
        length : int
            Total desired length
        pad : str, optional
            Padding character(s), by default ' '

        Returns
        -------
        Stringable
            A new Stringable with padding on both sides
        """
        s = str(self)
        if len(s) >= length:
            return Stringable(s)

        total_padding = length - len(s)
        left_padding = total_padding // 2
        right_padding = total_padding - left_padding

        left_pad = (pad * ((left_padding // len(pad)) + 1))[:left_padding]
        right_pad = (pad * ((right_padding // len(pad)) + 1))[:right_padding]

        return Stringable(left_pad + s + right_pad)

    def padLeft(self, length: int, pad: str = ' ') -> "Stringable":
        """
        Pad the left side of the string with another.

        Parameters
        ----------
        length : int
            Total desired length
        pad : str, optional
            Padding character(s), by default ' '

        Returns
        -------
        Stringable
            A new Stringable with left padding
        """
        s = str(self)
        if len(s) >= length:
            return Stringable(s)

        padding_needed = length - len(s)
        left_pad = (pad * ((padding_needed // len(pad)) + 1))[:padding_needed]

        return Stringable(left_pad + s)

    def padRight(self, length: int, pad: str = ' ') -> "Stringable":
        """
        Pad the right side of the string with another.

        Parameters
        ----------
        length : int
            Total desired length
        pad : str, optional
            Padding character(s), by default ' '

        Returns
        -------
        Stringable
            A new Stringable with right padding
        """
        s = str(self)
        if len(s) >= length:
            return Stringable(s)

        padding_needed = length - len(s)
        right_pad = (pad * ((padding_needed // len(pad)) + 1))[:padding_needed]

        return Stringable(s + right_pad)

    def trim(self, characters: Optional[str] = None) -> "Stringable":
        """
        Trim the string of the given characters.

        Parameters
        ----------
        characters : str, optional
            Characters to trim, by default None (whitespace)

        Returns
        -------
        Stringable
            A new trimmed Stringable
        """
        return Stringable(str(self).strip(characters))

    def ltrim(self, characters: Optional[str] = None) -> "Stringable":
        """
        Left trim the string of the given characters.

        Parameters
        ----------
        characters : str, optional
            Characters to trim, by default None (whitespace)

        Returns
        -------
        Stringable
            A new left-trimmed Stringable
        """
        return Stringable(str(self).lstrip(characters))

    def rtrim(self, characters: Optional[str] = None) -> "Stringable":
        """
        Right trim the string of the given characters.

        Parameters
        ----------
        characters : str, optional
            Characters to trim, by default None (whitespace)

        Returns
        -------
        Stringable
            A new right-trimmed Stringable
        """
        return Stringable(str(self).rstrip(characters))

    def charAt(self, index: int) -> Union[str, bool]:
        """
        Get the character at the specified index.

        Parameters
        ----------
        index : int
            The index of the character to get

        Returns
        -------
        str or False
            The character at the index, or False if index is out of bounds
        """
        try:
            return str(self)[index]
        except IndexError:
            return False

    def position(self, needle: str, offset: int = 0, encoding: Optional[str] = None) -> Union[int, bool]:
        """
        Find the multi-byte safe position of the first occurrence of the given substring.

        Parameters
        ----------
        needle : str
            The substring to search for
        offset : int, optional
            Starting offset for search, by default 0
        encoding : str, optional
            String encoding (for compatibility), by default None

        Returns
        -------
        int or False
            Position of the substring, or False if not found
        """
        try:
            pos = str(self).find(needle, offset)
            return pos if pos != -1 else False
        except Exception:
            return False

    def match(self, pattern: str) -> "Stringable":
        """
        Get the string matching the given pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern

        Returns
        -------
        Stringable
            A new Stringable with the first match, or empty if no match
        """
        match = re.search(pattern, str(self))
        return Stringable(match.group(0) if match else "")

    def matchAll(self, pattern: str) -> List[str]:
        """
        Get all strings matching the given pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern

        Returns
        -------
        list
            List of all matches
        """
        return re.findall(pattern, str(self))

    def isMatch(self, pattern: Union[str, List[str]]) -> bool:
        """
        Determine if a given string matches a given pattern.

        Parameters
        ----------
        pattern : str or list
            Regular expression pattern(s)

        Returns
        -------
        bool
            True if string matches pattern, False otherwise
        """
        if isinstance(pattern, str):
            pattern = [pattern]

        s = str(self)
        return any(re.search(p, s) is not None for p in pattern)

    def test(self, pattern: str) -> bool:
        """
        Determine if the string matches the given pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern

        Returns
        -------
        bool
            True if string matches pattern, False otherwise
        """
        return self.isMatch(pattern)

    def numbers(self) -> "Stringable":
        """
        Remove all non-numeric characters from a string.

        Returns
        -------
        Stringable
            A new Stringable with only numeric characters
        """
        return Stringable(re.sub(r'\D', '', str(self)))

    def excerpt(self, phrase: str = '', options: Optional[Dict] = None) -> Optional[str]:
        """
        Extracts an excerpt from text that matches the first instance of a phrase.

        Parameters
        ----------
        phrase : str, optional
            The phrase to search for, by default ''
        options : dict, optional
            Options for excerpt extraction, by default None

        Returns
        -------
        str or None
            The excerpt, or None if phrase not found
        """
        if options is None:
            options = {}

        radius = options.get('radius', 100)
        omission = options.get('omission', '...')

        s = str(self)
        if not phrase:
            return s[:radius * 2] + (omission if len(s) > radius * 2 else '')

        pos = s.lower().find(phrase.lower())
        if pos == -1:
            return None

        start = max(0, pos - radius)
        end = min(len(s), pos + len(phrase) + radius)

        excerpt = s[start:end]

        if start > 0:
            excerpt = omission + excerpt
        if end < len(s):
            excerpt = excerpt + omission

        return excerpt

    def basename(self, suffix: str = '') -> "Stringable":
        """
        Get the trailing name component of the path.

        Parameters
        ----------
        suffix : str, optional
            Suffix to remove, by default ''

        Returns
        -------
        Stringable
            A new Stringable with the basename
        """
        return Stringable(os.path.basename(str(self)).removesuffix(suffix))

    def dirname(self, levels: int = 1) -> "Stringable":
        """
        Get the parent directory's path.

        Parameters
        ----------
        levels : int, optional
            Number of levels up, by default 1

        Returns
        -------
        Stringable
            A new Stringable with the directory name
        """
        path = str(self)
        for _ in range(levels):
            path = os.path.dirname(path)
        return Stringable(path)

    def classBasename(self) -> "Stringable":
        """
        Get the basename of the class path.

        Returns
        -------
        Stringable
            A new Stringable with the class basename
        """
        # Extract the last part after the last dot (class name)
        parts = str(self).split('.')
        return Stringable(parts[-1] if parts else str(self))

    def between(self, from_str: str, to_str: str) -> "Stringable":
        """
        Get the portion of a string between two given values.

        Parameters
        ----------
        from_str : str
            Starting delimiter
        to_str : str
            Ending delimiter

        Returns
        -------
        Stringable
            A new Stringable with the text between delimiters
        """
        s = str(self)
        start = s.find(from_str)
        if start == -1:
            return Stringable("")

        start += len(from_str)
        end = s.find(to_str, start)
        if end == -1:
            return Stringable("")

        return Stringable(s[start:end])

    def betweenFirst(self, from_str: str, to_str: str) -> "Stringable":
        """
        Get the smallest possible portion of a string between two given values.

        Parameters
        ----------
        from_str : str
            Starting delimiter
        to_str : str
            Ending delimiter

        Returns
        -------
        Stringable
            A new Stringable with the text between first delimiters
        """
        s = str(self)
        start = s.find(from_str)
        if start == -1:
            return Stringable("")

        start += len(from_str)
        end = s.find(to_str, start)
        if end == -1:
            return Stringable("")

        return Stringable(s[start:end])

    def finish(self, cap: str) -> "Stringable":
        """
        Cap a string with a single instance of a given value.

        Parameters
        ----------
        cap : str
            The string to cap with

        Returns
        -------
        Stringable
            A new Stringable that ends with the cap
        """
        s = str(self)
        if not s.endswith(cap):
            s += cap
        return Stringable(s)

    def start(self, prefix: str) -> "Stringable":
        """
        Begin a string with a single instance of a given value.

        Parameters
        ----------
        prefix : str
            The string to start with

        Returns
        -------
        Stringable
            A new Stringable that starts with the prefix
        """
        s = str(self)
        if not s.startswith(prefix):
            s = prefix + s
        return Stringable(s)

    def explode(self, delimiter: str, limit: int = -1) -> List[str]:
        """
        Explode the string into a list using a delimiter.

        Splits the string by the specified delimiter and returns a list of substrings.
        If a limit is specified, the string will be split into at most that many parts.

        Parameters
        ----------
        delimiter : str
            The delimiter to split on.
        limit : int, optional
            Maximum number of elements to return, by default -1 (no limit).

        Returns
        -------
        list
            List of string parts after splitting by the delimiter.
        """

        # Check if limit is specified to control the number of splits
        if limit == -1:
            # Split without limit - all occurrences of delimiter are used
            return str(self).split(delimiter)
        else:
            # Split with limit - maximum of (limit-1) splits are performed
            return str(self).split(delimiter, limit - 1)

    def split(self, pattern: Union[str, int], limit: int = -1, flags: int = 0) -> List[str]:
        """
        Split a string using a regular expression or by length.

        Parameters
        ----------
        pattern : str or int
            Regular expression pattern or length for splitting
        limit : int, optional
            Maximum splits, by default -1 (no limit)
        flags : int, optional
            Regex flags, by default 0

        Returns
        -------
        list
            List of string segments
        """
        if isinstance(pattern, int):
            # Split by length
            s = str(self)
            return [s[i:i+pattern] for i in range(0, len(s), pattern)]
        else:
            # Split by regex
            # In re.split, maxsplit=0 means no limit, -1 means no splits
            maxsplit = 0 if limit == -1 else limit
            segments = re.split(pattern, str(self), maxsplit=maxsplit, flags=flags)
            return segments if segments else []

    def ucsplit(self) -> List[str]:
        """
        Split a string by uppercase characters.

        Returns
        -------
        list
            List of words split by uppercase characters
        """
        # Split on uppercase letters, keeping the uppercase letter with the following text
        parts = re.findall(r'[A-Z][a-z]*|[a-z]+|\d+', str(self))
        return parts if parts else [str(self)]

    def squish(self) -> "Stringable":
        """
        Remove all "extra" blank space from the given string.

        Returns
        -------
        Stringable
            A new Stringable with normalized whitespace
        """
        # Replace multiple whitespace characters with single spaces and trim
        return Stringable(re.sub(r'\s+', ' ', str(self)).strip())

    def words(self, words: int = 100, end: str = '...') -> "Stringable":
        """
        Limit the number of words in a string.

        Parameters
        ----------
        words : int, optional
            Maximum number of words, by default 100
        end : str, optional
            String to append if truncated, by default '...'

        Returns
        -------
        Stringable
            A new Stringable with limited words
        """
        word_list = str(self).split()
        if len(word_list) <= words:
            return Stringable(str(self))

        truncated = ' '.join(word_list[:words])
        return Stringable(truncated + end)

    def wordCount(self, characters: Optional[str] = None) -> int:
        """
        Get the number of words a string contains.

        Parameters
        ----------
        characters : str, optional
            Additional characters to consider as word separators, by default None

        Returns
        -------
        int
            Number of words in the string
        """
        s = str(self).strip()
        if not s:
            return 0

        if characters:
            # Replace additional characters with spaces
            for char in characters:
                s = s.replace(char, ' ')

        # Split by whitespace and count non-empty parts
        return len([word for word in s.split() if word])

    def wordWrap(self, characters: int = 75, break_str: str = "\n", cut_long_words: bool = False) -> "Stringable":
        """
        Wrap a string to a given number of characters.

        Parameters
        ----------
        characters : int, optional
            Line width, by default 75
        break_str : str, optional
            Line break string, by default "\\n"
        cut_long_words : bool, optional
            Whether to cut long words, by default False

        Returns
        -------
        Stringable
            A new Stringable with wrapped text
        """
        import textwrap

        if cut_long_words:
            wrapped = textwrap.fill(str(self), width=characters, break_long_words=True,
                                  break_on_hyphens=True, expand_tabs=False)
        else:
            wrapped = textwrap.fill(str(self), width=characters, break_long_words=False,
                                  break_on_hyphens=True, expand_tabs=False)

        return Stringable(wrapped.replace('\n', break_str))

    def wrap(self, before: str, after: Optional[str] = None) -> "Stringable":
        """
        Wrap the string with the given strings.

        Parameters
        ----------
        before : str
            String to prepend
        after : str, optional
            String to append, by default None (uses before)

        Returns
        -------
        Stringable
            A new Stringable wrapped with the given strings
        """
        if after is None:
            after = before
        return Stringable(before + str(self) + after)

    def unwrap(self, before: str, after: Optional[str] = None) -> "Stringable":
        """
        Unwrap the string with the given strings.

        Parameters
        ----------
        before : str
            String to remove from start
        after : str, optional
            String to remove from end, by default None (uses before)

        Returns
        -------
        Stringable
            A new Stringable with wrapping removed
        """
        if after is None:
            after = before

        s = str(self)
        if s.startswith(before):
            s = s[len(before):]
        if s.endswith(after):
            s = s[:-len(after)]

        return Stringable(s)

    # Advanced replacement methods
    def replaceArray(self, search: str, replace: List[str]) -> "Stringable":
        """
        Replace a given value in the string sequentially with an array.

        Parameters
        ----------
        search : str
            The string to search for
        replace : list
            List of replacement strings

        Returns
        -------
        Stringable
            A new Stringable with sequential replacements
        """
        s = str(self)
        replace_idx = 0

        while search in s and replace_idx < len(replace):
            s = s.replace(search, str(replace[replace_idx]), 1)
            replace_idx += 1

        return Stringable(s)

    def replaceFirst(self, search: str, replace: str) -> "Stringable":
        """
        Replace the first occurrence of a given value in the string.

        Parameters
        ----------
        search : str
            The string to search for
        replace : str
            The replacement string

        Returns
        -------
        Stringable
            A new Stringable with first occurrence replaced
        """
        return Stringable(str(self).replace(search, replace, 1))

    def replaceLast(self, search: str, replace: str) -> "Stringable":
        """
        Replace the last occurrence of a given value in the string.

        Parameters
        ----------
        search : str
            The string to search for
        replace : str
            The replacement string

        Returns
        -------
        Stringable
            A new Stringable with last occurrence replaced
        """
        s = str(self)
        idx = s.rfind(search)
        if idx != -1:
            s = s[:idx] + replace + s[idx + len(search):]
        return Stringable(s)

    def replaceStart(self, search: str, replace: str) -> "Stringable":
        """
        Replace the first occurrence of the given value if it appears at the start of the string.

        Parameters
        ----------
        search : str
            The string to search for at the start
        replace : str
            The replacement string

        Returns
        -------
        Stringable
            A new Stringable with start replacement
        """
        s = str(self)
        if s.startswith(search):
            s = replace + s[len(search):]
        return Stringable(s)

    def replaceEnd(self, search: str, replace: str) -> "Stringable":
        """
        Replace the last occurrence of a given value if it appears at the end of the string.

        Parameters
        ----------
        search : str
            The string to search for at the end
        replace : str
            The replacement string

        Returns
        -------
        Stringable
            A new Stringable with end replacement
        """
        s = str(self)
        if s.endswith(search):
            s = s[:-len(search)] + replace
        return Stringable(s)

    def replaceMatches(self, pattern: Union[str, List[str]], replace: Union[str, Callable], limit: int = -1) -> "Stringable":
        """
        Replace the patterns matching the given regular expression.

        Parameters
        ----------
        pattern : str or list
            Regular expression pattern(s)
        replace : str or callable
            Replacement string or callback function
        limit : int, optional
            Maximum replacements, by default -1 (no limit)

        Returns
        -------
        Stringable
            A new Stringable with pattern matches replaced
        """
        s = str(self)

        if isinstance(pattern, list):
            patterns = pattern
        else:
            patterns = [pattern]

        for pat in patterns:
            if callable(replace):
                s = re.sub(pat, replace, s, count=0 if limit == -1 else limit)
            else:
                s = re.sub(pat, str(replace), s, count=0 if limit == -1 else limit)

        return Stringable(s)

    def remove(self, search: Union[str, List[str]], case_sensitive: bool = True) -> "Stringable":
        """
        Remove any occurrence of the given string in the subject.

        Parameters
        ----------
        search : str or list
            The string(s) to remove
        case_sensitive : bool, optional
            Whether the search is case sensitive, by default True

        Returns
        -------
        Stringable
            A new Stringable with occurrences removed
        """
        s = str(self)

        if isinstance(search, str):
            search = [search]

        for needle in search:
            if case_sensitive:
                s = s.replace(needle, '')
            else:
                s = re.sub(re.escape(needle), '', s, flags=re.IGNORECASE)

        return Stringable(s)

    # Pluralization and singularization methods
    def plural(self, count: Union[int, List, Any] = 2, prepend_count: bool = False) -> "Stringable":
        """
        Get the plural form of an English word.

        Parameters
        ----------
        count : int, list or any, optional
            Count to determine if plural is needed, by default 2
        prepend_count : bool, optional
            Whether to prepend the count, by default False

        Returns
        -------
        Stringable
            A new Stringable with plural form
        """
        # Simple pluralization rules
        word = str(self).lower()

        # Determine if we need plural
        if hasattr(count, '__len__'):
            actual_count = len(count)
        elif isinstance(count, (int, float)):
            actual_count = count
        else:
            actual_count = 1

        if actual_count == 1:
            result = str(self)
        else:
            # Simple pluralization rules
            if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
                plural_word = str(self) + 'es'
            elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
                plural_word = str(self)[:-1] + 'ies'
            elif word.endswith('f'):
                plural_word = str(self)[:-1] + 'ves'
            elif word.endswith('fe'):
                plural_word = str(self)[:-2] + 'ves'
            else:
                plural_word = str(self) + 's'

            result = plural_word

        if prepend_count:
            result = f"{actual_count} {result}"

        return Stringable(result)

    def pluralStudly(self, count: Union[int, List, Any] = 2) -> "Stringable":
        """
        Pluralize the last word of an English, studly caps case string.

        Parameters
        ----------
        count : int, list or any, optional
            Count to determine if plural is needed, by default 2

        Returns
        -------
        Stringable
            A new Stringable with pluralized last word in StudlyCase
        """
        s = str(self)
        # Find the last word boundary
        parts = re.findall(r'[A-Z][a-z]*|[a-z]+', s)
        if parts:
            last_word = parts[-1]
            pluralized_last = Stringable(last_word).plural(count).studly().value()
            parts[-1] = pluralized_last
            return Stringable(''.join(parts))

        return self.plural(count).studly()

    def pluralPascal(self, count: Union[int, List, Any] = 2) -> "Stringable":
        """
        Pluralize the last word of an English, Pascal caps case string.

        Parameters
        ----------
        count : int, list or any, optional
            Count to determine if plural is needed, by default 2

        Returns
        -------
        Stringable
            A new Stringable with pluralized last word in PascalCase
        """
        # PascalCase is the same as StudlyCase
        s = str(self)
        if len(s) == 0:
            return Stringable(s)

        # Split by uppercase letters to find words
        words = re.findall(r'[A-Z][a-z]*|[a-z]+', s)
        if not words:
            return Stringable(s)

        # Determine if we need plural
        if isinstance(count, (list, tuple)):
            need_plural = len(count) != 1
        else:
            need_plural = count != 1

        if need_plural:
            # Pluralize the last word
            last_word = words[-1]
            pluralized = Stringable(last_word).plural(count)
            words[-1] = pluralized.studly().value()

        return Stringable(''.join(words))

    def singular(self) -> "Stringable":
        """
        Get the singular form of an English word.

        Returns
        -------
        Stringable
            A new Stringable with singular form
        """
        word = str(self).lower()
        s = str(self)

        # Simple singularization rules
        if word.endswith('ies') and len(word) > 3:
            result = s[:-3] + 'y'
        elif word.endswith('ves'):
            if word.endswith('ives'):
                result = s[:-3] + 'e'
            else:
                result = s[:-3] + 'f'
        elif word.endswith('es'):
            if word.endswith(('ches', 'shes', 'xes', 'zes')):
                result = s[:-2]
            elif word.endswith('ses'):
                result = s[:-2]
            else:
                result = s[:-1]
        elif word.endswith('s') and not word.endswith('ss'):
            result = s[:-1]
        else:
            result = s

        return Stringable(result)

    def parseCallback(self, default: Optional[str] = None) -> List[Optional[str]]:
        """
        Parse a Class@method style callback into class and method.

        Parameters
        ----------
        default : str, optional
            Default method name if not specified, by default None

        Returns
        -------
        list
            List containing [class_name, method_name]
        """
        callback_str = str(self)

        if '@' in callback_str:
            parts = callback_str.split('@', 1)
            return [parts[0], parts[1]]
        else:
            return [callback_str, default]

    def when(self, condition: Union[bool, Callable], callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if condition is true.

        Parameters
        ----------
        condition : bool or callable
            The condition to evaluate
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        if callable(condition):
            condition_result = condition(self)
        else:
            condition_result = condition

        if condition_result:
            result = callback(self)
            return Stringable(result) if not isinstance(result, Stringable) else result
        elif default:
            result = default(self)
            return Stringable(result) if not isinstance(result, Stringable) else result
        else:
            return self

    def whenContains(self, needles: Union[str, List[str]], callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string contains a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to search for
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.contains(needles), callback, default)

    def whenContainsAll(self, needles: List[str], callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string contains all array values.

        Parameters
        ----------
        needles : list
            The substrings to search for
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        contains_all = all(needle in str(self) for needle in needles)
        return self.when(contains_all, callback, default)

    def whenEmpty(self, callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string is empty.

        Parameters
        ----------
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.isEmpty(), callback, default)

    def whenNotEmpty(self, callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string is not empty.

        Parameters
        ----------
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.isNotEmpty(), callback, default)

    def whenEndsWith(self, needles: Union[str, List[str]], callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string ends with a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to check
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.endsWith(needles), callback, default)

    def whenDoesntEndWith(self, needles: Union[str, List[str]], callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string doesn't end with a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to check
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(not self.endsWith(needles), callback, default)

    def whenExactly(self, value: str, callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string is an exact match with the given value.

        Parameters
        ----------
        value : str
            The value to compare exactly
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.exactly(value), callback, default)

    def whenNotExactly(self, value: str, callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string is not an exact match with the given value.

        Parameters
        ----------
        value : str
            The value to compare exactly
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(not self.exactly(value), callback, default)

    def whenStartsWith(self, needles: Union[str, List[str]], callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string starts with a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to check
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        if isinstance(needles, str):
            needles = [needles]
        starts_with = any(str(self).startswith(needle) for needle in needles)
        return self.when(starts_with, callback, default)

    def whenDoesntStartWith(self, needles: Union[str, List[str]], callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string doesn't start with a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to check
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        if isinstance(needles, str):
            needles = [needles]
        starts_with = any(str(self).startswith(needle) for needle in needles)
        return self.when(not starts_with, callback, default)

    def whenTest(self, pattern: str, callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string matches the given pattern.

        Parameters
        ----------
        pattern : str
            Regular expression pattern
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.test(pattern), callback, default)

    def convertCase(self, mode: int = None) -> "Stringable":
        """
        Convert the case of a string.

        Parameters
        ----------
        mode : int, optional
            Case conversion mode:
            0 or None - MB_CASE_FOLD (casefold)
            1 - MB_CASE_UPPER (upper)
            2 - MB_CASE_LOWER (lower)
            3 - MB_CASE_TITLE (title)
            by default None (MB_CASE_FOLD)
        Returns
        -------
        Stringable
            A new Stringable with converted case
        """
        s = str(self)

        # Python doesn't have exact MB_CASE constants, so we'll use simple mappings
        if mode is None or mode == 0:  # MB_CASE_FOLD equivalent
            return Stringable(s.casefold())
        elif mode == 1:  # MB_CASE_UPPER equivalent
            return Stringable(s.upper())
        elif mode == 2:  # MB_CASE_LOWER equivalent
            return Stringable(s.lower())
        elif mode == 3:  # MB_CASE_TITLE equivalent
            return Stringable(s.title())
        else:
            return Stringable(s.casefold())

    def transliterate(self, unknown: str = '?', strict: bool = False) -> "Stringable":
        """
        Transliterate a string to its closest ASCII representation.

        Parameters
        ----------
        unknown : str, optional
            Character to use for unknown characters, by default '?'
        strict : bool, optional
            Whether to be strict about transliteration, by default False

        Returns
        -------
        Stringable
            A new Stringable with transliterated text
        """
        s = str(self)

        # Use unicodedata to normalize and transliterate
        normalized = unicodedata.normalize('NFKD', s)

        if strict:
            # Only keep ASCII characters
            ascii_chars = []
            for char in normalized:
                if ord(char) < 128:
                    ascii_chars.append(char)
                else:
                    ascii_chars.append(unknown)
            return Stringable(''.join(ascii_chars))
        else:
            # More lenient transliteration
            ascii_str = ''.join(char for char in normalized if ord(char) < 128)
            return Stringable(ascii_str)

    def hash(self, algorithm: str) -> "Stringable":
        """
        Hash the string using the given algorithm.

        Parameters
        ----------
        algorithm : str
            Hash algorithm (md5, sha1, sha256, etc.)

        Returns
        -------
        Stringable
            A new Stringable with the hash
        """
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(str(self).encode('utf-8'))
        return Stringable(hash_obj.hexdigest())

    def pipe(self, callback: Callable) -> "Stringable":
        """
        Call the given callback and return a new string.

        Parameters
        ----------
        callback : callable
            The callback function to apply

        Returns
        -------
        Stringable
            A new Stringable with the result of the callback
        """
        result = callback(self)
        return Stringable(result) if not isinstance(result, Stringable) else result

    def take(self, limit: int) -> "Stringable":
        """
        Take the first or last {limit} characters.

        Parameters
        ----------
        limit : int
            Number of characters to take (negative for from end)

        Returns
        -------
        Stringable
            A new Stringable with the taken characters
        """
        if limit < 0:
            return Stringable(str(self)[limit:])
        else:
            return Stringable(str(self)[:limit])

    def swap(self, map_dict: Dict[str, str]) -> "Stringable":
        """
        Swap multiple keywords in a string with other keywords.

        Parameters
        ----------
        map_dict : dict
            Dictionary mapping old values to new values

        Returns
        -------
        Stringable
            A new Stringable with swapped values
        """
        s = str(self)
        for old, new in map_dict.items():
            s = s.replace(old, new)
        return Stringable(s)

    def substrCount(self, needle: str, offset: int = 0, length: Optional[int] = None) -> int:
        """
        Returns the number of substring occurrences.

        Parameters
        ----------
        needle : str
            The substring to count
        offset : int, optional
            Starting offset, by default 0
        length : int, optional
            Length to search within, by default None

        Returns
        -------
        int
            Number of occurrences
        """
        s = str(self)

        if length is not None:
            s = s[offset:offset + length]
        else:
            s = s[offset:]

        return s.count(needle)

    def substrReplace(self, replace: Union[str, List[str]], offset: Union[int, List[int]] = 0,
                     length: Optional[Union[int, List[int]]] = None) -> "Stringable":
        """
        Replace text within a portion of a string.

        Parameters
        ----------
        replace : str or list
            Replacement string(s)
        offset : int or list, optional
            Starting position(s), by default 0
        length : int, list or None, optional
            Length(s) to replace, by default None

        Returns
        -------
        Stringable
            A new Stringable with replaced text
        """
        s = str(self)

        if isinstance(replace, str):
            replace = [replace]
        if isinstance(offset, int):
            offset = [offset]
        if length is not None and isinstance(length, int):
            length = [length]

        # Process replacements
        result = s
        for i, repl in enumerate(replace):
            off = offset[i] if i < len(offset) else offset[-1]
            if length and i < len(length):
                leng = length[i]
                result = result[:off] + repl + result[off + leng:]
            else:
                result = result[:off] + repl + result[off:]

        return Stringable(result)

    def scan(self, format_str: str) -> List[str]:
        """
        Parse input from a string to a list, according to a format.

        Parameters
        ----------
        format_str : str
            Format string (simplified sscanf-like)

        Returns
        -------
        list
            List of parsed values
        """
        # Simplified implementation - convert format to regex
        # This is a basic implementation, not as full-featured as PHP's sscanf
        pattern = format_str.replace('%s', r'(\S+)').replace('%d', r'(\d+)').replace('%f', r'([\d.]+)')
        matches = re.findall(pattern, str(self))
        return list(matches[0]) if matches else []

    def prepend(self, *values: str) -> "Stringable":
        """
        Prepend the given values to the string.

        Parameters
        ----------
        values : str
            Values to prepend

        Returns
        -------
        Stringable
            A new Stringable with prepended values
        """
        return Stringable(''.join(values) + str(self))

    def substr(self, start: int, length: Optional[int] = None) -> "Stringable":
        """
        Returns the portion of the string specified by the start and length parameters.

        Parameters
        ----------
        start : int
            Starting position
        length : int, optional
            Length to extract, by default None

        Returns
        -------
        Stringable
            A new Stringable with the substring
        """
        s = str(self)
        if length is None:
            return Stringable(s[start:])
        else:
            return Stringable(s[start:start + length])

    def doesntContain(self, needles: Union[str, List[str]], ignore_case: bool = False) -> bool:
        """
        Determine if a given string doesn't contain a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to search for
        ignore_case : bool, optional
            Whether to ignore case, by default False

        Returns
        -------
        bool
            True if string doesn't contain any needle, False otherwise
        """
        return not self.contains(needles, ignore_case)

    def doesntStartWith(self, needles: Union[str, List[str]]) -> bool:
        """
        Determine if a given string doesn't start with a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to check

        Returns
        -------
        bool
            True if string doesn't start with any needle, False otherwise
        """
        if isinstance(needles, str):
            needles = [needles]
        return not any(str(self).startswith(needle) for needle in needles)

    def doesntEndWith(self, needles: Union[str, List[str]]) -> bool:
        """
        Determine if a given string doesn't end with a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to check

        Returns
        -------
        bool
            True if string doesn't end with any needle, False otherwise
        """
        return not self.endsWith(needles)

    def startsWith(self, needles: Union[str, List[str]]) -> bool:
        """
        Determine if a given string starts with a given substring.

        Parameters
        ----------
        needles : str or list
            The substring(s) to check

        Returns
        -------
        bool
            True if string starts with any needle, False otherwise
        """
        if isinstance(needles, str):
            needles = [needles]
        return any(str(self).startswith(needle) for needle in needles)

    def jsonSerialize(self) -> str:
        """
        Convert the object to a string when JSON encoded.

        Returns
        -------
        str
            The string representation for JSON serialization
        """
        return str(self)

    def offsetExists(self, offset: int) -> bool:
        """
        Determine if the given offset exists.

        Parameters
        ----------
        offset : int
            The offset to check

        Returns
        -------
        bool
            True if offset exists, False otherwise
        """
        try:
            str(self)[offset]
            return True
        except IndexError:
            return False

    def offsetGet(self, offset: int) -> str:
        """
        Get the value at the given offset.

        Parameters
        ----------
        offset : int
            The offset to get

        Returns
        -------
        str
            The character at the offset
        """
        return str(self)[offset]

    def isPattern(self, pattern: Union[str, List[str]], ignore_case: bool = False) -> bool:
        """
        Determine if a given string matches a given pattern.

        This method checks if the string matches any of the given patterns,
        which can include wildcards (* and ?). The matching can be case-sensitive
        or case-insensitive based on the ignore_case parameter.

        Parameters
        ----------
        pattern : str or List[str]
            Pattern(s) to match (supports wildcards * and ?).
        ignore_case : bool, optional
            Whether to ignore case, by default False.

        Returns
        -------
        bool
            True if string matches any of the patterns, False otherwise.
        """
        import fnmatch

        # Normalize pattern to list for consistent processing
        if isinstance(pattern, str):
            patterns = [pattern]
        else:
            patterns = pattern

        # Get string representation
        s = str(self)

        # Apply case-insensitive matching if requested
        if ignore_case:
            s = s.lower()
            patterns = [p.lower() for p in patterns]

        # Check if string matches any of the patterns
        return any(fnmatch.fnmatch(s, p) for p in patterns)

    def containsAll(self, needles: List[str], ignore_case: bool = False) -> bool:
        """
        Determine if a given string contains all array values.

        Parameters
        ----------
        needles : list
            List of substrings to search for
        ignore_case : bool, optional
            Whether to ignore case, by default False

        Returns
        -------
        bool
            True if string contains all needles, False otherwise
        """
        s = str(self)
        if ignore_case:
            s = s.lower()
            needles = [needle.lower() for needle in needles]

        return all(needle in s for needle in needles)

    def whenIs(self, pattern: Union[str, List[str]], callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string matches a given pattern.

        Parameters
        ----------
        pattern : str or list
            Pattern(s) to match against
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.isPattern(pattern), callback, default)

    def whenIsAscii(self, callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string is 7 bit ASCII.

        Parameters
        ----------
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.isAscii(), callback, default)

    def whenIsUuid(self, callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string is a valid UUID.

        Parameters
        ----------
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.isUuid(), callback, default)

    def whenIsUlid(self, callback: Callable, default: Optional[Callable] = None) -> "Stringable":
        """
        Execute the given callback if the string is a valid ULID.

        Parameters
        ----------
        callback : callable
            The callback to execute if condition is true
        default : callable, optional
            The callback to execute if condition is false, by default None

        Returns
        -------
        Stringable
            Result of callback execution or self
        """
        return self.when(self.isUlid(), callback, default)

    def toDate(self, format_str: Optional[str] = None) -> Optional[datetime]:
        """
        Convert the string to a datetime object.

        Parameters
        ----------
        format_str : str, optional
            Format string for parsing, by default None (auto-detect)

        Returns
        -------
        datetime or None
            Parsed datetime object or None if parsing fails
        """

        s = str(self)

        if format_str:
            try:
                return datetime.strptime(s, format_str)
            except ValueError:
                return None

        # Try common date formats
        common_formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%m-%d-%Y'
        ]

        for fmt in common_formats:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue

        return None

    def encrypt(self) -> "Stringable":
        """
        Encrypt the string (placeholder implementation).

        Note: This is a placeholder. In a real implementation, you would use
        a proper encryption library like cryptography.

        Parameters
        ----------
        None

        Returns
        -------
        Stringable
            Encrypted string (base64 encoded for this placeholder)
        """

        return self.toBase64()

    def decrypt(self) -> "Stringable":
        """
        Decrypt the string (placeholder implementation).

        Note: This is a placeholder. In a real implementation, you would use
        a proper decryption library like cryptography.

        Parameters
        ----------
        None

        Returns
        -------
        Stringable
            Decrypted string
        """

        return self.fromBase64()

    def toHtmlString(self) -> "Stringable":
        """
        Create an HTML string representation (placeholder).

        Returns
        -------
        Stringable
            HTML-safe string
        """
        # Escape HTML entities
        return Stringable(html.escape(str(self)))

    def tap(self, callback: Callable) -> "Stringable":
        """
        Call the given callback with the string and return the string.

        Parameters
        ----------
        callback : callable
            The callback to execute with the string

        Returns
        -------
        Stringable
            The same Stringable instance
        """
        callback(self)
        return self
