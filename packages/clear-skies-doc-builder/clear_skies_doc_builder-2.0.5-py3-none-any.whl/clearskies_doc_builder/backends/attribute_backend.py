import inspect
from typing import Any

import clearskies
import clearskies.column
import clearskies.model
import clearskies.query

from clearskies_doc_builder.backends.module_backend import ModuleBackend


class AttributeBackend(ModuleBackend):
    _search_functions = {
        "id": lambda attribute, name, value: id(attribute) == int(value),  # type: ignore
        "name": lambda attribute, name, value: name == value,  # type: ignore
        "type": lambda attribute, name, value: attribute.__class__ == value,  # type: ignore
    }

    def records(
        self, query: clearskies.query.Query, next_page_data: dict[str, str | int] | None = None
    ) -> list[dict[str, Any]]:
        """
        Return a list of records that match the given query configuration.

        next_page_data is used to return data to the caller.  Pass in an empty dictionary, and it will be populated
        with the data needed to return the next page of results.  If it is still an empty dictionary when returned,
        then there is no additional data.
        """
        disallowed = ["joins", "selects", "group_by"]
        for attribute_name in disallowed:
            if getattr(query, attribute_name):
                raise ValueError(f"The AttributeBackend received {attribute_name} in a query but doesn't support this.")

        for condition in query.conditions:
            if condition.operator != "=":
                raise ValueError("The AttributeBackend only supports searching with the equals operator")

        if "parent_class" not in query.conditions_by_column:
            raise ValueError("When searching for attributes you must include a condition on 'parent_class'")

        parent_class = query.conditions_by_column["parent_class"][0].values[0]
        matching_attributes = []
        for name in dir(parent_class):
            attribute = getattr(parent_class, name)
            matches = True
            for condition in query.conditions:
                if condition.column_name not in self._search_functions:
                    continue
                if not self._search_functions[condition.column_name](attribute, name, condition.values[0]):  # type: ignore
                    matches = False

            if not matches:
                continue
            matching_attributes.append(self.unpack(attribute, name, parent_class))

        return self.paginate(matching_attributes, query)

    def unpack(self, attribute: Any, name: str, parent_class: type) -> dict[str, Any]:  # type: ignore
        all_args = []
        args = []
        kwargs = []
        defaults: dict[str, Any] = {}
        argdata = None
        try:
            argdata = inspect.getfullargspec(attribute)
        except:
            pass

        if argdata:
            nargs = len(argdata.args)
            nkwargs = len(argdata.defaults) if argdata.defaults else 0
            npargs = nargs - nkwargs
            all_args = argdata.args
            kwargs = all_args[nargs - nkwargs :]
            args = all_args[:nkwargs]
            defaults = {}
            if argdata.defaults:
                defaults = {argdata.args[index + npargs]: default for (index, default) in enumerate(argdata.defaults)}

        return {
            "id": id(attribute),
            "name": name,
            "type": attribute.__class__,
            "doc": attribute.__doc__,
            "parent_class": parent_class,
            "attribute": attribute,
            "all_args": all_args,
            "args": args,
            "kwargs": kwargs,
            "defaults": defaults,
        }
