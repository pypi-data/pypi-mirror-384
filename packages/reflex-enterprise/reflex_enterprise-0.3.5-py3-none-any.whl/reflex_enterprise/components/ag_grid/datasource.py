"""Datasource classes for AgGrid components."""

import json
from typing import Any, ClassVar, Type, TypeVar

import reflex as rx
from reflex.base import Base
from reflex.components.props import PropsBase
from reflex.utils.format import to_camel_case
from reflex.utils.serializers import serialize
from reflex.vars import Var
from reflex.vars.function import ArgsFunctionOperation, FunctionStringVar, FunctionVar
from reflex.vars.object import ObjectVar
from reflex.vars.sequence import ArrayVar

from reflex_enterprise.utils import encode_uri_component, fetch, get_backend_url
from reflex_enterprise.vars import PromiseVar


def _try_json_loads(value: str) -> Any:
    """Try to load a JSON string.

    Args:
        value: The JSON string to load.

    Returns:
        The loaded JSON object or the original string if loading fails.
    """
    try:
        return json.loads(value)
    except ValueError:
        return value


class DatasourceBase(Base):
    """Base datasource class for AgGrid components."""

    rowCount: Var[int] | int | None = None  # noqa: N815
    getRows: Var | None = None  # noqa: N815

    uri: str | None = None
    endpoint_uri: str | Var[str] | None = None
    endpoint_kwargs: dict[str, str] | Var[dict[str, str]] | None = None

    def _get_rows_function(self) -> Var:
        if self.getRows is not None:
            return self.getRows
        raise NotImplementedError("_get_rows_function must be implemented by subclass")

    def dict(self, **kwargs):
        """Convert the object to a dictionary.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The object as a dictionary.
        """
        kwargs.setdefault("exclude", set()).update(
            {"getRows", "uri", "endpoint_uri", "endpoint_kwargs"}
        )
        d = super().dict(**kwargs)
        d["getRows"] = self._get_rows_function()
        return d

    def json(self) -> str:
        """Convert the object to a json-like string.

        Vars will be unwrapped so they can represent actual JS var names and functions.

        Keys will be converted to camelCase.

        Returns:
            The object as a Javascript Object literal.
        """
        return self.__config__.json_dumps(
            {to_camel_case(key): value for key, value in self.dict().items()},
            default=serialize,
        )


DATASOURCE_PARAMS = TypeVar(
    "DATASOURCE_PARAMS",
    bound="DatasourceParamsBase",
)


class DatasourceParamsBase(PropsBase):
    """Base class for any Datasource params."""

    @classmethod
    def from_request(
        cls: Type[DATASOURCE_PARAMS], data: dict[str, str]
    ) -> DATASOURCE_PARAMS:
        """Create a DatasourceParams object from a dictionary.

        Args:
            data: The dictionary to convert.

        Returns:
            A DatasourceParams object.
        """
        kwargs = {
            to_camel_case(key): _try_json_loads(value) for key, value in data.items()
        }
        return cls(**kwargs)

    def __getattr__(self, item: str):
        """Get an attribute from the object."""
        if (cc_item := to_camel_case(item)) != item:
            return getattr(self, cc_item)
        return super().__getattribute__(item)


class DatasourceParams(DatasourceParamsBase):
    """Datasource getRows params for infinite row model."""

    startRow: int  # noqa: N815
    endRow: int  # noqa: N815
    sortModel: list[dict[str, str]]  # noqa: N815
    filterModel: dict[str, dict[str, str]]  # noqa: N815


class DatasourceEncodedVarMixin:
    """Common methods for Datasource param vars."""

    def __getattr__(self, item: str):
        """Get an attribute from the object."""
        if (cc_item := to_camel_case(item)) != item:
            return getattr(self, cc_item)
        return super().__getattr__(item)  # pyright: ignore [reportAttributeAccessIssue]

    def get_param_mapping(self) -> Var[dict[str, Any]]:
        """Get the mapping of params to their encoded values.

        Returns:
            A dictionary mapping param names to their encoded values.
        """
        return Var.create(
            {
                key: encode_uri_component(getattr(self, key).to_string())
                for key in self._var_type.__fields__
            }
        )


class DatasourceParamsVar(DatasourceEncodedVarMixin, ObjectVar[DatasourceParams]):
    """A Var wrapping DatasourceParams with some extra functionality."""

    @property
    def success_callback(self) -> FunctionVar:
        """Get the success callback function."""
        return FunctionStringVar.create(f"{self}.successCallback")

    @property
    def fail_callback(self) -> FunctionVar:
        """Get the fail callback function."""
        return FunctionStringVar.create(f"{self}.failCallback")


