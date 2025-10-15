from __future__ import annotations
import typing
from instaui.components.slot import Slot

from instaui_tdesign.components._icon_param_utils import (
    make_icon_for_bool_or_str,
    make_icon_for_str,
)
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack, Self
from instaui.common.binding_track_mixin import is_binding_tracker
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef

# region pandas protocol


@typing.runtime_checkable
class PandasDataFrameProtocol(typing.Protocol):
    def to_dict(self, orient: typing.Any) -> list: ...

    @property
    def columns(self) -> typing.Iterable: ...


# endregion


# region polars protocol


@typing.runtime_checkable
class PolarsDataFrameProtocol(typing.Protocol):
    @property
    def columns(self) -> list[str]: ...

    def to_dicts(self) -> list: ...


# endregion


class BaseTable(BaseElement):
    def __init__(
        self,
        data: typing.Union[
            TMaybeRef[typing.List],
            PandasDataFrameProtocol,
            PolarsDataFrameProtocol,
            None,
        ] = None,
        columns: typing.Optional[TMaybeRef[typing.List[TBaseTableCol]]] = None,
        row_key: typing.Optional[TMaybeRef[str]] = None,
        **kwargs: Unpack[TBaseTableProps],
    ):
        super().__init__("t-base-table")
        _common_table_props_update(kwargs)  # type: ignore
        if isinstance(data, PolarsDataFrameProtocol):
            data = _polars_to_data(data)
        elif isinstance(data, PandasDataFrameProtocol):
            data = _pandas_to_data(data)

        self.props({"data": data, "columns": columns, "row-key": row_key})

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_active_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "active_change",
            handler,
            extends=extends,
        )
        return self

    def on_active_row_action(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "active_row_action",
            handler,
            extends=extends,
        )
        return self

    def on_cell_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "cell_click",
            handler,
            extends=extends,
        )
        return self

    def on_column_resize_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "column_resize_change",
            handler,
            extends=extends,
        )
        return self

    def on_page_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "page_change",
            handler,
            extends=extends,
        )
        return self

    def on_row_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_click",
            handler,
            extends=extends,
        )
        return self

    def on_row_dblclick(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_dblclick",
            handler,
            extends=extends,
        )
        return self

    def on_row_mousedown(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_mousedown",
            handler,
            extends=extends,
        )
        return self

    def on_row_mouseenter(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_mouseenter",
            handler,
            extends=extends,
        )
        return self

    def on_row_mouseleave(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_mouseleave",
            handler,
            extends=extends,
        )
        return self

    def on_row_mouseover(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_mouseover",
            handler,
            extends=extends,
        )
        return self

    def on_row_mouseup(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_mouseup",
            handler,
            extends=extends,
        )
        return self

    def on_scroll(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "scroll",
            handler,
            extends=extends,
        )
        return self

    def on_scroll_x(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "scroll_x",
            handler,
            extends=extends,
        )
        return self

    def on_scroll_y(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "scroll_y",
            handler,
            extends=extends,
        )
        return self


