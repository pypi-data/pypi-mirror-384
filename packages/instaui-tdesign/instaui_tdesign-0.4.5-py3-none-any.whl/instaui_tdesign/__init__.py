"""
Easy to use TDesign UI components for InstaUI.

Examples:
.. code-block:: python
    from instaui import ui
    import instaui_tdesign as td

    td.use()

    @ui.page("/")
    def index_page():
        td.input(placeholder="input")
"""

__all__ = [
    "__version__",
    "use",
    "affix",
    "alert",
    "anchor",
    "anchor_item",
    "auto_complete",
    "avatar",
    "avatar_group",
    "back_top",
    "badge",
    "breadcrumb",
    "breadcrumb_item",
    "button",
    "calendar",
    "card",
    "cascader",
    "checkbox",
    "collapse",
    "collapse_panel",
    "color_picker",
    "color_picker_panel",
    "comment",
    "date_picker",
    "date_picker_panel",
    "date_range_picker",
    "date_range_picker_panel",
    "descriptions",
    "descriptions_item",
    "dialog",
    "divider",
    "drawer",
    "dropdown",
    "empty",
    "form",
    "form_item",
    "icon",
    "input_adornment",
    "input_number",
    "input",
    "link",
    "list",
    "list_item",
    "list_item_meta",
    "loadding",
    "select",
    "skeleton",
    "slider",
    "space",
    "statistic",
    "steps",
    "step_item",
    "sticky_tool",
    "sticky_item",
    "swiper",
    "swiper_item",
    "switch",
    "table",
    "base_table",
    "enhanced_table",
    "tabs",
    "tab_panel",
    "tag_input",
    "tag",
    "textarea",
    "time_picker",
    "time_range_picker",
    "timeline",
    "timeline_item",
    "tooltip",
    "tooltip_lite",
    "transfer",
    "tree_select",
    "tree",
    "menu",
    "menu_group",
    "menu_item",
    "sub_menu",
    "head_menu",
    "message",
    "notification",
    "pagination",
    "popconfirm",
    "popup",
    "progress",
    "radio",
    "radio_group",
    "range_input",
    "rate",
    "select_input",
    "typography_paragraph",
    "typography_text",
    "typography_title",
    "upload",
    "row",
    "col",
    "guide",
    "image",
    "image_viewer",
    "layout",
    "header",
    "aside",
    "content",
    "footer",
    "watermark",
]

from .version import __version__
from .setup import use
from .components.affix import Affix as affix
from .components.alert import Alert as alert
from .components.anchor import Anchor as anchor, AnchorItem as anchor_item
from .components.auto_complete import AutoComplete as auto_complete
from .components.avatar import Avatar as avatar, AvatarGroup as avatar_group
from .components.back_top import BackTop as back_top
from .components.badge import Badge as badge
from .components.breadcrumb import (
    Breadcrumb as breadcrumb,
    BreadcrumbItem as breadcrumb_item,
)
from .components.button import Button as button
from .components.calendar import Calendar as calendar
from .components.card import Card as card
from .components.cascader import Cascader as cascader
from .components.checkbox import Checkbox as checkbox
from .components.collapse import Collapse as collapse, CollapsePanel as collapse_panel
from .components.color_picker import (
    ColorPicker as color_picker,
    ColorPickerPanel as color_picker_panel,
)
from .components.comment import Comment as comment
from .components.date_picker import (
    DatePicker as date_picker,
    DatePickerPanel as date_picker_panel,
    DateRangePicker as date_range_picker,
    DateRangePickerPanel as date_range_picker_panel,
)
from .components.descriptions import (
    Descriptions as descriptions,
    DescriptionsItem as descriptions_item,
)
from .components.dialog import Dialog as dialog
from .components.divider import Divider as divider
from .components.drawer import Drawer as drawer
from .components.dropdown import Dropdown as dropdown
from .components.empty import Empty as empty
from .components.form import Form as form, FormItem as form_item
from .components.icon import Icon as icon
from .components.input_adornment import InputAdornment as input_adornment
from .components.input_number import InputNumber as input_number
from .components.input import Input as input
from .components.grid import Row as row, Col as col
from .components.guide import Guide as guide
from .components.image import Image as image
from .components.image_viewer import ImageViewer as image_viewer
from .components.link import Link as link
from .components.list import (
    List as list,
    ListItem as list_item,
    ListItemMeta as list_item_meta,
)
from .components.loadding import Loadding as loadding
from .components.select import Select as select
from .components.skeleton import Skeleton as skeleton
from .components.slider import Slider as slider
from .components.space import Space as space
from .components.statistic import Statistic as statistic
from .components.steps import Steps as steps, StepItem as step_item
from .components.sticky_tool import StickyTool as sticky_tool, StickyItem as sticky_item
from .components.swiper import Swiper as swiper, SwiperItem as swiper_item
from .components.switch import Switch as switch
from .components.table import (
    Table as table,
    BaseTable as base_table,
    EnhancedTable as enhanced_table,
)
from .components.tabs import Tabs as tabs, TabPanel as tab_panel
from .components.tag_input import TagInput as tag_input
from .components.tag import Tag as tag
from .components.textarea import Textarea as textarea
from .components.time_picker import (
    TimePicker as time_picker,
    TimeRangePicker as time_range_picker,
)
from .components.timeline import Timeline as timeline, TimelineItem as timeline_item
from .components.tooltip import Tooltip as tooltip, TooltipLite as tooltip_lite
from .components.transfer import Transfer as transfer
from .components.tree_select import TreeSelect as tree_select
from .components.tree import Tree as tree
from .components.menu import (
    Menu as menu,
    SubMenu as sub_menu,
    MenuItem as menu_item,
    MenuGroup as menu_group,
    HeadMenu as head_menu,
)
from .components.message import Message as message
from .components.notification import Notification as notification
from .components.pagination import Pagination as pagination
from .components.popconfirm import Popconfirm as popconfirm
from .components.popup import Popup as popup
from .components.progress import Progress as progress
from .components.radio import Radio as radio, RadioGroup as radio_group
from .components.range_input import RangeInput as range_input
from .components.rate import Rate as rate
from .components.select_input import SelectInput as select_input
from .components.typography import (
    TypographyText as typography_text,
    TypographyTitle as typography_title,
    TypographyParagraph as typography_paragraph,
)
from .components.upload import Upload as upload
from .components.layout import (
    Layout as layout,
    Header as header,
    Aside as aside,
    Content as content,
    Footer as footer,
)
from .components.watermark import Watermark as watermark
