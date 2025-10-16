import requests
import pandas as pd
import io
import fnmatch
import json
from datetime import datetime, timedelta
from typing import Optional
from msal import PublicClientApplication
from azure.identity import (
    ManagedIdentityCredential,
    AzureCliCredential,
    ClientSecretCredential,
    ChainedTokenCredential
)


class MicantisAPI:
    """
    A client for interacting with the Micantis API.

    Supports:
    - Username/password login
    - Microsoft Entra interactive login
    - Service Principal (client secret)
    - Managed Identity (for Azure-hosted apps)
    """

    def __init__(self,
                 service_url: str,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 client_id: Optional[str] = None,
                 authority: Optional[str] = None,
                 scopes: Optional[list] = None,
                 service_principal_id: Optional[str] = None,
                 service_principal_secret: Optional[str] = None,
                 tenant_id: Optional[str] = None,
                 use_managed_identity: bool = False):
        """
        Initialize the API client.
        """

        self.service_url = service_url.rstrip("/")
        self.username = username
        self.password = password
        self.client_id = client_id
        self.authority = authority
        self.scopes = scopes or ["user.read"]
        self.token = None
        self.headers = None

        # Extra options for service principal / managed identity
        self.service_principal_id = service_principal_id
        self.service_principal_secret = service_principal_secret
        self.tenant_id = tenant_id
        self.use_managed_identity = use_managed_identity

        # Internal cache for non-interactive tokens
        self._token_expires: Optional[datetime] = None
        self._credential = None  # Store credential object for token refresh

    # ------------------------
    # Username / password login
    # ------------------------
    def authenticate_via_login(self):
        try:
            response = requests.post(
                f"{self.service_url}/api/authenticate/login",
                json={"username": self.username, "password": self.password}
            )
            response.raise_for_status()
            self.token = response.json()["token"]
            if not self.token:
                raise ValueError("Authentication failed: Token not found in response.")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print("✅ Authentication via login successful!")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Authentication request failed: {e}")

    # ------------------------
    # Interactive Entra login
    # ------------------------
    def authenticate_via_entra(self):
        try:
            app = PublicClientApplication(self.client_id, authority=self.authority)
            result = app.acquire_token_interactive(self.scopes)
            if "access_token" in result:
                token = result["access_token"]
                self.headers = {"Authorization": f"Bearer {token}"}
                print("✅ Authentication via Entra (interactive) successful!")
            else:
                raise RuntimeError(f"Authentication failed: {result.get('error')}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Authentication request failed: {e}")

    # ------------------------
    # Non-interactive auth (SPN or MI)
    # ------------------------
    def authenticate_via_identity(self):
        """
        Authenticate using:
        - Managed Identity (preferred in Azure)
        - Service Principal (client ID + secret)
        - Azure CLI (fallback for local dev)
        """

        credentials = []

        if self.use_managed_identity:
            print("Using Managed Identity authentication")
            credentials.append(ManagedIdentityCredential())
        elif self.service_principal_id and self.service_principal_secret and self.tenant_id:
            print(f"Using Service Principal authentication (client_id: {self.service_principal_id})")
            credentials.append(ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.service_principal_id,
                client_secret=self.service_principal_secret
            ))
        else:
            print("Using default chain (Managed Identity → Azure CLI)")
            credentials.extend([ManagedIdentityCredential(), AzureCliCredential()])

        credential = ChainedTokenCredential(*credentials) if len(credentials) > 1 else credentials[0]

        # Store credential for future token refresh
        self._credential = credential

        # Scope must be api://<app-id>/.default
        scope = [f"api://{self.client_id}/.default"]
        token = credential.get_token(*scope)

        self.token = token.token
        self._token_expires = datetime.utcfromtimestamp(token.expires_on)
        self.headers = {"Authorization": f"Bearer {self.token}"}

        print(f"✅ Authentication via identity successful, expires at {self._token_expires}")

    def _refresh_token_if_needed(self):
        """
        Check if the token is expired or about to expire, and refresh it if needed.
        Only works for identity-based authentication (Service Principal / Managed Identity).

        Returns True if token was refreshed, False otherwise.
        """
        if not self._credential or not self._token_expires:
            return False

        # Refresh if token expires in less than 5 minutes
        now = datetime.utcnow()
        buffer = timedelta(minutes=5)

        if now + buffer >= self._token_expires:
            print(f"🔄 Token expired or expiring soon, refreshing...")
            scope = [f"api://{self.client_id}/.default"]
            token = self._credential.get_token(*scope)

            self.token = token.token
            self._token_expires = datetime.utcfromtimestamp(token.expires_on)
            self.headers = {"Authorization": f"Bearer {self.token}"}

            print(f"✅ Token refreshed, new expiry: {self._token_expires}")
            return True

        return False

    # ------------------------
    # Auto-select
    # ------------------------
    def authenticate(self):
        """
        Automatically selects authentication method:
        - Managed Identity / Service Principal if configured
        - Entra interactive if client_id + authority given
        - Username/password login otherwise
        """
        if self.use_managed_identity or self.service_principal_id:
            self.authenticate_via_identity()
        elif all([self.client_id, self.authority, self.scopes]):
            self.authenticate_via_entra()
        elif all([self.username, self.password]):
            self.authenticate_via_login()
        else:
            raise ValueError("Insufficient credentials provided.")


    def _retry_on_auth_failure(self, func, *args, **kwargs):
        """
        Internal helper: retry the API call once if authentication fails.
        Also proactively refreshes token if expired or expiring soon.
        """
        # Proactively refresh token if needed (for service principal / managed identity)
        self._refresh_token_if_needed()

        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            if "Authentication required" in str(e) or "401" in str(e):
                print("🔄 Re-authenticating and retrying...")
                self.authenticate()
                return func(*args, **kwargs)
            raise
    def _get_data_table(
        self,
        offset: int = 0,
        barcode: str = None,
        search: str = None,
        min_date=None,
        max_date=None,
        show_ignored: bool = True,
        limit: int = 500,
    ):
        """
        Fetches data table with optional filters and returns it as a Pandas DataFrame.

        :param offset: Pagination offset.
        :param barcode: Barcode filter (optional).
        :param search: Search text filter (optional).
        :param min_date: Minimum date filter (ISO format) (optional).
        :param max_date: Maximum date filter (ISO format) (optional).
        :param show_ignored: Whether to include soft deleted items.
        :param limit: Max number of rows to return.
        :return: Pandas DataFrame of the fetched data.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        params = {
            "offset": offset,
            "showIgnored": str(show_ignored).lower(),
            "limit": limit
        }

        filter_index = 0

        if min_date or max_date:
            params[f"filters[{filter_index}].specialColumn"] = 4
            if min_date:
                params[f"filters[{filter_index}].minDate"] = min_date
            if max_date:
                params[f"filters[{filter_index}].maxDate"] = max_date
            filter_index += 1

        if barcode:
            params[f"filters[{filter_index}].specialColumn"] = 27
            params[f"filters[{filter_index}].searchText"] = barcode
            filter_index += 1

        if search:
            params["search"] = search

        try:
            response = requests.get(
                f"{self.service_url}/publicapi/v1/data/list",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                print("⚠️ No data returned.")
                return pd.DataFrame()
            return pd.DataFrame(items)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"GET request failed: {e}")
        
    def get_data_table(
        self,
        offset: int = 0,
        barcode: str = None,
        search: str = None,
        min_date=None,
        max_date=None,
        show_ignored: bool = True,
        limit: int = 500,
    ):
        """
        Fetches data table with optional filters and returns it as a Pandas DataFrame.

        :param offset: Pagination offset.
        :param barcode: Barcode filter (optional).
        :param search: Search text filter (optional).
        :param min_date: Minimum date filter (ISO format) (optional).
        :param max_date: Maximum date filter (ISO format) (optional).
        :param show_ignored: Whether to include soft deleted items.
        :param limit: Max number of rows to return.
        :return: Pandas DataFrame of the fetched data.
        """
        return self._retry_on_auth_failure(
            self._get_data_table, offset, barcode, search, min_date, max_date, show_ignored, limit
        )
    
    def download_csv_file(self, guid: str) -> pd.DataFrame:
        """
        Download a CSV file from the API and convert it to a pandas DataFrame.

        Automatically reauthenticates if the session is expired or missing.
        Prints an error message and returns None if the request ultimately fails.

        Parameters
        ----------
        guid : str
            The unique identifier (GUID) of the file to be downloaded.

        Returns
        -------
        pd.DataFrame or None
            A pandas DataFrame if the download is successful,
            or None if an error occurs or the data is empty.
        """
        try:
            return self._retry_on_auth_failure(self._download_csv_file, guid)
        except Exception as e:
            print(f"⚠️ download_csv_file failed: {e}")
            return None

    def _download_csv_file(self, guid: str) -> pd.DataFrame:
        """
        Internal helper for download_csv_file. Does not handle retries or printing.

        Raises
        ------
        RuntimeError
            If the response is empty or the request fails.
        """
        r = requests.get(
            f"{self.service_url}/publicapi/v1/download/fullcsv/{guid}",
            headers=self.headers,
            timeout=10
        )
        r.raise_for_status()

        if not r.content:
            raise RuntimeError("No data returned from CSV endpoint")

        return pd.read_csv(io.BytesIO(r.content))
    
        
    def get_metadata(self, guid: str) -> dict:
        """
        Fetch metadata for a given data file.

        Parameters
        ----------
        guid : str
            Unique identifier for the file.

        Returns
        -------
        dict
            Metadata associated with the file.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        try:
            r = requests.get(f"{self.service_url}/publicapi/v1/data/getmetadata/{guid}", headers = self.headers)
            return r.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"GET request failed: {e}")
        
    def download_binary_file(self, guid: str) -> pd.DataFrame:
        """
        Download a binary file, decode it using its metadata, and return a DataFrame.

        Automatically reauthenticates if session is expired or missing.
        Prints an error message and returns None if the request ultimately fails.

        Parameters
        ----------
        guid : str
            File ID from the data table.

        Returns
        -------
        pd.DataFrame or None
            Parsed binary data as a DataFrame, or None if an error occurs.
        """
        try:
            return self._retry_on_auth_failure(self._download_binary_file, guid)
        except Exception as e:
            print(f"⚠️ download_binary_file failed: {e}")
            return None

    def _download_binary_file(self, guid: str) -> pd.DataFrame:
        """
        Internal helper for download_binary_file. Does not handle retries or printing.

        Raises
        ------
        RuntimeError
            If the response fails or the data is invalid.
        """
        r = requests.get(
            f"{self.service_url}/publicapi/v1/download/binary/{guid}",
            headers=self.headers,
            timeout=10
        )
        r.raise_for_status()

        metadata = self.get_metadata(guid)
        aux_names = [f"{entry['name']} ({entry['units']})" for entry in metadata.get('auxiliaryData', [])]
        
        try:
            return binary_to_dataframe(r.content, aux_names=aux_names)
        except Exception as e:
            raise RuntimeError(f"Failed to decode binary file: {e}")

        
    def get_cells_list(
        self,
        offset: int=0,
        barcode: str=None,
        search: str=None,
        min_date=None,
        max_date=None,
        show_ignored: bool=True,
        limit: int = 500
    ):
        """
        Fetches cells table list with optional filters and returns it as a Pandas DataFrame.

        :param offset: Pagination offset.
        :param barcode: Barcode filter (optional).
        :param search: Search text filter (optional).
        :param min_date: Minimum date filter (ISO format) (optional).
        :param max_date: Maximum date filter (ISO format) (optional).
        :param show_ignored: Whether to include soft deleted items (default: True).
        :return: Pandas DataFrame of the fetched data.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        # Build query parameters dynamically
        params = {
            "offset": offset,
            "showIgnored": str(show_ignored).lower(),
            "limit": limit
        }

        filter_index = 0
        if min_date or max_date:
            params[f"filters[{filter_index}].specialColumn"] = 4
            if min_date:
                params[f"filters[{filter_index}].minDate]"] = min_date
            if max_date:
                params[f"filters[{filter_index}].maxDate]"] = max_date
            filter_index += 1

        if barcode:
            params[f"filters[{filter_index}].specialColumn"] = 27
            params[f"filters[{filter_index}].searchText"] = barcode
            filter_index += 1

        if search:
            params["search"] = search

        try:
            # Make the GET request
            response = requests.get(
                f"{self.service_url}/publicapi/v1/cells/list",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()

            # Parse response JSON
            items = response.json().get("items", [])
            if not items:
                print("⚠️ No data returned.")
                return pd.DataFrame()

            # Convert to DataFrame
            return pd.DataFrame(items)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"GET request failed: {e}")

    def list_cell_metadata_definitions(self, type='df'):
        """
        Returns a list of cell metadata types
        """
        if not self.headers:
                raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        try:
            # Make the GET request
            response = requests.get(
                f"{self.service_url}/publicapi/v1/metadata/list/cells",
                headers=self.headers,
            )

            item = response.json()
            if type == 'df':
                df = pd.DataFrame(item)
                return df
            
            else:
                return item

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"GET request failed: {e}")
        
    def get_cell_metadata(self, cell_ids: list, metadata: list = None, return_images: bool = False):
        """
        Fetch metadata for specific cells, using either metadata names or IDs.

        Parameters
        ----------
        cell_ids : list of str
            List of cell IDs to fetch metadata for.
        metadata : list of str, optional
            List of metadata names or IDs. If None or empty, fetches all (filtered by return_images).
        return_images : bool, optional
            If False, excludes metadata entries where kind == 'Image'.

        Returns
        -------
        pd.DataFrame
            Metadata results per cell in wide format.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        if not isinstance(cell_ids, list) or not cell_ids:
            raise ValueError("cell_ids must be a non-empty list of Cell IDs.")

        # Get metadata definitions
        definitions_df = self.list_cell_metadata_definitions(type='df')
        
        if not return_images:
            definitions_df = definitions_df[definitions_df["kind"] != "Image"]

        # Resolve metadata names or use all if none provided
        if metadata:
            # Accept both IDs and names — look up names if needed
            id_set = set(definitions_df["id"])
            name_set = set(definitions_df["name"])
            
            resolved_ids = []
            for m in metadata:
                if m in id_set:
                    resolved_ids.append(m)
                elif m in name_set:
                    match_id = definitions_df.loc[definitions_df["name"] == m, "id"].values[0]
                    resolved_ids.append(match_id)
                else:
                    raise ValueError(f"Metadata item '{m}' not found as ID or name.")
            property_definition_ids = resolved_ids
        else:
            property_definition_ids = definitions_df["id"].tolist()

        # Build and send the request
        payload = {
            "cellTestIds": cell_ids,
            "propertyDefinitionIds": property_definition_ids
        }

        try:
            response = requests.post(
                f"{self.service_url}/publicapi/v1/cells/getmetadata",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

            items = response.json().get("items", [])

            rows = []
            for item in items:
                for prop in item["userProperties"]:
                    rows.append({
                        "id": item["id"],
                        "name": prop["name"],
                        "value": prop["value"],
                        "propertyDefinitionId": prop["propertyDefinitionId"]
                    })

            df = pd.DataFrame(rows)
            df_wide = df.pivot(index="id", columns="name", values="value").reset_index()
            return df_wide

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"POST request failed: {e}")
        
    def write_cell_metadata(self, changes: list, timeout: int = 10):
        """
        Wrapper for POST /cells/updatemetadata endpoint.
        Accepts either a metadata 'field' (human-readable name) or 'propertyDefinitionId'.

        Parameters
        ----------
        changes : list of dict
            A list of metadata change dictionaries. Each dictionary must contain:
            - "id": str
            - "field": str (human-readable name, e.g., "Weight (g)") OR
            - "propertyDefinitionId": str (UUID)
            - "value": any (will be cast to str)

        timeout : int, optional
            Timeout in seconds for the request. Default is 10.

        Returns
        -------
        bool
            True if successful (204 No Content), otherwise raises RuntimeError.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        # Build lookup: field name -> propertyDefinitionId
        metadata_df = self.list_cell_metadata_definitions(type='df')
        name_to_id = dict(zip(metadata_df['name'], metadata_df['id']))

        formatted_changes = []
        for change in changes:
            if "propertyDefinitionId" in change:
                property_id = change["propertyDefinitionId"]
            elif "field" in change:
                field_name = change["field"]
                if field_name not in name_to_id:
                    raise RuntimeError(f"Field name '{field_name}' not found in metadata definitions.")
                property_id = name_to_id[field_name]
            else:
                raise RuntimeError("Each change must include either 'field' or 'propertyDefinitionId'.")

            formatted_changes.append({
                "id": change["id"],
                "propertyDefinitionId": property_id,
                "value": str(change["value"])
            })

        payload = {"changes": formatted_changes}

        try:
            response = requests.post(
                f"{self.service_url}/publicapi/v1/cells/updatemetadata",
                headers=self.headers,
                json=payload,
                timeout=timeout
            )

            if response.status_code == 204:
                print("✅ Metadata update successful!")
                return True
            else:
                raise RuntimeError(f"Metadata update failed: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"POST request failed: {e}")
    
    def get_specifications_table(self):
        """
        Fetch specifications list with their user properties.

        Returns
        -------
        pd.DataFrame
            DataFrame containing specification data with flattened user properties.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        try:
            response = requests.get(
                f"{self.service_url}/publicapi/v1/specification/list",
                headers=self.headers
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            if not items:
                print("⚠️ No specifications returned.")
                return pd.DataFrame()

            # Flatten the data structure
            rows = []
            for item in items:
                row = {
                    "id": item["id"],
                    "name": item["name"]
                }

                # Add user properties as separate columns
                for prop in item.get("userProperties", []):
                    if prop.get("name"):
                        row[prop["name"]] = prop.get("value")

                rows.append(row)

            return pd.DataFrame(rows)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"GET request failed: {e}")

    def _parse_date_to_utc(self, date_input):
        """
        Parse date formats and convert to UTC ISO format.

        Parameters
        ----------
        date_input : str or None
            Date string in formats like "May 1, 2025", "2025-05-01", or "25-05-01"

        Returns
        -------
        str
            UTC ISO formatted date string
        """
        if date_input is None:
            return "2020-01-01T00:00:00Z"

        from datetime import datetime
        import re

        date_input = date_input.strip()

        # Try full month name formats first
        month_formats = [
            "%B %d, %Y",      # May 1, 2025
            "%b %d, %Y",      # May 1, 2025 (abbreviated)
            "%B %d %Y",       # May 1 2025 (without comma)
            "%b %d %Y",       # May 1 2025 (abbreviated, without comma)
        ]

        for fmt in month_formats:
            try:
                parsed_date = datetime.strptime(date_input, fmt)
                return parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue

        # Try ISO formats with 2-digit and 4-digit years
        iso_patterns = [
            (r"^(\d{4})-(\d{1,2})-(\d{1,2})$", "%Y-%m-%d"),    # 2025-05-01 or 2025-5-1
            (r"^(\d{2})-(\d{1,2})-(\d{1,2})$", "%y-%m-%d"),    # 25-05-01 or 25-5-1
        ]

        for pattern, fmt in iso_patterns:
            if re.match(pattern, date_input):
                try:
                    parsed_date = datetime.strptime(date_input, fmt)
                    return parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    continue

        # If we get here, the format wasn't recognized
        error_msg = (
            f"Unable to parse date: '{date_input}'. "
            f"Please use one of these formats:\n"
            f"  • Full month name: 'May 1, 2025' or 'January 15, 2024'\n"
            f"  • ISO format: '2025-05-01' or '25-05-01'\n"
            f"Avoid ambiguous formats like '05-01-2025' - use month names instead!"
        )
        raise ValueError(error_msg)

    def get_failed_test_requests(self, since=None):
        """
        Get a list of failed test requests since a given date.

        Parameters
        ----------
        since : str, optional
            Date string in various formats (e.g., "May 1, 2025", "01-05-2025").
            Defaults to January 1, 2020 if not provided.

        Returns
        -------
        pd.DataFrame
            DataFrame containing failed test request data.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        utc_date = self._parse_date_to_utc(since)

        try:
            response = requests.get(
                f"{self.service_url}/publicapi/v1/testmgt/list/failed/{utc_date}",
                headers=self.headers
            )
            response.raise_for_status()

            items = response.json()
            if not items:
                print("⚠️ No failed test requests returned.")
                return pd.DataFrame()

            return pd.DataFrame(items)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"GET request failed: {e}")

    def get_test_request_list(self, since=None):
        """
        Get a list of all test requests since a given date.

        Parameters
        ----------
        since : str, optional
            Date string in various formats (e.g., "May 1, 2025", "01-05-2025").
            Defaults to January 1, 2020 if not provided.

        Returns
        -------
        pd.DataFrame
            DataFrame containing test request data.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        utc_date = self._parse_date_to_utc(since)

        try:
            response = requests.get(
                f"{self.service_url}/publicapi/v1/testmgt/list/{utc_date}",
                headers=self.headers
            )
            response.raise_for_status()

            items = response.json()
            if not items:
                print("⚠️ No test requests returned.")
                return pd.DataFrame()

            return pd.DataFrame(items)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"GET request failed: {e}")

    def get_test_request(self, request_id):
        """
        Get the full details of a specific test request.

        Parameters
        ----------
        request_id : str
            GUID of the test request to retrieve.

        Returns
        -------
        dict
            Full test request details.
        """
        if not self.headers:
            raise RuntimeError("Authentication required. Call authenticate() first.")

        self._refresh_token_if_needed()

        try:
            response = requests.get(
                f"{self.service_url}/publicapi/v1/testmgt/request/get/{request_id}",
                headers=self.headers
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                raise RuntimeError(f"Test request {request_id} not found.")
            raise RuntimeError(f"GET request failed: {e}")
            


            






                
                