class Table(BaseElement):
    def __init__(
        self,
        data: typing.Union[
            TMaybeRef[typing.List],
            PandasDataFrameProtocol,
            PolarsDataFrameProtocol,
            None,
        ] = None,
        columns: typing.Optional[
            TMaybeRef[typing.Union[typing.Sequence[TPrimaryTableCol], typing.Sequence]]
        ] = None,
        row_key: typing.Optional[TMaybeRef[str]] = None,
        *,
        expand_icon: typing.Union[str, bool, None] = None,
        filter_icon: typing.Union[str, None] = None,
        sort_icon: typing.Union[str, None] = None,
        **kwargs: Unpack[TPrimaryTableProps],
    ):
        super().__init__("t-table")
        _common_table_props_update(kwargs)  # type: ignore
        if isinstance(data, PolarsDataFrameProtocol):
            data = _polars_to_data(data)
        elif isinstance(data, PandasDataFrameProtocol):
            data = _pandas_to_data(data)
        self.props({"data": data, "columns": columns, "row-key": row_key})
        make_icon_for_bool_or_str(self, "expandIcon", expand_icon)
        make_icon_for_str(self, filter_icon, slot_name="filterIcon")
        make_icon_for_str(self, sort_icon, slot_name="sortIcon")
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def add_header_slot(self, name: str):
        """
        Add a header slot to the table.

        Args:
            name (str): The name key to add the slot to.
        """
        return TableHeaderSlot(self.add_slot(f"header-cell-{name}"))

    def add_cell_slot(self, name: str):
        """
        Add a cell slot to the table.

        Args:
            name (str): The name key to add the slot to.
        """
        return TableCellSlot(self.add_slot(f"body-cell-{name}"))

    def on_async_loading_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "async_loading_click",
            handler,
            extends=extends,
        )
        return self

    @classmethod
    def from_pandas(
        cls,
        data: typing.Union[PandasDataFrameProtocol, dict],
        *,
        extra_columns: typing.Optional[
            dict[str, typing.Union[dict, typing.Callable[[str], dict]]]
        ] = None,
        **kwargs: Unpack[TPrimaryTableProps],
    ) -> Self:
        if isinstance(data, PandasDataFrameProtocol):
            extra_columns = extra_columns or {}
            columns = []

            for col in data.columns:
                extra = extra_columns.get(col, {})
                if callable(extra):
                    extra = extra(col)
                columns.append({"colKey": col, "label": col} | extra)

            return cls(data=data.to_dict(orient="records"), columns=columns, **kwargs)  # type: ignore

        if is_binding_tracker(data) or isinstance(data, dict):
            return cls(data=data["data"], columns=data["columns"], **kwargs)

        raise ValueError("Unsupported data type")

    @classmethod
    def from_polars(
        cls,
        data: typing.Union[PolarsDataFrameProtocol, dict],
        *,
        extra_columns: typing.Optional[
            dict[str, typing.Union[dict, typing.Callable[[str], dict]]]
        ] = None,
        **kwargs: Unpack[TPrimaryTableProps],
    ) -> Self:
        if isinstance(data, PolarsDataFrameProtocol):
            extra_columns = extra_columns or {}
            columns = []

            for col in data.columns:
                extra = extra_columns.get(col, {})
                if callable(extra):
                    extra = extra(col)
                columns.append({"colKey": col, "label": col} | extra)

            return cls(data=data.to_dicts(), columns=columns, **kwargs)  # type: ignore

        if is_binding_tracker(data) or isinstance(data, dict):
            return cls(data=data["data"], columns=data["columns"], **kwargs)

        raise ValueError("Unsupported data type")

    def on_cell_click(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "cell_click",
            handler,
            extends=extends,
        )
        return self

    def on_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "change",
            handler,
            extends=extends,
        )
        return self

    def on_column_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "column_change",
            handler,
            extends=extends,
        )
        return self

    def on_column_controller_visible_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "column_controller_visible_change",
            handler,
            extends=extends,
        )
        return self

    def on_data_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "data_change",
            handler,
            extends=extends,
        )
        return self

    def on_display_columns_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "display_columns_change",
            handler,
            extends=extends,
        )
        return self

    def on_drag_sort(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "drag_sort",
            handler,
            extends=extends,
        )
        return self

    def on_expand_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "expand_change",
            handler,
            extends=extends,
        )
        return self

    def on_filter_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "filter_change",
            handler,
            extends=extends,
        )
        return self

    def on_row_edit(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_edit",
            handler,
            extends=extends,
        )
        return self

    def on_row_validate(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "row_validate",
            handler,
            extends=extends,
        )
        return self

    def on_select_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "select_change",
            handler,
            extends=extends,
        )
        return self

    def on_sort_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "sort_change",
            handler,
            extends=extends,
        )
        return self

    def on_validate(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "validate",
            handler,
            extends=extends,
        )
        return self


class EnhancedTable(BaseElement):
    def __init__(
        self,
        data: typing.Optional[TMaybeRef[typing.List]] = None,
        columns: typing.Optional[TMaybeRef[typing.List[TPrimaryTableCol]]] = None,
        row_key: typing.Optional[TMaybeRef[str]] = None,
        *,
        tree_expand_and_fold_icon: typing.Union[str, None] = None,
        **kwargs: Unpack[TEnhancedTableProps],
    ):
        super().__init__("t-enhanced-table")
        self.props({"data": data, "columns": columns, "row-key": row_key})
        make_icon_for_str(
            self, tree_expand_and_fold_icon, slot_name="treeExpandAndFoldIcon"
        )
        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore


