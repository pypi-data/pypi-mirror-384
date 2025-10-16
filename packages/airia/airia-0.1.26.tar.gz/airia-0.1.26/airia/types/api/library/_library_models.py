from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TokenPriceConversion(BaseModel):
    """
    Common conversion values for token prices.

    Attributes:
        input_token_price_1k: Cost per 1,000 input tokens in USD. Pre-calculated for convenience when comparing pricing across models.
        output_token_price_1k: Cost per 1,000 output tokens in USD. Pre-calculated for convenience when comparing pricing across models.
        input_token_price_1m: Cost per 1 million input tokens in USD. Useful for large-scale usage estimation and enterprise planning.
        output_token_price_1m: Cost per 1 million output tokens in USD. Useful for large-scale usage estimation and enterprise planning.
    """

    input_token_price_1k: Optional[str] = Field(
        None,
        alias="inputTokenPrice1K",
        description="Gets or sets the input token cost.",
    )
    output_token_price_1k: Optional[str] = Field(
        None,
        alias="outputTokenPrice1K",
        description="Gets or sets the output token cost.",
    )
    input_token_price_1m: Optional[str] = Field(
        None,
        alias="inputTokenPrice1M",
        description="Gets or sets the input token cost per million tokens.",
    )
    output_token_price_1m: Optional[str] = Field(
        None,
        alias="outputTokenPrice1M",
        description="Gets or sets the output token cost per million tokens.",
    )


