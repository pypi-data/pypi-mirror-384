from pydantic import ConfigDict, Field, computed_field
from pydantic_settings import BaseSettings


class ClientConfig(BaseSettings):
    model_config = ConfigDict(
        env_prefix="AGENTCI_",
    )

    client_base_path: str = Field(
        default=".agentci",
        description="Base path name for AgentCI configuration in a project",
    )

    @computed_field
    @property
    def evaluation_path_name(self) -> str:
        return f"{self.client_base_path}/evals"


config = ClientConfig()
