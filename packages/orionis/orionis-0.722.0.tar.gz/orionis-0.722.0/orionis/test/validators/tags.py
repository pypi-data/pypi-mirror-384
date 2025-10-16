from orionis.test.exceptions import OrionisTestValueError

class __ValidTags:

    def __call__(self, tags) -> list | None:
        """
        Validates that the input is either None or a list of non-empty string tags.

        Parameters
        ----------
        tags : list or None
            The list of tags to validate. Must be None or a list of non-empty strings.

        Returns
        -------
        list or None
            The validated list of normalized tag strings, or None if input is None.

        Raises
        ------
        OrionisTestValueError
            If `tags` is not None or a list, if the list is empty, or if any tag
            is not a non-empty string.
        """
        if tags is None:
            return None

        if not isinstance(tags, list):
            raise OrionisTestValueError(
                f"Invalid tags: Expected a list or None, got '{tags}' ({type(tags).__name__})."
            )

        if not tags:
            raise OrionisTestValueError(
                "Invalid tags: Expected a non-empty list or None."
            )

        normalized_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise OrionisTestValueError(
                    f"Invalid tag: Expected a string, got '{tag}' ({type(tag).__name__})."
                )
            
            normalized_tag = tag.strip()
            if not normalized_tag:
                raise OrionisTestValueError(
                    "Invalid tag: Expected a non-empty string."
                )
            
            normalized_tags.append(normalized_tag)

        return normalized_tags

# Exported singleton instance
ValidTags = __ValidTags()