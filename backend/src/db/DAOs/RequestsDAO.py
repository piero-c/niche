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

    def count_requests_by_param(self, user_id: str, param: str) -> dict[str, int]:
        """
        Counts all requests for a user where `playlist_generated` exists, grouped by a param field.

        Args:
            user_id (str): The ID of the user.

        Returns:
            Dict[str, int]: A dictionary with genres as keys and counts as values.
        """
        # Validate that 'param' is a valid field in Params
        if(param not in Params.model_fields):
            raise ValueError(f"'{param}' is not a valid parameter.")
        pipeline = [
            {
                '$match': {
                    'user': user_id,
                    'playlist_generated': {'$exists': True, '$ne': None}
                }
            },
            {
                '$group': {
                    '_id': f'$params.{param}',
                    'count': {'$sum': 1}
                }
            }
        ]
        results = self.collection.aggregate(pipeline)
        return({doc['_id']: doc['count'] for doc in results})