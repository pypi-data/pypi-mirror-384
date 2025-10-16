import Kratos
from typing import overload

class KratosMetisApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosMetisApplication.KratosMetisApplication) -> None"""

class MetisDivideHeterogeneousInputInMemoryProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None

        5. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None

        6. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None

        7. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None

        8. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None

        5. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None

        6. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None

        7. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None

        8. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None

        5. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None

        6. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None

        7. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None

        8. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None

        5. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None

        6. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None

        7. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None

        8. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None

        5. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None

        6. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None

        7. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None

        8. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None

        5. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None

        6. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None

        7. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None

        8. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None

        5. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None

        6. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None

        7. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None

        8. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: Kratos.DataCommunicator, arg3: int, arg4: int, arg5: bool) -> None

        5. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int) -> None

        6. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int) -> None

        7. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int) -> None

        8. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputInMemoryProcess, arg0: Kratos.IO, arg1: Kratos.ModelPartIO, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """

class MetisDivideHeterogeneousInputProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int, arg4: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: int, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int, arg4: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int, arg4: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int, arg4: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideHeterogeneousInputProcess, arg0: Kratos.IO, arg1: int, arg2: int, arg3: int, arg4: bool) -> None
        """

class MetisDivideNodalInputToPartitionsProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: int, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideNodalInputToPartitionsProcess, arg0: Kratos.IO, arg1: int, arg2: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideNodalInputToPartitionsProcess, arg0: Kratos.IO, arg1: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideNodalInputToPartitionsProcess, arg0: Kratos.IO, arg1: int, arg2: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideNodalInputToPartitionsProcess, arg0: Kratos.IO, arg1: int) -> None
        """

class MetisDivideSubModelPartsHeterogeneousInputProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int, arg5: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int) -> None

        2. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int) -> None

        3. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int) -> None

        4. __init__(self: KratosMetisApplication.MetisDivideSubModelPartsHeterogeneousInputProcess, arg0: Kratos.IO, arg1: Kratos.Parameters, arg2: int, arg3: int, arg4: int, arg5: bool) -> None
        """
