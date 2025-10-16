from __future__ import annotations

from typing import Any, Dict, Optional, Iterable

from .http_client import HTTPClient


class LazyResource:
    def __init__(self) -> None:
        self._data_loaded = False

    def _mark_loaded(self) -> None:
        self._data_loaded = True


class Machine(LazyResource):
    def __init__(self, http: HTTPClient, machine_id: str) -> None:
        super().__init__()
        self._http = http
        self.id = machine_id
        self._data: Dict[str, Any] = {}
        self._qubit_map: Optional[QubitMap] = None
        self._coupler_map: Optional[CouplerMap] = None

    # --------- fetching helpers ---------
    def _endpoint(self) -> str:
        return self._http._url(f"machines/machine_state/{self.id}/")

    def _fetch(self) -> Dict[str, Any]:
        resp = self._http.request("GET", self._endpoint())
        data = self._http.handle(resp)
        if not isinstance(data, dict):
            raise ValueError("Unexpected machine response")
        self._data = data
        self._mark_loaded()
        return data

    def _ensure_loaded(self) -> None:
        if not self._data_loaded:
            self._fetch()

    # --------- minimal PATCH ---------
    def _patch(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._http.request("PATCH", self._endpoint(), json=fields)
        data = self._http.handle(resp)
        if isinstance(data, dict):
            # The machine endpoint returns full representation; store it
            self._data = data
            self._mark_loaded()
        return data

    # --------- properties ---------
    @property
    def title(self) -> str:
        self._ensure_loaded()
        return self._data.get("title")

    @title.setter
    def title(self, value: str) -> None:
        self._patch({"title": value})

    # --------- collections ---------
    @property
    def qubits(self) -> "QubitMap":
        if self._qubit_map is None:
            self._qubit_map = QubitMap(machine=self, http=self._http)
        return self._qubit_map

    @property
    def couplers(self) -> "CouplerMap":
        if self._coupler_map is None:
            self._coupler_map = CouplerMap(machine=self, http=self._http)
        return self._coupler_map

    # --------- machine_config access ---------
    def _get_machine_config(self) -> Dict[str, Any]:
        # Prefer cached data if available; otherwise fetch
        if not self._data_loaded:
            self._fetch()
        mc = self._data.get("machine_config") if isinstance(self._data, dict) else None
        if not isinstance(mc, dict):
            raise ValueError("Unexpected response: no machine_config present")
        return mc


class Qubit(LazyResource):
    # API fields for PATCH/GET
    _fields = {
        "number",
        "fmax",
        "fmin",
        "anharmonicity_max",
        "flux_bias",
        "num_lvl",
        "driving_freq",
        "detuning",
        # nested time_scales handled separately
    }

    def __init__(self, http: HTTPClient, machine: Machine, qubit_id: int, number: int) -> None:
        super().__init__()
        self._http = http
        self._machine = machine
        self.id = qubit_id
        self.number = number
        self._data: Dict[str, Any] = {"id": qubit_id, "number": number}
        self._time_scales: Optional[TimeScales] = None

    def _endpoint(self) -> str:
        return self._http._url(f"machines/qubits/{int(self.id)}/")

    def _fetch(self) -> Dict[str, Any]:
        resp = self._http.request("GET", self._endpoint())
        data = self._http.handle(resp)
        if not isinstance(data, dict):
            raise ValueError("Unexpected qubit response")
        self._data = data
        self._mark_loaded()
        return data

    def _ensure_loaded(self) -> None:
        if not self._data_loaded:
            self._fetch()

    def _patch(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._http.request("PATCH", self._endpoint(), json=fields)
        data = self._http.handle(resp)
        if isinstance(data, dict):
            self._data.update(data)
            self._mark_loaded()
        return data

    # --------- dynamic field access ---------
    def __getattr__(self, name: str) -> Any:
        if name in self._fields:
            self._ensure_loaded()
            return self._data.get(name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_http", "_machine", "id", "number", "_data", "_time_scales", "_data_loaded"}:
            object.__setattr__(self, name, value)
            return
        if name in self._fields:
            self._patch({name: value})
            return
        if name == "time_scales":
            if not isinstance(value, dict):
                raise TypeError("time_scales must be a dict when set directly")
            self._patch({"time_scales": value})
            return
        object.__setattr__(self, name, value)

    @property
    def time_scales(self) -> "TimeScales":
        if self._time_scales is None:
            # Create a proxy that updates qubit via nested PATCH
            self._time_scales = TimeScales(parent_qubit=self)
        return self._time_scales


class Coupler(LazyResource):
    _fields = {
        "number",
        "fmin",
        "fmax",
        "anharmonicity_max",
        "flux_bias",
        "num_lvl",
        "g12_zero_flux",
        "g1c_zero_flux",
        "g2c_zero_flux",
        "cz_dc_total_simulated",
        "cz_dc_total_expected",
        "cz_dc_incoherent_simulated",
        "cz_dc_incoherent_expected",
        "cz_dc_coherent_simulated",
        "cz_dc_coherent_expected",
        "iswap_dc_total_simulated",
        "iswap_dc_total_expected",
        "iswap_dc_incoherent_simulated",
        "iswap_dc_incoherent_expected",
        "iswap_dc_coherent_simulated",
        "iswap_dc_coherent_expected",
    }

    def __init__(self, http: HTTPClient, machine: Machine, coupler_id: int, number: int) -> None:
        super().__init__()
        self._http = http
        self._machine = machine
        self.id = coupler_id
        self.number = number
        self._data: Dict[str, Any] = {"id": coupler_id, "number": number}

    def _endpoint(self) -> str:
        return self._http._url(f"machines/couplers/{int(self.id)}/")

    def _fetch(self) -> Dict[str, Any]:
        resp = self._http.request("GET", self._endpoint())
        data = self._http.handle(resp)
        if not isinstance(data, dict):
            raise ValueError("Unexpected coupler response")
        self._data = data
        self._mark_loaded()
        return data

    def _ensure_loaded(self) -> None:
        if not self._data_loaded:
            self._fetch()

    def _patch(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._http.request("PATCH", self._endpoint(), json=fields)
        data = self._http.handle(resp)
        if isinstance(data, dict):
            self._data.update(data)
            self._mark_loaded()
        return data

    def __getattr__(self, name: str) -> Any:
        if name in self._fields:
            self._ensure_loaded()
            return self._data.get(name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_http", "_machine", "id", "number", "_data", "_data_loaded"}:
            object.__setattr__(self, name, value)
            return
        if name in self._fields:
            self._patch({name: value})
            return
        object.__setattr__(self, name, value)


class TimeScales:
    # Proxy object that updates parent qubit's nested time_scales via PATCH
    _fields = {"t1", "tphi", "tphi_1f", "t2star"}

    def __init__(self, parent_qubit: Qubit) -> None:
        self._parent_qubit = parent_qubit

    def __getattr__(self, name: str) -> Any:
        if name in self._fields:
            # pull from parent qubit data
            self._parent_qubit._ensure_loaded()
            ts = self._parent_qubit._data.get("time_scales") or {}
            return ts.get(name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_parent_qubit"}:
            object.__setattr__(self, name, value)
            return
        if name in self._fields:
            # Merge with existing values to satisfy backend nested validation
            self._parent_qubit._ensure_loaded()
            current = dict(self._parent_qubit._data.get("time_scales") or {})
            if not current and name in {"t1", "tphi", "tphi_1f"}:
                # Cannot create new TimeScales with a single required field; require all
                raise ValueError(
                    "time_scales does not exist yet; set all required fields at once via qubit.time_scales = {t1, tphi, tphi_1f, t2star?}"
                )
            current[name] = value
            self._parent_qubit._patch({"time_scales": current})
            return
        object.__setattr__(self, name, value)


class QubitMap:
    def __init__(self, machine: Machine, http: HTTPClient) -> None:
        self._machine = machine
        self._http = http
        self._number_to_id: Dict[int, int] = {}

    def _refresh_index(self) -> None:
        mc = self._machine._get_machine_config()
        qubits_dict = mc.get("qubits", {}) or {}
        mapping: Dict[int, int] = {}
        for number_str, value in qubits_dict.items():
            try:
                number = int(number_str)
            except Exception:
                continue
            if isinstance(value, dict) and "id" in value:
                mapping[number] = int(value["id"])
        self._number_to_id = mapping

    def __getitem__(self, number: int) -> Qubit:
        if not self._number_to_id:
            self._refresh_index()
        qubit_id = self._number_to_id.get(int(number))
        if qubit_id is None:
            # try refresh once more
            self._refresh_index()
            qubit_id = self._number_to_id.get(int(number))
        if qubit_id is None:
            raise KeyError(f"Qubit number {number} not found")
        return Qubit(http=self._http, machine=self._machine, qubit_id=qubit_id, number=int(number))

    def numbers(self) -> Iterable[int]:
        if not self._number_to_id:
            self._refresh_index()
        return list(self._number_to_id.keys())


class CouplerMap:
    def __init__(self, machine: Machine, http: HTTPClient) -> None:
        self._machine = machine
        self._http = http
        self._number_to_id: Dict[int, int] = {}

    def _refresh_index(self) -> None:
        mc = self._machine._get_machine_config()
        couplers_dict = mc.get("couplers", {}) or {}
        mapping: Dict[int, int] = {}
        for number_str, value in couplers_dict.items():
            try:
                number = int(number_str)
            except Exception:
                continue
            if isinstance(value, dict) and "id" in value:
                mapping[number] = int(value["id"])
        self._number_to_id = mapping

    def __getitem__(self, number: int) -> Coupler:
        if not self._number_to_id:
            self._refresh_index()
        coupler_id = self._number_to_id.get(int(number))
        if coupler_id is None:
            self._refresh_index()
            coupler_id = self._number_to_id.get(int(number))
        if coupler_id is None:
            raise KeyError(f"Coupler number {number} not found")
        return Coupler(http=self._http, machine=self._machine, coupler_id=coupler_id, number=int(number))

    def numbers(self) -> Iterable[int]:
        if not self._number_to_id:
            self._refresh_index()
        return list(self._number_to_id.keys())


