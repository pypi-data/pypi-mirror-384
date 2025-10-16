"""
WikiTree API Python Client
--------------------------

Implements the :class:`WikiTreeSession` class for interacting with the official
WikiTree JSON API. Handles authentication, request construction, and
standardized response handling.

Copyright (c) 2025 Steven Harris
License: GPL-3.0-only
"""

from __future__ import annotations

import re
import urllib.parse
import requests
from typing import Any, Dict, Optional, List, Union
from .exceptions import WikiTreeAPIError
from .utils import ensure_json, extract_status
from .fields_reference import list_fields


class WikiTreeSession:
    """
    Represents a session with the WikiTree API.

    Provides both authenticated and public (unauthenticated) access
    through a persistent :class:`requests.Session`.

    The class exposes one method per supported API ``action`` call.

    Available API wrappers
    ----------------------
    - :meth:`getProfile` — Retrieve a full profile.
    - :meth:`getPerson` — Retrieve a minimal profile.
    - :meth:`getPeople` — Retrieve multiple profiles.
    - :meth:`getAncestors` — Get a person's ancestors.
    - :meth:`getDescendants` — Get a person's descendants.
    - :meth:`getRelatives` — Immediate family and relatives.
    - :meth:`getFamily` — Parents, spouses, and children.
    - :meth:`getConnected` — People connected within N degrees.
    - :meth:`getConnections` — Shortest path between two profiles.
    - :meth:`getWatchlist` — User's watchlist (requires login).
    - :meth:`getBio` — Plain-text biography for a profile.
    - :meth:`getImages` — Media attached to a profile.
    - :meth:`getSpace` — Space page content.
    - :meth:`getCategories` — Search or list categories.
    - :meth:`getProfileUpdates` — Recent profile edits.
    - :meth:`searchPerson` — Search for profiles by name and filters.

    Example
    -------
    >>> from wikitree_api import WikiTreeSession
    >>> wt = WikiTreeSession()
    >>> wt.authenticate(email="user@example.com", password="secret")
    >>> data = wt.getProfile(key="Clemens-1")
    >>> print(data["person"]["Name"])
    """

    BASE_URL = "https://api.wikitree.com/api.php"

    def __init__(self) -> None:
        """Initialize a new WikiTree API session."""
        self.session = requests.Session()
        self.authenticated: bool = False
        self.user_id: Optional[int] = None
        self.user_name: Optional[str] = None
        self.email: Optional[str] = None
        self.cookies: Optional[Dict[str, str]] = None

    # ------------------------------------------------------------------
    # Core request handling
    # ------------------------------------------------------------------
    def request(self, action: str, **params: Any) -> Any:
        """
        Execute a WikiTree API request.

        Parameters
        ----------
        action : str
            The API action name (for example, ``getProfile``).
        **params :
            Additional form parameters for the request.

        Returns
        -------
        Any
            Parsed JSON object returned by the API.

        Raises
        ------
        WikiTreeAPIError
            If the response is not valid JSON or the API status is non-zero.
        """
        if not action:
            raise ValueError("Missing required parameter: action")

        payload = {"action": action, **params}
        response = self.session.post(self.BASE_URL, data=payload)

        try:
            data = response.json()
        except Exception:
            raise WikiTreeAPIError("Response is not valid JSON")

        data = ensure_json(data)
        status = extract_status(data)
        if status not in (None, 0, "0"):
            raise WikiTreeAPIError("API returned error", status=status, payload=data)

        return data

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def authenticate(self, *, email: str, password: str) -> bool:
        """Authenticate the user via the two-step clientLogin process."""
        print("Authenticating with WikiTree...")

        # Step 1: credentials → redirect with authcode
        data = {
            "action": "clientLogin",
            "doLogin": "1",
            "wpEmail": email,
            "wpPassword": password,
        }
        resp = self.session.post(self.BASE_URL, data=data, allow_redirects=False)
        if resp.status_code != 302:
            raise WikiTreeAPIError(f"Authentication failed: expected redirect (302), got {resp.status_code}")

        location = resp.headers.get("Location", "")
        match = re.search(r"authcode=([^&]+)", location)
        if not match:
            raise WikiTreeAPIError("Authentication failed: missing or invalid authcode in redirect")
        authcode = match.group(1)

        # Step 2: verify authcode
        resp = self.session.post(
            self.BASE_URL, data={"action": "clientLogin", "authcode": authcode}, allow_redirects=False
        )

        # Some installations return a redirect here instead of cookies immediately
        if resp.status_code in (301, 302) and "Location" in resp.headers:
            verify_url = resp.headers["Location"]
            self.session.get(verify_url)  # follow manually to ensure cookies set

        cookies = self.session.cookies.get_dict()

        # WikiTree sometimes uses one of these two cookie key names depending on backend version.
        if not any(k in cookies for k in ("wikidb_wtb__session", "wikitree_wtb_Token")):
            raise WikiTreeAPIError("Authentication failed: session cookies not set properly")

        user = urllib.parse.unquote(cookies.get("wikidb_wtb_UserName", "?"))
        print(f'User "{user}" is successfully authenticated!')

        self.authenticated = True
        self.cookies = cookies
        self.email = email
        self.user_name = user
        self.user_id = int(cookies.get("wikitree_wtb_UserID", 0)) or None
        return True

    # ------------------------------------------------------------------
    # API Action Wrappers
    # ------------------------------------------------------------------
    def getAncestors(self, *, key: str, depth: int = 1, fields: Optional[str] = None,
                     bioFormat: Optional[str] = None, resolveRedirect: Optional[int] = None,
                     **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve one or more ancestor profiles starting from a specified person.

        This action follows the ``Mother`` and ``Father`` links recursively
        up to the specified number of generations (``depth``). Each returned
        ancestor profile includes the selected fields.

        Parameters
        ----------
        key : str
            The WikiTree ID or numeric Person ID to start from.
            Example: ``"Adams-35"`` or ``3636``.
        depth : int, default=1
            The number of generations back to follow the parent links.
            ``1`` returns parents; ``2`` includes grandparents; etc.
        fields : str, optional
            Comma-separated list of profile fields to return.
            Defaults to all fields except biography, children, and spouses.
            Common fields can be viewed via :func:`fields_reference.list_fields`.
        bioFormat : {"wiki", "html", "both"}, optional
            Controls how biography text is returned if the ``bio`` field
            is included. ``"wiki"`` returns raw markup, ``"html"`` returns
            rendered HTML, and ``"both"`` includes both formats.
        resolveRedirect : int, optional
            If set to ``1``, any redirected profiles encountered during traversal
            will be resolved to their final (merged) profile.
        **kwargs :
            Additional parameters supported by the API.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``user_id``: ID of the starting person
              - ``ancestors``: list of ancestor profiles per requested depth

        Raises
        ------
        WikiTreeAPIError
            If the request fails, the API returns a non-zero status,
            or the response is invalid JSON.

        Examples
        --------
        >>> wt.getAncestors(key="Adams-35", depth=1,
        ...                 fields="Id,Name,Mother,Father")
        {
            "user_id": "3636",
            "ancestors": [
                {"Id": 3636, "Name": "Adams-35", "Father": 3640, "Mother": 3641},
                {"Id": 3640, "Name": "Adams-38", "Father": 3642, "Mother": 3643},
                {"Id": 3641, "Name": "Bass-1",  "Father": 3660, "Mother": 3661}
            ],
            "status": 0
        }
        """
        params = {"key": key, "depth": depth}
        if fields:
            params["fields"] = fields
        if bioFormat:
            params["bioFormat"] = bioFormat
        if resolveRedirect is not None:
            params["resolveRedirect"] = resolveRedirect
        params.update(kwargs)
        return self.request("getAncestors", **params)

    def getBio(self, *, key: str, bioFormat: Optional[str] = None,
               resolveRedirect: Optional[int] = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the biography text of a specific profile.

        This action returns the same ``bio`` data that would be included
        in :meth:`getProfile` or :meth:`getPerson` when the ``bio`` field
        is requested, but without the overhead of other fields.

        Parameters
        ----------
        key : str
            The WikiTree ID or numeric Person ID of the target profile.
            Example: ``"Clemens-1"`` or ``5185``.
        bioFormat : {"wiki", "html", "both"}, optional
            Controls how the biography text is returned:
              * ``"wiki"`` — return raw wikitext (default)
              * ``"html"`` — return rendered HTML
              * ``"both"`` — include both raw and rendered versions
        resolveRedirect : int, optional
            If set to ``1``, any requested profiles that have been merged or
            redirected will be automatically followed to their final profile.
        **kwargs :
            Additional parameters accepted by the API.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``user_id``: numeric ID of the profile owner
              - ``Id``: integer person ID
              - ``PageId``: internal page ID used by :meth:`getProfile`
              - ``Name``: WikiTree ID
              - ``bio``: biography wikitext
              - ``bioHTML``: rendered biography (if requested via ``bioFormat``)

        Raises
        ------
        WikiTreeAPIError
            If the API request fails or the response is not valid JSON.

        Examples
        --------
        >>> wt.getBio(key="Clemens-1")
        {
            "user_id": 5185,
            "Id": 5185,
            "PageId": 7146,
            "Name": "Clemens-1",
            "status": 0,
            "bio": "... biography text ..."
        }

        >>> wt.getBio(key="Clemens-1", bioFormat="html")
        {
            "bio": "... wikitext ...",
            "bioHTML": "<p>Rendered HTML...</p>"
        }
        """
        params = {"key": key}
        if bioFormat:
            params["bioFormat"] = bioFormat
        if isinstance(resolveRedirect, (int, str)) and resolveRedirect != 0:
            params["resolveRedirect"] = int(resolveRedirect)  # pyright: ignore[reportArgumentType]
        params.update(kwargs)
        return self.request("getBio", **params)

    def getCategories(self, *, key: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the list of categories connected to a specific profile.

        This action returns all categories linked to a Person or
        Free-Space profile. It can be used to identify topical, project,
        or location-based classifications associated with that page.

        Parameters
        ----------
        key : str
            The WikiTree ID, Free-Space Profile name, or numeric Page ID.
            Examples:
              * ``"Shoshone-1"`` — a person profile
              * ``"Space:Edward_D._Whitten's_Model_Ships"`` — a Free-Space profile
        **kwargs :
            Additional parameters accepted by the API (reserved for future use).

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``page_name``: the page or profile name requested
              - ``categories``: list of category titles connected to the profile

        Raises
        ------
        WikiTreeAPIError
            If the API call fails, returns a non-zero status, or provides
            invalid JSON data.

        Examples
        --------
        >>> wt.getCategories(key="Shoshone-1")
        {
            "page_name": "Shoshone-1",
            "categories": [
                "Example_Profiles_of_the_Week",
                "Lemhi_Shoshone",
                "Lewis_and_Clark_Expedition",
                "National_Women's_Hall_of_Fame_(United_States)"
            ],
            "status": 0
        }

        >>> wt.getCategories(key="Space:Texas_Project")
        {
            "page_name": "Space:Texas_Project",
            "categories": ["Texas", "US_Projects", "Regional_Groups"],
            "status": 0
        }
        """
        params = {"key": key}
        params.update(kwargs)
        return self.request("getCategories", **params)

    def getConnectedDNATestsByProfile(self, *, key: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve all DNA tests connected to a specific profile.

        This action returns information about all DNA tests and
        their corresponding test-taker profiles that are connected
        to the given WikiTree profile.

        Parameters
        ----------
        key : str
            The WikiTree ID or numeric Person ID of the profile whose
            connected DNA tests should be retrieved.
            Example: ``"Whitten-1"`` or ``32``.
        **kwargs :
            Additional optional parameters accepted by the API.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``page_name``: name of the profile queried
              - ``dnaTests``: list of DNA test objects, each including:
                * ``dna_id`` — integer test ID
                * ``dna_slug`` — short descriptive label
                * ``dna_name`` — test display title
                * ``dna_type`` — test category (e.g., ``auDNA``, ``YDNA``)
                * ``assigned`` — timestamp when the test was assigned
                * ``assignedBy`` — WikiTree ID of the member who assigned the test
                * ``haplo`` — Y-chromosome haplogroup
                * ``markers`` — number of YDNA markers tested
                * ``mttype`` — mitochondrial test type
                * ``haplom`` — mitochondrial haplogroup
                * ``ancestry`` — Ancestry.com username (if provided)
                * ``ftdna`` — Family Tree DNA kit number
                * ``gedmatch`` — GEDmatch ID
                * ``mitoydna`` — mitoYDNA ID
                * ``yourDNAportal`` — YourDNAPortal ID
                * ``taker`` — dictionary with test-taker information:
                    - ``Id`` — numeric user ID
                    - ``PageId`` — profile page ID
                    - ``Name`` — WikiTree ID

        Raises
        ------
        WikiTreeAPIError
            If the request fails or the API returns invalid data.

        Examples
        --------
        >>> wt.getConnectedDNATestsByProfile(key="Whitten-1")
        {
            "page_name": "Whitten-1",
            "status": 0,
            "dnaTests": [
                {
                    "dna_id": "1",
                    "dna_slug": "23andme_audna",
                    "dna_name": "23andMe",
                    "dna_type": "auDNA",
                    "assigned": "2020-04-02 13:40:30",
                    "assignedBy": "Whitten-1",
                    "haplo": "R1b1b2a1a1*",
                    "markers": "0",
                    "haplom": "U5a1a1",
                    "taker": {"Id": "32", "PageId": "24", "Name": "Whitten-1"}
                }
            ]
        }
        """
        params = {"key": key}
        params.update(kwargs)
        return self.request("getConnectedDNATestsByProfile", **params)

    def getConnectedProfilesByDNATest(self, *, key: str, dna_id: int, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve all profiles connected to a test-taker profile through a specific DNA test.

        This action identifies profiles connected via a particular DNA test assigned to
        the given test-taker's profile. It can be used to explore matches by test type,
        including autosomal (auDNA), Y-chromosome (yDNA), and mitochondrial (mtDNA) tests.

        Parameters
        ----------
        key : str
            The WikiTree ID or numeric Person ID of the DNA test-taker profile.
            Example: ``"Whitten-1"`` or ``32``.
        dna_id : int
            The integer ID of the DNA test used to find connected profiles.
            Supported values include:
              * 1 — 23andMe
              * 2 — AncestryDNA
              * 3 — AncestryDNA Paternal Lineage
              * 4 — AncestryDNA Maternal Lineage
              * 6 — Family Tree DNA Family Finder
              * 7 — Family Tree DNA mtDNA
              * 8 — Family Tree DNA yDNA
              * 9 — Other auDNA
              * 10 — Other mtDNA
              * 11 — Other yDNA
              * 12 — MyHeritage DNA
              * 13 — Living DNA
        **kwargs :
            Additional optional API parameters.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``page_name``: name of the DNA test-taker profile
              - ``dnaTest``: dictionary with details of the selected DNA test, including:
                  * ``dna_id`` — integer test ID
                  * ``dna_slug`` — short descriptive label
                  * ``dna_name`` — human-readable test name
                  * ``dna_type`` — type of test (``yDNA``, ``auDNA``, ``mtDNA``)
                  * ``assigned`` — assignment timestamp (if available)
                  * ``assignedBy`` — WikiTree ID of member who assigned the test
              - ``connections``: list of connected profiles, where each item contains:
                  * ``Id`` — numeric user ID
                  * ``PageId`` — profile page ID
                  * ``Name`` — WikiTree ID

        Raises
        ------
        WikiTreeAPIError
            If the API request fails, returns invalid JSON, or reports an error status.

        Examples
        --------
        >>> wt.getConnectedProfilesByDNATest(key="Whitten-1", dna_id=8)
        {
            "page_name": "Whitten-1",
            "status": 0,
            "dnaTest": {
                "dna_id": "8",
                "dna_slug": "ftdna_ydna",
                "dna_name": "FTDNA Y-Chromosome",
                "dna_type": "yDNA"
            },
            "connections": [
                {"Id": "13654071", "PageId": "14605469", "Name": "Whitten-1205"},
                {"Id": "7156327", "PageId": "7419651", "Name": "Whitten-692"},
                {"Id": "45783", "PageId": "53867", "Name": "Whitten-56"}
            ]
        }
        """
        params = {"key": key, "dna_id": dna_id}
        params.update(kwargs)
        return self.request("getConnectedProfilesByDNATest", **params)

    def getConnections(
        self,
        *,
        keys: str,
        appId: str,
        fields: Optional[str] = None,
        relation: int = 0,
        ignoreIds: Optional[str] = None,
        nopath: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve the relationship path and degrees of separation between two profiles.

        This action calculates the relationship path between two WikiTree profiles
        and can return either the full path or only the path length. It is useful
        for discovering how two individuals are connected through blood relations,
        marriage, or other links.

        Parameters
        ----------
        keys : str
            Two WikiTree IDs or User IDs separated by a comma.
            Examples: ``"Adams-35,Windsor-1"`` or ``"3636,64662"``.
        appId : str
            Identifier for your application (required).
            Used by WikiTree to track API usage.
        fields : str, optional
            Comma-separated list of fields to return for each profile in the path.
            Defaults to the standard profile field set.
            See :func:`fields_reference.list_fields` for available fields.
        relation : int, default=0
            Determines the type of relationship path to calculate:
              * 0 — Shortest path (default)
              * 1 — Shortest path excluding spouses
              * 2 — Shortest path through a common ancestor
              * 3 — Shortest path through a common descendant
              * 4 — Shortest path through fathers only
              * 5 — Shortest path through mothers only
              * 6 — Shortest path through yDNA
              * 7 — Shortest path through mtDNA
              * 8 — Shortest path through auDNA
              * 11 — Shortest path through ancestors (2), or all relations if none
        ignoreIds : str, optional
            Comma-separated list of numeric User IDs to exclude from the path search.
            Note that WikiTree IDs will not work here.
        nopath : int, optional
            Set to ``1`` to return only the path length (``pathLength``) without
            the detailed ``path`` array.
        **kwargs :
            Additional API parameters accepted by the endpoint.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: empty string if successful, otherwise error message
              - ``userid1``: User ID of the first profile
              - ``userid2``: User ID of the second profile
              - ``relation``: relation mode used (matches input)
              - ``ignoreids``: list of ignored IDs (if any)
              - ``pathType``: same as ``relation`` unless ``11`` (fallback to ``0``)
              - ``pathLength``: integer distance (number of profiles in path)
              - ``path``: list of dictionaries, each containing:
                  * ``Id`` — numeric profile ID
                  * ``Name`` — WikiTree ID
                  * ``pathType`` — relationship type from previous to current
                  * ``pathStatus`` — certainty status (``30``=confident, ``20``=unknown, ``0``=?)

        Raises
        ------
        WikiTreeAPIError
            If the API request fails or the response is invalid.

        Examples
        --------
        Get the full path between two profiles:

        >>> wt.getConnections(keys="Adams-35,Windsor-1",
        ...                   appId="apiDocumentation",
        ...                   fields="Id,Name")
        {
            "status": "",
            "userid1": 3636,
            "userid2": 64662,
            "relation": 0,
            "pathLength": 16,
            "path": [
                {"Id": 3636, "Name": "Adams-35"},
                {"Id": 3586, "Name": "Adams-10", "pathType": "child", "pathStatus": "20"},
                {"Id": 64662, "Name": "Windsor-1", "pathType": "child", "pathStatus": "20"}
            ]
        }

        Get only the path length between two profiles:

        >>> wt.getConnections(keys="Adams-35,Windsor-1",
        ...                   appId="apiDocumentation", nopath=1)
        {
            "status": "",
            "userid1": 3636,
            "userid2": 64662,
            "pathLength": 16
        }

        Exclude a specific profile from the connection path:

        >>> wt.getConnections(keys="Adams-35,Windsor-1",
        ...                   appId="apiDocumentation",
        ...                   ignoreIds="21375339")
        {
            "status": "",
            "userid1": 3636,
            "userid2": 64662,
            "ignoreids": [21375339],
            "pathLength": 16
        }
        """
        params = {
            "keys": keys,
            "appId": appId,
            "relation": relation,
        }
        if fields:
            params["fields"] = fields
        if ignoreIds:
            params["ignoreIds"] = ignoreIds
        if nopath:
            params["nopath"] = int(nopath)
        params.update(kwargs)
        return self.request("getConnections", **params)

    def getDNATestsByTestTaker(self, *, key: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve DNA test information for a specific test-taker profile.

        This action returns all DNA tests assigned to the given profile,
        including YDNA, mtDNA, and autosomal (auDNA) test details as they
        appear on the profile’s “DNA Tests” section.

        Parameters
        ----------
        key : str
            The WikiTree ID or numeric Person ID of the test-taker profile.
            Example: ``"Whitten-1"`` or ``32``.
        **kwargs :
            Additional optional parameters accepted by the API.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``page_name``: WikiTree ID of the test-taker profile
              - ``dnaTests``: list of DNA test objects, each including:
                  * ``dna_id`` — integer test ID
                  * ``dna_slug`` — short descriptive label
                  * ``dna_name`` — display title (e.g., “23andMe”)
                  * ``dna_type`` — test category (``auDNA``, ``yDNA``, or ``mtDNA``)
                  * ``assigned`` — timestamp when the test was assigned
                  * ``assignedBy`` — WikiTree ID of the member who assigned the test
                  * ``haplo`` — Y-chromosome haplogroup
                  * ``markers`` — number of YDNA markers tested
                  * ``mttype`` — mitochondrial test type
                  * ``haplom`` — mitochondrial haplogroup
                  * ``ancestry`` — Ancestry.com username (if linked)
                  * ``ftdna`` — Family Tree DNA kit number
                  * ``gedmatch`` — GEDmatch ID
                  * ``mitoydna`` — mitoYDNA ID
                  * ``yourDNAportal`` — YourDNAPortal ID

        Raises
        ------
        WikiTreeAPIError
            If the API request fails or returns invalid JSON data.

        Examples
        --------
        >>> wt.getDNATestsByTestTaker(key="Whitten-1")
        {
            "page_name": "Whitten-1",
            "status": 0,
            "dnaTests": [
                {
                    "dna_id": "1",
                    "dna_slug": "23andme_audna",
                    "dna_name": "23andMe",
                    "dna_type": "auDNA",
                    "assigned": "2020-04-02 13:40:30",
                    "assignedBy": "Whitten-1",
                    "haplo": "R1b1b2a1a1*",
                    "markers": "0",
                    "haplom": "U5a1a1"
                }
            ]
        }
        """
        params = {"key": key}
        params.update(kwargs)
        return self.request("getDNATestsByTestTaker", **params)

    def getDescendants(
        self,
        *,
        key: str,
        depth: int = 1,
        fields: Optional[str] = None,
        bioFormat: Optional[str] = None,
        resolveRedirect: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve one or more descendant profiles starting from a specified person.

        This action follows the ``Children`` links recursively down to the specified
        number of generations (``depth``). Each returned descendant profile includes
        the selected fields.

        Parameters
        ----------
        key : str
            The WikiTree ID or numeric Person ID to start from.
            Example: ``"Adams-35"`` or ``3636``.
        depth : int, default=1
            The number of generations forward to follow the child links.
            ``1`` returns immediate children, ``2`` includes grandchildren, etc.
        fields : str, optional
            Comma-separated list of profile fields to return.
            Defaults to all fields except biography, children, and spouses.
            Common fields can be viewed via :func:`fields_reference.list_fields`.
        bioFormat : {"wiki", "html", "both"}, optional
            Controls how biography text is returned if the ``bio`` field
            is included. ``"wiki"`` returns raw markup, ``"html"`` returns
            rendered HTML, and ``"both"`` includes both formats.
        resolveRedirect : int, optional
            If set to ``1``, any redirected profiles encountered during traversal
            will be resolved to their final (merged) profile.
        **kwargs :
            Additional parameters supported by the API.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``user_name``: starting profile’s WikiTree ID
              - ``descendants``: list of descendant profiles with the selected fields

        Raises
        ------
        WikiTreeAPIError
            If the API request fails, returns an error status,
            or the response cannot be parsed as valid JSON.

        Examples
        --------
        >>> wt.getDescendants(key="Adams-35", depth=1,
        ...                   fields="Id,Name,Mother,Father")
        {
            "user_name": "Adams-35",
            "descendants": [
                {"Id": 3636, "Name": "Adams-35", "Father": 3640, "Mother": 3641},
                {"Id": 3586, "Name": "Adams-10", "Father": 3636, "Mother": 3637},
                {"Id": 3638, "Name": "Adams-36", "Father": 3636, "Mother": 3637},
                {"Id": 3639, "Name": "Adams-37", "Father": 3636, "Mother": 3637}
            ],
            "status": 0
        }
        """
        params = {"key": key, "depth": depth}
        if fields:
            params["fields"] = fields
        if bioFormat:
            params["bioFormat"] = bioFormat
        if resolveRedirect is not None:
            params["resolveRedirect"] = int(resolveRedirect)
        params.update(kwargs)
        return self.request("getDescendants", **params)

    def getPeople(
        self,
        *,
        keys: List[str],
        fields: Optional[str] = None,
        bioFormat: Optional[str] = None,
        siblings: Optional[int] = 0,
        ancestors: Optional[int] = 0,
        descendants: Optional[int] = 0,
        nuclear: Optional[int] = 0,
        minGeneration: Optional[int] = None,
        limit: Optional[int] = 1000,
        start: Optional[int] = 0,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve one or more profiles and optionally include relatives
        to a specified number of generations.

        This action is the most flexible of the profile retrieval endpoints,
        supporting multi-key queries and recursive expansion for related profiles.

        Parameters
        ----------
        keys : list of str
            One or more WikiTree IDs or numeric Person IDs.
            Example: ``["Clemens-1", "Federer-4", "Windsor-1"]``.
        fields : str, optional
            Comma-separated list of profile fields to return.  
            Defaults to only ``Id`` and ``Name``.  
            Note: ``Parents``, ``Children``, and ``Siblings`` cannot be
            explicitly requested; use ``nuclear``, ``ancestors``, or
            ``descendants`` instead.  
            You may also include ``Meta`` to retrieve metadata such as ``Degrees``.  
            See :func:`fields_reference.list_fields` for available options.
        bioFormat : {"wiki", "html", "both"}, optional
            Controls how biography text is returned if ``bio`` is included.
            ``"wiki"`` returns wikitext, ``"html"`` returns rendered HTML,
            and ``"both"`` includes both versions.
        siblings : int, optional
            If set to ``1``, include siblings of each requested profile.  
            Default is ``0`` (disabled).
        ancestors : int, optional
            Number of generations of ancestors to include. Default ``0``.
        descendants : int, optional
            Number of generations of descendants to include. Default ``0``.
        nuclear : int, optional
            Number of generations of nuclear relatives (parents, children,
            siblings, and spouses) to include. Default ``0``.
        minGeneration : int, optional
            Minimum generation number to start gathering relatives from.
        limit : int, optional
            Maximum number of related profiles to return per call.  
            Default ``1000``; results beyond this must be paginated using ``start``.
        start : int, optional
            Starting offset for paginated results. Default ``0``.
        **kwargs :
            Additional optional parameters accepted by the API.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: empty string if successful, otherwise error message
              - ``resultByKey``: dictionary mapping each input key to its resolved ID and status
              - ``people``: dictionary of all returned profiles keyed by ID,
                each containing the selected fields

        Raises
        ------
        WikiTreeAPIError
            If the API request fails, returns a non-zero status,
            or produces invalid JSON.

        Examples
        --------
        Get multiple profiles at once:

        >>> wt.getPeople(
        ...     keys=["Clemens-1", "Federer-4", "Windsor-1"],
        ...     fields="Id,PageId,Name,FirstName,LastNameAtBirth,BirthDate,DeathDate,Father,Mother"
        ... )
        {
            "status": "",
            "resultByKey": {"Clemens-1": {"Id": 5185}, "Windsor-1": {"Id": 64662}},
            "people": {
                "5185": {"Name": "Clemens-1", "BirthDate": "1835-11-30"},
                "64662": {"Name": "Windsor-1", "BirthDate": "1926-04-21"}
            }
        }

        Get a profile with its parents and grandparents:

        >>> wt.getPeople(
        ...     keys=["Hamill-277"],
        ...     fields="Id,Name,FirstName,LastNameAtBirth,Father,Mother",
        ...     ancestors=2
        ... )

        Paginate through extended ancestor results:

        >>> wt.getPeople(keys=["Swift-1107"], ancestors=5, limit=10, start=0)
        >>> wt.getPeople(keys=["Swift-1107"], ancestors=5, limit=10, start=10)
        """
        params = {
            "keys": ",".join(keys),
            "siblings": siblings,
            "ancestors": ancestors,
            "descendants": descendants,
            "nuclear": nuclear,
            "limit": limit,
            "start": start,
        }
        if fields:
            params["fields"] = fields
        if bioFormat:
            params["bioFormat"] = bioFormat
        if minGeneration is not None:
            params["minGeneration"] = minGeneration
        params.update(kwargs)
        return self.request("getPeople", **params)

    def getPerson(
        self,
        *,
        key: str,
        fields: Optional[str] = None,
        bioFormat: Optional[str] = None,
        resolveRedirect: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve a single person profile by WikiTree ID or numeric ID.

        This action is similar to :meth:`getProfile` but only supports
        Person profiles (not Free-Space profiles). It is typically used when
        you need to follow family relationships such as ``Mother`` and ``Father``,
        which reference User IDs.

        Parameters
        ----------
        key : str
            The WikiTree ID or numeric Person ID of the profile to fetch.
            Examples: ``"Clemens-1"`` or ``5185``.
        fields : str, optional
            Comma-separated list of fields to include in the returned profile.
            Defaults to all fields except ``bio``, ``Children``, and ``Spouses``.  
            You can also specify ``"*"``
            to return all fields.  
            See :func:`fields_reference.list_fields` for available field names.
        bioFormat : {"wiki", "html", "both"}, optional
            Controls how biography text is returned if ``bio`` is included.
            ``"wiki"`` returns raw wikitext, ``"html"`` returns rendered HTML,
            and ``"both"`` includes both formats.
        resolveRedirect : int, optional
            If set to ``1``, automatically resolve merged or redirected profiles
            to their final target profile.
        **kwargs :
            Additional parameters accepted by the API.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``page_name``: WikiTree ID of the requested profile
              - ``profile``: dictionary of profile fields (as specified in ``fields``)

        Raises
        ------
        WikiTreeAPIError
            If the request fails, the API returns an error, or the response
            is not valid JSON.

        Examples
        --------
        Retrieve by WikiTree ID:

        >>> wt.getPerson(key="Clemens-1",
        ...              fields="Id,PageId,Name,FirstName,LastNameAtBirth,BirthDate,DeathDate")
        {
            "page_name": "Clemens-1",
            "profile": {
                "Id": 5185,
                "PageId": 7146,
                "Name": "Clemens-1",
                "FirstName": "Samuel",
                "LastNameAtBirth": "Clemens",
                "BirthDate": "1835-11-30",
                "DeathDate": "1910-04-21"
            },
            "status": 0
        }

        Retrieve by numeric ID:

        >>> wt.getPerson(key="5185", fields="Id,Name,BirthDate,DeathDate")
        {
            "page_name": "Clemens-1",
            "profile": {"Id": 5185, "Name": "Clemens-1", "BirthDate": "1835-11-30"},
            "status": 0
        }
        """
        params = {"key": key}
        if fields:
            params["fields"] = fields
        if bioFormat:
            params["bioFormat"] = bioFormat
        if resolveRedirect is not None:
            params["resolveRedirect"] = int(resolveRedirect)  # pyright: ignore[reportArgumentType]
        params.update(kwargs)
        return self.request("getPerson", **params)

    def getPhotos(
        self,
        *,
        key: str,
        resolveRedirect: Optional[int] = None,
        limit: int = 10,
        start: int = 0,
        order: str = "PageId",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve photo and image metadata attached to a profile.

        This action returns information about images linked to a
        Person or Free-Space profile, including titles, upload dates,
        image sizes, and relative URLs for multiple resolutions.

        Parameters
        ----------
        key : str
            The WikiTree ID, Free-Space Profile name, or numeric Page ID
            of the profile whose photos should be retrieved.
            Examples:
              * ``"Clemens-1"`` — a Person profile
              * ``"Space:Edward_D._Whitten's_Model_Ships"`` — a Free-Space profile
              * ``7146`` — numeric Page ID
        resolveRedirect : int, optional
            If set to ``1``, any redirected profile pages will be automatically
            followed to their final target.
        limit : int, default=10
            The maximum number of photos to return.  
            Valid range: 1–100. Defaults to 10.
        start : int, default=0
            Index of the first photo to return. Used for pagination.
        order : {"PageId", "Uploaded", "ImageName", "Date"}, default="PageId"
            Sort order of the returned results:
              * ``"PageId"`` — by page ID (default)
              * ``"Uploaded"`` — by upload timestamp
              * ``"Date"`` — by descriptive date
              * ``"ImageName"`` — alphabetically by file name
        **kwargs :
            Additional optional parameters accepted by the API.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``page_name`` or ``page_id``: resolved key identifier
              - ``limit``: limit parameter value
              - ``start``: start parameter value
              - ``order``: applied sort order
              - ``photos``: list of photo objects, each including:
                  * ``PageId`` — page ID of the image
                  * ``ImageName`` — base filename
                  * ``Title`` — title text from image details
                  * ``Location`` — location (if provided)
                  * ``Date`` — descriptive date
                  * ``Type`` — image type ("photo" or "source")
                  * ``Size`` — file size in bytes
                  * ``Width`` — image width in pixels
                  * ``Height`` — image height in pixels
                  * ``Uploaded`` — upload timestamp
                  * ``URL`` — relative link to the image page
                  * ``URL_300`` — relative link to a 300px version
                  * ``URL_75`` — relative link to a 75px version

        Raises
        ------
        WikiTreeAPIError
            If the request fails, the API reports an error,
            or the response cannot be parsed as valid JSON.

        Examples
        --------
        Retrieve the two most recent photos by date:

        >>> wt.getPhotos(key="Clemens-1", limit=2, start=5, order="Date")
        {
            "page_name": "Clemens-1",
            "limit": 2,
            "start": 5,
            "order": "Date",
            "photos": [
                {
                    "PageId": "7299",
                    "ImageName": "1860-_Clemens.jpg",
                    "Title": "Samuel L. Clemens",
                    "Date": "1860-00-00",
                    "Uploaded": "2009-01-08 00:25:37",
                    "URL": "/photo/jpg/1860-_Clemens",
                    "URL_300": "/photo.php/thumb/f/f1/1860-_Clemens.jpg/300px-1860-_Clemens.jpg",
                    "URL_75": "/photo.php/thumb/f/f1/1860-_Clemens.jpg/75px-1860-_Clemens.jpg"
                }
            ],
            "status": 0
        }
        """
        params = {
            "key": key,
            "limit": limit,
            "start": start,
            "order": order,
        }
        if resolveRedirect is not None:
            params["resolveRedirect"] = int(resolveRedirect)
        params.update(kwargs)
        return self.request("getPhotos", **params)

    def getProfile(
        self,
        *,
        key: str,
        fields: Optional[str] = None,
        bioFormat: Optional[str] = None,
        resolveRedirect: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve a Person or Free-Space profile by WikiTree ID or Page ID.

        This action returns detailed profile data, including core identity
        fields, metadata, privacy flags, relatives, categories, templates,
        and optional biography text. It supports both Person and Free-Space
        profiles and is the foundation for most read-type operations.

        Parameters
        ----------
        key : str
            The WikiTree ID or numeric Page ID of the profile to fetch.
            Examples:
              * ``"Clemens-1"`` — a Person profile
              * ``"Space:Edward_D._Whitten's_Model_Ships"`` — a Free-Space profile
              * ``7146`` — numeric Page ID
        fields : str, optional
            Comma-separated list of profile fields to include.  
            Defaults to all core fields except ``Bio``, ``Children``, and ``Spouses``.  
            Use ``"*"``
            to return all fields.  
            You can also request relational arrays (``Parents``, ``Children``,
            ``Spouses``, ``Siblings``), as well as extended fields like
            ``Managers``, ``TrustedList``, ``Categories``, or ``Templates``.  
            See :func:`fields_reference.list_fields` for available options.
        bioFormat : {"wiki", "html", "both"}, optional
            Controls how biography text is returned when the ``Bio`` field
            is requested.  
            ``"wiki"`` returns raw wikitext,  
            ``"html"`` returns rendered HTML,  
            ``"both"`` includes both versions.
        resolveRedirect : int, optional
            Determines whether redirections (e.g. merged profiles) are resolved.  
            * ``1`` — follow the redirect to the final profile (default behavior)  
            * ``0`` — return the original pre-merge profile only
        **kwargs :
            Additional optional API parameters.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``page_name``: WikiTree ID of the returned profile
              - ``profile``: dictionary of requested fields, which may include:
                * Core identity fields (``Id``, ``Name``, ``FirstName``, ``LastNameAtBirth``)
                * Life data (``BirthDate``, ``DeathDate``, ``BirthLocation``, ``DeathLocation``)
                * Privacy flags (``Privacy_IsPrivate``, ``Privacy_IsOpen``)
                * Manager and creator IDs
                * Relational arrays (``Parents``, ``Children``, ``Spouses``, ``Siblings``)
                * Template and Category metadata
                * Optional ``Bio`` field, depending on ``bioFormat``

        Raises
        ------
        WikiTreeAPIError
            If the API request fails, returns a non-zero status, or produces
            invalid JSON.

        Examples
        --------
        Retrieve by WikiTree ID:

        >>> wt.getProfile(key="Clemens-1",
        ...               fields="Id,PageId,Name,FirstName,LastNameAtBirth,BirthDate,DeathDate")
        {
            "page_name": "Clemens-1",
            "profile": {
                "Id": 5185,
                "PageId": 7146,
                "Name": "Clemens-1",
                "FirstName": "Samuel",
                "LastNameAtBirth": "Clemens",
                "BirthDate": "1835-11-30",
                "DeathDate": "1910-04-21"
            },
            "status": 0
        }

        Retrieve by Page ID:

        >>> wt.getProfile(key="7146", fields="Id,Name,BirthDate,DeathDate")
        {
            "page_name": "Clemens-1",
            "profile": {"Id": 5185, "Name": "Clemens-1", "BirthDate": "1835-11-30"},
            "status": 0
        }

        Request all available data including Bio in HTML format:

        >>> wt.getProfile(key="Clemens-1", fields="*", bioFormat="html")
        """
        params = {"key": key}
        if fields:
            params["fields"] = fields
        if bioFormat:
            params["bioFormat"] = bioFormat
        if resolveRedirect is not None:
            params["resolveRedirect"] = int(resolveRedirect) # pyright: ignore[reportArgumentType]
        params.update(kwargs)
        return self.request("getProfile", **params)

    def getRelatives(
        self,
        *,
        keys: Union[str, List[str]],
        fields: Optional[str] = None,
        bioFormat: Optional[str] = None,
        getParents: bool = False,
        getChildren: bool = False,
        getSiblings: bool = False,
        getSpouses: bool = False,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve relatives (parents, children, siblings, spouses) for one or more profiles.

        This action returns detailed person data for each specified profile along
        with the requested sets of relatives. It provides an efficient way to
        obtain nuclear family structures without making separate API calls for
        each relationship.

        Parameters
        ----------
        keys : str or list of str
            Comma-separated WikiTree IDs or numeric User IDs of the profiles to query.
            Examples:
              * ``"Clemens-1"`` — single profile
              * ``"Clemens-1,Adams-35"`` — multiple profiles
              * ``["Clemens-1", "Adams-35"]`` — equivalent list form
        fields : str, optional
            Comma-separated list of fields to include for each person profile.
            Defaults to all standard fields except biography and spouses/children lists.
            You may specify ``"*"``
            to return all available fields.
        bioFormat : {"wiki", "html", "both"}, optional
            Controls how biography text is returned if the ``bio`` field is requested.
            ``"wiki"`` returns raw wikitext, ``"html"`` returns rendered HTML, and
            ``"both"`` includes both formats.
        getParents : bool, default=False
            If ``True``, include parent profiles.
        getChildren : bool, default=False
            If ``True``, include child profiles.
        getSiblings : bool, default=False
            If ``True``, include sibling profiles.
        getSpouses : bool, default=False
            If ``True``, include spouse profiles and marriage details.
        **kwargs :
            Additional optional API parameters.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``items``: list of result items, each with:
                  * ``key`` — starting WikiTree ID
                  * ``user_id`` — numeric User ID
                  * ``user_name`` — same as WikiTree ID
                  * ``person`` — requested profile fields plus optional relative arrays:
                      - ``Parents`` — dict keyed by parent IDs
                      - ``Children`` — dict keyed by child IDs
                      - ``Siblings`` — dict keyed by sibling IDs
                      - ``Spouses`` — dict keyed by spouse IDs, including marriage details

        Raises
        ------
        WikiTreeAPIError
            If the API request fails or returns an invalid response.

        Examples
        --------
        Retrieve parents, children, siblings, and spouses for multiple profiles:

        >>> wt.getRelatives(
        ...     keys="Clemens-1,Adams-35",
        ...     fields="Id,PageId,Name",
        ...     getParents=True,
        ...     getChildren=True,
        ...     getSiblings=True,
        ...     getSpouses=True
        ... )
        {
            "items": [
                {
                    "key": "Clemens-1",
                    "user_id": 5185,
                    "user_name": "Clemens-1",
                    "person": {
                        "Id": 5185,
                        "PageId": 7146,
                        "Name": "Clemens-1",
                        "Parents": {
                            "5186": {"Id": 5186, "Name": "Clemens-2"},
                            "5188": {"Id": 5188, "Name": "Lampton-1"}
                        },
                        "Spouses": {
                            "5256": {
                                "Id": 5256,
                                "Name": "Langdon-1",
                                "marriage_location": "Elmira, New York, USA",
                                "marriage_date": "1870-02-02"
                            }
                        },
                        "Children": {
                            "5260": {"Id": 5260, "Name": "Clemens-12"},
                            "5261": {"Id": 5261, "Name": "Clemens-13"}
                        },
                        "Siblings": {
                            "5191": {"Id": 5191, "Name": "Clemens-3"},
                            "5195": {"Id": 5195, "Name": "Clemens-6"}
                        }
                    }
                }
            ],
            "status": 0
        }
        """
        if isinstance(keys, list):
            keys = ",".join(keys)

        params = {
            "keys": keys,
            "getParents": int(getParents),
            "getChildren": int(getChildren),
            "getSiblings": int(getSiblings),
            "getSpouses": int(getSpouses),
        }
        if fields:
            params["fields"] = fields
        if bioFormat:
            params["bioFormat"] = bioFormat
        params.update(kwargs)
        return self.request("getRelatives", **params)

    def getWatchlist(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        order: str = "user_id",
        getPerson: bool = True,
        getSpace: bool = True,
        onlyLiving: bool = False,
        excludeLiving: bool = False,
        fields: Optional[str] = None,
        bioFormat: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve the Watchlist of the currently authenticated WikiTree user.

        This action returns profiles for which the logged-in user is on the
        Trusted List. The results include both Person and Free-Space profiles,
        depending on the selected filters.

        Parameters
        ----------
        limit : int, default=100
            Number of Watchlist items to return per page.  
            Maximum recommended value is 100.
        offset : int, default=0
            Starting offset for paginated Watchlist results.
        order : {"user_id", "user_name", "user_last_name_current",
                 "user_birth_date", "user_death_date", "page_touched"}, default="user_id"
            Sort order for returned profiles:
              * ``"user_id"`` – by internal ID  
              * ``"user_name"`` – by WikiTree ID  
              * ``"user_last_name_current"`` – by current last name  
              * ``"user_birth_date"`` – by birth date  
              * ``"user_death_date"`` – by death date  
              * ``"page_touched"`` – by most recent modification
        getPerson : bool, default=True
            If ``True``, include Person profiles on the Watchlist.
        getSpace : bool, default=True
            If ``True``, include Free-Space profiles on the Watchlist.
        onlyLiving : bool, default=False
            If ``True``, restrict results to living Person profiles only.
        excludeLiving : bool, default=False
            If ``True``, restrict results to deceased or non-living profiles only.
        fields : str, optional
            Comma-separated list of fields to include for each profile.  
            Defaults to all standard non-biography fields.  
            Use ``"*"``
            to return all available fields.
        bioFormat : {"wiki", "html", "both"}, optional
            Controls how biography text is returned if the ``bio`` field is requested:
              * ``"wiki"`` — raw wiki markup  
              * ``"html"`` — rendered HTML  
              * ``"both"`` — both formats included
        **kwargs :
            Additional optional API parameters.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``watchlistCount``: total number of profiles on the user’s Watchlist
              - ``watchlist``: array of profile objects, each with requested fields such as:
                  * ``Id`` — profile ID
                  * ``Name`` — WikiTree ID
                  * ``PageId`` — page ID
                  * ``BirthDate`` / ``DeathDate`` — life dates
                  * ``Touched`` — timestamp of last modification

        Raises
        ------
        WikiTreeAPIError
            If authentication fails, or the response is invalid or incomplete.

        Examples
        --------
        Retrieve the first 50 Watchlist profiles, sorted by last modified date:

        >>> wt.getWatchlist(limit=50, order="page_touched")
        {
            "watchlistCount": 486,
            "watchlist": [
                {"Id": 5185, "Name": "Clemens-1", "Touched": "2024-03-18 14:52:09"},
                {"Id": 12116601, "Name": "Hamill-300", "Touched": "2024-03-12 08:33:41"}
            ],
            "status": 0
        }

        Retrieve only living Person profiles:

        >>> wt.getWatchlist(onlyLiving=True, getSpace=False)
        """
        params = {
            "limit": limit,
            "offset": offset,
            "order": order,
            "getPerson": int(getPerson),
            "getSpace": int(getSpace),
            "onlyLiving": int(onlyLiving),
            "excludeLiving": int(excludeLiving),
        }
        if fields:
            params["fields"] = fields
        if bioFormat:
            params["bioFormat"] = bioFormat
        params.update(kwargs)
        return self.request("getWatchlist", **params)

    def searchPerson(
        self,
        *,
        FirstName: Optional[str] = None,
        LastName: Optional[str] = None,
        BirthDate: Optional[str] = None,
        DeathDate: Optional[str] = None,
        RealName: Optional[str] = None,
        LastNameCurrent: Optional[str] = None,
        BirthLocation: Optional[str] = None,
        DeathLocation: Optional[str] = None,
        Gender: Optional[str] = None,
        fatherFirstName: Optional[str] = None,
        fatherLastName: Optional[str] = None,
        motherFirstName: Optional[str] = None,
        motherLastName: Optional[str] = None,
        watchlist: bool = False,
        dateInclude: Optional[str] = None,
        dateSpread: Optional[int] = None,
        centuryTypo: bool = False,
        isLiving: bool = False,
        skipVariants: bool = False,
        lastNameMatch: Optional[str] = None,
        sort: Optional[str] = None,
        secondarySort: Optional[str] = None,
        limit: int = 10,
        start: int = 0,
        fields: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Search for person profiles by name, date, location, and relationship criteria.

        This action mirrors the functionality of the public
        `Special:SearchPerson <https://www.wikitree.com/wiki/Special:SearchPerson>`_
        page and supports flexible matching and filtering options. The results
        include partial or full person data depending on the requested fields.

        Parameters
        ----------
        FirstName : str, optional
            First name of the person to search for.
        LastName : str, optional
            Last name at birth or current last name.
        BirthDate : str, optional
            Birth date in YYYY-MM-DD format. Partial dates (e.g., YYYY-00-00) are allowed.
        DeathDate : str, optional
            Death date in YYYY-MM-DD format. Partial dates allowed.
        RealName : str, optional
            Preferred or “real” first name.
        LastNameCurrent : str, optional
            Current last name, if different from birth name.
        BirthLocation : str, optional
            Birthplace text string (city, region, or country).
        DeathLocation : str, optional
            Death location text string.
        Gender : {"Male", "Female"}, optional
            Restrict matches by gender.
        fatherFirstName : str, optional
            First name of the father.
        fatherLastName : str, optional
            Last name of the father.
        motherFirstName : str, optional
            First name of the mother.
        motherLastName : str, optional
            Last name of the mother.
        watchlist : bool, default=False
            Restrict results to profiles on the authenticated user’s Watchlist.
        dateInclude : {"both", "neither"}, optional
            Controls whether matches require date fields to be present.
        dateSpread : int, optional
            Range of acceptable year differences (1–20) for date-based matches.
        centuryTypo : bool, default=False
            If ``True``, include profiles with possible century typos in dates.
        isLiving : bool, default=False
            If ``True``, restrict to living person profiles.
        skipVariants : bool, default=False
            If ``True``, disable variant surname matching (exact surname only).
        lastNameMatch : {"all", "current", "birth", "strict"}, optional
            Type of surname match to perform.
        sort : {"first", "last", "birth", "death", "manager"}, optional
            Primary sort order of results.
        secondarySort : {"first", "last", "birth", "death", "manager"}, optional
            Secondary sort order.
        limit : int, default=10
            Maximum number of results to return (1–100).
        start : int, default=0
            Starting offset for paginated results.
        fields : str, optional
            Comma-separated list of profile fields to return for each match.  
            See :func:`fields_reference.list_fields` for available fields.
        **kwargs :
            Additional optional API parameters.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
              - ``status``: API status code (``0`` for success)
              - ``matches``: list of profiles matching the search, each with requested fields
              - ``total``: total number of matching profiles
              - ``start``: starting index of current batch
              - ``limit``: number of results returned

        Raises
        ------
        WikiTreeAPIError
            If the request fails or the server returns invalid JSON.

        Examples
        --------
        Find all people named Samuel Clemens with basic birth data:

        >>> wt.searchPerson(FirstName="Sam", LastName="Clemens",
        ...                 fields="Id,Name,FirstName,BirthDate")
        {
            "status": 0,
            "matches": [
                {"Id": 5185, "Name": "Clemens-1", "FirstName": "Samuel", "BirthDate": "1835-11-30"},
                {"Id": 32229307, "Name": "Clemens-2686", "FirstName": "Samuel", "BirthDate": "1853-00-00"}
            ],
            "total": 164,
            "start": 0,
            "limit": 10
        }
        """
        params = {
            "limit": limit,
            "start": start,
            "watchlist": int(watchlist),
            "centuryTypo": int(centuryTypo),
            "isLiving": int(isLiving),
            "skipVariants": int(skipVariants),
        }

        # Add optional parameters if provided
        optional_params = {
            "FirstName": FirstName,
            "LastName": LastName,
            "BirthDate": BirthDate,
            "DeathDate": DeathDate,
            "RealName": RealName,
            "LastNameCurrent": LastNameCurrent,
            "BirthLocation": BirthLocation,
            "DeathLocation": DeathLocation,
            "Gender": Gender,
            "fatherFirstName": fatherFirstName,
            "fatherLastName": fatherLastName,
            "motherFirstName": motherFirstName,
            "motherLastName": motherLastName,
            "dateInclude": dateInclude,
            "dateSpread": dateSpread,
            "lastNameMatch": lastNameMatch,
            "sort": sort,
            "secondarySort": secondarySort,
            "fields": fields,
        }

        for k, v in optional_params.items():
            if v is not None:
                params[k] = v

        params.update(kwargs)
        return self.request("searchPerson", **params)
