from typing import Optional


class ExtractionQuery:
    """
    Contains useful context to run the query:
    - the sql statement itself
    - parameters { ... }
    - optionally, the target database (can be used to change the engine's URI)
    """

    def __init__(
        self,
        statement: str,
        params: dict,
        database: Optional[str] = None,
    ):
        self.statement = statement
        self.params = params
        self.database = database
