from typing import List
from models.pydantic.Request import Request, Params
from db.DB import DB
from db.DAOs.baseDAO import BaseDAO

class RequestDAO(BaseDAO[Request]):
    """
    Data Access Object for Request collection.
    """
    def __init__(self, db: DB) -> None:
        super().__init__(db.get_collection("requests"), Request)

    def read_all(self, filter: dict = {}) -> List[Request]:
        """
        Reads all requests matching a filter.

        Args:
            filter (dict): The filter criteria for finding requests.

        Returns:
            List[Request]: A list of matching requests.
        """
        documents = self.collection.find(filter)
        return ([Request.model_validate(doc) for doc in documents])

    def read_by_params(self, params: Params) -> List[Request]:
        """
        Reads requests based on specific parameters within the `params` field.

        Args:
            params (Params): The parameters to match in the `params` field of the requests.

        Returns:
            List[Request]: A list of requests that match the given parameters.
        """
        params_dict = params.model_dump(exclude_unset=True)
        query = {f"params.{key}": value for key, value in params_dict.items()}
        documents = self.collection.find(query)
        return ([Request.model_validate(doc) for doc in documents])
