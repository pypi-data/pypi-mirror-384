import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class BuildHook(BuildHookInterface):  # type: ignore
    """Ensure packaged frontend assets exist in src/frontend_dist before build.

    Behavior:
    - If src/frontend_dist/index.html exists, do nothing.
    - Else if frontend/dist/index.html exists, copy it to src/frontend_dist/.
    - Else raise a clear error instructing to run `make build_package` first.
      We intentionally DO NOT run npm during packaging to avoid assuming it
      on build/install environments.
    """

    def initialize(self, version: str, build_data: dict) -> None:  # noqa: D401 # type: ignore
        # For editable builds, just return without doing anything
        # This prevents failures during `uv sync` in CI environments
        if version == "editable":
            return

        # For wheel and sdist builds, ensure frontend assets and canonical DXT are present
        self._ensure_frontend_assets()
        self._ensure_canonical_dxt()

    def _ensure_frontend_assets(self) -> None:
        """Ensure frontend assets are available for packaging."""
        project_root = Path(self.root)
        src_frontend_dist = project_root / "src" / "frontend_dist"
        repo_frontend_dist = project_root / "frontend" / "dist"

        # Always ensure frontend assets are available for packaging
        # Fast path: already present in src/ with actual content
        if (src_frontend_dist / "index.html").exists():
            self.app.display_info("frontend_dist already present; skipping build/copy")
            return

        # Copy from repo frontend/dist if present
        if (repo_frontend_dist / "index.html").exists():
            if src_frontend_dist.exists():
                shutil.rmtree(src_frontend_dist)
            shutil.copytree(repo_frontend_dist, src_frontend_dist)
            self.app.display_info("Copied frontend/dist -> src/frontend_dist for packaging")
            return

        # If we reach here, neither src/frontend_dist nor frontend/dist exist
        # This should fail the build as requested
        raise RuntimeError(
            "Packaged dashboard (src/frontend_dist) missing and frontend/dist not found. "
            "Run 'make build_package' to generate assets before packaging/uvx."
        )

    def _ensure_canonical_dxt(self) -> None:
        """Ensure the desktop extension DXT exists at the canonical path.

        Canonical path: desktop_ext/open-edison-connector.dxt
        If absent but desktop_ext/desktop_ext.dxt exists, copy it to the canonical path.
        Otherwise, fail with a clear message.
        """
        project_root = Path(self.root)
        canonical = project_root / "desktop_ext" / "open-edison-connector.dxt"
        legacy = project_root / "desktop_ext" / "desktop_ext.dxt"

        if canonical.exists():
            return

        if legacy.exists():
            shutil.copyfile(legacy, canonical)
            self.app.display_info(
                "Copied desktop_ext/desktop_ext.dxt -> desktop_ext/open-edison-connector.dxt"
            )
            return

        raise RuntimeError(
            "Required desktop extension missing: desktop_ext/open-edison-connector.dxt. "
            "Either commit it or provide desktop_ext/desktop_ext.dxt so it can be copied."
        )
