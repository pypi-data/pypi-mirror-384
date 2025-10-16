from __future__ import annotations

from collections.abc import Iterable

from pabutools.election.instance import Project


class AllocationDetails:
    """
    Class representing participatory budgeting rule run details.
    Used as a parent class which can be inherited.
    """

    def __init__(self):
        pass


class BudgetAllocation(list[Project]):
    """
    A budget allocation is the outcome of rule. It simply corresponds to a list of projects.
    Additional information can also be stored in this class, for instance for explanation purposes.

    Parameters
    ----------
        init : Iterable[:py:class:`~pabutools.election.instance.Project`], optional
            An iterable of :py:class:`~pabutools.election.instance.Project` that is used an
            initializer for the list.
        details: :py:class:`~pabutools.rules.budgetallocation.AllocationDetails`, optional
            Used for storing various additional information about a participatory budgeting rule run.
            Defaults to None.

    Attributes
    ----------
        details: :py:class:`~pabutools.rules.budgetallocation.AllocationDetails`, optional
            Used for storing various additional information about a participatory budgeting rule run.
            Defaults to None.

    """

    def __init__(
        self, init: Iterable[Project] = (), details: AllocationDetails | None = None
    ) -> None:
        list.__init__(self, init)
        if details is None:
            if isinstance(init, BudgetAllocation):
                details = init.details
        self.details = details

    # Ensures that methods returning copies of sets cast back into BudgetAllocation
    @classmethod
    def _wrap_methods(cls, methods):
        def wrap_method_closure(method):
            def inner_method(self, *args):
                result = getattr(super(cls, self), method)(*args)
                if isinstance(result, list) and not isinstance(result, cls):
                    result = cls(init=result, details=self.details)
                return result

            inner_method.fn_name = method
            setattr(cls, method, inner_method)

        for m in methods:
            wrap_method_closure(m)


BudgetAllocation._wrap_methods(
    [
        "__add__",
        "__iadd__",
        "__imul__",
        "__mul__",
        "__reversed__",
        "__rmul__",
        "copy",
        "reverse",
        "__getitem__",
    ]
)
