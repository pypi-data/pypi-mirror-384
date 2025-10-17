"""Allow instantiation of AbstractModel."""

from ..model.abstract_model import AbstractModel


class InstantiatedModel:
    """Instantiation of AbstractModel."""

    def __init__(self, abs: AbstractModel, name: str | None = None, values: dict | None = None) -> None:
        self.abs = abs
        self.name = name if name is not None else abs.name
        self.values = values

    def get_values(self, all: bool = False) -> dict:
        """
        Return the values for indexes and capabilities of this instantiated model.

        Parameters
        ----------
        all : bool, optional
            If `True`, return values for all indexes and capacities.
            If `False` (default), return only values that were explicitly set.

        Returns
        -------
        dict
            A dictionary of values, keyed by index / capability name.
        """
        values = self.values.copy() if self.values is not None else {}
        if all:
            for i in self.abs.indexes + self.abs.capacities:
                if i.name not in values:
                    values[i.name] = i.value
        return values