class TBaseTableProps(TypedDict, total=False):
    active_row_keys: TMaybeRef[typing.List]
    default_active_row_keys: TMaybeRef[typing.List]
    active_row_type: TMaybeRef[str]
    allow_resize_column_width: TMaybeRef[bool]
    attach: TMaybeRef[str]
    bordered: TMaybeRef[bool]
    bottom_content: TMaybeRef[typing.Literal["TNode"]]
    cell_empty_content: TMaybeRef[typing.Literal["TNode"]]
    disable_data_page: TMaybeRef[bool]
    disable_space_inactive_row: TMaybeRef[bool]
    empty: TMaybeRef[typing.Literal["TNode"]]
    first_full_row: TMaybeRef[typing.Literal["TNode"]]
    fixed_rows: TMaybeRef[typing.List]
    foot_data: TMaybeRef[typing.List]
    footer_affix_props: TMaybeRef[typing.Dict]
    footer_affixed_bottom: TMaybeRef[
        typing.Union[TMaybeRef[bool], TMaybeRef[typing.Dict]]
    ]
    footer_summary: TMaybeRef[typing.Literal["TNode"]]
    header_affix_props: TMaybeRef[typing.Dict]
    header_affixed_top: TMaybeRef[typing.Union[TMaybeRef[bool], TMaybeRef[typing.Dict]]]
    height: TMaybeRef[typing.Union[TMaybeRef[float], TMaybeRef[str]]]
    horizontal_scroll_affixed_bottom: TMaybeRef[
        typing.Union[TMaybeRef[bool], TMaybeRef[typing.Dict]]
    ]
    hover: TMaybeRef[bool]
    keyboard_row_hover: TMaybeRef[bool]
    last_full_row: TMaybeRef[typing.Literal["TNode"]]
    lazy_load: TMaybeRef[bool]
    loading: TMaybeRef[typing.Union[bool, str]]
    loading_props: TMaybeRef[typing.Dict]
    locale: TMaybeRef[typing.Dict]
    max_height: TMaybeRef[typing.Union[TMaybeRef[float], TMaybeRef[str]]]
    pagination: typing.Union[TMaybeRef[typing.Dict], bool, int]
    pagination_affixed_bottom: TMaybeRef[typing.Union[bool, typing.Dict]]
    resizable: TMaybeRef[bool]
    row_attributes: TMaybeRef[typing.Union[str, typing.Dict, typing.List]]
    row_class_name: TMaybeRef[typing.Union[str, typing.Dict, typing.List]]
    rowspan_and_colspan: TMaybeRef[str]
    rowspan_and_colspan_in_footer: TMaybeRef[str]
    scroll: TMaybeRef[typing.Dict]
    show_header: TMaybeRef[bool]
    size: TMaybeRef[typing.Literal["small", "medium", "large"]]
    stripe: TMaybeRef[bool]
    table_content_width: TMaybeRef[str]
    table_layout: TMaybeRef[typing.Literal["auto", "fixed"]]
    top_content: TMaybeRef[typing.Literal["TNode"]]
    vertical_align: TMaybeRef[typing.Literal["top", "middle", "bottom"]]
    on_active_change: EventMixin
    on_active_row_action: EventMixin
    on_cell_click: EventMixin
    on_column_resize_change: EventMixin
    on_page_change: EventMixin
    on_row_click: EventMixin
    on_row_dblclick: EventMixin
    on_row_mousedown: EventMixin
    on_row_mouseenter: EventMixin
    on_row_mouseleave: EventMixin
    on_row_mouseover: EventMixin
    on_row_mouseup: EventMixin
    on_scroll: EventMixin
    on_scroll_x: EventMixin
    on_scroll_y: EventMixin


class TBaseTableCol(TypedDict, total=False):
    align: typing.Literal["left", "right", "center"]
    attrs: typing.Union[str, typing.Dict]
    cell: str
    children: typing.List
    class_name: typing.Union[str, typing.List, typing.Dict]
    col_key: str
    colspan: float
    ellipsis: typing.Union[bool, str, typing.Dict]
    ellipsis_title: typing.Union[bool, str, typing.Dict]
    fixed: typing.Literal["left", "right"]
    foot: str
    min_width: typing.Union[float, str]
    render: str
    resizable: bool
    resize: typing.Dict
    stop_propagation: bool
    th_class_name: typing.Union[str, typing.List, typing.Dict]
    title: str
    width: typing.Union[float, str]


