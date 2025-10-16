from amsdal.contrib.app_config import AppConfig


class AmsdalWorkflowAppConfig(AppConfig):
    name = 'amsdal_workflow'
    verbose_name = 'AMSDAL Workflow Plugin'

    def on_ready(self) -> None: ...
