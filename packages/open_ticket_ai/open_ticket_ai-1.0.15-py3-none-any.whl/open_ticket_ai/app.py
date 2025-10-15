import tomllib
from pathlib import Path

import pyfiglet
from injector import inject

from open_ticket_ai.core.config.config_models import RawOpenTicketAIConfig
from open_ticket_ai.core.logging_iface import LoggerFactory
from open_ticket_ai.core.orchestration.orchestrator import Orchestrator


def get_project_info() -> dict[str, str]:
    pyproject_path = Path("../../pyproject.toml")

    defaults = {
        "name": "Open Ticket AI",
        "version": "unknown",
        "license": "Not specified",
        "author_name": "Unknown",
        "author_email": "Unknown",
        "homepage": "Not specified",
    }

    if not pyproject_path.exists():
        return defaults

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project_data = data.get("project", {})

    authors = project_data.get("authors", [{}])
    author_name = authors[0].get("name", defaults["author_name"])
    author_email = authors[0].get("email", defaults["author_email"])

    license_info = project_data.get("license", {}).get("text", defaults["license"])

    homepage = project_data.get("urls", {}).get("Homepage", defaults["homepage"])

    return {
        "name": project_data.get("name", defaults["name"]),
        "version": project_data.get("version", defaults["version"]),
        "license": license_info,
        "author_name": author_name,
        "author_email": author_email,
        "homepage": homepage,
    }


class OpenTicketAIApp:
    @inject
    def __init__(self, config: RawOpenTicketAIConfig, orchestrator: Orchestrator, logger_factory: LoggerFactory):
        self.config = config
        self.orchestrator = orchestrator

        self._logger = logger_factory.get_logger(self.__class__.__name__)
        self.print_info()

    def print_info(self) -> None:
        project_info = get_project_info()
        banner = pyfiglet.figlet_format(project_info["name"])
        print(banner)
        self._logger.info(f" Version: {project_info['version']}")
        self._logger.info(f" License: {project_info['license']}")
        self._logger.info(f" Author:  {project_info['author_name']} <{project_info['author_email']}>")
        self._logger.info(f" Website: {project_info['homepage']}\n")

    async def run(self) -> None:
        self._logger.info("🚀 Starting Open Ticket AI orchestration...")
        self._logger.info(f"📦 Loaded {len(self.config.services)} services")
        self._logger.info(f"🔧 Orchestrator has {len(self.config.orchestrator.runners)} runners\n")

        try:
            await self.orchestrator.run()
        except KeyboardInterrupt:
            self._logger.info("\n⚠️  Shutdown requested...")
            self.orchestrator.stop()

        self._logger.info("✅ Orchestration complete")
