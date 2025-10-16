"""
This module contains all string representations of all day filter options, used by :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm` and
:class:`~integreat_cms.cms.views.events.event_list_view.EventListView`.

The module also contains a constant :attr:`~integreat_cms.cms.constants.all_day.DATATYPE`, which contains the type of the constant
values linked to the strings and is used for correctly instantiating :class:`django.forms.TypedMultipleChoiceField`
instances in :class:`~integreat_cms.cms.forms.events.event_filter_form.EventFilterForm`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: Only events which are all day long
READ: Final = "READ"
#: Exclude events which are all day long
UNREAD: Final = "UNREAD"

#: Choices to use these constants in a database field
CHOICES: Final[list[tuple[str, Promise]]] = [
    (READ, _("Read")),
    (UNREAD, _("Unread")),
]

INITIAL: Final[list[str]] = [key for (key, val) in CHOICES]
