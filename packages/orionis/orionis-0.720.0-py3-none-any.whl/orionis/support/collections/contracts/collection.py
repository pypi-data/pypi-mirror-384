from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

class ICollection(ABC):

    @abstractmethod
    def take(self, number: int) -> 'ICollection':
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def all(self) -> List[Any]:
        """Get all items in the collection.

        Returns
        -------
        list
            All items in the collection.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def chunk(self, size: int) -> 'ICollection':
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
        pass

    @abstractmethod
    def collapse(self) -> 'ICollection':
        """Collapse the collection of arrays into a single, flat collection.

        Returns
        -------
        Collection
            A new flattened collection.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def count(self) -> int:
        """Get the number of items in the collection.

        Returns
        -------
        int
            The number of items.
        """
        pass

    @abstractmethod
    def diff(self, items: Union[List[Any], 'ICollection']) -> 'ICollection':
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
        pass

    @abstractmethod
    def each(self, callback: Callable) -> 'ICollection':
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def filter(self, callback: Callable) -> 'ICollection':
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
        pass

    @abstractmethod
    def flatten(self) -> 'ICollection':
        """Flatten a multi-dimensional collection into a single dimension.

        Returns
        -------
        Collection
            A new flattened collection.
        """
        pass

    @abstractmethod
    def forget(self, *keys: Any) -> 'ICollection':
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
        pass

    @abstractmethod
    def forPage(self, page: int, number: int) -> 'ICollection':
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def isEmpty(self) -> bool:
        """Determine if the collection is empty.

        Returns
        -------
        bool
            True if the collection is empty, False otherwise.
        """
        pass

    @abstractmethod
    def map(self, callback: Callable) -> 'ICollection':
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
        pass

    @abstractmethod
    def mapInto(self, cls: type, method: Optional[str] = None, **kwargs: Any) -> 'ICollection':
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
        pass

    @abstractmethod
    def merge(self, items: Union[List[Any], 'ICollection']) -> 'ICollection':
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
        pass

    @abstractmethod
    def pluck(self, value: str, key: Optional[str] = None) -> 'ICollection':
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
        pass

    @abstractmethod
    def pop(self) -> Any:
        """Remove and return the last item from the collection.

        Returns
        -------
        mixed
            The last item from the collection.
        """
        pass

    @abstractmethod
    def prepend(self, value: Any) -> 'ICollection':
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def push(self, value: Any) -> 'ICollection':
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
        pass

    @abstractmethod
    def put(self, key: Any, value: Any) -> 'ICollection':
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
        pass

    @abstractmethod
    def random(self, count: Optional[int] = None) -> Union[Any, 'ICollection', None]:
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def reject(self, callback: Callable) -> 'ICollection':
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
        pass

    @abstractmethod
    def reverse(self) -> 'ICollection':
        """Reverse items order in the collection.

        Returns
        -------
        Collection
            The current collection instance.
        """
        pass

    @abstractmethod
    def serialize(self) -> List[Any]:
        """Get the collection items as a serialized array.

        Returns
        -------
        list
            The serialized items.
        """
        pass

    @abstractmethod
    def addRelation(self, result: Optional[Dict[str, Any]] = None) -> 'ICollection':
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
        pass

    @abstractmethod
    def shift(self) -> Any:
        """Remove and return the first item from the collection.

        Returns
        -------
        mixed
            The first item from the collection.
        """
        pass

    @abstractmethod
    def sort(self, key: Optional[str] = None) -> 'ICollection':
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def groupBy(self, key: str) -> 'ICollection':
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
        pass

    @abstractmethod
    def transform(self, callback: Callable) -> 'ICollection':
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
        pass

    @abstractmethod
    def unique(self, key: Optional[str] = None) -> 'ICollection':
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
        pass

    @abstractmethod
    def where(self, key: str, *args: Any) -> 'ICollection':
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
        pass

    @abstractmethod
    def whereIn(self, key: str, values: Union[List[Any], 'ICollection']) -> 'ICollection':
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
        pass

    @abstractmethod
    def whereNotIn(self, key: str, values: Union[List[Any], 'ICollection']) -> 'ICollection':
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
        pass

    @abstractmethod
    def zip(self, items: Union[List[Any], 'ICollection']) -> 'ICollection':
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
        pass

    @abstractmethod
    def setAppends(self, appends: List[str]) -> 'ICollection':
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
        pass
