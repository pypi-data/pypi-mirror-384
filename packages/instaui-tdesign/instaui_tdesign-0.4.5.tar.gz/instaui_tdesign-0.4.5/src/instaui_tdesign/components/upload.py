from __future__ import annotations
import typing
from ._base_element import BaseElement
from instaui.event.event_mixin import EventMixin
from typing_extensions import TypedDict, Unpack
from ._utils import handle_props, handle_event_from_props

if typing.TYPE_CHECKING:
    from instaui.vars.types import TMaybeRef


class Upload(BaseElement):
    def __init__(
        self,
        **kwargs: Unpack[TUploadProps],
    ):
        super().__init__("t-upload")

        self.props(handle_props(kwargs))  # type: ignore
        handle_event_from_props(self, kwargs)  # type: ignore

    def on_cancel_upload(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "cancel_upload",
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

    def on_dragenter(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "dragenter",
            handler,
            extends=extends,
        )
        return self

    def on_dragleave(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "dragleave",
            handler,
            extends=extends,
        )
        return self

    def on_drop(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "drop",
            handler,
            extends=extends,
        )
        return self

    def on_fail(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "fail",
            handler,
            extends=extends,
        )
        return self

    def on_one_file_fail(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "one_file_fail",
            handler,
            extends=extends,
        )
        return self

    def on_one_file_success(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "one_file_success",
            handler,
            extends=extends,
        )
        return self

    def on_preview(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "preview",
            handler,
            extends=extends,
        )
        return self

    def on_progress(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "progress",
            handler,
            extends=extends,
        )
        return self

    def on_remove(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "remove",
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

    def on_success(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "success",
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

    def on_waiting_upload_files_change(
        self,
        handler: EventMixin,
        *,
        extends: typing.Optional[typing.List] = None,
    ):
        self.on(
            "waiting_upload_files_change",
            handler,
            extends=extends,
        )
        return self


class TUploadProps(TypedDict, total=False):
    abridge_name: TMaybeRef[typing.List]
    accept: TMaybeRef[str]
    action: TMaybeRef[str]
    allow_upload_duplicate_file: TMaybeRef[bool]
    auto_upload: TMaybeRef[bool]
    before_all_files_upload: TMaybeRef[str]
    before_upload: TMaybeRef[str]
    cancel_upload_button: TMaybeRef[
        typing.Union[TMaybeRef[str], TMaybeRef[typing.Dict]]
    ]
    data: TMaybeRef[typing.Union[TMaybeRef[str], TMaybeRef[typing.Dict]]]
    default: TMaybeRef[str]
    disabled: TMaybeRef[bool]
    drag_content: TMaybeRef[str]
    draggable: TMaybeRef[bool]
    file_list_display: TMaybeRef[str]
    files: TMaybeRef[typing.List]
    default_files: TMaybeRef[typing.List]
    format: TMaybeRef[str]
    format_request: TMaybeRef[str]
    format_response: TMaybeRef[str]
    headers: TMaybeRef[typing.Dict]
    image_viewer_props: TMaybeRef[typing.Dict]
    input_attributes: TMaybeRef[typing.Dict]
    is_batch_upload: TMaybeRef[bool]
    locale: TMaybeRef[typing.Dict]
    max: TMaybeRef[float]
    method: TMaybeRef[
        typing.Literal[
            "POST",
            "GET",
            "PUT",
            "OPTIONS",
            "PATCH",
            "post",
            "get",
            "put",
            "options",
            "patch",
        ]
    ]
    mock_progress_duration: TMaybeRef[float]
    multiple: TMaybeRef[bool]
    name: TMaybeRef[str]
    placeholder: TMaybeRef[str]
    request_method: TMaybeRef[str]
    show_image_file_name: TMaybeRef[bool]
    show_thumbnail: TMaybeRef[bool]
    show_upload_progress: TMaybeRef[bool]
    size_limit: TMaybeRef[typing.Union[TMaybeRef[float], TMaybeRef[typing.Dict]]]
    status: TMaybeRef[typing.Literal["default", "success", "warning", "error"]]
    theme: TMaybeRef[
        typing.Literal[
            "custom", "file", "file-input", "file-flow", "image", "image-flow"
        ]
    ]
    tips: TMaybeRef[str]
    trigger: TMaybeRef[str]
    trigger_button_props: TMaybeRef[typing.Dict]
    upload_all_files_in_one_request: TMaybeRef[bool]
    upload_button: TMaybeRef[typing.Union[TMaybeRef[str], TMaybeRef[typing.Dict]]]
    upload_pasted_files: TMaybeRef[bool]
    use_mock_progress: TMaybeRef[bool]
    value: TMaybeRef[typing.List]
    default_value: TMaybeRef[typing.List]
    with_credentials: TMaybeRef[bool]
    on_cancel_upload: EventMixin
    on_change: EventMixin
    on_dragenter: EventMixin
    on_dragleave: EventMixin
    on_drop: EventMixin
    on_fail: EventMixin
    on_one_file_fail: EventMixin
    on_one_file_success: EventMixin
    on_preview: EventMixin
    on_progress: EventMixin
    on_remove: EventMixin
    on_select_change: EventMixin
    on_success: EventMixin
    on_validate: EventMixin
    on_waiting_upload_files_change: EventMixin
