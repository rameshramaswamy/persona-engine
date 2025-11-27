from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

class PromptEngine:
    def __init__(self, template_dir: str = "src/templates"):
        path = Path(__file__).parent.parent.parent / "src/templates"
        # OPTIMIZATION: Enable async mode
        self.env = Environment(
            loader=FileSystemLoader(path),
            autoescape=select_autoescape(),
            enable_async=True 
        )

    async def build_prompt(self, template_name: str, **kwargs) -> str:
        """
        Renders template asynchronously. 
        Crucial when 'context_data' becomes large (RAG results).
        """
        try:
            template = self.env.get_template(template_name)
            # OPTIMIZATION: render_async yields to event loop
            return await template.render_async(**kwargs)
        except Exception as e:
            raise ValueError(f"Error rendering template {template_name}: {str(e)}")