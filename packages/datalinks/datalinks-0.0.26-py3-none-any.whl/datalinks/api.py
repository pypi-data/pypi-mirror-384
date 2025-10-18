import datetime
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Type, TypeAlias

import requests
from requests import Request, Response, Session, RequestException
import dotenv

from datalinks.pipeline import Pipeline
from datalinks.links import MatchTypeConfig

_logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 30  # seconds
READ_TIMEOUT = 600  # seconds
MAX_INGEST_ATTEMPTS = 3


@dataclass
class DLConfig:
    """
    DLConfig class is a configuration container for managing the required settings
    to interact with DataLinks. It loads configuration values from environment
    variables to provide flexibility across different environments.

    This class is designed to simplify the initialization and storage of connection
    and namespace details required to communicate with DataLinks.

    :ivar host: The host URL for the data layer connection.
    :type host: str
    :ivar apikey: The API key for authentication with the data layer.
    :type apikey: str
    :ivar index: The index name to be used in the data layer operations.
    :type index: str
    :ivar namespace: The namespace for organizing data in the data layer.
    :type namespace: str
    :ivar objectname: The name of the object associated with the configuration.
                      Defaults to an empty string.
    :type objectname: str
    """
    host: str
    apikey: str
    index: str
    namespace: str
    objectname: str

    @classmethod
    def from_env(cls: Type["DLConfig"], load_dotenv: bool = True):
        if load_dotenv: dotenv.load_dotenv()
        return cls(
            host=os.getenv("HOST", "host-notset"),
            apikey=os.getenv("DL_API_KEY", "api-key-notset"),
            index=os.getenv("INDEX", "index-notset"),
            namespace=os.getenv("NAMESPACE", "namespace-notset"),
            objectname=os.getenv("OBJECT_NAME", ""),
        )


Dataset: TypeAlias = List[Dict[str, Any]]


@dataclass
class IngestionResult:
    """
    Represents the result of a data ingestion process into DataLinks.

    This class is a data structure used to store the results of a data ingestion
    operation. It separates the successfully ingested items from the failed ones,
    enabling users to track and handle both cases effectively.

    :ivar successful: A list of records successfully ingested. Each record is
        represented as a dictionary.
    :type successful: Dataset
    :ivar failed: A list of records that failed ingestion. Each record is
        represented as a dictionary.
    :type failed: Dataset
    """
    successful: Dataset
    failed: Dataset


class DataLinksRequestError(Exception):
    def __init__(self, endpoint: str, e: RequestException):
        self.status_code = getattr(e.response, 'status_code', None)
        self.content = getattr(e.response, 'content', None)

        _logger.error(
            "Request to %s failed with status %s: %s",
            endpoint,
            self.status_code if self.status_code is not None else "N/A",
            self.content
        )
        super().__init__(f"Request to {endpoint} failed with status {self.status_code}: {self.content}")


