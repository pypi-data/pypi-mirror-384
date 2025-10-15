from typing import Any

from injector import inject
from jinja2.sandbox import SandboxedEnvironment

from open_ticket_ai.base.template_renderers.jinja_renderer_extras import (
    at_path,
    build_filtered_env,
    has_failed,
    get_pipe_result,
)
from open_ticket_ai.core.logging_iface import LoggerFactory
from open_ticket_ai.core.template_rendering.renderer_config import JinjaRendererConfig
from open_ticket_ai.core.template_rendering.template_renderer import TemplateRenderer


class JinjaRenderer(TemplateRenderer):
    @inject
    def __init__(self, config: JinjaRendererConfig, logger_factory: LoggerFactory):
        super().__init__(logger_factory)
        self._config = JinjaRendererConfig.model_validate(config.model_dump())
        self.jinja_env = SandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)

    def render(self, template_str: str, scope: dict[str, Any]) -> Any:
        self.jinja_env.globals.update(scope)
        self.jinja_env.globals["at_path"] = at_path
        self.jinja_env.globals["env"] = build_filtered_env()
        self.jinja_env.globals["has_failed"] = has_failed
        self.jinja_env.globals["get_pipe_result"] = get_pipe_result
        template = self.jinja_env.from_string(template_str)
        rendered = template.render(self._to_dict(scope))
        return self._parse_rendered_value(rendered)