class LibraryModel(BaseModel):
    """
    Models response for the library.

    Attributes:
        credentials_id: UUID of the required credentials to use this model. None if no specific credentials needed.
        id: Unique identifier for the library model. Used in API calls to specify which model to use.
        category: Model category (e.g., "Multimodal", "NLP", "ComputerVision"). Helps classify model capabilities.
        description: Detailed description of the model's purpose, capabilities, and use cases.
        downloads: Number of times this model has been downloaded. Indicates popularity and usage.
        type: Input type the model accepts (e.g., "text", "image", "audio", "video").
        languages: List of languages the model supports. Important for international applications.
        license_type: License under which the model is distributed (e.g., "MIT", "Apache20", "Commercial").
        name: Internal name of the model. Used for identification and API references.
        display_name: Human-readable name for display in UIs. More user-friendly than internal name.
        price: General pricing information as a string. May include currency and billing details.
        input_token_price: Cost per input token. Used for precise cost calculation.
        output_token_price: Cost per output token. Used for precise cost calculation.
        price_type: Type of pricing model (e.g., "AITextOutputModelPrice", "AIImageOutputModelPrice").
        prompt_id: UUID of associated prompt template if applicable.
        url: URL to model documentation, homepage, or additional information.
        provider: Company or organization that provides the model (e.g., "OpenAI", "Anthropic", "Google").
        rating: Average user rating of the model (typically 1-5 scale). Indicates user satisfaction.
        tags: List of descriptive tags for categorization and search. Helps discovery and filtering.
        available: Whether the model is currently available for use. False if deprecated or temporarily unavailable.
        token_price_conversion: Pre-calculated pricing conversions for different token quantities.
        allow_airia_credentials: Whether the model can be used with Airia-managed credentials.
        allow_byok_credentials: Whether the model supports Bring Your Own Key (BYOK) credentials.
        author: Person or organization who created or maintains the model.
        license_link: Direct URL to the full license text or terms of service.
        released_at: Date when the model was first released or made available.
        deprecated_at: Date when the model was deprecated. None if still active.
        is_open_source: Whether the model is open source. Important for compliance and transparency.
        chat_specialized: Whether the model is optimized for conversational/chat use cases.
        industry: Primary industry or domain the model is designed for.
        commercial_use: Whether the model can be used for commercial purposes.
        certifications: List of compliance certifications (e.g., "SOC2", "HIPAA", "ISO 27001").
        has_tool_support: Whether the model supports tool calling/function calling capabilities.
        has_stream_support: Whether the model supports streaming responses for real-time output.
        context_window: Maximum number of tokens the model can process in a single request.
        max_output_tokens: Maximum number of tokens the model can generate in a single response.
        state: Current operational state of the model (e.g., "active", "deprecated", "beta").
    """

    credentials_id: Optional[UUID] = Field(
        None,
        alias="credentialsId",
        description="Gets or sets the required Credentials ID for the model.",
    )
    id: Optional[UUID] = Field(
        None, description="Gets or sets the library model identifier."
    )
    category: Optional[str] = Field(None, description="Gets or sets the category.")
    description: Optional[str] = Field(
        None, description="Gets or sets the description of the library model."
    )
    downloads: int = Field(
        description="Gets or sets the number of times this model has been downloaded."
    )
    type: str = Field(description="Gets the input type of the model.")
    languages: List[str] = Field(
        description="Gets or sets the languages this model supports."
    )
    license_type: Optional[str] = Field(
        None, alias="licenseType", description="Gets or sets the license of this model."
    )
    name: Optional[str] = Field(
        None,
        description="Gets the name of the library model.",
        examples=["CHATGPT-4o, CHATGPT-4Turbo."],
    )
    display_name: Optional[str] = Field(
        None,
        alias="displayName",
        description="Gets the display name of the library model.",
    )
    price: str = Field(description="Gets or sets the price.")
    input_token_price: Optional[str] = Field(
        None, alias="inputTokenPrice", description="Gets or sets the input token cost."
    )
    output_token_price: Optional[str] = Field(
        None,
        alias="outputTokenPrice",
        description="Gets or sets the output token cost.",
    )
    price_type: str = Field(alias="priceType", description="Gets the price type.")
    prompt_id: Optional[UUID] = Field(
        None, alias="promptId", description="Gets the PromptId."
    )
    url: Optional[str] = Field(None, description="Gets the Url.")
    provider: Optional[str] = Field(None, description="Gets the provider of the model.")
    rating: int = Field(
        description="Gets or sets the average user rating of the model."
    )
    tags: List[str] = Field(description="Gets or sets the related tags.")
    available: bool = Field(
        description="Gets or sets a value indicating whether the model is available."
    )
    token_price_conversion: Optional[TokenPriceConversion] = Field(
        None,
        alias="tokenPriceConversion",
        description="Gets or sets common token price conversion values.",
    )
    allow_airia_credentials: bool = Field(
        alias="allowAiriaCredentials",
        description="Gets or sets a value indicating whether the model is allowed to use the Airia Credentials.",
    )
    allow_byok_credentials: bool = Field(
        alias="allowBYOKCredentials",
        description="Gets or sets a value indicating whether the model is allowed to use BYOK Credentials.",
    )
    author: str = Field(description="Gets or sets the author of the model.")
    license_link: Optional[str] = Field(
        None,
        alias="licenseLink",
        description="Gets or sets a direct link to the license for the model.",
    )
    released_at: Optional[datetime] = Field(
        None,
        alias="releasedAt",
        description="Gets or sets the date the model was released.",
    )
    deprecated_at: Optional[datetime] = Field(
        None,
        alias="deprecatedAt",
        description="Gets or sets the date the model was deprecated.",
    )
    is_open_source: bool = Field(
        alias="isOpenSource",
        description="Gets or sets a value indicating whether the model is open source.",
    )
    chat_specialized: bool = Field(
        alias="chatSpecialized",
        description="Gets or sets a value indicating whether the model is chat specialized.",
    )
    industry: str = Field(description="Gets or sets the industry.")
    commercial_use: bool = Field(
        alias="commercialUse",
        description="Gets or sets a value indicating whether the model is for commercial use.",
    )
    certifications: Optional[List[str]] = Field(
        None, description="Gets or sets the certifications."
    )
    has_tool_support: bool = Field(
        alias="hasToolSupport",
        description="Gets a value indicating whether the model has tool support.",
    )
    has_stream_support: bool = Field(
        alias="hasStreamSupport",
        description="Gets a value indicating whether the model supports response streaming.",
    )
    context_window: int = Field(
        alias="contextWindow",
        description="Gets the context window size for this model.",
    )
    max_output_tokens: int = Field(
        alias="maxOutputTokens",
        description="Gets the maximum number of tokens that can be generated by the model.",
    )
    state: str = Field(description="Gets or sets the state of the model.")


class GetLibraryModelsResponse(BaseModel):
    """
    A response for getting library models.

    Attributes:
        models: List of LibraryModel objects containing detailed information about each available model.
        total_count: Total number of models matching the query criteria, useful for pagination calculations.
    """

    models: List[LibraryModel] = Field(
        description="Gets or sets Models that the library allows provisioning."
    )
    total_count: int = Field(
        alias="totalCount",
        description="Gets or sets the total count of models in the library.",
    )
