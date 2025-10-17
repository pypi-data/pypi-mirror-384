from __future__ import annotations

import io
import os
from typing import Any, Mapping, Optional, List, Dict

import requests

from .logging import get_logger


class CPZAIClient:
    """Client for accessing CPZ AI database (strategies and files)"""

    # Default platform REST URL (not configurable via env for end-users)
    # New base targets consolidated CPZ API (no /rest/v1 here); PostgREST paths are tried as fallback
    DEFAULT_API_URL = "https://api-ai.cpz-lab.com/cpz"

    def __init__(self, url: str, api_key: str, secret_key: str, user_id: str = None, is_admin: bool = False) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.secret_key = secret_key
        self.user_id = user_id
        self.is_admin = is_admin
        self.logger = get_logger()

    @staticmethod
    def from_env(environ: Optional[Mapping[str, str]] = None) -> "CPZAIClient":
        env = environ or os.environ
        # URL is fixed by SDK; do not require env variable
        url = CPZAIClient.DEFAULT_API_URL
        api_key = env.get("CPZ_AI_API_KEY", "")
        # Prefer new var name; keep backward compat with older deployments
        secret_key = env.get("CPZ_AI_API_SECRET", "") or env.get("CPZ_AI_SECRET_KEY", "")
        user_id = env.get("CPZ_AI_USER_ID", "")
        is_admin = env.get("CPZ_AI_IS_ADMIN", "false").lower() == "true"
        return CPZAIClient(url=url, api_key=api_key, secret_key=secret_key, user_id=user_id, is_admin=is_admin)

    @staticmethod
    def from_keys(api_key: str, secret_key: str, user_id: Optional[str] = None, is_admin: bool = False) -> "CPZAIClient":
        """Create client from keys only, using built-in default URL."""
        return CPZAIClient(url=CPZAIClient.DEFAULT_API_URL, api_key=api_key, secret_key=secret_key, user_id=user_id or "", is_admin=is_admin)

    def _headers(self) -> dict[str, str]:
        # Support both gateway styles: custom header keys and PostgREST defaults
        return {
            "X-CPZ-KEY": self.api_key,
            "X-CPZ-SECRET": self.secret_key,
            "apikey": self.secret_key,
            "Authorization": f"Bearer {self.secret_key}",
            # Default PostgREST schema headers (safe no-ops for non-PostgREST endpoints)
            "Accept-Profile": "public",
            "Content-Profile": "public",
            "Content-Type": "application/json",
        }

    def _timeout(self, default: int = 10) -> int:
        """Resolve request timeout from env with sane bounds.

        Honors CPZ_REQUEST_TIMEOUT_SECONDS if set; otherwise uses provided default.
        """
        try:
            value = int(os.getenv("CPZ_REQUEST_TIMEOUT_SECONDS", str(default)))
            # Clamp to [2, 60] seconds to avoid extremes
            return max(2, min(60, value))
        except Exception:
            return default

    def health(self) -> bool:
        """Check if the CPZ AI Platform is accessible"""
        try:
            # Try PostgREST style first
            resp = requests.get(f"{self.url}/", headers=self._headers(), timeout=self._timeout(10))
            return resp.status_code < 500
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_platform_health_error", error=str(exc))
            return False

    def get_strategies(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's strategies from strategies table"""
        try:
            params = {"limit": limit, "offset": offset}
            
            # Filter by user_id unless admin
            if not self.is_admin and self.user_id:
                params["user_id"] = f"eq.{self.user_id}"
            
            resp = requests.get(
                f"{self.url}/strategies",
                headers=self._headers(),
                params=params,
                timeout=self._timeout(10)
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                self.logger.error("cpz_ai_get_strategies_error", status=resp.status_code, response=resp.text)
                return []
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_get_strategies_exception", error=str(exc))
            return []

    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific strategy by ID"""
        try:
            resp = requests.get(
                f"{self.url}/strategies",
                headers=self._headers(),
                params={"id": f"eq.{strategy_id}"},
                timeout=self._timeout(10)
            )
            if resp.status_code == 200:
                strategies = resp.json()
                return strategies[0] if strategies else None
            else:
                self.logger.error("cpz_ai_get_strategy_error", status=resp.status_code, response=resp.text)
                return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_get_strategy_exception", error=str(exc))
            return None

    def create_strategy(self, strategy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new strategy"""
        try:
            # Automatically set user_id unless admin
            if not self.is_admin and self.user_id:
                strategy_data["user_id"] = self.user_id
            
            resp = requests.post(
                f"{self.url}/strategies",
                headers=self._headers(),
                json=strategy_data,
                timeout=self._timeout(10)
            )
            if resp.status_code == 201:
                return resp.json()[0] if resp.json() else None
            else:
                self.logger.error("cpz_ai_create_strategy_error", status=resp.status_code, response=resp.text)
                return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_create_strategy_exception", error=str(exc))
            return None

    def update_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing strategy"""
        try:
            resp = requests.patch(
                f"{self.url}/strategies",
                headers=self._headers(),
                params={"id": f"eq.{strategy_id}"},
                json=strategy_data,
                timeout=self._timeout(10)
            )
            if resp.status_code == 200:
                return resp.json()[0] if resp.json() else None
            else:
                self.logger.error("cpz_ai_update_strategy_error", status=resp.status_code, response=resp.text)
                return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_update_strategy_exception", error=str(exc))
            return None

    def delete_strategy(self, strategy_id: str) -> None:
        """Delete a strategy"""
        try:
            resp = requests.delete(
                f"{self.url}/strategies",
                headers=self._headers(),
                params={"id": f"eq.{strategy_id}"},
                timeout=self._timeout(10)
            )
            return resp.status_code == 200
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_delete_strategy_error", error=str(exc))
            return False

    def get_files(self, bucket_name: str = "default") -> List[Dict[str, Any]]:
        """Get files from a storage bucket"""
        try:
            # For user-specific access, use user-specific bucket or filter by prefix
            if not self.is_admin and self.user_id:
                # Use user-specific bucket name
                user_bucket = f"{bucket_name}-{self.user_id}"
                bucket_name = user_bucket
            
            resp = requests.get(
                f"{self.url}/storage/object/list/{bucket_name}",
                headers=self._headers(),
                timeout=self._timeout(10)
            )
            if resp.status_code == 200:
                files = resp.json()
                
                # Filter files by user_id unless admin
                if not self.is_admin and self.user_id and files:
                    # Filter files that belong to this user
                    user_files = []
                    for file in files:
                        # Check if file path contains user_id or if metadata indicates ownership
                        if (self.user_id in file.get('name', '') or 
                            file.get('metadata', {}).get('user_id') == self.user_id):
                            user_files.append(file)
                    return user_files
                
                return files
            else:
                self.logger.error("cpz_ai_get_files_error", status=resp.status_code, response=resp.text)
                return []
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_get_files_exception", error=str(exc))
            return []

    def get_file(self, bucket_name: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from storage"""
        try:
            resp = requests.get(
                f"{self.url}/storage/object/info/{bucket_name}/{file_path}",
                headers=self._headers(),
                timeout=self._timeout(10)
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                self.logger.error("cpz_ai_get_file_error", status=resp.status_code, response=resp.text)
                return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_get_file_exception", error=str(exc))
            return None

    def upload_file(self, bucket_name: str, file_path: str, file_content: bytes, content_type: str = "application/octet-stream") -> Optional[Dict[str, Any]]:
        """Upload a file to storage"""
        try:
            # For user-specific access, use user-specific bucket
            if not self.is_admin and self.user_id:
                user_bucket = f"{bucket_name}-{self.user_id}"
                bucket_name = user_bucket
                
                # Add user_id to file path for organization
                if not file_path.startswith(f"{self.user_id}/"):
                    file_path = f"{self.user_id}/{file_path}"
            
            headers = self._headers()
            headers["Content-Type"] = content_type
            
            resp = requests.post(
                f"{self.url}/storage/object/{bucket_name}/{file_path}",
                headers=headers,
                data=file_content,
                timeout=self._timeout(30)
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                self.logger.error("cpz_ai_upload_file_error", status=resp.status_code, response=resp.text)
                return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_upload_file_exception", error=str(exc))
            return None

    def upload_csv_file(self, bucket_name: str, file_path: str, csv_content: str, encoding: str = "utf-8") -> Optional[Dict[str, Any]]:
        """Upload a CSV file to storage"""
        try:
            csv_bytes = csv_content.encode(encoding)
            return self.upload_file(bucket_name, file_path, csv_bytes, "text/csv")
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_upload_csv_exception", error=str(exc))
            return None

    def upload_dataframe(self, bucket_name: str, file_path: str, df: Any, format: str = "csv", **kwargs) -> Optional[Dict[str, Any]]:
        """Upload a pandas DataFrame to storage"""
        try:
            if format.lower() == "csv":
                csv_content = df.to_csv(index=False, **kwargs)
                return self.upload_csv_file(bucket_name, file_path, csv_content)
            elif format.lower() == "json":
                json_content = df.to_json(orient="records", **kwargs)
                json_bytes = json_content.encode("utf-8")
                return self.upload_file(bucket_name, file_path, json_bytes, "application/json")
            elif format.lower() == "parquet":
                # Convert DataFrame to parquet bytes
                buffer = io.BytesIO()
                df.to_parquet(buffer, index=False, **kwargs)
                buffer.seek(0)
                return self.upload_file(bucket_name, file_path, buffer.getvalue(), "application/octet-stream")
            else:
                raise ValueError(f"Unsupported format: {format}. Use 'csv', 'json', or 'parquet'")
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_upload_dataframe_exception", error=str(exc))
            return None

    def download_file(self, bucket_name: str, file_path: str) -> Optional[bytes]:
        """Download a file from storage"""
        try:
            # For user-specific access, use user-specific bucket
            if not self.is_admin and self.user_id:
                user_bucket = f"{bucket_name}-{self.user_id}"
                bucket_name = user_bucket
                
                # Add user_id to file path if not already present
                if not file_path.startswith(f"{self.user_id}/"):
                    file_path = f"{self.user_id}/{file_path}"
            
            resp = requests.get(
                f"{self.url}/storage/object/{bucket_name}/{file_path}",
                headers=self._headers(),
                timeout=self._timeout(30)
            )
            if resp.status_code == 200:
                return resp.content
            else:
                self.logger.error("cpz_ai_download_file_error", status=resp.status_code, response=resp.text)
                return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_download_file_exception", error=str(exc))
            return None

    def download_csv_to_dataframe(self, bucket_name: str, file_path: str, encoding: str = "utf-8", **kwargs) -> Optional[Any]:
        """Download a CSV file and load it into a pandas DataFrame"""
        try:
            import pandas as pd
            
            file_content = self.download_file(bucket_name, file_path)
            if file_content:
                csv_content = file_content.decode(encoding)
                return pd.read_csv(io.StringIO(csv_content), **kwargs)
            return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_download_csv_exception", error=str(exc))
            return None

    def download_json_to_dataframe(self, bucket_name: str, file_path: str, **kwargs) -> Optional[Any]:
        """Download a JSON file and load it into a pandas DataFrame"""
        try:
            import pandas as pd
            
            file_content = self.download_file(bucket_name, file_path)
            if file_content:
                json_content = file_content.decode("utf-8")
                return pd.read_json(json_content, **kwargs)
            return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_download_json_exception", error=str(exc))
            return None

    def download_parquet_to_dataframe(self, bucket_name: str, file_path: str, **kwargs) -> Optional[Any]:
        """Download a Parquet file and load it into a pandas DataFrame"""
        try:
            import pandas as pd
            
            file_content = self.download_file(bucket_name, file_path)
            if file_content:
                buffer = io.BytesIO(file_content)
                return pd.read_parquet(buffer, **kwargs)
            return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_download_parquet_exception", error=str(exc))
            return None

    def list_files_in_bucket(self, bucket_name: str, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files in a storage bucket with optional prefix filtering"""
        try:
            # For user-specific access, use user-specific bucket
            if not self.is_admin and self.user_id:
                user_bucket = f"{bucket_name}-{self.user_id}"
                bucket_name = user_bucket
                
                # Add user_id to prefix for filtering
                if prefix and not prefix.startswith(f"{self.user_id}/"):
                    prefix = f"{self.user_id}/{prefix}"
                elif not prefix:
                    prefix = f"{self.user_id}/"
            
            params = {"limit": limit}
            if prefix:
                params["prefix"] = prefix
                
            resp = requests.get(
                f"{self.url}/storage/object/list/{bucket_name}",
                headers=self._headers(),
                params=params,
                timeout=self._timeout(10)
            )
            if resp.status_code == 200:
                files = resp.json()
                
                # Filter files by user_id unless admin
                if not self.is_admin and self.user_id and files:
                    # Filter files that belong to this user
                    user_files = []
                    for file in files:
                        # Check if file path contains user_id or if metadata indicates ownership
                        if (self.user_id in file.get('name', '') or 
                            file.get('metadata', {}).get('user_id') == self.user_id):
                            user_files.append(file)
                    return user_files
                
                return files
            else:
                self.logger.error("cpz_ai_list_files_error", status=resp.status_code, response=resp.text)
                return []
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_list_files_exception", error=str(exc))
            return []

    def create_bucket(self, bucket_name: str, public: bool = False) -> bool:
        """Create a new storage bucket"""
        try:
            # For user-specific access, create user-specific bucket
            if not self.is_admin and self.user_id:
                user_bucket = f"{bucket_name}-{self.user_id}"
                bucket_name = user_bucket
            
            bucket_data = {
                "name": bucket_name,
                "public": public
            }
            
            resp = requests.post(
                f"{self.url}/storage/bucket",
                headers=self._headers(),
                json=bucket_data,
                timeout=self._timeout(10)
            )
            return resp.status_code == 200
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_create_bucket_exception", error=str(exc))
            return False

    def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Delete a file from storage"""
        try:
            # For user-specific access, use user-specific bucket
            if not self.is_admin and self.user_id:
                user_bucket = f"{bucket_name}-{self.user_id}"
                bucket_name = user_bucket
                
                # Add user_id to file path if not already present
                if not file_path.startswith(f"{self.user_id}/"):
                    file_path = f"{self.user_id}/{file_path}"
            
            resp = requests.delete(
                f"{self.url}/storage/object/{bucket_name}/{file_path}",
                headers=self._headers(),
                timeout=self._timeout(10)
            )
            return resp.status_code == 200
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_delete_file_error", error=str(exc))
            return False

    def list_tables(self) -> list[str]:
        """List available tables in the CPZ AI Platform"""
        # Prefer consolidated /metadata endpoint with flexible shapes
        try:
            meta = requests.get(f"{self.url}/metadata", headers=self._headers(), timeout=self._timeout(10))
            if meta.status_code == 200:
                data = meta.json()
                tables: list[str] = []
                if isinstance(data, dict):
                    # Common shapes we support:
                    # 1) { "orders": {"columns": [...]}, "strategies": {...}, ... }
                    # 2) { "tables": ["orders", "strategies", ...] }
                    # 3) { "tables": [{"name": "orders"}, {"name": "strategies"}] }
                    # 4) { "columns": { "orders": [...], "strategies": [...] } }
                    if any(isinstance(v, dict) and "columns" in v for v in data.values()):
                        tables = [str(k) for k, v in data.items() if isinstance(v, dict) and ("columns" in v or "fields" in v)]
                    elif "tables" in data:
                        t = data.get("tables")
                        if isinstance(t, list):
                            if t and isinstance(t[0], str):
                                tables = [str(x) for x in t]
                            elif t and isinstance(t[0], dict):
                                tables = [str(x.get("name") or x.get("table") or x.get("id")) for x in t if (x.get("name") or x.get("table") or x.get("id"))]
                    elif "columns" in data and isinstance(data["columns"], dict):
                        tables = [str(k) for k in data["columns"].keys()]
                    else:
                        # As a last resort, if dict looks like {"columns": ..., "user_id": ...}, ignore and try fallback
                        tables = []
                if tables:
                    return sorted({t for t in tables if t})
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("cpz_ai_metadata_error", error=str(exc))
        # Fallback to PostgREST discovery
        try:
            resp = requests.get(f"{self.url}/", headers=self._headers(), timeout=self._timeout(10))
            if resp.status_code == 200 and isinstance(resp.json(), dict):
                # PostgREST root returns an object whose keys are allowed tables/views
                allowed = resp.json()
                return sorted([str(k) for k in allowed.keys()])
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("cpz_ai_list_tables_error", error=str(exc))
        return []

    def list_trading_credentials(self) -> list[Dict[str, Any]]:
        """Return rows strictly from trading_credentials_private."""
        # Gateway private endpoint
        try:
            resp = requests.get(
                f"{self.url}/trading_credentials_private",
                headers=self._headers(),
                timeout=self._timeout(10),
            )
            if resp.status_code == 200 and isinstance(resp.json(), list):
                return resp.json()
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("cpz_ai_list_trading_credentials_private_error", error=str(exc))
        # PostgREST private table
        try:
            resp = requests.get(
                f"{self.url}/rest/v1/trading_credentials_private",
                headers=self._headers(),
                params={"select": "*"},
                timeout=self._timeout(10),
            )
            if resp.status_code == 200 and isinstance(resp.json(), list):
                return resp.json()
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("cpz_ai_list_trading_credentials_private_pgrest_error", error=str(exc))
        return []

    # --- Orders ---
    def record_order(
        self,
        *,
        order_id: str,
        symbol: str,
        side: str,
        qty: float,
        type: str,
        time_in_force: str,
        broker: str,
        env: str,
        strategy_id: Optional[str] = None,
        status: Optional[str] = None,
        filled_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Persist an execution record into CPZ orders table.

        Writes to consolidated gateway first (POST /orders) and falls back to
        PostgREST path if needed.
        """
        # Discover actual columns to avoid schema mismatches (e.g., quantity vs qty)
        columns: set[str] = set()
        try:
            meta = requests.get(f"{self.url}/metadata", headers=self._headers(), timeout=8)
            if meta.ok and isinstance(meta.json(), dict):
                orders_meta = meta.json().get("orders") or {}
                cols = orders_meta.get("columns") or []
                if isinstance(cols, list):
                    columns = {str(c) for c in cols}
        except Exception:
            pass

        def include(name: str) -> bool:
            return not columns or name in columns

        payload: Dict[str, Any] = {}
        if order_id and include("order_id"):
            payload["order_id"] = order_id
        if include("symbol"):
            payload["symbol"] = symbol
        if include("side"):
            payload["side"] = side
        # quantity column variations
        if "quantity" in columns:
            payload["quantity"] = qty
        elif include("qty"):
            payload["qty"] = qty
        # order type variations
        if "order_type" in columns:
            payload["order_type"] = type
        elif include("type"):
            payload["type"] = type
        if include("time_in_force"):
            payload["time_in_force"] = time_in_force
        if include("broker"):
            payload["broker"] = broker
        # Do not persist env; account_id/broker is sufficient for routing
        if strategy_id and include("strategy_id"):
            payload["strategy_id"] = strategy_id
        if status and include("status"):
            payload["status"] = status
        if filled_at and include("filled_at"):
            payload["filled_at"] = filled_at

        headers = self._headers()
        try:
            resp = requests.post(f"{self.url}/orders", headers=headers, json=payload, timeout=self._timeout(10))
            if 200 <= resp.status_code < 300:
                try:
                    data = resp.json()
                except Exception:
                    data = None
                return data
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("cpz_ai_record_order_error", error=str(exc))

        # Fallback to PostgREST
        try:
            resp = requests.post(
                f"{self.url}/orders",
                headers=headers,
                json=payload,
                timeout=self._timeout(10),
            )
            if 200 <= resp.status_code < 300:
                try:
                    return resp.json()
                except Exception:
                    return None
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("cpz_ai_record_order_pgrest_error", error=str(exc))
        return None

    # Intent-first logging. Create a row before broker handoff; returns created row (must include id)
    def create_order_intent(
        self,
        *,
        symbol: str,
        side: str,
        qty: float,
        type: str,
        time_in_force: str,
        broker: str,
        env: str,
        strategy_id: str,
        status: str = "pending",
        account_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        # Discover columns
        columns: set[str] = set()
        try:
            meta = requests.get(f"{self.url}/metadata", headers=self._headers(), timeout=8)
            if meta.ok and isinstance(meta.json(), dict):
                orders_meta = meta.json().get("orders") or {}
                cols = orders_meta.get("columns") or []
                if isinstance(cols, list):
                    columns = {str(c) for c in cols}
        except Exception:
            pass

        def include(name: str) -> bool:
            return not columns or name in columns

        payload: Dict[str, Any] = {}
        if include("symbol"):
            payload["symbol"] = symbol
        if include("side"):
            payload["side"] = side
        if "quantity" in columns:
            payload["quantity"] = qty
        elif include("qty"):
            payload["qty"] = qty
        if "order_type" in columns:
            payload["order_type"] = type
        elif include("type"):
            payload["type"] = type
        if include("time_in_force"):
            payload["time_in_force"] = time_in_force
        if include("broker"):
            payload["broker"] = broker
        # Do not persist env into orders
        if include("strategy_id"):
            payload["strategy_id"] = strategy_id
        if include("status"):
            payload["status"] = status
        if account_id and include("account_id"):
            payload["account_id"] = account_id

        # Enrich from trading credentials: user_id/account_id/broker if present
        try:
            rows = self.list_trading_credentials()
            broker_l = (broker or "").lower()
            env_l = (env or "").lower()
            acct_l = (account_id or "").strip()
            match = None
            for r in rows:
                if str(r.get("broker", "")).lower() != broker_l:
                    continue
                env_val = str(r.get("env") or r.get("environment") or r.get("mode") or "").lower()
                is_paper = r.get("is_paper") or r.get("paper") or r.get("sandbox") or r.get("is_sandbox") or r.get("paper_trading")
                r_acct = str(r.get("account_id") or r.get("account") or "")
                if acct_l:
                    # Require matching account_id; env optional
                    if r_acct == acct_l and (not env_l or env_val == env_l or (env_l == "paper" and bool(is_paper))):
                        match = r
                        break
                    else:
                        continue
                # No account filter; match by env if provided
                if env_l and (env_val == env_l or (env_l == "paper" and bool(is_paper))):
                    match = r
                    break
                if not env_l:
                    match = r
                    break
            if match:
                uid = match.get("user_id") or match.get("owner_id")
                aid = match.get("account_id") or match.get("account")
                mbroker = match.get("broker") or match.get("provider") or match.get("platform")
                if uid and include("user_id"):
                    payload["user_id"] = uid
                # Prefer user_id; do not require owner_id. If only owner_id exists and table expects it, include it.
                if uid and include("owner_id") and "user_id" not in columns:
                    payload["owner_id"] = uid
                if aid and include("account_id"):
                    payload["account_id"] = aid
                if mbroker and include("broker"):
                    payload["broker"] = mbroker
        except Exception:
            pass

        headers = self._headers()
        # Gateway first with bounded retries for transient 5xx / BOOT_ERROR
        last_exc: Optional[Exception] = None
        try:
            for attempt in range(3):
                try:
                    r = requests.post(f"{self.url}/orders", headers=headers, json=payload, timeout=self._timeout(10))
                except Exception as req_exc:  # noqa: BLE001
                    last_exc = req_exc
                    # Backoff and retry
                    if attempt < 2:
                        import time as _t
                        _t.sleep(0.5 * (2 ** attempt))
                        continue
                    raise RuntimeError(f"orders insert failed (gateway error): {req_exc}")

                # Success path
                if 200 <= r.status_code < 300:
                    try:
                        data = r.json()
                        # Accept dict or list-of-dicts
                        if isinstance(data, dict) and data.get("id"):
                            return data
                        if isinstance(data, list) and data:
                            first = data[0]
                            if isinstance(first, dict) and first.get("id"):
                                return first
                        # Some gateways return empty body or no id; try to find the row we just inserted
                        params: Dict[str, str] = {"select": "*", "order": "created_at.desc", "limit": "1"}
                        for key in ("user_id", "account_id", "broker", "strategy_id", "symbol", "status"):
                            if key in payload and payload[key] is not None:
                                params[key] = f"eq.{payload[key]}"
                        rr = requests.get(f"{self.url}/orders", headers=headers, params=params, timeout=8)
                        if rr.ok:
                            found = rr.json()
                            if isinstance(found, list) and found:
                                row = found[0]
                                if isinstance(row, dict):
                                    return row
                        # Relax filters (drop broker/account_id) and retry
                        relaxed = {k: v for k, v in params.items() if k not in ("broker", "account_id")}
                        rr2 = requests.get(f"{self.url}/orders", headers=headers, params=relaxed, timeout=8)
                        if rr2.ok:
                            found = rr2.json()
                            if isinstance(found, list) and found:
                                row = found[0]
                                if isinstance(row, dict):
                                    return row
                    except Exception:
                        return None

                # Decide whether to retry on gateway errors
                body_text = ""
                try:
                    body_text = r.text
                except Exception:
                    body_text = ""
                transient = r.status_code >= 500 or ("BOOT_ERROR" in body_text)
                if transient and attempt < 2:
                    import time as _t
                    _t.sleep(0.5 * (2 ** attempt))
                    continue
                # Non-transient or final attempt -> raise to consider fallback
                raise RuntimeError(f"orders insert failed ({r.status_code}): {body_text}")
            # Should not reach here
            raise RuntimeError(f"orders insert failed (gateway error): {last_exc}")
        except Exception as gw_exc:  # noqa: BLE001
            # PostgREST fallback only if available; otherwise surface gateway error clearly
            def _pgrest_available() -> bool:
                try:
                    probe = requests.get(f"{self.url}/rest/v1/", headers=headers, timeout=3)
                    # PostgREST root usually returns 404 or JSON; consider available if not a 5xx and content-type json-ish
                    if probe.status_code >= 500:
                        return False
                    ctype = probe.headers.get("Content-Type", "")
                    return "json" in ctype.lower() or probe.status_code in (200, 404)
                except Exception:
                    return False

            if not _pgrest_available():
                raise RuntimeError(f"orders insert failed via gateway and PostgREST is unavailable | gateway_error={gw_exc}")

            try:
                r = requests.post(
                    f"{self.url}/rest/v1/orders",
                    headers=headers,
                    json=payload,
                    params={"select": "*"},
                    timeout=self._timeout(10),
                )
                if 200 <= r.status_code < 300:
                    data = r.json()
                    if isinstance(data, list) and data:
                        return data[0]
                raise RuntimeError(f"orders insert failed ({getattr(r,'status_code', 'err')}): {getattr(r,'text','')} | gateway_error={gw_exc}")
            except Exception as pg_exc:  # noqa: BLE001
                raise RuntimeError(str(pg_exc))

    def update_order_record(
        self,
        *,
        id: str,
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        filled_qty: Optional[float] = None,
        average_fill_price: Optional[float] = None,
        submitted_at: Optional[str] = None,
        filled_at: Optional[str] = None,
    ) -> bool:
        headers = self._headers()
        body: Dict[str, Any] = {}
        if order_id is not None:
            body["order_id"] = order_id
        if status is not None:
            body["status"] = status
        if filled_qty is not None:
            # Support both filled_qty and filled_quantity columns
            body["filled_qty"] = filled_qty
            body["filled_quantity"] = filled_qty
        if average_fill_price is not None:
            body["average_fill_price"] = average_fill_price
        if submitted_at is not None:
            body["submitted_at"] = submitted_at
        if filled_at is not None:
            body["filled_at"] = filled_at
        if not body:
            return True
        ok = False
        # Gateway attempt
        try:
            r = requests.patch(f"{self.url}/orders", headers=headers, params={"id": f"eq.{id}"}, json=body, timeout=self._timeout(10))
            ok = r.status_code in (200, 204)
        except Exception:
            ok = False
        if ok:
            return True
        # PostgREST fallback
        try:
            r = requests.patch(f"{self.url}/rest/v1/orders", headers=headers, params={"id": f"eq.{id}"}, json=body, timeout=self._timeout(10))
            return r.status_code in (200, 204)
        except Exception:
            return False

    def echo(self) -> dict[str, Any]:
        """Test connection to CPZ AI Platform"""
        try:
            resp = requests.get(f"{self.url}/", headers=self._headers(), timeout=self._timeout(10))
            return {"status": resp.status_code, "ok": resp.ok}
        except Exception as exc:  # noqa: BLE001
            return {"status": 0, "ok": False, "error": str(exc)}

    # --- Trading & Credentials ---
    def get_broker_credentials(self, broker: str = "alpaca", env: Optional[str] = None, account_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Fetch broker trading credentials from CPZ AI using the service key.

        Tries a few common table/field shapes to maximize compatibility without
        hard-coding a single schema. Returns a dict with keys
        {"api_key_id", "api_secret_key", "env"} if found, else None.
        """
        try:
            # Normalize inputs
            broker = (broker or "").strip().lower()
            env_norm = (env or "").strip().lower() or None
            account_norm = (account_id or "").strip()

            # Quick path: CPZ consolidated gateway without PostgREST query params
            # Example: GET {base}/trading_credentials_private returns an array of records
            try:
                rows = self.list_trading_credentials()
                if rows:
                    # If caller specified account_id, return the first row matching that account strictly
                    if account_norm:
                        for r in rows:
                            row_account = str(r.get("account_id") or r.get("account") or "")
                            if row_account == account_norm:
                                api_key_id = str(r.get("api_key_id") or r.get("api_key") or r.get("key_id") or r.get("key") or "")
                                api_secret_key = str(r.get("api_secret_key") or r.get("api_secret") or r.get("secret_key") or r.get("secret") or "")
                                env_val = str(r.get("env") or r.get("environment") or r.get("mode") or "").lower()
                                is_paper = r.get("is_paper") or r.get("paper") or r.get("sandbox") or r.get("is_sandbox") or r.get("paper_trading")
                                # Infer paper/live from account_id prefix if env columns missing
                                inferred_from_account = None
                                if not env_val and is_paper is None and row_account.upper().startswith("PA"):
                                    inferred_from_account = "paper"
                                resolved_env = env_norm or (env_val if env_val else (inferred_from_account or ("paper" if bool(is_paper) else "live")))
                                if api_key_id and api_secret_key:
                                    return {"api_key_id": api_key_id, "api_secret_key": api_secret_key, "env": resolved_env}

                    def normalized_broker_value(row: Dict[str, Any]) -> str:
                        # Consider many possible name fields
                        for k in [
                            "broker", "broker_name", "name", "provider", "platform",
                            "broker_display_name", "provider_display_name", "display_name", "title",
                        ]:
                            v = row.get(k)
                            if v:
                                return str(v).lower()
                        return ""

                    def pick(row: Dict[str, Any]) -> Optional[Dict[str, str]]:
                        b_val = normalized_broker_value(row)
                        env_val = str(row.get("env") or row.get("environment") or row.get("mode") or "").lower()
                        is_paper = row.get("is_paper") or row.get("paper") or row.get("sandbox") or row.get("is_sandbox") or row.get("paper_trading")
                        row_account = str(row.get("account_id") or row.get("account") or "")

                        # Match broker either exact or fuzzy substring (e.g., "alpaca" in "alpaca paper account")
                        broker_match = (b_val == broker) or (b_val and broker in b_val) or (b_val and b_val in broker)

                        # Account filter takes precedence when provided
                        account_match = True
                        if account_norm:
                            account_match = (row_account == account_norm)

                        env_match = True
                        if env_norm:
                            env_match = (env_val == env_norm) or (env_norm == "paper" and bool(is_paper))

                        if broker_match and account_match and env_match:
                            api_key_id = str(row.get("api_key_id") or row.get("api_key") or row.get("key_id") or row.get("key") or "")
                            api_secret_key = str(row.get("api_secret_key") or row.get("api_secret") or row.get("secret_key") or row.get("secret") or "")
                            if api_key_id and api_secret_key:
                                resolved_env = env_norm or env_val or ("paper" if bool(is_paper) else "live")
                                return {"api_key_id": api_key_id, "api_secret_key": api_secret_key, "env": resolved_env}
                        return None
                    # Prefer exact env match if provided; otherwise first match
                    if account_norm or env_norm:
                        matched = None
                        for r in rows:
                            creds = pick(r)
                            if creds:
                                matched = creds
                                break
                        if matched:
                            return matched
                        # Fallback: take first row for this broker regardless of env/account
                        for r in rows:
                            b_val = (str(r.get("broker") or r.get("broker_name") or r.get("name") or r.get("provider") or r.get("platform") or "")).lower()
                            if b_val == broker or broker in b_val or b_val in broker:
                                api_key_id = str(r.get("api_key_id") or r.get("api_key") or r.get("key_id") or r.get("key") or "")
                                api_secret_key = str(r.get("api_secret_key") or r.get("api_secret") or r.get("secret_key") or r.get("secret") or "")
                                if api_key_id and api_secret_key:
                                    env_val = str(r.get("env") or r.get("environment") or r.get("mode") or "paper").lower()
                                    return {"api_key_id": api_key_id, "api_secret_key": api_secret_key, "env": env_val}
                    else:
                        for r in rows:
                            b_val = (str(r.get("broker") or r.get("broker_name") or r.get("name") or r.get("provider") or r.get("platform") or "")).lower()
                            if b_val == broker or broker in b_val or b_val in broker:
                                api_key_id = str(r.get("api_key_id") or r.get("api_key") or r.get("key_id") or r.get("key") or "")
                                api_secret_key = str(r.get("api_secret_key") or r.get("api_secret") or r.get("secret_key") or r.get("secret") or "")
                                if api_key_id and api_secret_key:
                                    env_val = str(r.get("env") or r.get("environment") or r.get("mode") or "paper").lower()
                                    return {"api_key_id": api_key_id, "api_secret_key": api_secret_key, "env": env_val}
            except Exception as exc_simple:  # noqa: BLE001
                # Fall through to PostgREST path
                self.logger.warning("cpz_ai_simple_credentials_path_error", error=str(exc_simple))

            # Candidate tables and param shapes to try in order (PostgREST)
            candidate_tables = [
                # Use only the private table; drop legacy/public names
                "trading_credentials_private",
            ]
            # Restrict to canonical columns used by trading_credentials_private
            candidate_broker_param_keys = ["broker"]
            candidate_broker_display_keys = []
            # string env fields, e.g., env=paper|live
            candidate_env_param_keys = ["env", "environment", "mode", "account_type"]
            # boolean env fields, e.g., is_paper=true|false
            candidate_env_bool_keys = ["is_paper", "paper", "sandbox", "is_sandbox", "paper_trading"]
            # Account identifier column name can vary; support both
            candidate_account_id_keys = ["account_id", "account"]

            def _extract_creds(row: Dict[str, Any]) -> Optional[Dict[str, str]]:
                # Prefer canonical columns first (api_key, api_secret, environment)
                key_id_fields = ["api_key", "api_key_id", "key_id", "key"]
                secret_fields = ["api_secret", "api_secret_key", "secret_key", "secret"]
                env_fields = ["environment", "env", "mode"]

                api_key_id: Optional[str] = None
                api_secret_key: Optional[str] = None
                env_value: Optional[str] = None

                for k in key_id_fields:
                    if k in row and row[k]:
                        api_key_id = str(row[k])
                        break
                for k in secret_fields:
                    if k in row and row[k]:
                        api_secret_key = str(row[k])
                        break
                for k in env_fields:
                    if k in row and row[k]:
                        env_value = str(row[k])
                        break

                if api_key_id and api_secret_key:
                    return {
                        "api_key_id": api_key_id,
                        "api_secret_key": api_secret_key,
                        "env": (env_norm or (env_value or "paper")).lower(),
                    }
                return None

            headers = self._headers()

            # Fast path: if caller provided account_id, try account-only lookups first
            if account_norm:
                for table in candidate_tables:
                    for akey in candidate_account_id_keys:
                        params_account_only: Dict[str, str] = {"select": "*", akey: f"eq.{account_norm}"}
                        # Try with env string if provided
                        if env_norm:
                            for ekey in candidate_env_param_keys:
                                params_env = dict(params_account_only)
                                params_env[ekey] = f"eq.{env_norm}"
                                resp = requests.get(
                                    f"{self.url}/rest/v1/{table}", headers=headers, params=params_env, timeout=self._timeout(10)
                                )
                                if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                                    creds = _extract_creds(resp.json()[0])
                                    if creds:
                                        return creds
                            # Try with env boolean if provided
                            for ekey in candidate_env_bool_keys:
                                params_env = dict(params_account_only)
                                params_env[ekey] = "eq.true" if env_norm == "paper" else "eq.false"
                                resp = requests.get(
                                    f"{self.url}/rest/v1/{table}", headers=headers, params=params_env, timeout=self._timeout(10)
                                )
                                if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                                    creds = _extract_creds(resp.json()[0])
                                    if creds:
                                        return creds
                        # No env filter
                        resp = requests.get(
                            f"{self.url}/rest/v1/{table}", headers=headers, params=params_account_only, timeout=self._timeout(10)
                        )
                        if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                            creds = _extract_creds(resp.json()[0])
                            if creds:
                                return creds

            for table in candidate_tables:
                # Try several param shapes per table
                for bkey in candidate_broker_param_keys:
                    params: Dict[str, str] = {"select": "*"}
                    params[bkey] = f"eq.{broker}"
                    # Try account if provided
                    if account_norm:
                        for akey in candidate_account_id_keys:
                            params_account = dict(params)
                            params_account[akey] = f"eq.{account_norm}"
                            # With env
                            if env_norm:
                                for ekey in candidate_env_param_keys:
                                    params_env = dict(params_account)
                                    params_env[ekey] = f"eq.{env_norm}"
                                    resp = requests.get(
                                        f"{self.url}/rest/v1/{table}", headers=headers, params=params_env, timeout=10
                                    )
                                    if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                                        creds = _extract_creds(resp.json()[0])
                                        if creds:
                                            return creds
                                for ekey in candidate_env_bool_keys:
                                    params_env = dict(params_account)
                                    params_env[ekey] = "eq.true" if env_norm == "paper" else "eq.false"
                                    resp = requests.get(
                                        f"{self.url}/rest/v1/{table}", headers=headers, params=params_env, timeout=10
                                    )
                                    if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                                        creds = _extract_creds(resp.json()[0])
                                        if creds:
                                            return creds
                            # Without env
                            resp = requests.get(
                                f"{self.url}/rest/v1/{table}", headers=headers, params=params_account, timeout=10
                            )
                            if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                                creds = _extract_creds(resp.json()[0])
                                if creds:
                                    return creds

                    # Try with and without env filter
                    env_keys_to_try = candidate_env_param_keys if env_norm else []
                    env_bool_keys_to_try = candidate_env_bool_keys if env_norm else []

                    # First, try with env if provided
                    for ekey in env_keys_to_try:
                        params_env = dict(params)
                        params_env[ekey] = f"eq.{env_norm}"
                        resp = requests.get(
                            f"{self.url}/rest/v1/{table}", headers=headers, params=params_env, timeout=10
                        )
                        if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                            creds = _extract_creds(resp.json()[0])
                            if creds:
                                return creds

                    # Try boolean env fields (paper/live)
                    for ekey in env_bool_keys_to_try:
                        params_env = dict(params)
                        params_env[ekey] = "eq.true" if env_norm == "paper" else "eq.false"
                        resp = requests.get(
                            f"{self.url}/rest/v1/{table}", headers=headers, params=params_env, timeout=10
                        )
                        if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                            creds = _extract_creds(resp.json()[0])
                            if creds:
                                return creds

                    # Then, try without env (let server-side default apply)
                    resp = requests.get(
                        f"{self.url}/rest/v1/{table}", headers=headers, params=params, timeout=10
                    )
                    if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                        creds = _extract_creds(resp.json()[0])
                        if creds:
                            return creds

                # Fallback: try display-name fuzzy match (ilike)
                for dkey in candidate_broker_display_keys:
                    params: Dict[str, str] = {"select": "*", dkey: f"ilike.*{broker}*"}
                    # with env string field
                    if env_norm:
                        for ekey in ["env", "environment", "mode", "account_type"]:
                            params_env = dict(params)
                            params_env[ekey] = f"eq.{env_norm}"
                            resp = requests.get(
                                f"{self.url}/rest/v1/{table}", headers=headers, params=params_env, timeout=10
                            )
                            if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                                creds = _extract_creds(resp.json()[0])
                                if creds:
                                    return creds
                        # with env boolean field
                        for ekey in ["is_paper", "paper", "sandbox", "is_sandbox", "paper_trading"]:
                            params_env = dict(params)
                            params_env[ekey] = "eq.true" if env_norm == "paper" else "eq.false"
                            resp = requests.get(
                                f"{self.url}/rest/v1/{table}", headers=headers, params=params_env, timeout=10
                            )
                            if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                                creds = _extract_creds(resp.json()[0])
                                if creds:
                                    return creds
                    # no env filter
                    resp = requests.get(
                        f"{self.url}/rest/v1/{table}", headers=headers, params=params, timeout=10
                    )
                    if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                        creds = _extract_creds(resp.json()[0])
                        if creds:
                            return creds

            # Not found
            return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("cpz_ai_get_broker_credentials_error", error=str(exc))
            return None


# Legacy alias for backward compatibility (will be removed in future versions)
# Use CPZAIClient instead
