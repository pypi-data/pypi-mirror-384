from typing import Literal

type SearchType = Literal["web", "image", "video", "news", "discover", "googleNews"]
type AggregationType = Literal["auto", "byPage", "byProperty", "byNewsShowcasePanel"]
type Dimension = Literal["query", "page", "country", "device", "searchAppearance"]