"""Utilities for handling paginated API responses, cursor-based pagination, filtering, sorting, etc."""

import math as _math
import typing as _typing

import pydantic as _pydantic

T = _typing.TypeVar("T")


class PaginatedResponse(_pydantic.BaseModel, _typing.Generic[T]):
    """Pydantic model for paginated response
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[PaginationParams, Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...
    >>> return PaginatedResponse[Order](
            data=orders,
            total=count,
            page=params.page,
            page_size=params.page_size,
            prev=PaginatedResponse.get_prev_page(params.page),
            next=PaginatedResponse.get_next_page(count, params.page_size, params.page),
            last=PaginatedResponse.get_last_page(count, params.page_size),
        )
    """

    data: list[T]
    total: int = _pydantic.Field(description="The total number of items")
    page: int = _pydantic.Field(description="The current page number")
    page_size: int = _pydantic.Field(description="The number of items per page")
    prev: _typing.Optional[int] = _pydantic.Field(
        None, description="The previous page number"
    )
    next: _typing.Optional[int] = _pydantic.Field(
        None, description="The next page number"
    )
    last: _typing.Optional[int] = _pydantic.Field(
        None, description="The last page number"
    )

    @staticmethod
    def get_next_page(total: int, page_size: int, page: int) -> _typing.Optional[int]:
        """Get the next page number"""
        if page < _math.ceil(total / page_size):
            return page + 1
        return None

    @staticmethod
    def get_prev_page(page: int) -> _typing.Optional[int]:
        """Get the previous page number"""
        if page > 1:
            return page - 1
        return None

    @staticmethod
    def get_last_page(total: int, page_size: int) -> int:
        """Get the last page number"""
        return max(1, _math.ceil(total / page_size))


class PaginationParams(_pydantic.BaseModel, _typing.Generic[T]):
    """Standard pagination parameters for usage in API endpoints. Check the [fastapi docs](https://fastapi.tiangolo.com/tutorial/query-param-models/?h=qu#query-parameters-with-a-pydantic-model) for usage examples.
    You should inherit from this class when adding additional parameters. You should use this class in combination with `PaginatedResponse` to return the paginated response.
    Usage:
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[PaginationParams[Order], Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...

    The default size is 10 items per page and there is a `HeavyPaginationParams` class with 100 items per page. You can override this default:
    >>> class LightPaginationParams(PaginationParams):
    >>>     page_size: int = Field(default=5, description="The number of items per page")
    """

    page: int = _pydantic.Field(default=1, description="The current page number")
    page_size: _typing.Annotated[int, _pydantic.Field(ge=1, le=100)] = _pydantic.Field(
        10, description="The number of items per page. Default is 10, max is 100."
    )


class HeavyPaginationParams(PaginationParams[T]):
    """Pagination parameters with a higher default size. Refer to `PaginationParams` for usage examples."""

    page_size: _typing.Annotated[int, _pydantic.Field(ge=1, le=1000)] = _pydantic.Field(
        100, description="The number of items per page. Default is 100, max is 1000."
    )


class SortParams(_pydantic.BaseModel, _typing.Generic[T]):
    """Standard sort parameters for usage in API endpoints. Check the [fastapi docs](https://fastapi.tiangolo.com/tutorial/query-param-models/?h=qu#query-parameters-with-a-pydantic-model) for usage examples.
    You should inherit from this class when adding additional parameters.
    Usage:
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[SortParams[Order], Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...
    """

    sort_order: _typing.Optional[_typing.Literal["asc", "desc"]] = _pydantic.Field(
        None, description="The order to sort by"
    )
    sort_by: _typing.Optional[str] = _pydantic.Field(
        None, description="The field to sort by"
    )

    @_pydantic.model_validator(mode="after")
    def validate_sort(self):
        self._validate_sort()
        return self

    def _validate_sort(self):
        # Extract the generic argument type
        args = self.__pydantic_generic_metadata__.get("args")
        if not args or not issubclass(args[0], _pydantic.BaseModel):
            raise TypeError(
                "SortParams must be used with a Pydantic BaseModel as a generic parameter"
            )
        if self.sort_by:
            # check if the sort field is valid
            model: _typing.Type[_pydantic.BaseModel] = args[0]
            if self.sort_by not in model.model_fields:
                raise ValueError(
                    f"Invalid field: '{self.sort_by}'. Must be one of: {list(model.model_fields)}"
                )
        if self.sort_order and self.sort_order not in ["asc", "desc"]:
            raise ValueError(
                f"Invalid order: '{self.sort_order}' — must be one of: ['asc', 'desc']"
            )
        if (
            self.sort_order
            and self.sort_by is None
            or self.sort_by
            and self.sort_order is None
        ):
            raise ValueError("sort_order and sort_by must be provided together")
        return self


