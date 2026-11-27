"""FastAPI application: upload / analyze / status / report."""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

from epitoperank import __version__
from epitoperank.analysis import extra_figures, visualization
from epitoperank.config import ensure_runtime_dirs, load_prepared_settings
from epitoperank.interface.web_ui import render as render_web_ui
from epitoperank.pipeline import list_projects, project_status, run_analysis
from epitoperank.observability import (
    configure_logging,
    new_request_id,
    reset_request_id,
    set_request_id,
)

#: 版本号以包内 __version__ 为唯一来源，避免与 Release tag 漂移
API_VERSION = __version__
logger = logging.getLogger(__name__)

#: Remembered CDS column mappings, stored next to the table it describes.
CDS_MAPPING_FILE = ".cds_mapping.json"

# Dark ocean tile with the teal helix + purple AI node, matching the app icon.
# Served as a real endpoint because browsers probe /favicon.ico unconditionally
# and a 404 there shows up as a console error.
_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<defs>'
    '<linearGradient id="p" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#0e3240"/><stop offset="1" stop-color="#04101a"/>'
    "</linearGradient>"
    '<linearGradient id="s" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#c8fff6"/><stop offset="1" stop-color="#2dd4bf"/>'
    "</linearGradient>"
    "</defs>"
    '<rect width="32" height="32" rx="7" fill="url(#p)"/>'
    '<path d="M10.50 5.25L10.61 5.70L10.94 6.15L11.47 6.59L12.18 7.04L13.05 7.49L14.04 7.94'
    "L15.10 8.39L16.21 8.83L17.30 9.28L18.34 9.73L19.29 10.18L20.10 10.62L20.75 11.07L21.21 11.52"
    "L21.46 11.97L21.48 12.42L21.29 12.86L20.89 13.31L20.28 13.76L19.51 14.21L18.59 14.66L17.57 15.10"
    "L16.49 15.55L15.38 16.00L14.31 16.45L13.29 16.90L12.39 17.34L11.64 17.79L11.06 18.24L10.67 18.69"
    "L10.51 19.14L10.56 19.58L10.83 20.03L11.32 20.48L11.99 20.93L12.82 21.38L13.78 21.82L14.83 22.27"
    "L15.92 22.72L17.02 23.17L18.08 23.61L19.06 24.06L19.91 24.51L20.60 24.96L21.11 25.41L21.41 25.85"
    'L21.50 26.30L21.36 26.75" fill="none" stroke="#11837d" stroke-width="2.6" stroke-linecap="round"/>'
    '<path d="M21.50 5.25L21.39 5.70L21.06 6.15L20.53 6.59L19.82 7.04L18.95 7.49L17.96 7.94'
    "L16.90 8.39L15.79 8.83L14.70 9.28L13.66 9.73L12.71 10.18L11.90 10.62L11.25 11.07L10.79 11.52"
    "L10.54 11.97L10.52 12.42L10.71 12.86L11.11 13.31L11.72 13.76L12.49 14.21L13.41 14.66L14.43 15.10"
    "L15.51 15.55L16.62 16.00L17.69 16.45L18.71 16.90L19.61 17.34L20.36 17.79L20.94 18.24L21.33 18.69"
    "L21.49 19.14L21.44 19.58L21.17 20.03L20.68 20.48L20.01 20.93L19.18 21.38L18.22 21.82L17.17 22.27"
    "L16.08 22.72L14.98 23.17L13.92 23.61L12.94 24.06L12.09 24.51L11.40 24.96L10.89 25.41L10.59 25.85"
    'L10.50 26.30L10.64 26.75" fill="none" stroke="url(#s)" stroke-width="2.6" stroke-linecap="round"/>'
    '<circle cx="16" cy="15.75" r="2.6" fill="none" stroke="#c4b5fd" stroke-opacity=".7" stroke-width=".8"/>'
    '<circle cx="16" cy="15.75" r="1.7" fill="#a855f7"/>'
    '<circle cx="15.5" cy="15.25" r=".55" fill="#fff"/>'
    "</svg>"
)


# 中文备注：Web 接口：辅助处理覆盖项（参数：settings、thresholds）
def _with_overrides(settings: Any, thresholds: Any) -> Any:
    """Return settings with optional per-request analysis thresholds applied.

    The UI exposes FDR / |delta PSI| / min reads / min samples / top-N as
    "advanced parameters"; anything not supplied keeps the configured value.
    """
    if not isinstance(thresholds, dict) or not thresholds:
        return settings
    import dataclasses

    analysis = settings.analysis
    mapping = {
        "fdr": "fdr_threshold",
        "fdr_threshold": "fdr_threshold",
        "delta_psi": "delta_psi_threshold",
        "delta_psi_threshold": "delta_psi_threshold",
        "min_support_reads": "min_support_reads",
        "min_valid_samples": "min_valid_samples",
        "top_candidates": "top_candidates",
        "enrichment_alpha": "enrichment_alpha",
    }
    changes: dict[str, Any] = {}
    casters = {
        "fdr_threshold": float,
        "delta_psi_threshold": float,
        "min_support_reads": int,
        "min_valid_samples": int,
        "top_candidates": int,
        "enrichment_alpha": float,
    }
    for key, value in thresholds.items():
        field = mapping.get(str(key))
        if field is None or value in (None, ""):
            continue
        try:
            changes[field] = casters[field](value)  # type: ignore[operator]
        except (TypeError, ValueError):
            continue
    if not changes:
        return settings
    new_analysis = dataclasses.replace(analysis, **changes)
    return dataclasses.replace(settings, analysis=new_analysis)


def _export_project_bundle(
    settings: Any,
    project_id: str,
    project_name: str,
    *,
    input_dir: str | None = None,
) -> str:
    """Copy a finished project's deliverables into its own browsable folder.

    Users should not have to dig through ``%LOCALAPPDATA%`` to find a report, so
    every run also publishes ``results/<项目名>_<ID>/``. Failure here must never
    fail the analysis itself: the run's own output directory is still valid.
    """
    from epitoperank.config import PROJECT_ROOT
    from epitoperank.memory.project_memory import ProjectMemory
    from epitoperank.report.antigens import append_html, append_pdf, load_sections
    from epitoperank.results_export import default_results_root, export_bundle

    project_dir = settings.paths.runtime_root / "projects" / project_id
    stats: dict[str, Any] = {}
    try:
        memory = ProjectMemory(settings.paths.memory_db)
        for row in memory.list_projects_with_stats():
            if row.get("project_id") == project_id:
                stats = row
                break
        project = memory.get_project(project_id)
        if not input_dir and project:
            input_dir = project.get("source_dir")
    except Exception:  # noqa: BLE001 - stats are cosmetic
        logger.debug("Could not load stats for %s", project_id, exc_info=True)

    try:
        source = Path(input_dir) if input_dir else None
        sections = load_sections(project_dir, source)
        reports = {}
        base_html, base_pdf = project_dir / "report.html", project_dir / "report.pdf"
        if base_html.is_file():
            reports["report.html"] = append_html(base_html.read_text(encoding="utf-8"), sections).encode("utf-8")
        if base_pdf.is_file():
            reports["report.pdf"] = append_pdf(base_pdf, sections)
        target = export_bundle(
            project_dir,
            project_name or stats.get("name") or project_id,
            project_id,
            results_root=default_results_root(PROJECT_ROOT),
            stats=stats,
            input_dir=input_dir,
            reports=reports,
        )
    except OSError:
        logger.warning("Could not publish results bundle for %s", project_id, exc_info=True)
        return ""
    return str(target) if target else ""


# 中文备注：构建并返回 FastAPI 应用（参数：无）
def _list_project_artifacts(folder: Path) -> list[dict[str, Any]]:
    """列出一次运行的实际产物，供界面直接告诉用户「数据在哪」。"""
    items: list[dict[str, Any]] = []

    def add(path: Path, kind: str) -> None:
        if path.is_file():
            items.append({"name": path.name, "kind": kind, "path": str(path),
                          "size": path.stat().st_size})

    for name, kind in (("report.html", "report:html"), ("report.pdf", "report:pdf"),
                       ("agent_state.json", "trace")):
        add(folder / name, kind)
    figures = folder / "figures"
    if figures.is_dir():
        for path in sorted(figures.glob("*.png"))[:12]:
            add(path, "figure")
    return items


def _require_local_client(request: Request) -> None:
    """校验请求是否来自本机回环地址，防止桌面/敏感接口在公网或反代场景被远程调用。"""
    if request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP"):
        raise HTTPException(status_code=403, detail="该接口仅允许本机直连访问")
    host = (request.client.host if request.client else "").strip().lower()
    if host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
        raise HTTPException(status_code=403, detail="该接口仅允许本机直连访问")


