from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import date

PrimaryBU = Literal[
    "Chemistry Services",
    "ClinPharma Services",
    "Bioinformatics Services",
    "Scientific Products",
    "Cross-BU",
]

AssetType = Literal[
    "Dataset",
    "Model",
    "Pipeline",
    "Library",
    "App/UI",
    "Benchmark",
    "Ontology",
    "Paper/Reference",
]

LicenseFlag = Literal["Green", "Yellow", "Red"]

class Asset(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=2)
    short_summary: str = Field(..., min_length=10)
    url: str = Field(..., min_length=5)

    primary_bu: PrimaryBU
    secondary_bus: List[PrimaryBU] = Field(default_factory=list)

    use_cases: List[str] = Field(default_factory=list)
    asset_type: AssetType

    license_flag: LicenseFlag = "Yellow"
    license_notes: str = ""

    readiness_score: int = Field(3, ge=0, le=5)
    engineering_score: int = Field(3, ge=0, le=5)
    maintenance_score: int = Field(3, ge=0, le=5)

    last_validated_on: Optional[date] = None
    owner: str = ""  # SME name/team
    notes: str = ""