class TPrimaryTableProps(TBaseTableProps, total=False):
    async_loading: TMaybeRef[str]
    column_controller: TMaybeRef[typing.Dict]
    column_controller_visible: TMaybeRef[bool]
    display_columns: TMaybeRef[typing.List]
    default_display_columns: TMaybeRef[typing.List]
    drag_sort: TMaybeRef[
        typing.Literal["row", "row-handler", "col", "row-handler-col", "drag-col"]
    ]
    drag_sort_options: TMaybeRef[typing.Dict]
    editable_cell_state: TMaybeRef[str]
    editable_row_keys: TMaybeRef[typing.List]
    expand_on_row_click: TMaybeRef[bool]
    expanded_row: TMaybeRef[TBaseTableCol]
    expanded_row_keys: TMaybeRef[typing.List]
    default_expanded_row_keys: TMaybeRef[typing.List]
    filter_row: TMaybeRef[typing.Literal["TNode"]]
    filter_value: TMaybeRef[typing.Dict]
    default_filter_value: TMaybeRef[typing.Dict]
    hide_sort_tips: TMaybeRef[bool]
    indeterminate_selected_row_keys: TMaybeRef[typing.List]
    multiple_sort: TMaybeRef[bool]
    reserve_selected_row_on_paginate: TMaybeRef[bool]
    row_selection_allow_uncheck: TMaybeRef[bool]
    row_selection_type: TMaybeRef[typing.Literal["single", "multiple"]]
    select_on_row_click: TMaybeRef[bool]
    selected_row_keys: TMaybeRef[typing.List]
    default_selected_row_keys: TMaybeRef[typing.List]
    show_sort_column_bg_color: TMaybeRef[bool]
    sort: TMaybeRef[typing.Union[TMaybeRef[typing.Dict], TMaybeRef[typing.List]]]
    default_sort: TMaybeRef[
        typing.Union[TMaybeRef[typing.Dict], TMaybeRef[typing.List]]
    ]
    sort_on_row_draggable: TMaybeRef[bool]
    on_async_loading_click: EventMixin
    on_cell_click: EventMixin
    on_change: EventMixin
    on_column_change: EventMixin
    on_column_controller_visible_change: EventMixin
    on_data_change: EventMixin
    on_display_columns_change: EventMixin
    on_drag_sort: EventMixin
    on_expand_change: EventMixin
    on_filter_change: EventMixin
    on_row_edit: EventMixin
    on_row_validate: EventMixin
    on_select_change: EventMixin
    on_sort_change: EventMixin
    on_validate: EventMixin


class TPrimaryTableCol(TBaseTableCol):
    cell: str
    check_props: typing.Union[str, typing.Dict]
    children: typing.List
    colKey: str
    disabled: str
    edit: typing.Dict
    filter: typing.Dict
    # render: str
    sortType: typing.Literal["desc", "asc", "all"]
    sorter: typing.Union[bool, str]
    title: str
    type: typing.Literal["single", "multiple"]


class TEnhancedTableProps(TPrimaryTableCol):
    before_drag_sort: TMaybeRef[str]
    expanded_tree_nodes: TMaybeRef[typing.List]
    default_expanded_tree_nodes: TMaybeRef[typing.List]
    tree: TMaybeRef[typing.Dict]
    on_abnormal_drag_sort: EventMixin
    on_expanded_tree_nodes_change: EventMixin
    on_tree_expand_change: EventMixin


class TableCellSlot:
    def __init__(self, slot: Slot) -> None:
        self.__slot = slot

    def __enter__(self):
        self.__slot.__enter__()
        return self

    def __exit__(self, *exc_info):
        self.__slot.__exit__(*exc_info)

    def param(self, name: typing.Literal["col", "colIndex", "row", "rowIndex"]):
        """
        Get slot parameter by name.

        Args:
            name (typing.Literal[&quot;col&quot;, &quot;colIndex&quot;, &quot;row&quot;, &quot;rowIndex&quot;]): Slot parameter name.
        """
        return typing.cast(typing.Any, self.__slot.slot_props(name))


class TableHeaderSlot:
    def __init__(self, slot: Slot) -> None:
        self.__slot = slot

    def __enter__(self):
        self.__slot.__enter__()
        return self

    def __exit__(self, *exc_info):
        self.__slot.__exit__(*exc_info)

    def param(self, name: typing.Literal["col", "colIndex"]):
        """
        Get slot parameter by name.

        Args:
            name (typing.Literal[&quot;col&quot;, &quot;colIndex&quot;]): Slot parameter name.
        """
        return typing.cast(typing.Any, self.__slot.slot_props(name))


def _common_table_props_update(props: typing.Dict):
    pass
    # if props.get("pagination") is True:
    #     props.update({"pagination": {"defaultCurrent": 1, "defaultPageSize": 10}})


def _pandas_to_data(dataframe: PandasDataFrameProtocol) -> list:
    return dataframe.to_dict(orient="records")


def _polars_to_data(dataframe: PolarsDataFrameProtocol) -> list:
    return dataframe.to_dicts()
