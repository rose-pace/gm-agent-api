from typing import Dict, List, Union, Any, Optional
from pydantic import BaseModel


class ChromaFilter:
    """
    A chainable filter builder for Chroma DB queries.
    """
    def __init__(self):
        """
        Initialize an empty filter.
        """
        self.filters = []
        self.current_filter = {}

    def field(self, field_name: str) -> 'ChromaFilter':
        """
        Start filtering on a specific field.
        
        Args:
            field_name: The name of the field to filter on
            
        Returns:
            Self for method chaining
        """
        self.current_filter = {'field_name': field_name}
        return self

    def equals(self, value: Any) -> 'ChromaFilter':
        """
        Add an equals filter for the current field.
        
        Args:
            value: The value to filter for
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using equals()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$eq': value}})
        self.current_filter = {}
        return self

    def not_equals(self, value: Any) -> 'ChromaFilter':
        """
        Add a not equals filter for the current field.
        
        Args:
            value: The value to filter against
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using not_equals()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$ne': value}})
        self.current_filter = {}
        return self

    def in_list(self, values: List[Any]) -> 'ChromaFilter':
        """
        Add an in filter for the current field.
        
        Args:
            values: The list of values to filter for
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using in_list()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$in': values}})
        self.current_filter = {}
        return self

    def not_in_list(self, values: List[Any]) -> 'ChromaFilter':
        """
        Add a not in filter for the current field.
        
        Args:
            values: The list of values to filter against
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using not_in_list()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$nin': values}})
        self.current_filter = {}
        return self

    def greater_than(self, value: Union[int, float]) -> 'ChromaFilter':
        """
        Add a greater than filter for the current field.
        
        Args:
            value: The value to compare against
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using greater_than()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$gt': value}})
        self.current_filter = {}
        return self

    def greater_than_equals(self, value: Union[int, float]) -> 'ChromaFilter':
        """
        Add a greater than or equal to filter for the current field.
        
        Args:
            value: The value to compare against
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using greater_than_equals()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$gte': value}})
        self.current_filter = {}
        return self

    def less_than(self, value: Union[int, float]) -> 'ChromaFilter':
        """
        Add a less than filter for the current field.
        
        Args:
            value: The value to compare against
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using less_than()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$lt': value}})
        self.current_filter = {}
        return self

    def less_than_equals(self, value: Union[int, float]) -> 'ChromaFilter':
        """
        Add a less than or equal to filter for the current field.
        
        Args:
            value: The value to compare against
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using less_than_equals()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$lte': value}})
        self.current_filter = {}
        return self

    def contains(self, value: str) -> 'ChromaFilter':
        """
        Add a contains filter for the current field (useful for string fields).
        
        Args:
            value: The substring to check for
            
        Returns:
            Self for method chaining
        """
        if 'field_name' not in self.current_filter:
            raise ValueError('Must call field() before using contains()')
        field_name = self.current_filter['field_name']
        self.filters.append({field_name: {'$contains': value}})
        self.current_filter = {}
        return self

    def and_group(self, filters: List[Dict[str, Any]]) -> 'ChromaFilter':
        """
        Add an AND filter combining multiple filters.
        
        Args:
            filters: A list of filter dictionaries to combine with AND
            
        Returns:
            Self for method chaining
        """
        self.filters.append({'$and': filters})
        return self

    def or_group(self, filters: List[Dict[str, Any]]) -> 'ChromaFilter':
        """
        Add an OR filter combining multiple filters.
        
        Args:
            filters: A list of filter dictionaries to combine with OR
            
        Returns:
            Self for method chaining
        """
        self.filters.append({'$or': filters})
        return self

    def generate(self) -> Dict[str, Any]:
        """
        Generates the final filter dictionary to be passed to a Chroma DB query.
        
        Returns:
            A dictionary to be used as a filter in a Chroma DB query
        """
        if len(self.filters) == 1:
            return self.filters[0]
        elif len(self.filters) > 1:
            return {'$and': self.filters}
        else:
            return {}


def create_filter() -> ChromaFilter:
    """
    Creates a ChromaFilter instance to start building a filter chain.
    
    Returns:
        A new ChromaFilter instance
    """
    return ChromaFilter()


# Convenience methods for common filtering patterns
def filter_by_category(category: str) -> Dict[str, Any]:
    """
    Shortcut function to filter documents by category.
    
    Args:
        category: The category to filter for
        
    Returns:
        A dictionary to be used as a filter for category
    """
    return create_filter().field('category').equals(category).generate()


def filter_by_author(author: str) -> Dict[str, Any]:
    """
    Shortcut function to filter documents by author.
    
    Args:
        author: The author to filter for
        
    Returns:
        A dictionary to be used as a filter for author
    """
    return create_filter().field('author').equals(author).generate()


def filter_by_date_range(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Shortcut function to filter documents by a date range.
    
    Args:
        start_date: The start date in the format 'YYYY-MM-DD'
        end_date: The end date in the format 'YYYY-MM-DD'
        
    Returns:
        A dictionary to be used as a filter for date range
    """
    return (create_filter()
            .field('date').greater_than_equals(start_date)
            .field('date').less_than_equals(end_date)
            .generate())