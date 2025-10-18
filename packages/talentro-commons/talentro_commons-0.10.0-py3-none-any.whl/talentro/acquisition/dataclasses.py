from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from ..acquisition.models import ChannelType, CampaignGoal, Campaign as CampaignModel
from ..general.dataclasses import ResolvableCompanyModel
from ..integrations.dataclasses import LinkInfo
from ..services.clients import MSClient
from ..vacancies.dataclasses import FeedInfo


# Campaign object
class CampaignInfo(ResolvableCompanyModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    name: str
    external_id: Optional[str]
    status: str
    last_sync_date: Optional[datetime]
    ad_count: int
    channel: LinkInfo
    channel_type: ChannelType
    campaign_goal: Optional[CampaignGoal]
    feed: FeedInfo
    selection_criteria: Optional[dict]

    @staticmethod
    async def resolve_object(object_id: UUID, organization_id: UUID) -> "CampaignInfo | None":
        result = await MSClient.acquisition().get(f"campaigns/{object_id}/resolve", headers={"X-Organization-ID": str(organization_id)})

        if result.status_code != 200:
            return None

        return CampaignInfo(**result.json())

    @classmethod
    async def from_model(cls: "CampaignInfo", model: CampaignModel) -> 'CampaignInfo':
        channel = await LinkInfo.resolve_object(model.channel_id, model.organization)
        feed = await FeedInfo.resolve_object(model.feed_id, model.organization)

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,
            name=model.name,
            external_id=model.external_id,
            status=model.status,
            last_sync_date=model.last_sync_date,
            ad_count=model.ad_count,
            channel=channel,
            channel_type=model.channel_type,
            campaign_goal=model.campaign_goal,
            feed=feed,
            selection_criteria=model.selection_criteria
        )


class CampaignConfig(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    name: str
    external_id: Optional[str]
    status: str
    last_sync_date: Optional[datetime]
    ad_count: int
    channel_id: UUID
    channel_type: ChannelType
    campaign_goal: Optional[CampaignGoal]
    feed_id: UUID
    selection_criteria: Optional[dict]

    @classmethod
    async def from_model(cls: "CampaignConfig", model: CampaignModel) -> 'CampaignConfig':
        return cls(**model.model_dump())
