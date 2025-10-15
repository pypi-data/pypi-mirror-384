from luna_quantum.solve.interfaces.backend_i import IBackend


class Fujitsu(IBackend):
    """Configuration class for the Fujitsu backend."""

    @property
    def provider(self) -> str:
        """
        Retrieve the name of the provider.

        Returns
        -------
        str
            The name of the provider.
        """
        return "fda"
