from typing import List, Optional, Union
from pydantic import BaseModel, Field


class FacetValue(BaseModel):
    count: int
    value: Optional[Union[str, bool]] = None
    label: Union[str, bool]


class Facet(BaseModel):
    key: str
    value: List[FacetValue]
    is_collection: Optional[bool] = False
    translate: bool


class SearchStocks(BaseModel):
    warehouse: str
    quantity: int
    reserved: int


class SearchPrices(BaseModel):
    price_list_id: int = Field(..., alias='priceListId')
    price_list: str = Field(..., alias='priceList') 
    amount: float
    currency: str


class SearchIntegration(BaseModel):
    app: Optional[int] = None
    integration_id: Optional[str] = Field(None, alias='integrationId')
    permalink: Optional[str] = None
    status: Optional[str] = None
    listing_type: Optional[str] = Field(None, alias='listingType')
    safety_stock: Optional[int] = Field(None, alias='safetyStock')
    synchronize_stock: Optional[bool] = Field(None, alias='synchronizeStock')
    is_active: Optional[bool] = Field(None, alias='isActive')
    is_active_or_paused: Optional[bool] = Field(None, alias='isActiveOrPaused')
    id: Optional[int] = None


class SearchDeals(BaseModel):
    campaign: str
    product: int
    variation: str
    deal_price: float
    discount: float
    regular_price: float
    enabled: bool
    currency: str
    id: str


class SearchResultItem(BaseModel):
    search_score: float = Field(..., alias='@search.score')
    id: int
    product_id: int = Field(..., alias='productId')
    company_id: int = Field(..., alias='companyId')
    name: str
    code: str
    skus: List[str]
    brand: str
    category: str
    thumbnail: str
    stocks: List[SearchStocks]
    warehouses_with_stock: List[str] = Field(..., alias='warehousesWithStock')
    total_stock: int = Field(..., alias='totalStock')
    has_pictures: bool = Field(..., alias='hasPictures')
    buying_price: float = Field(..., alias='buyingPrice')
    prices: List[SearchPrices]
    integration_ids: List[str] = Field(..., alias='integrationIds')
    integration_apps: List[str] = Field(..., alias='integrationApps')
    integrations: List[SearchIntegration]
    campaigns: List[str]
    app: Optional[int] = None
    status: Optional[str] = None
    synchronize_stock: Optional[bool] = Field(None, alias='synchronizeStock')
    listing_type: Optional[str] = Field(None, alias='listingType')
    price_amount: Optional[float] = Field(None, alias='priceAmount')
    price_currency: Optional[str] = Field(None, alias='priceCurrency')
    category_id: Optional[str] = Field(None, alias='categoryId')
    category_base_id: Optional[str] = Field(None, alias='categoryBaseId')
    category_l1: Optional[str] = Field(None, alias='categoryL1')
    category_l2: Optional[str] = Field(None, alias='categoryL2')
    category_l3: Optional[str] = Field(None, alias='categoryL3')
    category_l4: Optional[str] = Field(None, alias='categoryL4')
    category_l5: Optional[str] = Field(None, alias='categoryL5')
    category_l6: Optional[str] = Field(None, alias='categoryL6')
    has_category: Optional[bool] = Field(None, alias='hasCategory')
    category_fixed: Optional[bool] = Field(None, alias='categoryFixed')
    accepts_mercadoenvios: Optional[bool] = Field(None, alias='acceptsMercadoenvios')
    shipping_mode: Optional[str] = Field(None, alias='shippingMode')
    local_pickup: Optional[bool] = Field(None, alias='localPickup')
    mandatory_free_shipping: Optional[bool] = Field(None, alias='mandatoryFreeShipping')
    free_shipping: Optional[bool] = Field(None, alias='freeShipping')
    free_shipping_cost: Optional[float] = Field(None, alias='freeShippingCost')
    template: Optional[str] = None
    youtube_id: Optional[str] = Field(None, alias='youtubeId')
    warranty: Optional[str] = None
    permalink: Optional[str] = None
    domain: Optional[str] = None
    attribute_completion_status: Optional[str] = Field(None, alias='attributeCompletionStatus')
    attribute_completion_count: Optional[int] = Field(None, alias='attributeCompletionCount')
    attribute_completion_total: Optional[int] = Field(None, alias='attributeCompletionTotal')
    deals: Optional[SearchDeals] = None
    campaign_status: Optional[List[str]] = Field(None, alias='campaignStatus')
    size_chart: Optional[str] = Field(None, alias='sizeChart')
    channel_status: Optional[List[str]] = Field(None, alias='channelStatus')
    channel_category_l1: Optional[List[str]] = Field(None, alias='channelCategoryL1')
    channel_category_l2: Optional[List[str]] = Field(None, alias='channelCategoryL2')
    channel_category_l3: Optional[List[str]] = Field(None, alias='channelCategoryL3')
    channel_category_id: Optional[List[str]] = Field(None, alias='channelCategoryId')
    channel_synchronizes_stock: Optional[List[str]] = Field(None, alias='channelSynchronizesStock')
    channel_has_category: Optional[List[str]] = Field(None, alias='channelHasCategory')
    catalog_products_status: Optional[List[str]] = Field(None, alias='catalogProductsStatus')
    metadata: Optional[List[str]] = None
    integration_tags: Optional[List[str]] = Field(None, alias='integrationTags')
    variations_integration_ids: Optional[List[str]] = Field(None, alias='variationsIntegrationIds')
    channel_pictures_templates: Optional[List[str]] = Field(None, alias='channelPicturesTemplates')
    channel_pictures_templates_apps: Optional[List[str]] = Field(None, alias='channelPicturesTemplatesApps')


class SearchProduct(BaseModel):
    count: int
    facets: List[Facet]
    results: List[SearchResultItem]


class SearchProductParams(BaseModel):
    top: Optional[int]
    skip: Optional[int]
    filter: Optional[str] = Field(default=None, alias='$filter')
    search: Optional[str] = Field(default=None)
    sales_channel: Optional[str] = Field(default='2', alias='salesChannel')
