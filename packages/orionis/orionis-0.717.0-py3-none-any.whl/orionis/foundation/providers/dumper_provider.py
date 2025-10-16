from orionis.console.debug.dumper import Dumper
from orionis.console.contracts.dumper import IDumper
from orionis.container.providers.service_provider import ServiceProvider

class DumperProvider(ServiceProvider):

    def register(self) -> None:
        """
        Registers the Dumper service in the application container.

        This method binds the `IDumper` interface to its concrete implementation, the `Dumper` class,
        within the application's dependency injection container. The service is registered as
        transient, ensuring that a new instance is created each time it is requested. An alias is
        also assigned to the service for convenient retrieval throughout the application.

        This registration allows the application to resolve dependencies related to dumping,
        debugging, and console diagnostics by referencing the interface or its alias.

        Returns
        -------
        None
            This method does not return any value. It modifies the application's service registry
            by registering the Dumper service.
        """

        # Register the Dumper service as a transient binding for the IDumper interface.
        # Each request for IDumper will result in a new Dumper instance.
        # The alias allows for easy retrieval of the service elsewhere in the application.
        self.app.transient(IDumper, Dumper, alias="x-orionis.console.contracts.dumper.IDumper")
