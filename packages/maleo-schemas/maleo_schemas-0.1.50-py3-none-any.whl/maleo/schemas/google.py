from google.cloud.pubsub_v1 import PublisherClient
from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class PubslisherHandler(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: Annotated[PublisherClient, Field(..., description="Publisher client")]
    project_id: Annotated[str, Field(..., description="Project ID")]
    topic_id: Annotated[str, Field(..., description="Topic ID")]