def create_app() -> FastAPI:
    """创建并装配 EpitopeRank FastAPI 应用实例，挂载所有业务路由与安全中间件。"""
    # Load .env file so API keys are available in environment variables
    from epitoperank.llm.envfile import load_env_values
    load_env_values()

    app = FastAPI(title="EpitopeRank API", version=API_VERSION)
    settings, storage_warnings = load_prepared_settings()
    ensure_runtime_dirs(settings)

    # Merge any pre-0.2 runtime directory (system temp dir or the folder next
    # to the executable) into the stable per-user root. Without this, projects
    # analysed by an older build would silently disappear from the UI.
    storage_migration: dict[str, Any] = {"migrated_from": []}
    if not os.getenv("EPITOPERANK_RUNTIME_ROOT", "").strip():
        try:
            from epitoperank.storage import migrate_legacy_storage

            storage_migration = migrate_legacy_storage(
                settings.paths.runtime_root, logger=logger.info
            )
            if storage_migration.get("migrated_from"):
                logger.warning(
                    "Merged legacy runtime storage into %s (sources: %s)",
                    settings.paths.runtime_root,
                    ", ".join(storage_migration["migrated_from"]),
                )
        except Exception as error:  # noqa: BLE001 - never block boot
            logger.warning("Legacy storage migration skipped: %s", error)

    log_path = os.getenv("EPITOPERANK_LOG_FILE") or (
        settings.paths.runtime_root / "logs" / "epitoperank.log"
    )
    configure_logging(log_path)
    configured_api_key = os.getenv("EPITOPERANK_API_KEY", "").strip()
    try:
        configured_rate_limit = max(0, int(os.getenv("EPITOPERANK_RATE_LIMIT", "0")))
    except ValueError:
        configured_rate_limit = 0
    rate_state: dict[str, tuple[float, int]] = {}
    rate_lock = threading.Lock()

    @app.get("/")
    # 中文备注：HTTP 接口：GET /（参数：无）
    def index() -> Any:
        """Serve the browser UI (what the desktop exe opens automatically)."""
        return render_web_ui(f"EpitopeRank v{API_VERSION}")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        """返回内嵌的 SVG 站点图标，避免浏览器探测 /favicon.ico 时报 404。"""
        return Response(content=_FAVICON_SVG, media_type="image/svg+xml")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        """健康探针：返回版本号与是否已配置模型端点。"""
        return {"status": "ok", "version": API_VERSION, "llm_configured": settings.llm.configured}

    @app.middleware("http")
    # 中文备注：Web 接口：辅助处理请求boundary（参数：request、call_next）
    async def request_boundary(request: Request, call_next: Any) -> Response:
        """Apply request correlation, baseline headers, and optional API auth."""
        # Reject encoded or literal parent-directory segments before routing.
        # Several handlers build paths from {project_id}/{name} path params.
        from urllib.parse import unquote

        raw_path = request.scope.get("raw_path", b"").decode("latin-1", "ignore")
        decoded_path = unquote(raw_path)
        if ".." in decoded_path or "\x00" in decoded_path:
            return JSONResponse(status_code=400, content={"detail": "invalid path"})
        request_id = new_request_id(request.headers.get("X-Request-ID"))
        token = set_request_id(request_id)
        started = time.perf_counter()
        response: Response
        try:
            protected = request.url.path.startswith("/api/") and request.url.path != (
                "/api/health"
            )
            rate_limited = False
            if configured_rate_limit and protected:
                client_id = request.client.host if request.client else "unknown"
                now = time.monotonic()
                with rate_lock:
                    window_start, count = rate_state.get(client_id, (now, 0))
                    if now - window_start >= 60:
                        window_start, count = now, 0
                    if count >= configured_rate_limit:
                        rate_limited = True
                        retry_after = max(1, int(60 - (now - window_start)) + 1)
                    else:
                        rate_state[client_id] = (window_start, count + 1)
            if rate_limited:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)},
                )
            elif configured_api_key and protected:
                supplied = request.headers.get("X-API-Key", "")
                authorization = request.headers.get("Authorization", "")
                if not supplied and authorization.lower().startswith("bearer "):
                    supplied = authorization[7:].strip()
                if not secrets.compare_digest(supplied, configured_api_key):
                    response = JSONResponse(
                        status_code=401,
                        content={"detail": "API authentication required"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    response = await call_next(request)
            else:
                response = await call_next(request)
        except Exception:
            logger.exception("request_failed", extra={"event": "request_failed"})
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            # The response is intentionally logged only after call_next returns;
            # rejected requests are still observable without logging credentials.
            if "response" in locals():
                logger.info(
                    "request_completed",
                    extra={
                        "event": "request_completed",
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
            reset_request_id(token)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    # 中文备注：Web 接口：辅助处理fresh设置（参数：无）
    def _fresh_settings() -> Any:
        """Reload settings so a key saved through /api/llm/config is live.

        ``settings`` captured above would otherwise keep the credentials the
        process started with, which makes "paste the key in the UI" look like
        it silently failed.
        """
        from epitoperank.config import load_settings

        try:
            return load_settings()
        except Exception:  # noqa: BLE001 - keep the boot-time settings
            return settings

    @app.get("/api/llm/status")
    # 中文备注：HTTP 接口：GET /api/llm/status（参数：无）
    def llm_status_endpoint() -> dict[str, Any]:
        """Is a model endpoint configured, and what may it enrich?"""
        from epitoperank.llm.enrich import llm_status
        from epitoperank.llm.envfile import env_config_payload

        payload = llm_status(_fresh_settings())
        payload["config"] = env_config_payload()
        return payload

    @app.post("/api/llm/config")
    # 中文备注：HTTP 接口：POST /api/llm/config（参数：payload）
    def llm_config(payload: dict[str, Any]) -> dict[str, Any]:
        """Save model credentials into the local ``.env`` file.

        Accepts ``{"values": {...}}`` or the flat form (``{"MODEL_API_KEY":
        "sk-..."}``). A preset id may be merged in first with
        ``{"preset": "deepseek-flash"}``. Secrets never leave this machine and
        only a masked copy is returned.
        """
        from epitoperank.llm.envfile import PRESETS, write_env_values

        updates: dict[str, str] = {}
        preset = str(payload.get("preset", "")).strip()
        if preset:
            chosen = PRESETS.get(preset)
            if chosen is None:
                raise HTTPException(status_code=400, detail=f"unknown preset: {preset}")
            updates.update({k: v for k, v in chosen.items() if k != "label"})
        raw = payload.get("values")
        if isinstance(raw, dict):
            updates.update({str(key): str(value) for key, value in raw.items()})
        else:
            updates.update({
                str(key): str(value) for key, value in payload.items() if key not in ("preset", "values")
            })
        if not updates:
            raise HTTPException(status_code=400, detail="no configuration values supplied")
        try:
            path, changed = write_env_values(updates)
        except OSError as error:
            raise HTTPException(status_code=500, detail=f"cannot write .env: {error}") from error
        from epitoperank.llm.enrich import llm_status
        from epitoperank.llm.envfile import env_config_payload

        return {
            "saved": True,
            "path": str(path),
            "updated": changed,
            "status": llm_status(_fresh_settings()),
            "config": env_config_payload(),
        }

    @app.get("/api/esm2/status")
    def esm2_status_endpoint(force: bool = False) -> dict[str, Any]:
        """探测远程 ESM-2-650M LoRA 推理服务连通状态与配置信息。"""
        from epitoperank.peptide import esm2_client

        info = esm2_client.status(force=force)
        info["has_api_key"] = bool(os.getenv("EPITOPERANK_ESM2_API_KEY", "").strip())
        info["ensemble"] = os.getenv("EPITOPERANK_ESM2_ENSEMBLE", "true").strip().lower() not in {
            "false", "0", "no", "off",
        }
        return info

    @app.post("/api/esm2/config")
    def esm2_config_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        """保存 ESM-2 服务地址与密钥到本地 .env 并立即实测连通性（无需重启）。"""
        from epitoperank.llm.envfile import write_env_values
        from epitoperank.peptide import esm2_client

        updates: dict[str, str] = {}
        if "url" in payload:
            updates["EPITOPERANK_ESM2_URL"] = str(payload.get("url") or "").strip().rstrip("/")
        api_key = str(payload.get("api_key") or "").strip()
        if api_key:
            updates["EPITOPERANK_ESM2_API_KEY"] = api_key
        if "ensemble" in payload:
            updates["EPITOPERANK_ESM2_ENSEMBLE"] = "true" if payload.get("ensemble") else "false"
        if not updates:
            raise HTTPException(status_code=400, detail="请至少填写 ESM-2 服务地址或 API Key")
        try:
            path, changed = write_env_values(updates)
        except OSError as error:
            raise HTTPException(status_code=500, detail=f"写入 .env 失败: {error}") from error
        esm2_client.clear_status_cache()
        st = esm2_client.status(force=True)
        st["has_api_key"] = bool(os.getenv("EPITOPERANK_ESM2_API_KEY", "").strip())
        return {"saved": True, "path": str(path), "updated": changed, "status": st}

    @app.get("/api/projects")
    def projects() -> dict[str, Any]:
        """列出全部项目（纯读库，供首页项目列表使用）。"""
        return {"projects": list_projects(settings)}

    @app.get("/api/storage")
    # 中文备注：HTTP 接口：GET /api/storage（参数：request）
    def storage(request: Request) -> dict[str, Any]:
        """返回本机数据存储与迁移信息（仅限本机直连访问，防止泄露宿主机路径）。"""
        _require_local_client(request)
        from epitoperank.storage import storage_info

        info = storage_info(settings.paths.runtime_root)
        info["memory_db"] = str(settings.paths.memory_db)
        info["literature_db"] = str(settings.paths.literature_db)
        info["migration"] = storage_migration
        return info

    @app.get("/api/status/{project_id}")
    def status(project_id: str) -> dict[str, Any]:
        """返回某项目的分析状态汇总（读库）；项目不存在时返回 404。"""
        payload = project_status(project_id, settings)
        if payload is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return payload

    @app.get("/api/projects/{project_id}/events")
    # 中文备注：HTTP 接口：GET /api/projects/{project_id}/events（参数：project_id、page、size、q）
    def project_events(
        project_id: str,
        page: int = 1,
        size: int = 50,
        q: str = "",
        event_type: str = "",
        significant_only: bool = False,
        order_by: str = "fdr",
    ) -> dict[str, Any]:
        """Paged, filterable event browser for a *historical* project.

        Paging happens in SQLite: real rMATS runs carry 10^5-10^6 events, which
        cannot be shipped to the browser in one response.
        """
        from epitoperank.memory.project_memory import ProjectMemory

        memory = ProjectMemory(settings.paths.memory_db)
        if memory.get_project(project_id) is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        size = max(1, min(int(size), 500))
        page = max(1, int(page))
        filters = {
            "search": q.strip(),
            "event_type": event_type.strip(),
            "significant_only": bool(significant_only),
        }
        total = memory.count_events(project_id, **filters)
        rows = memory.query_events(
            project_id,
            offset=(page - 1) * size,
            limit=size,
            order_by=order_by,
            **filters,
        )
        return {
            "project_id": project_id,
            "total": total,
            "page": page,
            "size": size,
            "pages": max(1, (total + size - 1) // size),
            "events": rows,
            "event_types": memory.event_type_counts(project_id),
        }

    @app.delete("/api/projects/{project_id}")
    # 中文备注：HTTP 接口：DELETE /api/projects/{project_id}（参数：project_id）
    def delete_project(project_id: str) -> dict[str, Any]:
        """Delete a project: database rows plus its output folder."""
        from epitoperank.memory.project_memory import ProjectMemory

        memory = ProjectMemory(settings.paths.memory_db)
        if memory.get_project(project_id) is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        removed_rows = memory.delete_project(project_id)
        project_dir = settings.paths.runtime_root / "projects" / project_id
        if project_dir.is_dir():
            shutil.rmtree(project_dir, ignore_errors=True)
        return {"deleted": project_id, "rows": removed_rows}

    @app.post("/api/projects/{project_id}/export")
    # 中文备注：HTTP 接口：POST /api/projects/{project_id}/export（参数：project_id）
    def export_project(project_id: str) -> dict[str, Any]:
        """Publish this project's report/figures into its own results folder."""
        from epitoperank.memory.project_memory import ProjectMemory

        memory = ProjectMemory(settings.paths.memory_db)
        project = memory.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        name = project.get("name") if isinstance(project, dict) else ""
        bundle = _export_project_bundle(settings, project_id, str(name or project_id))
        if not bundle:
            raise HTTPException(
                status_code=404,
                detail="这个项目还没有可导出的报告，跑完分析后再试",
            )
        return {"ok": True, "path": bundle}

    @app.post("/api/projects/{project_id}/reveal-bundle")
    # 中文备注：HTTP 接口：POST /api/projects/{project_id}/reveal-bundle（参数：project_id、request）
    def reveal_project_bundle(project_id: str, request: Request) -> dict[str, Any]:
        """导出并在系统文件管理器中打开成果目录（仅限本机桌面直连访问）。"""
        _require_local_client(request)
        from epitoperank.memory.project_memory import ProjectMemory

        memory = ProjectMemory(settings.paths.memory_db)
        project = memory.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        name = project.get("name") if isinstance(project, dict) else ""
        bundle = _export_project_bundle(settings, project_id, str(name or project_id))
        if not bundle:
            raise HTTPException(status_code=404, detail="这个项目还没有可导出的报告")
        try:
            if sys.platform == "win32":
                os.startfile(bundle)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", bundle])
            else:
                subprocess.Popen(["xdg-open", bundle])
        except OSError as error:
            raise HTTPException(status_code=500, detail=f"Cannot open folder: {error}") from error
        return {"ok": True, "path": bundle}

    def _bundle_dir_for(project_id: str) -> str:
        """导出并返回项目的成果目录；项目不存在或没有可导出内容时抛 404。"""
        from epitoperank.memory.project_memory import ProjectMemory

        memory = ProjectMemory(settings.paths.memory_db)
        project = memory.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        name = project.get("name") if isinstance(project, dict) else ""
        bundle = _export_project_bundle(settings, project_id, str(name or project_id))
        if not bundle:
            raise HTTPException(status_code=404, detail="这个项目还没有可导出的报告")
        return bundle

    @app.post("/api/projects/{project_id}/package")
    # 中文备注：HTTP 接口：POST /api/projects/{project_id}/package（参数：project_id）
    def package_project(project_id: str) -> dict[str, Any]:
        """Zip the project's results folder for e-mail, archive or upload."""
        from epitoperank.results_export import package_bundle

        archive = package_bundle(_bundle_dir_for(project_id))
        if archive is None:
            raise HTTPException(status_code=404, detail="打包失败：成果文件夹不存在")
        return {"ok": True, "path": str(archive), "size_mb": round(archive.stat().st_size / 1048576, 2)}

    @app.post("/api/projects/{project_id}/upload")
    # 中文备注：HTTP 接口：POST /api/projects/{project_id}/upload（参数：project_id）
    def upload_project(project_id: str) -> dict[str, Any]:
        """Push the project's bundle to the configured cloud endpoint."""
        from epitoperank.results_export import (
            cloud_upload_target,
            package_bundle,
            upload_bundle,
        )

        url, _token = cloud_upload_target()
        if not url:
            raise HTTPException(
                status_code=400,
                detail="还没有配置云端地址（环境变量 EPITOPERANK_CLOUD_URL）",
            )
        archive = package_bundle(_bundle_dir_for(project_id))
        if archive is None:
            raise HTTPException(status_code=404, detail="打包失败：成果文件夹不存在")
        result = upload_bundle(archive)
        if not result.get("ok"):
            raise HTTPException(status_code=502, detail=f"上传失败：{result.get('detail')}")
        return {"ok": True, "archive": str(archive), "cloud": result.get("detail", "")}

    @app.post("/api/analyze")
    def analyze(payload: dict[str, Any]) -> dict[str, Any]:
        """同步跑完整条分析流水线并返回摘要，随后尝试把成果导出到 results 目录。

        请求需带 ``query`` 与存在的 ``input_dir``；``thresholds`` 里给出的阈值只对本次生效。
        """
        query = str(payload.get("query", "")).strip()
        input_dir = str(payload.get("input_dir", "")).strip()
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        if not input_dir or not Path(input_dir).exists():
            raise HTTPException(status_code=400, detail=f"input_dir does not exist: {input_dir}")

        run_settings = _with_overrides(settings, payload.get("thresholds"))
        project_name = str(payload.get("project_name") or "").strip()[:120]
        try:
            outcome = run_analysis(query, input_dir, settings=run_settings, project_name=project_name)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        summary = outcome.summary()
        try:
            bundle = _export_project_bundle(
                run_settings, outcome.project_id, project_name, input_dir=input_dir
            )
        except Exception:  # noqa: BLE001 - publishing must never fail a run
            logger.warning("Results bundle failed for %s", outcome.project_id, exc_info=True)
            bundle = ""
        if bundle:
            summary["results_dir"] = bundle
        return JSONResponse(summary)

    # 中文备注：Web 接口：辅助处理ingest输入目录（参数：raw）
    def _ingest_input_dir(raw: str) -> Path:
        """Resolve an ingestion directory and keep model exposure local.

        The UI always uploads into the runtime directory; this guard stops a
        remote caller (when the API is exposed) from pointing the model-backed
        profiler at arbitrary files elsewhere on the machine.
        """
        value = str(raw or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="input_dir is required")
        path = Path(value).expanduser().resolve()
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"input_dir does not exist: {path}")
        if os.getenv("EPITOPERANK_INGEST_ALLOW_EXTERNAL", "").strip().lower() in {"1", "true", "yes"}:
            return path
        roots = [settings.paths.runtime_root.resolve(), Path.cwd().resolve()]
        if not any(path == root or root in path.parents for root in roots):
            raise HTTPException(
                status_code=400,
                detail="input_dir must be inside the runtime or working directory for ingestion",
            )
        return path

    @app.post("/api/ingest/preview")
    # 中文备注：HTTP 接口：POST /api/ingest/preview（参数：payload）
    def ingest_preview(payload: dict[str, Any]) -> dict[str, Any]:
        """Profile messy input and propose a reviewed mapping (no files written)."""
        from epitoperank.data.ingestion import preview_ingestion

        directory = _ingest_input_dir(str(payload.get("input_dir", "")))
        try:
            return preview_ingestion(
                directory,
                settings=_fresh_settings(),
                use_llm=bool(payload.get("use_llm", True)),
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except Exception as error:  # noqa: BLE001 - surface a useful 500
            logger.exception("Ingestion preview failed")
            raise HTTPException(status_code=500, detail=f"Ingestion preview failed: {error}") from error

    @app.post("/api/ingest/apply")
    # 中文备注：HTTP 接口：POST /api/ingest/apply（参数：payload）
    def ingest_apply(payload: dict[str, Any]) -> dict[str, Any]:
        """Convert files with a confirmed mapping into a standardized directory."""
        from epitoperank.data.ingestion import apply_ingestion

        directory = _ingest_input_dir(str(payload.get("input_dir", "")))
        mapping = payload.get("mapping")
        if not isinstance(mapping, dict) or not mapping:
            raise HTTPException(status_code=400, detail="mapping is required")
        try:
            return apply_ingestion(directory, mapping)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except OSError as error:
            raise HTTPException(status_code=500, detail=f"Cannot write standardized data: {error}") from error
        except Exception as error:  # noqa: BLE001 - surface a useful 500
            logger.exception("Ingestion apply failed")
            raise HTTPException(status_code=500, detail=f"Ingestion apply failed: {error}") from error

    @app.post("/api/ingest/groups")
    # 中文备注：HTTP 接口：POST /api/ingest/groups（参数：payload）
    def ingest_groups(payload: dict[str, Any]) -> dict[str, Any]:
        """Persist confirmed sample groups for an already recognized input."""
        from epitoperank.data.ingestion import apply_native_groups

        directory = _ingest_input_dir(str(payload.get("input_dir", "")))
        groups = payload.get("sample_groups")
        if not isinstance(groups, dict):
            raise HTTPException(status_code=400, detail="sample_groups is required")
        try:
            return apply_native_groups(directory, groups)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    neo_workflows: dict[str, dict] = {}
    neo_workflows_lock = threading.RLock()
    neo_workflows_dir = settings.paths.runtime_root / 'neoantigen_workflows'

    def _neo_session_file(workflow_id: str) -> Path:
        """校验 workflow_id 为 32 位安全字符并返回会话文件路径；格式非法时抛 404。"""
        if not re.fullmatch(r'[A-Za-z0-9_-]{32}', workflow_id):
            raise HTTPException(status_code=404, detail='流程不存在')
        return neo_workflows_dir / (workflow_id + '.json')

    def _neo_save(workflow_id: str, session: dict) -> None:
        """原子地写入流程会话（先写 .tmp 再 os.replace），同时更新内存缓存。"""
        path = _neo_session_file(workflow_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(session, ensure_ascii=False), encoding='utf-8')
        os.replace(temporary, path)
        neo_workflows[workflow_id] = session

    def _neo_load(workflow_id: str) -> dict:
        """读取流程会话：命中内存缓存则直接返回，否则从磁盘 JSON 载入；读不到抛 404。"""
        path = _neo_session_file(workflow_id)
        if workflow_id not in neo_workflows:
            try:
                neo_workflows[workflow_id] = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                raise HTTPException(status_code=404, detail='流程不存在或无法读取')
        return neo_workflows[workflow_id]

    @app.get('/api/neoantigen/workflow/{workflow_id}')
    def neo_workflow_get(workflow_id: str) -> dict[str, Any]:
        """返回指定新抗原流程会话的当前阶段状态。"""
        with neo_workflows_lock:
            session = _neo_load(workflow_id)
            return {'workflow_id': workflow_id, **session['state']}

    @app.get('/api/neoantigen/readiness/{project_id}')
    def neo_readiness(project_id: str) -> dict[str, Any]:
        """体检项目的编码序列表与 rMATS 文件是否齐备，并给出列映射与预览。

        只按表头与列内容判断，不校验读码框；检测失败时返回 422 并带出原因。
        """
        import csv
        from epitoperank.data.loader import load_dataset
        from epitoperank.neoantigen import (CDS_FIELD_LABELS, CDS_FIELDS, discover_cds_tables,
                                           pick_cds_table)
        from epitoperank.splicing.parsers.rmats import discover_rmats_tables
        project = project_status(project_id, settings)
        if not project:
            raise HTTPException(status_code=404, detail='未找到项目，请先选择项目')
        directory = _ingest_input_dir(str(project['project'].get('source_dir') or ''))
        roots = [directory]
        if directory.name == 'standardized':
            roots.append(_ingest_input_dir(str(directory.parent)))
        try:
            known_count = project.get('events')
            discovered = discover_cds_tables(*roots, include_partial=True, event_ids=None)
            need_full_dataset = (
                not isinstance(known_count, int)
                or known_count <= 0
                or any(item.get('needs_confirmation') for item in discovered)
            )
            if need_full_dataset:
                dataset = load_dataset(directory)
                event_count = len(dataset.events)
                if any(item.get('needs_confirmation') for item in discovered):
                    event_ids = {event.event_id for event in dataset.events}
                    discovered = discover_cds_tables(*roots, include_partial=True, event_ids=event_ids)
            else:
                event_count = known_count
            candidates = [item for item in discovered if item['valid']]
            partial = [item for item in discovered if not item['valid']]
            chosen = pick_cds_table(candidates)
            details = {}
            for item in candidates:
                stored = _load_cds_mappings(Path(item['path']).parent).get(item['name'], {})
                mapping = stored.get('map') or item['mapping']
                details[item['name']] = {
                    'map': mapping,
                    'source': 'saved' if stored else item['mapping_source'],
                    'confidence': 'high' if stored else item['confidence'],
                    'needs_confirmation': False if stored else item['needs_confirmation'],
                    'header': item['header'],
                    'preview': item['preview'],
                    'row_count': item.get('row_count') or 0,
                }
            fasta_files: list[str] = []
            seen_fastas: set[str] = set()
            for root in roots:
                if not root.is_dir():
                    continue
                for entry in sorted(root.iterdir()):
                    if (entry.is_file() and entry.suffix.lower() in {'.fa', '.fasta', '.faa'}
                            and entry.name not in seen_fastas):
                        seen_fastas.add(entry.name)
                        fasta_files.append(entry.name)
            return {'project_name': project['project'].get('name') or project_id,
                    'event_count': event_count,
                    'cds_status': 'available' if candidates else 'missing',
                    'cds_files': [item['name'] for item in candidates],
                    'cds_selected': chosen.name if chosen else None,
                    'cds_choices': [{'name': item['name'], 'columns': item['header']} for item in candidates],
                    'cds_details': details,
                    'cds_needs_confirmation': bool(chosen and details.get(chosen.name, {}).get('needs_confirmation')),
                    'cds_partial': [{'name': item['name'], 'missing': item['missing'],
                                     'reason': item['reason']} for item in partial[:5]],
                    'fasta_files': fasta_files,
                    'field_labels': CDS_FIELD_LABELS,
                    'required_fields': list(CDS_FIELDS),
                    'rmats_files': [table.name for root in roots
                                    for table in discover_rmats_tables(root).values()],
                    'note': '仅检查表头与列内容，序列读码框和数据质量须在分析时进一步核实。'}
        except (ValueError, OSError, UnicodeError, csv.Error) as error:
            raise HTTPException(status_code=422, detail=f'无法读取项目数据：{error}') from error

    @app.post('/api/neoantigen/workflow/start')
    def neo_workflow_start(payload: dict[str, Any]) -> dict[str, Any]:
        """用项目数据集开启一轮新抗原流程，生成随机 workflow_id 并落盘会话。"""
        from epitoperank.data.loader import load_dataset
        from epitoperank.neoantigen_workflow import start
        project = project_status(str(payload.get('project_id') or ''), settings)
        if not project:
            raise HTTPException(status_code=404, detail='请先选择有效项目')
        directory = _ingest_input_dir(str(project['project'].get('source_dir') or ''))
        evidence = payload.get('evidence') or {}
        if not isinstance(evidence, dict):
            raise HTTPException(status_code=422, detail='evidence 必须为对象')
        try:
            state = start(load_dataset(directory), evidence)
        except (ValueError, OSError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        workflow_id = secrets.token_urlsafe(24)
        with neo_workflows_lock:
            _neo_save(workflow_id, {'directory': str(directory), 'state': state})
        return {'workflow_id': workflow_id, **state}

    @app.post('/api/neoantigen/workflow/advance')
    def neo_workflow_advance(payload: dict[str, Any]) -> dict[str, Any]:
        """把流程推进到下一阶段；客户端 expected_stage 过期时返回 409 以防重复提交。"""
        from epitoperank.data.loader import load_dataset
        from epitoperank.neoantigen_workflow import advance
        workflow_id = str(payload.get('workflow_id') or '')
        params = payload.get('parameters') or {}
        if not isinstance(params, dict):
            raise HTTPException(status_code=422, detail='parameters 必须为对象')
        with neo_workflows_lock:
            session = _neo_load(workflow_id)
            if payload.get('expected_stage') != session['state']['next_stage']:
                raise HTTPException(status_code=409, detail='阶段已改变，请刷新状态')
            try:
                state = advance(session['state'], load_dataset(session['directory']), params)
            except (ValueError, TypeError, OSError) as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
            _neo_save(workflow_id, {**session, 'state': state})
        return {'workflow_id': workflow_id, **state}

    def _project_input_dirs(project_id: str) -> tuple[Path, list[Path]]:
        """返回项目的数据目录，以及需一并搜索的目录列表（standardized 时含其父目录）。"""
        project = project_status(project_id, settings)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在，请重新选择项目")
        directory = _ingest_input_dir(str(project['project'].get('source_dir') or ''))
        roots = [directory]
        if directory.name == 'standardized':
            roots.append(_ingest_input_dir(str(directory.parent)))
        return directory, roots

    # 中文备注：Web 接口：解析CDS表（参数：value、roots）
    def _resolve_cds_table(value: Any, roots: list[Path]) -> Path:
        """Map a customer-supplied file name or path onto an existing CDS table."""
        from epitoperank.neoantigen import inspect_cds_table

        raw = str(value or "").strip()
        if not raw:
            raise HTTPException(status_code=422, detail="请先选择编码序列表文件")
        requested = Path(raw).expanduser()
        options = [requested] if requested.is_absolute() else [root / requested for root in roots]
        allowed = [root.resolve() for root in roots]
        for option in options:
            try:
                resolved = option.resolve()
            except OSError:
                continue
            if not resolved.is_file():
                continue
            if not any(resolved.parent == root or root in resolved.parents for root in allowed):
                raise HTTPException(status_code=422, detail="编码序列表必须位于当前项目的数据目录中，请先上传到项目")
            info = inspect_cds_table(resolved)
            if not info['valid']:
                raise HTTPException(status_code=422, detail=f"{resolved.name} 不能作为编码序列表：{info['reason']}")
            return resolved
        raise HTTPException(status_code=404, detail=f"当前项目里没有找到文件「{raw}」，请重新选择或上传")

    def _detect_cds_table(roots: list[Path]) -> Path:
        """在给定目录里自动挑一张可用的编码序列表；一张都没有时抛 422 并说明所需四列。"""
        from epitoperank.neoantigen import discover_cds_tables

        candidates = discover_cds_tables(*roots)
        if not candidates:
            raise HTTPException(status_code=422, detail=(
                "当前项目里还没找到编码序列表。需要一份包含 event_id、reference_cds、altered_cds、"
                "junction_nt 四列的表（TSV/CSV/TXT，文件名不限），上传后即可生成候选肽。"))
        return candidates[0]['path']

    # Customer-confirmed column mappings live next to the table so a manual fix
    # only has to be made once per project.
    def _load_cds_mappings(directory: Path) -> dict[str, Any]:
        """读取表目录下已确认的列映射文件；文件缺失或内容损坏时返回空字典。"""
        path = Path(directory) / CDS_MAPPING_FILE
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_cds_mapping(directory: Path, name: str, mapping: dict[str, str]) -> None:
        """把某张表的列映射并入映射文件（按表名覆盖旧值）并写回磁盘。"""
        data = _load_cds_mappings(directory)
        data[name] = {'map': mapping}
        (Path(directory) / CDS_MAPPING_FILE).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    # 中文备注：Web 接口：辅助处理映射（参数：table、requested、roots）
    def _mapping_for(table: Path, requested: Any, roots: list[Path]) -> dict[str, str] | None:
        """Merge an explicit mapping from the request with one saved earlier."""
        saved = _load_cds_mappings(Path(table).parent).get(Path(table).name, {}).get('map') or {}
        supplied = requested if isinstance(requested, dict) else {}
        merged = {str(key): str(value) for key, value in {**saved, **supplied}.items()
                  if str(value or '').strip()}
        return merged or None

    @app.post("/api/neoantigen/column-map")
    # 中文备注：HTTP 接口：POST /api/neoantigen/column-map（参数：payload）
    def neo_column_map(payload: dict[str, Any]) -> dict[str, Any]:
        """Persist a human-confirmed column mapping for one CDS table."""
        from epitoperank.neoantigen import CDS_FIELDS, read_table_rows

        directory, roots = _project_input_dirs(str(payload.get("project_id") or "").strip())
        table = _resolve_cds_table(payload.get("file"), roots)
        mapping = payload.get("map") or {}
        if not isinstance(mapping, dict):
            raise HTTPException(status_code=400, detail="列映射格式应为 {字段: 列名}")
        try:
            header, body, _delimiter = read_table_rows(table, limit=5)
        except OSError as error:
            raise HTTPException(status_code=422, detail=f"无法读取 {table.name}：{error}") from error
        cleaned: dict[str, str] = {}
        for field in CDS_FIELDS:
            value = str(mapping.get(field) or "").strip()
            if not value:
                raise HTTPException(status_code=422, detail=f"请为每个字段选择一列（缺少 {field}）")
            if value not in header:
                raise HTTPException(status_code=422, detail=f"表里没有列「{value}」")
            cleaned[field] = value
        if len(set(cleaned.values())) != len(cleaned):
            raise HTTPException(status_code=422, detail="同一个列不能承担两个字段角色，请分别选择")
        # Verify the mapping really produces peptides before we remember it.
        from epitoperank.neoantigen import junction_peptides

        produced = 0
        for row in body:
            cells = {field: (row[header.index(name)] if header.index(name) < len(row) else '').strip()
                     for field, name in cleaned.items()}
            try:
                if junction_peptides(cells['reference_cds'], cells['altered_cds'],
                                     int(cells['junction_nt'])):
                    produced += 1
            except (ValueError, TypeError):
                continue
        _save_cds_mapping(Path(table).parent, table.name, cleaned)
        return {'saved': table.name, 'map': cleaned,
                'verified_rows': produced,
                'warning': None if produced else '这套映射没有为样本行生成任何肽，请核对参考与改变后序列是否填反。'}

    @app.post("/api/neoantigen/cds-upload")
    # 中文备注：HTTP 接口：POST /api/neoantigen/cds-upload（参数：project_id、file）
    async def neo_cds_upload(project_id: Annotated[str, Form()], file: Annotated[UploadFile, File()]) -> dict[str, Any]:
        """Store a CDS table chosen from the customer's disk into the project directory."""
        from epitoperank.neoantigen import CDS_TABLE_MAX_BYTES, CDS_TABLE_SUFFIXES, discover_cds_tables, inspect_cds_table

        directory, roots = _project_input_dirs(str(project_id or '').strip())
        name = Path(file.filename or "").name
        if not name:
            raise HTTPException(status_code=400, detail="请选择一个文件")
        if Path(name).suffix.lower() not in CDS_TABLE_SUFFIXES:
            raise HTTPException(status_code=422, detail="编码序列表只支持 TSV、CSV 或 TXT 文本文件（Excel 请另存为 CSV）")
        content = await file.read()
        if not content:
            raise HTTPException(status_code=422, detail=f"{name} 是空文件")
        if len(content) > CDS_TABLE_MAX_BYTES:
            raise HTTPException(status_code=413, detail=f"{name} 超过 {CDS_TABLE_MAX_BYTES // (1024 * 1024)} MB 上限")
        target = directory / name
        target.write_bytes(content)
        info = inspect_cds_table(target)
        if not info['valid']:
            try:
                target.unlink()
            except OSError:
                pass
            raise HTTPException(status_code=422, detail=(
                f"{name} 不能作为编码序列表：{info['reason']}。需要包含 event_id、reference_cds、"
                "altered_cds、junction_nt 四列（列名可用常见别名，如事件ID / 参考序列 / 变异序列 / 连接点）。"))
        discovered = discover_cds_tables(*roots)
        return {'saved': name, 'cds_status': 'available',
                'cds_files': [item['name'] for item in discovered],
                'cds_selected': name, 'columns': info['header']}

    @app.post("/api/orf/build")
    def orf_build(payload: dict[str, Any]) -> dict[str, Any]:
        """从项目里的 rMATS 事件坐标重建 CDS 对照表（项目内 ORF 重建入口）。

        参考源 ``ensembl`` 走 Ensembl REST（联网、结果缓存到运行根）；
        ``local`` 用本地 GTF + FASTA，路径必须落在允许目录内。
        """
        from epitoperank.splicing.orf_builder import (
            EnsemblReference, LocalReference, build_orf_table)

        project_id = str(payload.get('project_id') or '').strip()
        if project_id:
            directory, roots = _project_input_dirs(project_id)
        else:
            directory = _ingest_input_dir(str(payload.get('input_dir', '')))
            roots = [directory]
        source = str(payload.get('source') or 'ensembl').strip().lower()
        if source == 'local':
            # 中文备注：Web 接口：辅助处理参考表（参数：value）
            def _reference(value: Any) -> Path:
                raw = str(value or '').strip()
                if not raw:
                    raise HTTPException(status_code=422, detail='本地参考源需要 GTF 与 FASTA 路径')
                path = Path(raw).expanduser().resolve()
                allowed = [r.resolve() for r in roots] + [settings.paths.runtime_root.resolve(),
                                                          Path.cwd().resolve()]
                if not path.is_file() or not any(
                        path == root or root in path.parents for root in allowed):
                    raise HTTPException(status_code=422, detail=f'参考文件不在允许目录内：{raw}')
                return path

            provider = LocalReference(_reference(payload.get('gtf')),
                                      _reference(payload.get('fasta')))
        elif source == 'ensembl':
            provider = EnsemblReference(cache_dir=settings.paths.runtime_root / 'orf_cache')
        else:
            raise HTTPException(status_code=422, detail='source 只能是 ensembl 或 local')

        # 中文备注：Web 接口：辅助处理bounded（参数：key、default、low、high）
        def _bounded(key: str, default: int, low: int, high: int) -> int:
            try:
                return max(low, min(high, int(payload.get(key) or default)))
            except (TypeError, ValueError):
                return default

        # 中文备注：Web 接口：辅助处理float（参数：key、default）
        def _float(key: str, default: float) -> float:
            try:
                return float(payload.get(key) or default)
            except (TypeError, ValueError):
                return default

        raw_ids = payload.get('event_ids') or []
        if isinstance(raw_ids, str):
            raw_ids = [part.strip() for part in raw_ids.split(',')]
        event_ids = [str(x).strip() for x in raw_ids if str(x).strip()] or None
        name = Path(str(payload.get('output') or 'splice_orfs.tsv')).name
        if not name.endswith(('.tsv', '.csv', '.txt')):
            name = 'splice_orfs.tsv'
        output = directory / name
        try:
            manifest = build_orf_table(
                directory, output, provider=provider, event_ids=event_ids,
                fdr_max=_float('fdr_max', 0.05),
                min_abs_dpsi=_float('min_abs_dpsi', 0.1),
                max_events=_bounded('max_events', 25, 1, 200),
                time_budget=max(30.0, min(600.0, _float('time_budget', 180.0))))
        except (ValueError, OSError, RuntimeError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {
            'ok': True, 'output': str(output), 'output_name': name,
            'reference': manifest['reference'], 'event_count': manifest['event_count'],
            'written': manifest['written'], 'skipped': manifest['skipped'],
            'genome_build': manifest['genome_build'],
            'manifest': str(output) + '.manifest.json',
            'cds_status': 'available' if manifest['written'] else 'empty',
        }

    @app.post("/api/neoantigen/run")
    # 中文备注：HTTP 接口：POST /api/neoantigen/run（参数：payload）
    def neoantigen_run(payload: dict[str, Any]) -> dict[str, Any]:
        """Generate auditable junction peptides; optionally query IEDB."""
        from epitoperank.neoantigen import run

        project_id = str(payload.get("project_id") or "").strip()
        requested = payload.get("cds_table")
        if project_id:
            directory, roots = _project_input_dirs(project_id)
        else:
            directory = _ingest_input_dir(str(payload.get("input_dir", "")))
            roots = [directory]
        cds_table = _resolve_cds_table(requested, roots) if str(requested or "").strip() else _detect_cds_table(roots)
        alleles = payload.get("alleles") or []
        if not isinstance(alleles, list):
            raise HTTPException(status_code=400, detail="alleles must be a list")
        results_base = settings.paths.runtime_root / "projects" / project_id if project_id else directory
        output = results_base / "neoantigen_results"
        from epitoperank.neoantigen import DEFAULT_MAX_PREDICTIONS

        try:
            max_predictions = int(payload.get("max_predictions") or DEFAULT_MAX_PREDICTIONS)
        except (TypeError, ValueError):
            max_predictions = DEFAULT_MAX_PREDICTIONS
        try:
            result = run(directory, cds_table, output, alleles=alleles,
                         max_predictions=max_predictions,
                         column_map=_mapping_for(cds_table, payload.get("column_map"), roots))
        except (ValueError, OSError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        result['cds_table_name'] = cds_table.name
        result['cds_table_auto_selected'] = not str(requested or "").strip()
        result['results_input_dir'] = str(results_base)
        return result

    @app.get("/api/neoantigen/file")
    def neoantigen_file(input_dir: str, name: str) -> FileResponse:
        """下载新抗原结果文件，仅允许固定白名单内的文件名。"""
        directory = _ingest_input_dir(input_dir)
        if name not in {"splice_peptides.tsv", "mhc_i_predictions.tsv",
                        "ranked_candidates.tsv", "neoantigen_manifest.json"}:
            raise HTTPException(status_code=400, detail="Unsupported result file")
        path = directory / "neoantigen_results" / name
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Result file not found")
        return FileResponse(path, filename=name)

    @app.post("/api/neoantigen/reveal")
    # 中文备注：HTTP 接口：POST /api/neoantigen/reveal（参数：payload、request）
    def neoantigen_reveal(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        """在系统文件管理器中打开新抗原结果目录（仅限本机桌面直连访问）。"""
        _require_local_client(request)
        directory = _ingest_input_dir(str(payload.get("input_dir", "")))
        folder = str(payload.get("folder") or "neoantigen_results").strip()
        if folder not in {"neoantigen_results", "peptide_results"}:
            raise HTTPException(status_code=400, detail="Unsupported result folder")
        results = directory / folder
        if not results.is_dir():
            raise HTTPException(status_code=404, detail="Result directory not found")
        try:
            if sys.platform == "win32":
                os.startfile(str(results))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(results)])
            else:
                subprocess.Popen(["xdg-open", str(results)])
        except OSError as error:
            raise HTTPException(status_code=500, detail=f"Cannot open results folder: {error}") from error
        return {"ok": True, "path": str(results)}

    # ------------------------------------------------------------------
    # Peptide prediction (MHC-I/II binding, processing, ranking)
    # ------------------------------------------------------------------

    @app.get("/api/peptide/capabilities")
    # 中文备注：HTTP 接口：GET /api/peptide/capabilities（参数：无）
    def peptide_capabilities() -> dict[str, Any]:
        """Report which peptide predictors, models and reference tables exist."""
        from epitoperank.peptide import capabilities

        try:
            return capabilities()
        except (OSError, ValueError, RuntimeError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.get("/api/peptide/reference")
    # 中文备注：HTTP 接口：GET /api/peptide/reference（参数：mhc_class、search、limit）
    def peptide_reference(
        mhc_class: int = 1, search: str = "", limit: int = 500
    ) -> dict[str, Any]:
        """Search the bundled IEDB-derived allele catalogue."""
        from epitoperank.peptide import reference

        if mhc_class not in (1, 2):
            raise HTTPException(status_code=422, detail="mhc_class must be 1 or 2")
        limit = max(1, min(int(limit), 5000))
        try:
            items = reference.load_alleles(mhc_class)
            manifest = reference.manifest()
        except (OSError, ValueError, RuntimeError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        needle = str(search or "").strip().lower()
        if needle:
            items = [item for item in items
                     if needle in str(item.get("allele", "")).lower()]
        return {"total": len(items), "items": items[:limit], "manifest": manifest}

    @app.post("/api/peptide/predict")
    # 中文备注：HTTP 接口：POST /api/peptide/predict（参数：payload）
    def peptide_predict(payload: dict[str, Any]) -> dict[str, Any]:
        """Predict MHC binding/processing for a small peptide list."""
        from epitoperank.peptide import IedbError, predict_peptides
        from epitoperank.peptide.sequences import normalize_peptide

        raw_peptides = payload.get("peptides")
        raw_alleles = payload.get("alleles")
        if not isinstance(raw_peptides, list) or not raw_peptides:
            raise HTTPException(status_code=422, detail="peptides must be a non-empty list")
        if not isinstance(raw_alleles, list) or not raw_alleles:
            raise HTTPException(status_code=422, detail="alleles must be a non-empty list")
        if len(raw_peptides) > 2000:
            raise HTTPException(status_code=422, detail="单次最多 2000 条肽；更多请分批提交")
        if len(raw_alleles) > 8:
            raise HTTPException(status_code=422, detail="at most 8 alleles per request")
        peptides: list[str] = []
        for value in raw_peptides:
            try:
                peptide = normalize_peptide(str(value))
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
            if not 8 <= len(peptide) <= 30:
                raise HTTPException(
                    status_code=422,
                    detail=f"peptide length must be 8-30 aa: {peptide}",
                )
            peptides.append(peptide)
        alleles = [str(item).strip() for item in raw_alleles if str(item).strip()]
        if not alleles:
            raise HTTPException(status_code=422, detail="alleles must be a non-empty list")
        mhc_class = str(payload.get("mhc_class") or "class1")
        predictor = str(payload.get("predictor") or "iedb")
        if mhc_class not in {"class1", "class2", "both"}:
            raise HTTPException(status_code=422, detail="mhc_class must be class1, class2 or both")
        if predictor not in {"iedb", "local", "auto", "none"}:
            raise HTTPException(status_code=422, detail="predictor must be iedb, local, auto or none")
        processing = bool(payload.get("processing", True))
        lookup_epitopes = bool(payload.get("lookup_epitopes", False))

        try:
            if predictor == "none":
                # Offline smoke test: no model is consulted and no network call is made.
                result: dict[str, Any] = {"predictions": [], "errors": [],
                                          "methods": {}}
            else:
                result = predict_peptides(
                    peptides,
                    alleles,
                    mhc_class=mhc_class,
                    predictor=predictor,
                    processing=processing,
                )
        except (ValueError, OSError, IedbError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        epitope_matches: list[dict[str, Any]] = []
        if lookup_epitopes and predictor in {"iedb", "auto"} and result.get("predictions"):
            try:
                from epitoperank.peptide import IedbClient

                found = IedbClient().lookup_epitopes(peptides[:10])
                for peptide, hits in found.items():
                    for hit in hits:
                        epitope_matches.append({"candidate_peptide": peptide, **hit})
            except IedbError as error:
                result.setdefault("errors", []).append(
                    {"stage": "epitope_lookup", "error": str(error)[:500]}
                )

        predictions = result.get("predictions") or []
        return {
            "candidate_count": len(peptides),
            "prediction_count": len(predictions),
            "predictions": predictions,
            "errors": result.get("errors") or [],
            "methods": result.get("methods") or {},
            "epitope_matches": epitope_matches,
        }

    @app.post("/api/peptide/self-fasta-upload")
    # 中文备注：HTTP 接口：POST /api/peptide/self-fasta-upload（参数：project_id、file）
    async def peptide_self_fasta_upload(
        project_id: Annotated[str, Form()],
        file: Annotated[UploadFile, File()],
    ) -> dict[str, Any]:
        """Upload an optional normal proteome FASTA into the project directory for self-filtering."""
        directory, roots = _project_input_dirs(str(project_id or "").strip())
        name = Path(file.filename or "").name
        if not name:
            raise HTTPException(status_code=400, detail="请选择一个 FASTA 文件")
        if Path(name).suffix.lower() not in {".fa", ".fasta", ".faa"}:
            raise HTTPException(status_code=422, detail="参考蛋白组文件需为 .fa / .fasta / .faa 格式")
        content = await file.read()
        if not content:
            raise HTTPException(status_code=422, detail=f"{name} 是空文件")
        max_bytes = 64 * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"{name} 超过 64 MB 上限")
        head = content[:4096].decode("utf-8-sig", errors="replace").lstrip()
        if not head.startswith(">"):
            raise HTTPException(status_code=422, detail=f"{name} 不是有效的 FASTA 文件（须以 '>' 开头）")
        target = directory / name
        target.write_bytes(content)
        fasta_files = sorted({
            entry.name
            for root in roots if root.is_dir()
            for entry in root.iterdir()
            if entry.is_file() and entry.suffix.lower() in {".fa", ".fasta", ".faa"}
        })
        return {"saved": name, "fasta_files": fasta_files}

    _peptide_jobs: dict[str, dict[str, Any]] = {}
    _peptide_jobs_lock = threading.Lock()

    def _execute_peptide_run(
        payload: dict[str, Any],
        progress_hook: Any = None,
    ) -> dict[str, Any]:
        """Shared implementation for synchronous /api/peptide/run and async job API."""
        from epitoperank.peptide import PeptideOptions, run as run_peptides

        def _report(pct: int, msg: str) -> None:
            if progress_hook is not None:
                progress_hook(max(1, min(99, int(pct))), msg)

        _report(3, "正在校验项目与输入文件…")
        project_id = str(payload.get("project_id") or "").strip()
        if project_id:
            project = project_status(project_id, settings)
            if not project:
                raise HTTPException(status_code=404, detail="请先选择有效项目")
            directory = _ingest_input_dir(str(project["project"].get("source_dir") or ""))
            search_dirs = [directory]
            if directory.name == "standardized":
                search_dirs.append(_ingest_input_dir(str(directory.parent)))
        else:
            directory = _ingest_input_dir(str(payload.get("input_dir") or ""))
            search_dirs = [directory]
        roots = [path.resolve() for path in search_dirs]

        def input_file(raw: Any, label: str) -> Path:
            """校验请求里的文件路径：为空或越出项目目录、文件不存在都按 4xx 报错。"""
            value = str(raw or "").strip()
            if not value:
                raise HTTPException(status_code=422, detail=f"{label} 不能为空")
            candidate = Path(value).expanduser()
            path = (candidate if candidate.is_absolute() else directory / candidate).resolve()
            if not path.is_file():
                for alt_root in roots:
                    alt = (alt_root / value).resolve()
                    if (alt == alt_root or alt_root in alt.parents) and alt.is_file():
                        path = alt
                        break
            if not any(path == root or root in path.parents for root in roots):
                raise HTTPException(status_code=400, detail="文件必须位于当前项目上传目录内")
            if not path.is_file():
                raise HTTPException(status_code=400, detail=f"{label} 文件不存在")
            return path

        cds_value = str(payload.get("cds_table") or "").strip()
        peptides_value = str(payload.get("peptides_file") or "").strip()
        if cds_value and peptides_value:
            raise HTTPException(status_code=422, detail="cds_table 与 peptides_file 只能提供一个")

        raw_orf_ids = payload.get("orf_event_ids") or []
        if isinstance(raw_orf_ids, str):
            raw_orf_ids = [part.strip() for part in raw_orf_ids.split(",")]
        orf_event_ids = [str(item).strip() for item in raw_orf_ids if str(item).strip()]
        auto_build_orf = bool(payload.get("auto_build_orf", False))
        force_rebuild_orf = bool(payload.get("force_rebuild_orf", False))
        orf_summary: dict[str, Any] | None = None

        def _auto_build_cds() -> Path:
            """按需自动重建 ORF，使前端一键筛选不再拆成手动多步。"""
            nonlocal orf_summary
            from epitoperank.splicing.orf_builder import (
                EnsemblReference, LocalReference, build_orf_table)

            orf_source = str(payload.get("orf_source") or "ensembl").strip().lower()
            if orf_source == "local":
                def _ref(value: Any) -> Path:
                    raw = str(value or "").strip()
                    if not raw:
                        raise HTTPException(status_code=422, detail="本地参考源需要提供 GTF 与 FASTA 路径")
                    p = Path(raw).expanduser().resolve()
                    allowed = [r.resolve() for r in roots] + [
                        settings.paths.runtime_root.resolve(), Path.cwd().resolve()]
                    if not p.is_file() or not any(p == r or r in p.parents for r in allowed):
                        raise HTTPException(status_code=422, detail=f"参考文件不在允许目录内：{raw}")
                    return p
                provider = LocalReference(_ref(payload.get("orf_gtf")), _ref(payload.get("orf_fasta")))
            elif orf_source == "ensembl":
                provider = EnsemblReference(cache_dir=settings.paths.runtime_root / "orf_cache")
            else:
                raise HTTPException(status_code=422, detail="orf_source 只能是 ensembl 或 local")

            try:
                max_events = max(1, min(200, int(payload.get("orf_max_events") or 20)))
            except (TypeError, ValueError):
                max_events = 20
            try:
                fdr_max = float(payload.get("orf_fdr_max") if payload.get("orf_fdr_max") is not None else 0.05)
            except (TypeError, ValueError):
                fdr_max = 0.05
            try:
                min_abs_dpsi = float(payload.get("orf_min_abs_dpsi") if payload.get("orf_min_abs_dpsi") is not None else 0.1)
            except (TypeError, ValueError):
                min_abs_dpsi = 0.1

            out_name = "splice_orfs_selected.tsv" if orf_event_ids else "splice_orfs.tsv"
            out_path = directory / out_name

            def _orf_cb(done: int, total: int, label: str) -> None:
                frac = (done / max(1, total))
                _report(int(5 + frac * 35), f"[1/3] 自动重建跨连接点 ORF：{label}")

            try:
                manifest = build_orf_table(
                    directory, out_path, provider=provider,
                    event_ids=orf_event_ids or None,
                    fdr_max=fdr_max, min_abs_dpsi=min_abs_dpsi,
                    max_events=max_events, time_budget=180.0,
                    progress_cb=_orf_cb,
                )
            except (ValueError, OSError, RuntimeError) as error:
                raise HTTPException(status_code=422, detail=f"自动重建编码序列失败：{error}") from error
            orf_summary = {
                "output_name": out_name,
                "reference": manifest["reference"],
                "genome_build": manifest["genome_build"],
                "event_count": manifest["event_count"],
                "written": manifest["written"],
                "skipped_count": len(manifest.get("skipped") or []),
                "skipped": (manifest.get("skipped") or [])[:20],
            }
            if not manifest["written"]:
                reasons: dict[str, int] = {}
                for item in manifest.get("skipped") or []:
                    key = str(item.get("reason") or "skipped")
                    reasons[key] = reasons.get(key, 0) + 1
                reason_text = "、".join(f"{k}({v})" for k, v in reasons.items()) or "无可用编码区事件"
                raise HTTPException(
                    status_code=422,
                    detail=f"自动重建 ORF 未能生成可用编码序列（共检查 {manifest['event_count']} 个事件，跳过原因：{reason_text}）。",
                )
            return out_path.resolve()

        cds_path: Path | None = None
        peptides_path: Path | None = None
        if cds_value and not force_rebuild_orf and not orf_event_ids:
            cds_path = input_file(cds_value, "cds_table")
        elif peptides_value:
            peptides_path = input_file(peptides_value, "peptides_file")
        else:
            if orf_event_ids or force_rebuild_orf:
                cds_path = _auto_build_cds()
            elif not project_id:
                raise HTTPException(status_code=422, detail="需要提供 cds_table 或 peptides_file")
            else:
                from epitoperank.neoantigen import discover_cds_tables

                detected = discover_cds_tables(*roots)
                if detected:
                    cds_path = detected[0]["path"].resolve()
                elif auto_build_orf:
                    cds_path = _auto_build_cds()
                else:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            "当前项目里还没找到编码序列表。需要一份包含 event_id、reference_cds、altered_cds、"
                            "junction_nt 四列的表（TSV/CSV/TXT，文件名不限），上传后即可生成候选肽。"
                        ),
                    )

        raw_fastas = payload.get("self_fastas") or []
        if not isinstance(raw_fastas, list):
            raise HTTPException(status_code=422, detail="self_fastas 必须为路径列表")
        self_fastas = [str(input_file(item, "self_fastas")) for item in raw_fastas]
        raw_alleles = payload.get("alleles") or []
        if not isinstance(raw_alleles, list):
            raise HTTPException(status_code=422, detail="alleles 必须为列表")
        alleles = [str(item).strip() for item in raw_alleles if str(item).strip()]
        mhc_class = str(payload.get("mhc_class") or "both")
        predictor = str(payload.get("predictor") or "iedb")
        if mhc_class not in {"class1", "class2", "both"}:
            raise HTTPException(status_code=422, detail="mhc_class 必须为 class1、class2 或 both")
        if predictor not in {"iedb", "local", "auto", "none"}:
            raise HTTPException(status_code=422, detail="predictor 必须为 iedb、local、auto 或 none")
        try:
            class2_window = int(payload.get("class2_window") or 15)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="class2_window 必须为整数") from None
        try:
            max_predictions = max(1, min(20000, int(payload.get("max_predictions") or 2000)))
        except (TypeError, ValueError):
            max_predictions = 2000
        options = PeptideOptions(
            alleles=alleles,
            mhc_class=mhc_class,
            predictor=predictor,
            processing=bool(payload.get("processing", True)),
            self_fastas=self_fastas,
            class2_window=class2_window,
            max_predictions=max_predictions,
            lookup_epitopes=bool(payload.get("lookup_epitopes", False)),
        )
        results_base = settings.paths.runtime_root / "projects" / project_id if project_id else directory
        col_map = _mapping_for(cds_path, payload.get("column_map"), roots) if cds_path is not None else None
        def _pipe_cb(stage: str, done: int, total: int, msg: str) -> None:
            if stage == "candidates":
                _report(42, f"[2/3] {msg}")
            elif stage == "iedb":
                frac = done / max(1, total)
                _report(int(45 + frac * 45), f"[2/3] {msg}")
            elif stage == "ranking":
                _report(93, f"[3/3] {msg}")

        try:
            result = run_peptides(
                output_dir=results_base / "peptide_results",
                input_dir=directory if cds_path is not None else None,
                cds_table=cds_path,
                peptides=peptides_path,
                options=options,
                column_map=col_map,
                progress_cb=_pipe_cb,
            )
        except (ValueError, OSError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        result["results_input_dir"] = str(results_base)
        if cds_path is not None:
            result["cds_table_name"] = cds_path.name
        if orf_summary is not None:
            result["orf_summary"] = orf_summary
        return result

    @app.post("/api/peptide/run")
    def peptide_run(payload: dict[str, Any]) -> dict[str, Any]:
        """Generate splice-derived candidates, predict, filter and rank peptides."""
        return _execute_peptide_run(payload)

    @app.get("/api/peptide/results/{project_id}")
    def peptide_saved_results(project_id: str) -> dict[str, Any]:
        """Load previously saved peptide/neoantigen results for a project if available."""
        from epitoperank.peptide.pipeline import load_saved_result

        pid = str(project_id or "").strip()
        if not pid:
            return {"available": False}
        results_base = settings.paths.runtime_root / "projects" / pid
        saved = load_saved_result(results_base / "peptide_results")
        if saved is None:
            return {"available": False}
        saved["available"] = True
        saved["results_input_dir"] = str(results_base)
        return saved

    @app.post("/api/peptide/job/start")
    def peptide_job_start(payload: dict[str, Any]) -> dict[str, Any]:
        """Start an asynchronous neoantigen screening job with live progress."""
        import time as _time
        import uuid

        project_id = str(payload.get("project_id") or "").strip()
        with _peptide_jobs_lock:
            if project_id:
                for existing in _peptide_jobs.values():
                    if existing.get("project_id") == project_id and existing.get("state") == "running":
                        return {
                            "job_id": existing["job_id"],
                            "state": "running",
                            "percent": existing["percent"],
                            "stage": existing["stage"],
                        }
            job_id = uuid.uuid4().hex[:16]
            job: dict[str, Any] = {
                "job_id": job_id,
                "project_id": project_id,
                "state": "running",
                "percent": 2,
                "stage": "正在初始化新抗原筛选任务…",
                "started_at": _time.monotonic(),
                "result": None,
                "error": None,
            }
            _peptide_jobs[job_id] = job

        def _worker() -> None:
            def _hook(pct: int, msg: str) -> None:
                with _peptide_jobs_lock:
                    job["percent"] = pct
                    job["stage"] = msg

            try:
                res = _execute_peptide_run(dict(payload), progress_hook=_hook)
                with _peptide_jobs_lock:
                    job["percent"] = 100
                    job["stage"] = "筛选完成"
                    job["result"] = res
                    job["state"] = "completed"
            except HTTPException as exc:
                with _peptide_jobs_lock:
                    job["error"] = str(exc.detail)
                    job["state"] = "failed"
            except Exception as exc:  # noqa: BLE001
                with _peptide_jobs_lock:
                    job["error"] = str(exc)
                    job["state"] = "failed"

        threading.Thread(target=_worker, name=f"pep-job-{job_id[:6]}", daemon=True).start()
        return {"job_id": job_id, "state": "running", "percent": 2, "stage": job["stage"]}

    @app.get("/api/peptide/job/active/{project_id}")
    def peptide_job_active(project_id: str) -> dict[str, Any]:
        import time as _time

        pid = str(project_id or "").strip()
        with _peptide_jobs_lock:
            for job in _peptide_jobs.values():
                if job.get("project_id") == pid and job.get("state") == "running":
                    return {
                        "active": True,
                        "job_id": job["job_id"],
                        "state": job["state"],
                        "percent": job["percent"],
                        "stage": job["stage"],
                        "elapsed_sec": round(_time.monotonic() - float(job["started_at"]), 1),
                    }
        return {"active": False}

    @app.get("/api/peptide/job/{job_id}")
    def peptide_job_status(job_id: str) -> dict[str, Any]:
        import time as _time

        with _peptide_jobs_lock:
            job = _peptide_jobs.get(str(job_id or "").strip())
            if not job:
                raise HTTPException(status_code=404, detail="未找到筛选任务")
            return {
                "job_id": job["job_id"],
                "project_id": job["project_id"],
                "state": job["state"],
                "percent": job["percent"],
                "stage": job["stage"],
                "elapsed_sec": round(_time.monotonic() - float(job["started_at"]), 1),
                "result": job["result"] if job["state"] == "completed" else None,
                "error": job["error"],
            }

    @app.get("/api/peptide/file")
    # 中文备注：HTTP 接口：GET /api/peptide/file（参数：input_dir、name）
    def peptide_file(input_dir: str, name: str) -> FileResponse:
        """Download one whitelisted peptide result file."""
        directory = _ingest_input_dir(input_dir)
        allowed = {
            "splice_peptides.tsv",
            "mhc_predictions.tsv",
            "ranked_candidates.tsv",
            "epitope_matches.tsv",
            "manifest.json",
            "summary.md",
        }
        if name not in allowed:
            raise HTTPException(status_code=400, detail="无效结果文件")
        path = directory / "peptide_results" / name
        if not path.is_file():
            raise HTTPException(status_code=404, detail="结果文件不存在")
        return FileResponse(path, filename=name)

    @app.post("/api/upload")
    # 中文备注：HTTP 接口：POST /api/upload（参数：files）
    async def upload(files: list[UploadFile] = File(...)) -> dict[str, Any]:
        """Upload analysis input files into a new staging directory."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Received {len(files)} files in request")
        logger.info(f"Files type: {type(files)}")
        for idx, f in enumerate(files):
            logger.info(f"  File {idx}: {f.filename}, content_type={f.content_type}")
        
        if not files:
            logger.error("No files found in form data")
            raise HTTPException(status_code=400, detail="No files provided")
        
        try:
            staging = Path(tempfile.mkdtemp(prefix="epitoperank_upload_", dir=str(settings.paths.runtime_root)))
            logger.info(f"Created staging directory: {staging}")
            
            uploaded_files = []
            seen_names: set[str] = set()
            for idx, upload in enumerate(files):
                if not upload.filename:
                    logger.warning(f"File {idx} has no filename, skipping")
                    continue
                    
                filename = Path(upload.filename).name
                if filename.lower() in seen_names:
                    raise HTTPException(status_code=422, detail=f"Duplicate uploaded filename: {filename}")
                seen_names.add(filename.lower())
                destination = staging / filename
                logger.info(f"Saving file {idx+1}/{len(files)}: {upload.filename} ({upload.content_type}) -> {destination}")
                
                with destination.open("wb") as handle:
                    size = 0
                    while chunk := await upload.read(1024 * 1024):
                        handle.write(chunk)
                        size += len(chunk)
                    logger.info(f"Saved {size} bytes to {destination}")
                
                uploaded_files.append(upload.filename)
            
            logger.info(f"Upload complete: {len(uploaded_files)} files saved to {staging}")
            return {"upload_dir": str(staging), "files": uploaded_files}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from e
    
    @app.get("/api/report/{project_id}")
    def report(project_id: str, format: str = "html") -> Any:
        """返回项目的 HTML/PDF 报告：先查产物表登记的路径，再退回项目目录下的约定位置。"""
        payload = project_status(project_id, settings)
        if payload is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        from epitoperank.report.antigens import append_html, append_pdf, load_sections

        extension = "pdf" if format.lower() == "pdf" else "html"
        media = "application/pdf" if extension == "pdf" else "text/html"
        # 1) the stored artifact, 2) the conventional location inside the
        # project folder — the second one survives a runtime-root migration
        # even when the database still carries an old absolute path.
        candidates: list[Path] = [
            Path(artifact["path"])
            for artifact in payload["artifacts"]
            if artifact["kind"] == f"report:{extension}"
        ]
        project_dir = settings.paths.runtime_root / "projects" / project_id
        candidates.append(project_dir / f"report.{extension}")
        for candidate in candidates:
            if candidate.is_file():
                recorded_source = payload["project"].get("source_dir")
                sections = load_sections(project_dir, Path(recorded_source) if recorded_source else None)
                content = (append_pdf(candidate, sections) if extension == "pdf"
                           else append_html(candidate.read_text(encoding="utf-8"), sections))
                return Response(content, media_type=media, headers={"Cache-Control": "no-store"})
        raise HTTPException(status_code=404, detail=f"No {extension} report for project {project_id}")

    # ==================== Skills Endpoints ====================

    @app.get("/api/figure/{project_id}/{figure_name}")
    def figure(project_id: str, figure_name: str) -> Any:
        """返回项目图表；先查项目 figures 目录与产物记录，缺图时按需现画再返回。"""
        safe_name = Path(figure_name).stem
        for extension in (".png", ".svg"):
            candidate = settings.paths.runtime_root / "projects" / project_id / "figures" / f"{safe_name}{extension}"
            if candidate.is_file() and candidate.stat().st_size:
                return FileResponse(candidate)
        payload = project_status(project_id, settings)
        if payload is not None:
            for artifact in payload["artifacts"]:
                path = Path(artifact["path"])
                if artifact["kind"] == f"figure:{safe_name}" and path.is_file() and path.stat().st_size:
                    return FileResponse(artifact["path"])
            target_dir = settings.paths.runtime_root / "projects" / project_id / "figures"
            try:
                if safe_name in visualization.FIGURE_SPECS:
                    from epitoperank.analysis.project_figures import build_figure
                    from epitoperank.memory.project_memory import ProjectMemory

                    memory = ProjectMemory(settings.paths.memory_db)
                    result = build_figure(safe_name, memory, payload["project"], target_dir, settings.analysis)
                    if result is not None:
                        memory.save_artifact(project_id, f"figure:{safe_name}", result.png_path)
                        return FileResponse(result.png_path)
                elif safe_name in extra_figures.ON_DEMAND_FIGURES:
                    generated = _build_on_demand_figure(safe_name, payload, target_dir)
                    if generated is not None and generated.is_file():
                        return FileResponse(generated)
            except Exception as exc:
                logger.exception("On-demand figure %s failed for %s", safe_name, project_id)
                raise HTTPException(status_code=500, detail="Figure rendering failed") from exc
        raise HTTPException(status_code=404, detail=f"Figure {figure_name} not found")

    return app


# 中文备注：Web 接口：构建ondemand图表（参数：name、payload、target_dir）
def _build_on_demand_figure(name: str, payload: dict[str, Any], target_dir: Path) -> Path | None:
    """Generate a lazy figure from persisted project state."""
    candidates = payload.get("candidates") or []
    samples = payload.get("samples") or []
    if name == "dpsi_waterfall":
        return extra_figures.plot_dpsi_waterfall(candidates, target_dir)
    if name == "dpsi_ecdf":
        return extra_figures.plot_dpsi_ecdf(candidates, target_dir)
    if name == "fdr_scree":
        return extra_figures.plot_fdr_scree(candidates, target_dir)
    if name == "event_significance":
        return extra_figures.plot_event_significance(candidates, target_dir)
    if name == "score_components":
        return extra_figures.plot_score_components(candidates, target_dir)
    if name == "sample_composition":
        return extra_figures.plot_sample_composition(samples, target_dir)
    if name == "event_schematic":
        return extra_figures.plot_event_schematic(target_dir)
    return None


app = create_app()
