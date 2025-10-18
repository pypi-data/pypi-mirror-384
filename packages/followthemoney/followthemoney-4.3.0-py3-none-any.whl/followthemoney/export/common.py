from typing import Generator, List, Optional, Tuple
from followthemoney.property import Property
from followthemoney.proxy import EntityProxy
from followthemoney.schema import Schema
from followthemoney.types import registry


class Exporter(object):
    def __init__(self, export_all: bool = False) -> None:
        self.export_all = export_all

    def exportable_properties(self, schema: Schema) -> Generator[Property, None, None]:
        for prop in schema.sorted_properties:
            if not self.export_all:
                if prop.hidden or prop.type == registry.entity:
                    continue
            yield prop

    def exportable_fields(
        self, proxy: EntityProxy
    ) -> Generator[Tuple[Property, List[str]], None, None]:
        for prop in self.exportable_properties(proxy.schema):
            yield prop, proxy.get(prop)

    def write(self, proxy: EntityProxy, extra: Optional[List[str]] = None) -> None:
        raise NotImplementedError

    def finalize(self) -> None:
        pass