class DataLinksAPI:
    """
    Class for interfacing with the DataLinks API.

    Provides methods for ingesting data, managing namespaces, and querying data
    from DataLinks. Designed to interact with a configurable
    backend, providing flexibility for deployment environments.

    :ivar config: Configuration object containing API key, host, index, namespace,
        and object name.
    :type config: Optional[DLConfig]
    """

    def __init__(self, config: Optional[DLConfig] = None):
        self.config: DLConfig = config if config else DLConfig.from_env()

    @property
    def __headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config.apikey}"}

    @property
    def __ingest_url(self) -> str:
        return f"{self.config.host}/ingest/{self.config.namespace}/{self.config.objectname}"

    @property
    def __create_url(self) -> str:
        return f"{self.config.host}/ingest/new/{self.config.namespace}/{self.config.objectname}"

    @property
    def __data_url(self) -> str:
        return f"{self.config.host}/data/self/{self.config.namespace}/{self.config.objectname}"

    @property
    def __query_dataset_url(self) -> str:
        return f"{self.config.host}/query/self/{self.config.namespace}/{self.config.objectname}"

    @property
    def __query_namespace_url(self) -> str:
        return f"{self.config.host}/query/self/{self.config.namespace}"

    @property
    def __autorag_url(self) -> str:
        return f"{self.config.host}/query/autorag/self/{self.config.namespace}"

    @property
    def __datasets_url(self) -> str:
        return f"{self.config.host}/data"

    def __post_request(self, payload: str | Dict[str, Any], endpoint: str) -> Response:
        s = Session()
        if isinstance(payload, dict):
            req = Request('POST', url=endpoint, json=payload, headers=self.__headers)
        else:
            req = Request('POST', url=endpoint, data=payload, headers=self.__headers)

        prepped = req.prepare()
        if _logger.getEffectiveLevel() == logging.DEBUG:
            tag = datetime.datetime.today().strftime("%Y%m%d_%H%M%S")
            with open(f"request_debug_{tag}.json", "wt") as f:
                json.dump({
                    "method": prepped.method,
                    "url": prepped.url,
                    "headers": dict(prepped.headers),
                    "body": prepped.body.decode() if isinstance(prepped.body, bytes) else prepped.body
                }, f, indent=2)

        try:
            response = s.send(prepped, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise DataLinksRequestError(endpoint, e)

    def __get_request(self, endpoint: str) -> Response:
        try:
            response = requests.get(
                endpoint,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                headers=self.__headers
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise DataLinksRequestError(endpoint, e)

    def ingest(self, data: Dataset,
               inference_steps: Pipeline | None,
               entity_resolution: MatchTypeConfig | None,
               batch_size=0,
               max_attempts=MAX_INGEST_ATTEMPTS) -> IngestionResult:
        """
        Ingests data into the namespace by batching the given data and performing multiple retries
        in case of failures. This function sends data in chunks (batches), to be processed through configured
        inference steps, and to resolve entities based on the provided configuration. If a batch fails, it
        is retried up to a maximum number of attempts.

        :param data: List of dictionaries, where each dictionary represents a data block to be ingested.
        :param inference_steps: Pipeline of inference steps to be applied for processing the data. If `None` the data will be ingested as is.
        :param entity_resolution: Configuration specifying how entity resolution is to be performed.
        :param batch_size: Number of data blocks to be included in each batch. Defaults to the size of the
            entire dataset if not provided.
        :param max_attempts: Maximum number of retry attempts for failed batches. Defaults to the
            provided constant MAX_INGEST_ATTEMPTS.
        :return: An IngestionResult object containing lists of successfully ingested data blocks and
            data blocks that failed to be ingested.
        """
        start = time.perf_counter()

        if not batch_size:
            batch_size = len(data)
        _logger.info(f"Sending {len(data)} data blocks to ingestion endpoint (batch size {batch_size})")

        retry_data: Dataset = []
        successful_batches = []

        for attempt in range(max_attempts):
            _logger.debug(f"Attempt {attempt + 1} of {max_attempts}")
            retry_data = []

            for start_idx in range(0, len(data), batch_size):
                batch = data[start_idx:start_idx + batch_size]
                payload: dict[str, Any] = {
                    "data": batch
                }
                if inference_steps is not None:
                    payload["infer"] = {"steps": inference_steps.to_list()}
                if entity_resolution is not None:
                    payload["link"] = entity_resolution.config

                try:
                    response = self.__post_request(payload, self.__ingest_url)
                    if response.status_code == 200:
                        successful_batches.extend(batch)
                    else:
                        _logger.error(f"Batch failed with status {response.status_code}. "
                                      f"{response.content.decode()}")
                        retry_data.extend(batch)
                except DataLinksRequestError:
                    retry_data.extend(batch)

            if retry_data:
                data = retry_data
            else:
                break

        end = time.perf_counter()
        _logger.info(f"Ingestion took {end - start:.2f} seconds.")
        return IngestionResult(
            successful=successful_batches,
            failed=retry_data
        )

    def create_space(self, is_private: bool = True,
                     data_description: Optional[str] = "",
                     field_definitions: Optional[str] = "") -> None:
        """
        Creates a new space with the specified privacy settings. This function sends a
        POST request to create a namespace with the given privacy status. Information
        about the namespace creation will be logged, including the HTTP status code
        and response reason. If the namespace already exists, a warning will be logged.

        :param is_private: Determines whether the created namespace will be private
            or public.
        :type is_private: bool
        :return: None
        :raises HTTPError: If the HTTP request fails due to connectivity issues or
            server-side problems.
        """
        payload = {
            "inferDefinition": {
                "dataDescription": data_description,
                "fieldDefinition": field_definitions
            },
            "visibility": "Private" if is_private else "Public"
        }

        try:
            response = self.__post_request(payload, self.__create_url)

            _logger.info(f"Namespace creation (private: {is_private}) | "
                         f"{response.status_code} | {response.reason}")
        except DataLinksRequestError as e:
            if e.status_code == 409: pass
            else: raise

    def list_datasets(self, namespace: Optional[str] = None) -> List[Dict] | None:
        """
        Retrieves the list of datasets for the user, optionally filtered by a specific namespace.

        :param namespace: Optional namespace to filter the datasets by.
            If provided, only datasets associated with the given
            namespace will be returned. If not provided, all datasets are
            retrieved.
        :type namespace: Optional[AnyStr]

        :return: A list of datasets represented as dictionaries if the
            query is successful and returns a status code of 200, or
            None if the query fails or encounters an error.
        :rtype: List[Dict] | None
        """
        _url = self.__datasets_url
        if namespace:
            _url += f"/{namespace}"
        try:
            response = self.__get_request(_url)
            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"Query data failed with status {response.status_code}")
        except DataLinksRequestError:
            pass

        return None

    def query_data(self, query: Optional[str] = None, model: Optional[str] = None, provider: Optional[str] = None,
                   include_metadata: bool = False) -> Optional[Dataset]:
        """
        Queries data from a specified data source and processes the response.

        The method allows querying with a specific query string or with a wildcard
        ("*") for all data. The response from the query can be filtered to exclude
        metadata fields if `include_metadata` is set to False. Metadata fields are
        identified by key names starting with an underscore.

        :param query: The query string to use for fetching data. Defaults to "*",
                      which retrieves all data.
        :type query: str
        :param model: The model name to use for inference.
        :type model: str
        :param provider: The provider of the LLM model (ollama, openai, etc)
        :type provider: str
        :param include_metadata: Specifies whether to include metadata fields in
                                 the returned data. Defaults to False.
        :type include_metadata: bool
        :return: A list of records represented as dictionaries, or None if the query
                 fails or an exception occurs during the request.
        :rtype: List[Dict] | None
        :raises requests.exceptions.RequestException: If a request-related error
            occurs during querying.
        """
        if query is None:
            query = f"Ontology({self.config.namespace}/{self.config.objectname})"
        payload = {"query": query,
                   "model": model,
                   "provider": provider,
                   "useNaturalLanguageQuery": False}
        return self.__handle_data_query(payload, include_metadata)

    def ask(self, query: str, model: Optional[str] = None, provider: Optional[str] = None) -> Optional[Any]:
        """
        Queries data from a specified data source using natural language and processes the response.

        The method allows querying with a natural language string (that will be translated into
        a datalinks query). The response from the query can be filtered to exclude
        metadata fields if `include_metadata` is set to False. Metadata fields are
        identified by key names starting with an underscore.

        :param query: The natural language query to use for fetching data.
        :type query: str
        :param model: The model name to use for inference.
        :type model: str
        :param provider: The provider of the LLM model (ollama, openai, etc)
        :type provider: str
        :return: A string with json response from the API
        :rtype: Any
        :raises requests.exceptions.RequestException: If a request-related error
            occurs during querying.
        """
        payload = {
            "query": query,
            "model": model,
            "provider": provider}
        # TODO do better!
        json_data = None
        try:
            response = self.__post_request(payload, self.__autorag_url)
            json_data = response.json()
        except DataLinksRequestError:
            pass

        return json_data

    def __handle_data_query(self, payload: Dict[str, Any], include_metadata: bool) -> Dataset | None:
        json_data: Dataset = []
        try:
            response = self.__post_request(payload, self.__query_dataset_url)
            json_data = response.json()
        except DataLinksRequestError:
            pass

        if json_data and not include_metadata:
            return [dict(filter(lambda key_value: not str(key_value[0]).startswith("_"),
                                record.items()))
                    for record in json_data]
        return json_data
