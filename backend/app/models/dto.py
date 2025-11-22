from pydantic import BaseModel
from typing import Optional, List, Dict


class MaxDimensions(BaseModel):
    lengthStuds: Optional[int] = None
    widthStuds: Optional[int] = None
    heightPlates: Optional[int] = None


class LegoComponent(BaseModel):
    id: int
    name: str
    # category лишаємо як str, бо в json можуть бути:
    # motor, sensor, controller, power, wheel, track, manipulator, accessory, structure, water, propeller, tire, tread …
    category: str

    price: float
    weight: float
    image: Optional[str] = None

    # Опційні розширені поля (для більш складного json у майбутньому)
    lego_number: Optional[str] = None
    family: Optional[str] = None
    system_type: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = "ABS"

    geometry: Optional[Dict] = None
    connectors: Optional[List[Dict]] = None
    roles: Optional[List[str]] = None
    primary_role: Optional[str] = None

    mechanical: Optional[Dict] = None
    electronics: Optional[Dict] = None
    constraints: Optional[Dict] = None
    compatibility: Optional[Dict] = None
    scores: Optional[Dict] = None
    inventory: Optional[Dict] = None

    # Для фільтрації за “середовищем” (ground/air/water/universal) — в поточному json відсутнє, тому буде "universal"
    domain: Optional[str] = "universal"


class ConfigRequest(BaseModel):
    functions: List[str]
    subFunctions: Optional[Dict[str, str]] = {}
    budget: float
    weight: float
    priority: str
    sensors: List[str] = []

    # Нові поля опитування

    terrain: Optional[str] = None          # 'indoor' | 'outdoor_flat' | 'offroad' | 'water_pool'
    sizeClass: Optional[str] = None        # 'small' | 'medium' | 'large'
    maxDimensions: Optional[MaxDimensions] = None

    complexityLevel: Optional[int] = 2     # 1 / 2 / 3

    powerProfile: Optional[str] = None     # 'long_runtime' | 'balanced' | 'performance'

    decorationLevel: Optional[str] = None  # 'minimal' | 'normal' | 'rich'
    preferredColors: Optional[List[str]] = None

    ownedSets: Optional[List[str]] = None
    useOnlyOwnedParts: Optional[bool] = False


class ConfigResponse(BaseModel):
    selected: List[LegoComponent]
    total_price: float
    total_weight: float
    remaining_budget: float
    note: Optional[str] = None
