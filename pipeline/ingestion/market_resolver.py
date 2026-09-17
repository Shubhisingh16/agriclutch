"""
Authoritative Market Registry and Identity Resolver for AgriClutch.
Enforces deterministic market resolution without ad-hoc string hacks or invented IDs.
Preserves raw source_market_id while mapping to canonical APMC entities.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AuthoritativeMarketEntry:
    """Master APMC market definition derived from official Agmarknet / DCA directories."""

    market_id: str
    apmc_code: int
    name: str
    state: str
    district: str
    latitude: float
    longitude: float
    is_terminal_market: bool = False
    dca_centre_id: Optional[int] = None


class MarketResolver:
    """
    Authoritative Market Identity Resolver.
    Maintains a deterministic master registry of APMC mandis and resolves
    source market strings or APMC codes into canonical AgriClutch market IDs.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, AuthoritativeMarketEntry] = {}
        self._apmc_to_id: Dict[int, str] = {}
        self._alias_to_id: Dict[str, str] = {}
        self._initialize_core_registry()

    def _initialize_core_registry(self) -> None:
        """Seed the core cluster of APMC mandis (Chandigarh Agricultural Cluster)."""
        core_mandis = [
            AuthoritativeMarketEntry(
                market_id="mandi_ch_49",
                apmc_code=49,
                name="Chandigarh",
                state="Chandigarh",
                district="Chandigarh",
                latitude=30.7333,
                longitude=76.7794,
                is_terminal_market=True,
                dca_centre_id=14,
            ),
            AuthoritativeMarketEntry(
                market_id="mandi_hr_660",
                apmc_code=660,
                name="Panchkula",
                state="Haryana",
                district="Panchkula",
                latitude=30.6942,
                longitude=76.8606,
                is_terminal_market=False,
            ),
            AuthoritativeMarketEntry(
                market_id="mandi_hr_kalka",
                apmc_code=661,
                name="Kalka",
                state="Haryana",
                district="Panchkula",
                latitude=30.8333,
                longitude=76.9333,
                is_terminal_market=False,
            ),
            AuthoritativeMarketEntry(
                market_id="mandi_pb_patiala",
                apmc_code=312,
                name="Patiala",
                state="Punjab",
                district="Patiala",
                latitude=30.3398,
                longitude=76.3869,
                is_terminal_market=False,
            ),
            AuthoritativeMarketEntry(
                market_id="mandi_dl_164",
                apmc_code=164,
                name="Azadpur",
                state="Delhi",
                district="North Delhi",
                latitude=28.7166,
                longitude=77.1706,
                is_terminal_market=True,
                dca_centre_id=1,
            ),
        ]

        for m in core_mandis:
            self.register_market(m)

        # Register standard known aliases from official Agmarknet scraping sources
        self.register_alias("Chandigarh(Grain)", "mandi_ch_49")
        self.register_alias("Chandigarh (Grain)", "mandi_ch_49")
        self.register_alias("Chandigarh(Fruit & Veg)", "mandi_ch_49")
        self.register_alias("Azadpur(Delhi)", "mandi_dl_164")
        self.register_alias("Panchkula(F&V)", "mandi_hr_660")

    def register_market(self, entry: AuthoritativeMarketEntry) -> None:
        """Register an authoritative market entry."""
        self._registry[entry.market_id] = entry
        self._apmc_to_id[entry.apmc_code] = entry.market_id
        # Standardize name alias
        normalized_name = self._normalize_key(entry.name)
        self._alias_to_id[normalized_name] = entry.market_id

    def register_alias(self, alias: str, canonical_market_id: str) -> None:
        """Register an external naming alias for a known market."""
        if canonical_market_id not in self._registry:
            raise KeyError(f"Cannot map alias to unknown market_id: {canonical_market_id}")
        self._alias_to_id[self._normalize_key(alias)] = canonical_market_id

    @staticmethod
    def _normalize_key(text: str) -> str:
        """Normalize string for dictionary key comparison."""
        return text.strip().lower().replace(" ", "").replace("_", "").replace("-", "")

    def resolve_market(
        self,
        source_market_str: Optional[str] = None,
        apmc_code: Optional[int] = None,
    ) -> Optional[AuthoritativeMarketEntry]:
        """
        Resolve an external market identifier to an authoritative market entry.
        Returns None if the market cannot be authoritatively resolved (never invents an ID).
        """
        if apmc_code is not None and apmc_code in self._apmc_to_id:
            market_id = self._apmc_to_id[apmc_code]
            return self._registry.get(market_id)

        if source_market_str:
            # First check direct market_id match
            if source_market_str in self._registry:
                return self._registry[source_market_str]

            # Check alias table
            key = self._normalize_key(source_market_str)
            if key in self._alias_to_id:
                market_id = self._alias_to_id[key]
                return self._registry.get(market_id)

        return None

    def get_canonical_id(
        self,
        source_market_str: Optional[str] = None,
        apmc_code: Optional[int] = None,
    ) -> Optional[str]:
        """Return the canonical market ID or None if unresolvable."""
        entry = self.resolve_market(source_market_str=source_market_str, apmc_code=apmc_code)
        return entry.market_id if entry else None

    def list_known_markets(self) -> List[AuthoritativeMarketEntry]:
        """List all markets currently registered in the authoritative master."""
        return list(self._registry.values())


# Global default market resolver instance
default_market_resolver = MarketResolver()