class FilterParams(_pydantic.BaseModel, _typing.Generic[T]):
    """Standard filter parameters for usage in API endpoints. Check the [fastapi docs](https://fastapi.tiangolo.com/tutorial/query-param-models/?h=qu#query-parameters-with-a-pydantic-model) for usage examples.
    You should inherit from this class when adding additional parameters.
    Usage:
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[FilterParams[Order], Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...
    """

    filter_by: _typing.Optional[str] = _pydantic.Field(
        None, description="The field to filter by"
    )
    filter_value: _typing.Optional[str] = _pydantic.Field(
        None, description="The value to filter with"
    )
    # currently openapi-gen does not support typing.Any in combo with None, so we use str
    # this is fine since the input is a string anyways from the request and the correct type is enforced by the model validator from the filter_by field

    @_pydantic.model_validator(mode="after")
    def validate_filter(self):
        self._validate_filter()
        return self

    def _validate_filter(self):
        if self.filter_by and not self.filter_value:
            raise ValueError("filter_by and filter_value must be provided together")
        if self.filter_by:
            # Extract the generic argument type
            args = self.__pydantic_generic_metadata__.get("args")
            if not args or not issubclass(args[0], _pydantic.BaseModel):
                raise TypeError(
                    "FilterParams must be used with a Pydantic BaseModel as a generic parameter"
                )
            # check if the filter field is valid
            model: _typing.Type[_pydantic.BaseModel] = args[0]
            if self.filter_by not in model.model_fields:
                raise ValueError(
                    f"Invalid field: '{self.filter_by}'. Must be one of: {list(model.model_fields)}"
                )
            self.filter_value = _enforce_field_type(
                model, self.filter_by, self.filter_value
            )
        return self


class SortFilterParams(SortParams[T], FilterParams[T]):
    """Combines sort and filter parameters. Just a convenience class for when you need to combine sort and filter parameters.
    You should inherit from this class when adding additional parameters.
    Usage:
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[SortFilterParams[Order], Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...
    """

    @_pydantic.model_validator(mode="after")
    def validate_sort_filter(self):
        self._validate_sort()
        self._validate_filter()
        return self


class PageFilterParams(PaginationParams[T], FilterParams[T]):
    """Combines pagination and filter parameters. Just a convenience class for when you need to combine pagination and filter parameters.
    You should inherit from this class when adding additional parameters.
    Usage:
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[PageFilterParams[Order], Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...
    """

    @_pydantic.model_validator(mode="after")
    def validate_page_filter(self):
        self._validate_filter()
        return self


class PageSortParams(PaginationParams[T], SortParams[T]):
    """Combines pagination and sort parameters. Just a convenience class for when you need to combine pagination and sort parameters.
    You should inherit from this class when adding additional parameters.
    Usage:
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[PageSortParams[Order], Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...
    """

    @_pydantic.model_validator(mode="after")
    def validate_page_sort(self):
        self._validate_sort()
        return self


class PageSortFilterParams(
    PaginationParams[T],
    SortParams[T],
    FilterParams[T],
):
    """Combines pagination, filter, and sort parameters. Just a convenience class for when you need to combine pagination, filter, and sort parameters.
    You should inherit from this class when adding additional parameters.
    Usage:
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[PageSortFilterParams[Order], Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...
    """

    @_pydantic.model_validator(mode="after")
    def validate_filter_combo(self):
        self._validate_filter()
        self._validate_sort()
        return self


class HeavyPageSortFilterParams(
    HeavyPaginationParams[T], FilterParams[T], SortParams[T]
):
    """Combines heavy pagination, filter, and sort parameters. Just a convenience class for when you need to combine heavy pagination, filter, and sort parameters.
    You should inherit from this class when adding additional parameters.
    Usage:
    >>> @router.get("", operation_id="getOrders")
    >>> async def get_orders(
    >>>     params: Annotated[HeavyPageSortFilterParams[Order], Query()],
    >>> ) -> PaginatedResponse[Order]:
    >>>     ...
    """

    @_pydantic.model_validator(mode="after")
    def validate_heavy_page_sort_filter(self):
        self._validate_filter()
        self._validate_sort()
        return self


_FIELD_ADAPTER_CACHE: dict[tuple[type, str], _pydantic.TypeAdapter] = {}


def _get_field_adapter(
    model: _typing.Type[_pydantic.BaseModel], field_name: str
) -> _pydantic.TypeAdapter:
    key = (model, field_name)
    adapter = _FIELD_ADAPTER_CACHE.get(key)
    if adapter is not None:
        return adapter
    expected_type = model.model_fields[field_name].annotation
    adapter = _pydantic.TypeAdapter(expected_type)
    _FIELD_ADAPTER_CACHE[key] = adapter
    return adapter


def _enforce_field_type(
    model: _typing.Type[_pydantic.BaseModel], field_name: str, value: _typing.Any
) -> _typing.Any:
    """
    Coerce or validate `value` by leveraging Pydantic's TypeAdapter for the field's
    annotation. This supports Optional/Union/Literal and standard primitives using
    Pydantic's well-tested conversion rules.

    Raises ValueError on validation errors to preserve previous behavior.
    """

    expected_type = model.model_fields[field_name].annotation
    if expected_type is None:
        return value

    try:
        # Pre-normalize textual nulls for Optional/Union[..., None]
        origin = _typing.get_origin(expected_type)
        if origin is _typing.Union:
            args = _typing.get_args(expected_type)
            allows_none = any(a is type(None) for a in args)
            if (
                allows_none
                and isinstance(value, str)
                and value.strip().lower() in ("none", "null", "")
            ):
                value = None

        adapter = _get_field_adapter(model, field_name)
        return adapter.validate_python(value)
    except Exception:
        raise ValueError(
            f"Expected {expected_type} for field {field_name}, got {type(value)}"
        )
