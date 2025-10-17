from typing import Annotated

from pydantic import StringConstraints

TerritoryCode = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9]*$")
]

# comme un TerritoryCode mais prend en compte l'exception pour la France entière : territory=FR0,FR1,FR2-fr
MutualisedTerritoryCode = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9,]*$")
]

SQlName = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9_]*$")
]

SimpleIDType = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9_\-]*$")
]
