import json
import operator
import random
from functools import reduce
from typing import Any, Callable, Dict, List, Optional, Union
from dotty_dict import Dotty, dotty
from orionis.support.structures.contracts.collection import ICollection

class Collection(ICollection):

    def __init__(self, items: Optional[List[Any]] = None) -> None:
        """Initialize a new collection instance.

        Parameters
        ----------
        items : list, optional
            Initial items for the collection, by default None
        """
        self._items = items or []
        self.__appends__ = []

    def take(self, number: int) -> 'Collection':
        """Take a specific number of results from the items.

        Parameters
        ----------
        number : int
            The number of results to take. If negative, takes from the end.

        Returns
        -------
        Collection
            A new collection with the specified number of items.
        """
        if number < 0:
            return self[number:]

        return self[:number]

    def first(self, callback: Optional[Callable] = None) -> Any:
        """Get the first result in the items.

        Parameters
        ----------
        callback : callable, optional
            Filter function to apply before returning the first item, by default None

        Returns
        -------
        mixed
            The first item in the collection, or None if empty.
        """
        filtered = self
        if callback:
            filtered = self.filter(callback)
        response = None
        if filtered:
            response = filtered[0]
        return response

    def last(self, callback: Optional[Callable] = None) -> Any:
        """Get the last result in the items.

        Parameters
        ----------
        callback : callable, optional
            Filter function to apply before returning the last item, by default None

        Returns
        -------
        mixed
            The last item in the collection.
        """
        filtered = self
        if callback:
            filtered = self.filter(callback)
        return filtered[-1]

    def all(self) -> List[Any]:
        """Get all items in the collection.

        Returns
        -------
        list
            All items in the collection.
        """
        return self._items

    def avg(self, key: Optional[str] = None) -> float:
        """Calculate the average of the items.

        Parameters
        ----------
        key : str, optional
            The key to use for calculating the average of values, by default None

        Returns
        -------
        float
            The average value.
        """
        result = 0
        items = self.__getValue(key) or self._items
        try:
            result = sum(items) / len(items)
        except TypeError:
            pass
        return result

    def max(self, key: Optional[str] = None) -> Any:
        """Get the maximum value from the items.

        Parameters
        ----------
        key : str, optional
            The key to use for finding the maximum value, by default None

        Returns
        -------
        mixed
            The maximum value.
        """
        result = 0
        items = self.__getValue(key) or self._items

        try:
            return max(items)
        except (TypeError, ValueError):
            pass
        return result

    def min(self, key: Optional[str] = None) -> Any:
        """Get the minimum value from the items.

        Parameters
        ----------
        key : str, optional
            The key to use for finding the minimum value, by default None

        Returns
        -------
        mixed
            The minimum value.
        """
        result = 0
        items = self.__getValue(key) or self._items

        try:
            return min(items)
        except (TypeError, ValueError):
            pass
        return result

    def chunk(self, size: int) -> 'Collection':
        """Break the collection into multiple smaller collections of a given size.

        Parameters
        ----------
        size : int
            The number of values in each chunk.

        Returns
        -------
        Collection
            A new collection containing the chunks.
        """
        items = []
        for i in range(0, self.count(), size):
            items.append(self[i : i + size])
        return self.__class__(items)

    def collapse(self) -> 'Collection':
        """Collapse the collection of arrays into a single, flat collection.

        Returns
        -------
        Collection
            A new flattened collection.
        """
        items = []
        for item in self:
            items += self.__getItems(item)
        return self.__class__(items)

    def contains(self, key: Union[str, Callable], value: Any = None) -> bool:
        """Determine if the collection contains a given item.

        Parameters
        ----------
        key : mixed
            The key or callback function to check for
        value : mixed, optional
            The value to match when key is a string, by default None

        Returns
        -------
        bool
            True if the item is found, False otherwise.
        """
        if value:
            return self.contains(lambda x: self.__dataGet(x, key) == value)

        if self.__checkIsCallable(key, raise_exception=False):
            return self.first(key) is not None

        return key in self

    def count(self) -> int:
        """Get the number of items in the collection.

        Returns
        -------
        int
            The number of items.
        """
        return len(self._items)

    def diff(self, items: Union[List[Any], 'Collection']) -> 'Collection':
        """Get the items that are not present in the given collection.

        Parameters
        ----------
        items : mixed
            The items to diff against

        Returns
        -------
        Collection
            A new collection with the difference.
        """
        items = self.__getItems(items)
        return self.__class__([x for x in self if x not in items])

    def each(self, callback: Callable) -> 'Collection':
        """Iterate over the items in the collection and pass each item to the given callback.

        Parameters
        ----------
        callback : callable
            The callback function to apply to each item

        Returns
        -------
        Collection
            The current collection instance.
        """
        self.__checkIsCallable(callback)

        for k, v in enumerate(self):
            result = callback(v)
            if not result:
                break
            self[k] = result

        return self

    def every(self, callback: Callable) -> bool:
        """Determine if all items pass the given callback test.

        Parameters
        ----------
        callback : callable
            The callback function to test each item

        Returns
        -------
        bool
            True if all items pass the test, False otherwise.
        """
        self.__checkIsCallable(callback)
        return all(callback(x) for x in self)

    def filter(self, callback: Callable) -> 'Collection':
        """Filter the collection using the given callback.

        Parameters
        ----------
        callback : callable
            The callback function to filter items

        Returns
        -------
        Collection
            A new filtered collection.
        """
        self.__checkIsCallable(callback)
        return self.__class__(list(filter(callback, self)))

    def flatten(self) -> 'Collection': # NOSONAR
        """Flatten a multi-dimensional collection into a single dimension.

        Returns
        -------
        Collection
            A new flattened collection.
        """
        def _flatten(items):
            if isinstance(items, dict):
                for v in items.values():
                    for x in _flatten(v):
                        yield x
            elif isinstance(items, list):
                for i in items:
                    for j in _flatten(i):
                        yield j
            else:
                yield items

        return self.__class__(list(_flatten(self._items)))

    def forget(self, *keys: Any) -> 'Collection':
        """Remove an item from the collection by key.

        Parameters
        ----------
        *keys : mixed
            The keys to remove from the collection

        Returns
        -------
        Collection
            The current collection instance.
        """
        keys = sorted(keys, reverse=True)

        for key in keys:
            del self[key]

        return self

    def forPage(self, page: int, number: int) -> 'Collection':
        """Slice the underlying collection array for pagination.

        Parameters
        ----------
        page : int
            The page number
        number : int
            Number of items per page

        Returns
        -------
        Collection
            A new collection with the paginated items.
        """
        return self.__class__(self[page:number])

    def get(self, key: Any, default: Any = None) -> Any:
        """Get an item from the collection by key.

        Parameters
        ----------
        key : mixed
            The key to retrieve
        default : mixed, optional
            The default value to return if key not found, by default None

        Returns
        -------
        mixed
            The item at the specified key or default value.
        """
        try:
            return self[key]
        except IndexError:
            pass

        return self.__value(default)

    def implode(self, glue: str = ",", key: Optional[str] = None) -> str:
        """Join all items from the collection using a string.

        Parameters
        ----------
        glue : str, optional
            The string to use for joining, by default ","
        key : str, optional
            The key to pluck from items before joining, by default None

        Returns
        -------
        str
            The joined string.
        """
        first = self.first()
        if not isinstance(first, str) and key:
            return glue.join(self.pluck(key))
        return glue.join([str(x) for x in self])

    def isEmpty(self) -> bool:
        """Determine if the collection is empty.

        Returns
        -------
        bool
            True if the collection is empty, False otherwise.
        """
        return not self

    def map(self, callback: Callable) -> 'Collection':
        """Run a map over each of the items.

        Parameters
        ----------
        callback : callable
            The callback function to apply to each item

        Returns
        -------
        Collection
            A new collection with the mapped items.
        """
        self.__checkIsCallable(callback)
        items = [callback(x) for x in self]
        return self.__class__(items)

    def mapInto(self, cls: type, method: Optional[str] = None, **kwargs: Any) -> 'Collection':
        """Map items into instances of the given class.

        Parameters
        ----------
        cls : class
            The class to map items into
        method : str, optional
            The method to call on the class, by default None
        **kwargs : dict
            Additional keyword arguments to pass to the constructor or method

        Returns
        -------
        Collection
            A new collection with the mapped instances.
        """
        results = []
        for item in self:
            if method:
                results.append(getattr(cls, method)(item, **kwargs))
            else:
                results.append(cls(item))

        return self.__class__(results)

    def merge(self, items: Union[List[Any], 'Collection']) -> 'Collection':
        """Merge the collection with the given items.

        Parameters
        ----------
        items : list or Collection
            The items to merge into the collection

        Returns
        -------
        Collection
            The current collection instance.

        Raises
        ------
        ValueError
            If items cannot be merged due to incompatible types.
        """
        if not isinstance(items, list):
            raise ValueError("Unable to merge uncompatible types")

        items = self.__getItems(items)

        self._items += items
        return self

    def pluck(self, value: str, key: Optional[str] = None) -> 'Collection': # NOSONAR
        """Get the values of a given key from all items.

        Parameters
        ----------
        value : str
            The key to pluck from each item
        key : str, optional
            The key to use as the result key, by default None

        Returns
        -------
        Collection
            A new collection with the plucked values.
        """
        if key:
            attributes = {}
        else:
            attributes = []

        if isinstance(self._items, dict):
            return Collection([self._items.get(value)])

        for item in self:
            if isinstance(item, dict):
                iterable = item.items()
            elif hasattr(item, "serialize"):
                iterable = item.serialize().items()
            else:
                iterable = self.all().items()

            for k, v in iterable:
                if k == value:
                    if key:
                        attributes[self.__dataGet(item, key)] = self.__dataGet(
                            item, value
                        )
                    else:
                        attributes.append(v)

        return Collection(attributes)

    def pop(self) -> Any:
        """Remove and return the last item from the collection.

        Returns
        -------
        mixed
            The last item from the collection.
        """
        last = self._items.pop()
        return last

    def prepend(self, value: Any) -> 'Collection':
        """Add an item to the beginning of the collection.

        Parameters
        ----------
        value : mixed
            The value to prepend

        Returns
        -------
        Collection
            The current collection instance.
        """
        self._items.insert(0, value)
        return self

    def pull(self, key: Any) -> Any:
        """Remove an item from the collection and return it.

        Parameters
        ----------
        key : mixed
            The key of the item to remove

        Returns
        -------
        mixed
            The removed item.
        """
        value = self.get(key)
        self.forget(key)
        return value

    def push(self, value: Any) -> 'Collection':
        """Add an item to the end of the collection.

        Parameters
        ----------
        value : mixed
            The value to add

        Returns
        -------
        Collection
            The current collection instance.
        """
        self._items.append(value)
        return self

    def put(self, key: Any, value: Any) -> 'Collection':
        """Put an item in the collection by key.

        Parameters
        ----------
        key : mixed
            The key to set
        value : mixed
            The value to set

        Returns
        -------
        Collection
            The current collection instance.
        """
        self[key] = value
        return self

    def random(self, count: Optional[int] = None) -> Union[Any, 'Collection', None]:
        """Get one or more random items from the collection.

        Parameters
        ----------
        count : int, optional
            The number of items to return, by default None

        Returns
        -------
        mixed or Collection
            A single random item if count is None, otherwise a Collection.

        Raises
        ------
        ValueError
            If count is greater than collection length.
        """
        collection_count = self.count()
        if collection_count == 0:
            return None
        elif count and count > collection_count:
            raise ValueError("count argument must be inferior to collection length.")
        elif count:
            self._items = random.sample(self._items, k=count)
            return self
        else:
            return random.choice(self._items)

    def reduce(self, callback: Callable, initial: Any = 0) -> Any:
        """Reduce the collection to a single value.

        Parameters
        ----------
        callback : callable
            The callback function for reduction
        initial : mixed, optional
            The initial value, by default 0

        Returns
        -------
        mixed
            The reduced value.
        """
        return reduce(callback, self, initial)

    def reject(self, callback: Callable) -> 'Collection':
        """Filter items that do not pass a given truth test.

        Parameters
        ----------
        callback : callable
            The callback function to test items

        Returns
        -------
        Collection
            The current collection instance.
        """
        self.__checkIsCallable(callback)

        items = self.__getValue(callback) or self._items
        self._items = items
        return self

    def reverse(self) -> 'Collection':
        """Reverse items order in the collection.

        Returns
        -------
        Collection
            The current collection instance.
        """
        self._items = self[::-1]
        return self

    def serialize(self) -> List[Any]:
        """Get the collection items as a serialized array.

        Returns
        -------
        list
            The serialized items.
        """
        def _serialize(item):
            if self.__appends__:
                item.set_appends(self.__appends__)

            if hasattr(item, "serialize"):
                return item.serialize()
            elif hasattr(item, "to_dict"):
                return item.to_dict()
            return item

        return list(map(_serialize, self))

    def addRelation(self, result: Optional[Dict[str, Any]] = None) -> 'Collection':
        """Add relation data to all models in the collection.

        Parameters
        ----------
        result : dict, optional
            The relation data to add, by default None

        Returns
        -------
        Collection
            The current collection instance.
        """
        for model in self._items:
            model.add_relations(result or {})

        return self

    def shift(self) -> Any:
        """Remove and return the first item from the collection.

        Returns
        -------
        mixed
            The first item from the collection.
        """
        return self.pull(0)

    def sort(self, key: Optional[str] = None) -> 'Collection':
        """Sort through each item with a callback.

        Parameters
        ----------
        key : str, optional
            The key to sort by, by default None

        Returns
        -------
        Collection
            The current collection instance.
        """
        if key:
            self._items.sort(key=lambda x: x[key], reverse=False)
            return self

        self._items = sorted(self)
        return self

    def sum(self, key: Optional[str] = None) -> float:
        """Get the sum of the given values.

        Parameters
        ----------
        key : str, optional
            The key to sum by, by default None

        Returns
        -------
        float
            The sum of the values.
        """
        result = 0
        items = self.__getValue(key) or self._items
        try:
            result = sum(items)
        except TypeError:
            pass
        return result

    def toJson(self, **kwargs: Any) -> str:
        """Get the collection items as JSON.

        Parameters
        ----------
        **kwargs : dict
            Additional arguments to pass to json.dumps

        Returns
        -------
        str
            The JSON representation of the collection.
        """
        return json.dumps(self.serialize(), **kwargs)

    def groupBy(self, key: str) -> 'Collection':
        """Group the collection items by a given key.

        Parameters
        ----------
        key : str
            The key to group by

        Returns
        -------
        Collection
            A new collection with grouped items.
        """
        from itertools import groupby

        self.sort(key)

        new_dict = {}

        for k, v in groupby(self._items, key=lambda x: x[key]):
            new_dict.update({k: list(v)})

        return Collection(new_dict)

    def transform(self, callback: Callable) -> 'Collection':
        """Transform each item in the collection using a callback.

        Parameters
        ----------
        callback : callable
            The callback function to transform items

        Returns
        -------
        Collection
            The current collection instance.
        """
        self.__checkIsCallable(callback)
        self._items = self.__getValue(callback)
        return self

    def unique(self, key: Optional[str] = None) -> 'Collection':
        """Return only unique items from the collection array.

        Parameters
        ----------
        key : str, optional
            The key to use for uniqueness comparison, by default None

        Returns
        -------
        Collection
            A new collection with unique items.
        """
        if not key:
            items = list(set(self._items))
            return self.__class__(items)

        keys = set()
        items = []
        if isinstance(self.all(), dict):
            return self

        for item in self:
            if isinstance(item, dict):
                comparison = item.get(key)
            elif isinstance(item, str):
                comparison = item
            else:
                comparison = getattr(item, key)
            if comparison not in keys:
                items.append(item)
                keys.add(comparison)

        return self.__class__(items)

    def where(self, key: str, *args: Any) -> 'Collection':
        """Filter items by a given key value pair.

        Parameters
        ----------
        key : str
            The key to filter by
        *args : mixed
            The operator and value, or just the value

        Returns
        -------
        Collection
            A new collection with filtered items.
        """
        op = "=="
        value = args[0]

        if len(args) >= 2:
            op = args[0]
            value = args[1]

        attributes = []

        for item in self._items:
            if isinstance(item, dict):
                comparison = item.get(key)
            else:
                comparison = getattr(item, key)
            if self.__makeComparison(comparison, value, op):
                attributes.append(item)

        return self.__class__(attributes)

    def whereIn(self, key: str, values: Union[List[Any], 'Collection']) -> 'Collection':
        """Filter items where a given key's value is in a list of values.

        Parameters
        ----------
        key : str
            The key to filter by
        values : list or Collection
            The list of values to check against

        Returns
        -------
        Collection
            A new collection with filtered items.
        """
        values = self.__getItems(values)
        attributes = []

        for item in self._items:
            if isinstance(item, dict):
                comparison = item.get(key)
            else:
                comparison = getattr(item, key, None)

            # Handle string comparison for numeric values
            if comparison in values or str(comparison) in [str(v) for v in values]:
                attributes.append(item)

        return self.__class__(attributes)

    def whereNotIn(self, key: str, values: Union[List[Any], 'Collection']) -> 'Collection':
        """Filter items where a given key's value is not in a list of values.

        Parameters
        ----------
        key : str
            The key to filter by
        values : list or Collection
            The list of values to check against

        Returns
        -------
        Collection
            A new collection with filtered items.
        """
        values = self.__getItems(values)
        attributes = []

        for item in self._items:
            if isinstance(item, dict):
                comparison = item.get(key)
            else:
                comparison = getattr(item, key, None)

            # Handle string comparison for numeric values
            if comparison not in values and str(comparison) not in [str(v) for v in values]:
                attributes.append(item)

        return self.__class__(attributes)

    def zip(self, items: Union[List[Any], 'Collection']) -> 'Collection':
        """Merge the collection with the given items by index.

        Parameters
        ----------
        items : list or Collection
            The items to zip with

        Returns
        -------
        Collection
            A new collection with zipped items.

        Raises
        ------
        ValueError
            If items parameter is not a list or Collection.
        """
        items = self.__getItems(items)
        if not isinstance(items, list):
            raise ValueError("The 'items' parameter must be a list or a Collection")

        _items = []
        for x, y in zip(self, items):
            _items.append([x, y])
        return self.__class__(_items)

    def setAppends(self, appends: List[str]) -> 'Collection':
        """Set the attributes that should be appended to the Collection.

        Parameters
        ----------
        appends : list
            The attributes to append

        Returns
        -------
        Collection
            The current collection instance.
        """
        self.__appends__ += appends
        return self

    def __getValue(self, key: Union[str, Callable, None]) -> Optional[List[Any]]:
        """Get values from items using a key or callback.

        Parameters
        ----------
        key : str or callable
            The key to extract or callback to apply

        Returns
        -------
        list
            List of extracted values.
        """
        if not key:
            return None

        items = []
        for item in self:
            if isinstance(key, str):
                if hasattr(item, key) or (key in item):
                    items.append(getattr(item, key, item[key]))
            elif callable(key):
                result = key(item)
                if result:
                    items.append(result)
        return items

    def __dataGet(self, item: Any, key: str, default: Any = None) -> Any:
        """Read dictionary value from key using nested notation.

        Parameters
        ----------
        item : mixed
            The item to extract data from
        key : str
            The key to look for
        default : mixed, optional
            Default value if key not found, by default None

        Returns
        -------
        mixed
            The extracted value or default.
        """
        try:
            if isinstance(item, (list, tuple)):
                item = item[key]
            elif isinstance(item, (dict, Dotty)):
                # Use dotty for nested key access
                dotty_key = key.replace("*", ":")
                dotty_item = dotty(item)
                item = dotty_item.get(dotty_key, default)
            elif isinstance(item, object):
                item = getattr(item, key)
        except (IndexError, AttributeError, KeyError, TypeError):
            return self.__value(default)

        return item

    def __value(self, value: Any) -> Any:
        """Get the value from a callable or return the value itself.

        Parameters
        ----------
        value : mixed
            The value or callable to evaluate

        Returns
        -------
        mixed
            The evaluated value.
        """
        if callable(value):
            return value()
        return value

    def __checkIsCallable(self, callback: Any, raise_exception: bool = True) -> bool:
        """Check if the given callback is callable.

        Parameters
        ----------
        callback : mixed
            The callback to check
        raise_exception : bool, optional
            Whether to raise exception if not callable, by default True

        Returns
        -------
        bool
            True if callable, False otherwise.

        Raises
        ------
        ValueError
            If callback is not callable and raise_exception is True.
        """
        if not callable(callback):
            if not raise_exception:
                return False
            raise ValueError("The 'callback' should be a function")
        return True

    def __makeComparison(self, a: Any, b: Any, op: str) -> bool:
        """Make a comparison between two values using an operator.

        Parameters
        ----------
        a : mixed
            First value
        b : mixed
            Second value
        op : str
            Comparison operator

        Returns
        -------
        bool
            Result of the comparison.
        """
        operators = {
            "<": operator.lt,
            "<=": operator.le,
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            ">=": operator.ge,
        }
        return operators[op](a, b)

    def __iter__(self) -> Any:
        """
        Iterate over the items in the collection.

        Returns
        -------
        generator
            A generator yielding each item in the collection.
        """

        # Yield each item in the internal _items list
        for item in self._items:
            yield item

    def __eq__(self, other: Any) -> bool:
        """
        Compare the current collection with another object for equality.

        Parameters
        ----------
        other : Any
            The object to compare with the current collection.

        Returns
        -------
        bool
            True if the collections are equal, False otherwise.
        """

        # If the other object is a Collection, compare its items with self._items
        if isinstance(other, Collection):
            return other.all() == self._items

        # Otherwise, compare the other object directly with self._items
        return other == self._items

    def __getitem__(self, item: Union[int, slice]) -> Union[Any, 'Collection']:
        """
        Retrieve an item or a slice of items from the collection.

        Parameters
        ----------
        item : int or slice
            The index or slice to retrieve from the collection.

        Returns
        -------
        Any or Collection
            The item at the specified index, or a new Collection containing the sliced items.

        Notes
        -----
        If a slice is provided, a new Collection instance is returned containing the sliced items.
        If an integer index is provided, the corresponding item is returned.
        """

        # If the item is a slice, return a new Collection with the sliced items
        if isinstance(item, slice):
            return self.__class__(self._items[item])

        # Otherwise, return the item at the specified index
        return self._items[item]

    def __setitem__(self, key: Any, value: Any) -> None:
        """
        Set the value of an item in the collection at the specified key.

        Parameters
        ----------
        key : Any
            The index or key at which to set the value.
        value : Any
            The value to assign at the specified key.

        Returns
        -------
        None
            This method does not return a value.

        Notes
        -----
        Updates the internal _items list at the given key with the provided value.
        """

        # Assign the value to the specified key in the internal _items list
        self._items[key] = value

    def __delitem__(self, key: Any) -> None:
        """
        Remove an item from the collection at the specified key.

        Parameters
        ----------
        key : Any
            The index or key of the item to remove from the collection.

        Returns
        -------
        None
            This method does not return a value.

        Notes
        -----
        Deletes the item at the given key from the internal _items list.
        """

        # Delete the item at the specified key from the internal _items list
        del self._items[key]

    def __ne__(self, other: Any) -> bool:
        """
        Determine if the current collection is not equal to another object.

        Parameters
        ----------
        other : Any
            The object to compare with the current collection.

        Returns
        -------
        bool
            True if the collections are not equal, False otherwise.

        Notes
        -----
        Uses the internal items for comparison. If `other` is a Collection, compares its items.
        """

        # Extract items from the other object if it is a Collection
        other = self.__getItems(other)

        # Return True if the items are not equal, False otherwise
        return other != self._items

    def __len__(self) -> int:
        """
        Return the number of items in the collection.

        Returns
        -------
        int
            The total number of items contained in the collection.
        """

        # Return the length of the internal _items list
        return len(self._items)

    def __le__(self, other: Any) -> bool:
        """
        Determine if the current collection is less than or equal to another object.

        Parameters
        ----------
        other : Any
            The object to compare with the current collection.

        Returns
        -------
        bool
            True if the current collection is less than or equal to the other object, False otherwise.

        Notes
        -----
        Uses the internal items for comparison. If `other` is a Collection, compares its items.
        """

        # Extract items from the other object if it is a Collection
        other = self.__getItems(other)

        # Return True if the items are less than or equal, False otherwise
        return self._items <= other

    def __lt__(self, other: Any) -> bool:
        """
        Determine if the current collection is less than another object.

        Parameters
        ----------
        other : Any
            The object to compare with the current collection.

        Returns
        -------
        bool
            True if the current collection is less than the other object, False otherwise.

        Notes
        -----
        Uses the internal items for comparison. If `other` is a Collection, compares its items.
        """

        # Extract items from the other object if it is a Collection
        other = self.__getItems(other)

        # Return True if the items are less than, False otherwise
        return self._items < other

    def __ge__(self, other: Any) -> bool:
        """
        Determine if the current collection is greater than or equal to another object.

        Parameters
        ----------
        other : Any
            The object to compare with the current collection.

        Returns
        -------
        bool
            True if the current collection is greater than or equal to the other object, False otherwise.

        Notes
        -----
        Uses the internal items for comparison. If `other` is a Collection, compares its items.
        """

        # Extract items from the other object if it is a Collection
        other = self.__getItems(other)

        # Return True if the items are greater than or equal, False otherwise
        return self._items >= other

    def __gt__(self, other: Any) -> bool:
        """
        Determine if the current collection is greater than another object.

        Parameters
        ----------
        other : Any
            The object to compare with the current collection.

        Returns
        -------
        bool
            True if the current collection is greater than the other object, False otherwise.

        Notes
        -----
        Uses the internal items for comparison. If `other` is a Collection, compares its items.
        """

        # Extract items from the other object if it is a Collection
        other = self.__getItems(other)

        # Return True if the items are greater than, False otherwise
        return self._items > other

    @classmethod
    def __getItems(cls, items: Any) -> Any:
        """
        Extracts the underlying items from a Collection instance or returns the input as-is.

        Parameters
        ----------
        items : Collection or Any
            The input to extract items from. If a Collection, its items are returned; otherwise, the input is returned unchanged.

        Returns
        -------
        Any
            The extracted items if `items` is a Collection, otherwise the original input.
        """

        # If the input is a Collection, extract its items using the all() method
        if isinstance(items, Collection):
            items = items.all()

        # Return the extracted items or the original input
        return items


