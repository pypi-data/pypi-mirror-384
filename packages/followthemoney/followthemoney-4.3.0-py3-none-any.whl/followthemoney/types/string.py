from followthemoney.types.common import PropertyType
from followthemoney.util import const, defer as _
from followthemoney.util import MEGABYTE


class StringType(PropertyType):
    """A simple string property with no additional semantics."""

    name = const("string")
    label = _("Label")
    plural = _("Labels")
    matchable = False
    max_length = 1024

    def node_id(self, value: str) -> None:
        return None


class TextType(StringType):
    """Longer text fragments, such as descriptions or document text. Unlike
    string properties, it might make sense to treat properties of this type as
    full-text search material."""

    name = const("text")
    label = _("Text")
    plural = _("Texts")
    total_size = 30 * MEGABYTE
    max_length = 65000


class HTMLType(StringType):
    """Properties that contain raw hypertext markup (HTML).

    User interfaces rendering properties of this type need to take extreme
    care not to allow attacks such as cross-site scripting. It is recommended
    to perform server-side sanitisation, or to not render this property at all.
    """

    name = const("html")
    label = _("HTML")
    plural = _("HTMLs")
    total_size = 30 * MEGABYTE
    max_length = 65000
