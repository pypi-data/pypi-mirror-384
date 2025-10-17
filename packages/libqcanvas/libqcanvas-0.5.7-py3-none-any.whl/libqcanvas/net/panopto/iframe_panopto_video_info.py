from pydantic import BaseModel, Field


class IFramePanoptoVideoInfo(BaseModel):
    delivery_id: str = Field(alias="DeliveryId")
    viewer_link: str = Field(alias="ViewerLink")
    thumb_url: str = Field(alias="ThumbUrl")