PARAMS = DatasourceParamsVar("params", _var_type=DatasourceParams)
DATA = ArrayVar("data", _var_type=list[dict[str, str]])


class Datasource(DatasourceBase):
    """Infinite row model datasource for AgGrid components."""

    __default_query_params__: ClassVar[Var[dict[str, Var]]] = PARAMS.get_param_mapping()

    def get_uri(self) -> Var[str] | str:
        """Get the URI for the datasource.

        Returns:
            The URI for the datasource.
        """
        if self.uri:
            return self.uri

        if not self.endpoint_uri:
            raise ValueError("uri or endpoint_uri must be set")

        query = (
            self.__default_query_params__.merge(self.endpoint_kwargs)  # pyright: ignore [reportAttributeAccessIssue]
            if self.endpoint_kwargs is not None
            else self.__default_query_params__
        )

        return Var.create(
            f"{self.endpoint_uri}?{query.items().foreach(lambda kv: f'{kv[0]}={kv[1]}').join('&')}"  # pyright: ignore [reportAttributeAccessIssue]
        )

    def _get_rows_function(self) -> str | Var:
        return ArgsFunctionOperation.create(
            args_names=(str(PARAMS),),
            return_expr=fetch(
                get_backend_url(self.get_uri()),
            )
            .then(
                ArgsFunctionOperation.create(
                    args_names=("response",),
                    return_expr=PromiseVar("response.json()").then(
                        ArgsFunctionOperation.create(
                            args_names=(str(DATA),),
                            return_expr=PARAMS.success_callback(
                                DATA,
                                rx.cond(
                                    DATA.length() < (PARAMS.end_row - PARAMS.start_row),
                                    PARAMS.start_row + DATA.length(),
                                    -1,
                                ),
                            ),
                        )
                    ),
                )
            )
            .catch(
                ArgsFunctionOperation.create(
                    args_names=("error",), return_expr=PARAMS.fail_callback()
                )
            ),
        )


class SSRMDatasourceRequestParams(DatasourceParams):
    """Datasource getRows params for server-side row model."""

    rowGroupCols: list[dict[str, str]]  # noqa: N815
    groupKeys: list[str]  # noqa: N815
    valueCols: list[dict[str, str]]  # noqa: N815
    pivotMode: bool  # noqa: N815
    pivotCols: list[dict[str, str]]  # noqa: N815


class SSRMDatasourceParams(Base):
    """Datasource params for server-side row model."""

    request: SSRMDatasourceRequestParams


class SSRMDatasourceRequestParamsVar(
    DatasourceEncodedVarMixin, ObjectVar[SSRMDatasourceRequestParams]
):
    """A Var wrapping SSRMDatasourceRequestParams with some extra functionality."""


class SSRMDatasourceParamsVar(ObjectVar[SSRMDatasourceParams]):
    """A Var wrapping SSRMDatasourceParams with some extra functionality."""

    @property
    def request(self) -> SSRMDatasourceRequestParamsVar:
        """Get the request params."""
        return SSRMDatasourceRequestParamsVar(
            f"{self}.request", _var_type=SSRMDatasourceRequestParams
        )

    @property
    def success(self) -> FunctionVar:
        """Get the success callback function."""
        return FunctionStringVar.create(f"{self}.success")

    @property
    def fail(self) -> FunctionVar:
        """Get the fail callback function."""
        return FunctionStringVar.create(f"{self}.fail")


SSPARAMS = SSRMDatasourceParamsVar("params", _var_type=SSRMDatasourceParams)


class SSRMDatasource(Datasource):
    """Server-side row model datasource class for AgGrid components."""

    __default_query_params__: ClassVar[Var[dict[str, Var]]] = (
        SSPARAMS.request.get_param_mapping()
    )

    def _get_rows_function(self) -> str | Var:
        return ArgsFunctionOperation.create(
            args_names=(str(SSPARAMS),),
            return_expr=fetch(
                get_backend_url(self.get_uri()),
            )
            .then(
                ArgsFunctionOperation.create(
                    args_names=("response",),
                    return_expr=PromiseVar("response.json()").then(
                        ArgsFunctionOperation.create(
                            args_names=(str(DATA),),
                            return_expr=SSPARAMS.success({"rowData": DATA}),
                        )
                    ),
                )
            )
            .catch(
                ArgsFunctionOperation.create(
                    args_names=("error",), return_expr=SSPARAMS.fail()
                )
            ),
        )
