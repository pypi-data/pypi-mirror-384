from __future__ import annotations
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Tuple
from pydantic import BaseModel

from nys_constants.nys_constants import SortOrder
from .utils import prepare_filter_value

T = TypeVar('T', bound=BaseModel)
FilterType = TypeVar('FilterType', bound=BaseModel)

class BaseResource(Generic[T]):
    """Base class for API resources. e.g. Job, Request, Sku, etc"""
    
    def __init__(self, client: 'NysClient'):
        self._client = client

    #TODO consider renaming to _get
    def _search(
        self,
        *,
        endpoint: str,
        response_model: Type[T],
        filters: Optional[FilterType] = None,
        search: Optional[str] = None,
        sort_by: Optional[Union[str, List[Tuple[str, SortOrder]]]] = None,
        page: int = 1,
        size: int = 50
    ) -> List[T]:
        """Generic search method used by all resource-specific search methods."""
        params: Dict[str, Any] = {
            "page": page,
            "size": size
        }

        # Add sorting parameters if provided
        if sort_by:
            if isinstance(sort_by, str):
                params["sort_by"] = sort_by
            else:
                # Convert list of tuples to comma-separated string with prefixes
                sort_str = ','.join(
                    f"{'-' if order == SortOrder.DESC else ''}{field}"
                    for field, order in sort_by
                )
                params["sort_by"] = sort_str

        # Add search fields if provided
        if search:
            if isinstance(search, str):
                # leave the validation to the API
                params['search'] = search
            else:
                raise ValueError("search must be a string")

        # Add filters if provided
        if filters:
            # Convert filter model to dict and remove None values
            filter_dict = filters.dict(exclude_unset=True, exclude_defaults=True)
            
            # Add each non-None filter to params, converting values as needed
            for field_name, value in filter_dict.items():
                if value is not None:
                    params[field_name] = prepare_filter_value(value)

        # Make API request
        response = self._client._request(
            method="GET",
            endpoint=endpoint,
            params=params
        )
        
        # Parse response into list of model instances
        data = response.json()
        return [response_model(**item) for item in data["items"]] 