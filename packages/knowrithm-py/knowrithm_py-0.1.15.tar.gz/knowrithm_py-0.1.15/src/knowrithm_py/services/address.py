
from typing import Any, Dict, List, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class AddressService:
    """
    Client helper for the geographic reference data routes exposed under
    ``app/blueprints/address/routes.py``. Each method mirrors a documented
    endpoint and captures the expected payload, headers, and response shape so
    that SDK consumers do not need to re-implement request boilerplate.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def seed_reference_data(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Trigger the one-time bootstrap that populates countries, states, and cities.

        Endpoint:
            ``GET /v1/address-seed`` (no authentication required).

        Args:
            headers: Optional overrides (for example when you want to omit the API
                key headers configured on the session or inject a JWT).

        Returns:
            JSON payload describing which datasets were seeded.
        """
        return self.client._make_request("GET", "/address-seed", headers=headers)

    # --------------------------------------------------------------------- #
    # Country operations
    # --------------------------------------------------------------------- #
    def create_country(
        self,
        name: str,
        iso_code: Optional[str] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a country record.

        Endpoint:
            ``POST /v1/country`` - requires ``Authorization: Bearer <token>`` with an
            admin role or API keys that include the ``admin`` scope.

        Payload:
            ``name`` (str, required), ``iso_code`` (str, optional).

        Args:
            name: Country name as it should appear to users.
            iso_code: Optional ISO-3166 alpha code.
            headers: Optional header overrides (useful for JWT flows).

        Returns:
            JSON object for the created country.
        """
        payload: Dict[str, Any] = {"name": name}
        if iso_code is not None:
            payload["iso_code"] = iso_code
        return self.client._make_request("POST", "/country", data=payload, headers=headers)

    def list_countries(self, headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        List all countries with their metadata.

        Endpoint:
            ``GET /v1/country`` - public.

        Args:
            headers: Optional header overrides.

        Returns:
            List of country dictionaries, each containing nested state information
            if available.
        """
        return self.client._make_request("GET", "/country", headers=headers)

    def get_country(self, country_id: int, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve a single country and its nested states.

        Endpoint:
            ``GET /v1/country/<country_id>`` - public.

        Args:
            country_id: Primary key of the country to fetch.
            headers: Optional header overrides.

        Returns:
            Country record with an embedded ``states`` collection.
        """
        return self.client._make_request("GET", f"/country/{country_id}", headers=headers)

    def update_country(
        self,
        country_id: int,
        *,
        name: Optional[str] = None,
        iso_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update the mutable fields of a country.

        Endpoint:
            ``PATCH /v1/country/<country_id>`` - requires admin privileges.

        Payload:
            ``name`` and/or ``iso_code`` (both optional, at least one required).

        Args:
            country_id: Target country identifier.
            name: Replacement name.
            iso_code: Replacement ISO code.
            headers: Optional header overrides.

        Returns:
            Updated country representation from the API.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if iso_code is not None:
            payload["iso_code"] = iso_code
        return self.client._make_request("PATCH", f"/country/{country_id}", data=payload, headers=headers)

    # --------------------------------------------------------------------- #
    # State operations
    # --------------------------------------------------------------------- #
    def create_state(
        self,
        name: str,
        country_id: int,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a state within a given country.

        Endpoint:
            ``POST /v1/state`` - requires admin privileges.

        Payload:
            ``name`` (str, required) and ``country_id`` (int, required).

        Args:
            name: Human readable name for the state or province.
            country_id: Foreign key referencing the parent country.
            headers: Optional header overrides.

        Returns:
            API response describing the created state.
        """
        payload = {"name": name, "country_id": country_id}
        return self.client._make_request("POST", "/state", data=payload, headers=headers)

    def list_states_by_country(
        self,
        country_id: int,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List states that belong to a given country.

        Endpoint:
            ``GET /v1/state/country/<country_id>`` - public.

        Args:
            country_id: Country identifier.
            headers: Optional header overrides.

        Returns:
            List of state dictionaries, each with nested city collections when available.
        """
        return self.client._make_request("GET", f"/state/country/{country_id}", headers=headers)

    def get_state(self, state_id: int, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve a specific state together with its cities.

        Endpoint:
            ``GET /v1/state/<state_id>`` - public.

        Args:
            state_id: State identifier.
            headers: Optional header overrides.

        Returns:
            State representation containing nested city metadata.
        """
        return self.client._make_request("GET", f"/state/{state_id}", headers=headers)

    def update_state(
        self,
        state_id: int,
        *,
        name: Optional[str] = None,
        country_id: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update the fields of a state or transfer it to a different country.

        Endpoint:
            ``PATCH /v1/state/<state_id>`` - requires admin privileges.

        Payload:
            ``name`` and/or ``country_id`` (both optional, at least one required).

        Args:
            state_id: Target state identifier.
            name: New state name.
            country_id: Target country identifier when moving the state.
            headers: Optional header overrides.

        Returns:
            Updated state record.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if country_id is not None:
            payload["country_id"] = country_id
        return self.client._make_request("PATCH", f"/state/{state_id}", data=payload, headers=headers)

    # --------------------------------------------------------------------- #
    # City operations
    # --------------------------------------------------------------------- #
    def create_city(
        self,
        name: str,
        state_id: int,
        *,
        postal_code_prefix: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a city within the supplied state.

        Endpoint:
            ``POST /v1/city`` - requires admin privileges.

        Payload:
            ``name`` (str, required), ``state_id`` (int, required),
            ``postal_code_prefix`` (str, optional).

        Args:
            name: City or locality name.
            state_id: Parent state identifier.
            postal_code_prefix: Optional postal prefix to aid lookups.
            headers: Optional header overrides.

        Returns:
            City representation returned by the API.
        """
        payload: Dict[str, Any] = {"name": name, "state_id": state_id}
        if postal_code_prefix is not None:
            payload["postal_code_prefix"] = postal_code_prefix
        return self.client._make_request("POST", "/city", data=payload, headers=headers)

    def list_cities_by_state(
        self,
        state_id: int,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List cities linked to a given state.

        Endpoint:
            ``GET /v1/city/state/<state_id>`` - public.

        Args:
            state_id: Target state identifier.
            headers: Optional header overrides.

        Returns:
            List of city dictionaries.
        """
        return self.client._make_request("GET", f"/city/state/{state_id}", headers=headers)

    def get_city(self, city_id: int, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve an individual city record.

        Endpoint:
            ``GET /v1/city/<city_id>`` - public.

        Args:
            city_id: City identifier.
            headers: Optional header overrides.

        Returns:
            City record as provided by the API.
        """
        return self.client._make_request("GET", f"/city/{city_id}", headers=headers)

    def update_city(
        self,
        city_id: int,
        *,
        name: Optional[str] = None,
        state_id: Optional[int] = None,
        postal_code_prefix: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update city metadata.

        Endpoint:
            ``PATCH /v1/city/<city_id>`` - requires admin privileges.

        Payload:
            Any subset of ``name``, ``state_id``, ``postal_code_prefix``.

        Args:
            city_id: Target city identifier.
            name: New name for the city.
            state_id: New state to associate.
            postal_code_prefix: Updated prefix information.
            headers: Optional header overrides.

        Returns:
            Updated city record.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if state_id is not None:
            payload["state_id"] = state_id
        if postal_code_prefix is not None:
            payload["postal_code_prefix"] = postal_code_prefix
        return self.client._make_request("PATCH", f"/city/{city_id}", data=payload, headers=headers)

    # --------------------------------------------------------------------- #
    # Company address management
    # --------------------------------------------------------------------- #
    def create_address(
        self,
        street_address: str,
        city_id: int,
        state_id: int,
        country_id: int,
        *,
        lat: Optional[float] = None,
        lan: Optional[float] = None,
        postal_code: Optional[str] = None,
        is_primary: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a company address record.

        Endpoint:
            ``POST /v1/address`` - admin JWT or API key scope ``admin`` required.

        Payload:
            - ``street_address`` (str, required)
            - ``city_id`` (int, required)
            - ``state_id`` (int, required)
            - ``country_id`` (int, required)
            - ``lat`` (float, optional)
            - ``lan`` (float, optional - longitude)
            - ``postal_code`` (str, optional)
            - ``is_primary`` (bool, optional)

        Args:
            street_address: Address line 1 for the company.
            city_id: Foreign key referencing the city.
            state_id: Foreign key referencing the state.
            country_id: Foreign key referencing the country.
            lat: Optional latitude value.
            lan: Optional longitude value (API naming uses ``lan``).
            postal_code: Optional postal or ZIP code.
            is_primary: Mark the address as the primary company location.
            headers: Optional header overrides.

        Returns:
            Created address payload from the API.
        """
        payload: Dict[str, Any] = {
            "street_address": street_address,
            "city_id": city_id,
            "state_id": state_id,
            "country_id": country_id,
        }
        if lat is not None:
            payload["lat"] = lat
        if lan is not None:
            payload["lan"] = lan
        if postal_code is not None:
            payload["postal_code"] = postal_code
        if is_primary is not None:
            payload["is_primary"] = is_primary
        return self.client._make_request("POST", "/address", data=payload, headers=headers)

    def get_company_address(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve the address for the authenticated company.

        Endpoint:
            ``GET /v1/address`` - requires company context via JWT or API key.

        Args:
            headers: Optional header overrides.

        Returns:
            Address payload associated with the current authentication context.
        """
        return self.client._make_request("GET", "/address", headers=headers)


