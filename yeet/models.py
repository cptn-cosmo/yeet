"""
Yeet - Data Models & Structures
App ID: gay.geeks.Yeet
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class Target:
    id: str
    name: str
    type: str  # "box", "circle", "capsule", "polygon"
    x: float = 0.5            # Normalized center X [0.0 - 1.0]
    y: float = 0.5            # Normalized center Y [0.0 - 1.0]
    width: float = 0.2        # Normalized width [0.0 - 1.0]
    height: float = 0.3       # Normalized height [0.0 - 1.0]
    radius: float = 0.1       # For circle [0.0 - 1.0]
    rotation: float = 0.0     # Degrees [-180.0 - 180.0]
    points: List[List[float]] = field(default_factory=list)  # For polygon [[x, y], ...]
    bounciness: float = 0.6   # Restitution [0.0 - 1.0]
    friction: float = 0.1     # Friction [0.0 - 1.0]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Target':
        return cls(
            id=data.get('id', 'target_1'),
            name=data.get('name', 'Target'),
            type=data.get('type', 'capsule'),
            x=float(data.get('x', 0.5)),
            y=float(data.get('y', 0.5)),
            width=float(data.get('width', 0.2)),
            height=float(data.get('height', 0.3)),
            radius=float(data.get('radius', 0.1)),
            rotation=float(data.get('rotation', 0.0)),
            points=data.get('points', []),
            bounciness=float(data.get('bounciness', 0.6)),
            friction=float(data.get('friction', 0.1)),
        )

@dataclass
class ThrowableItem:
    id: str
    name: str
    image_url: str            # Relative or absolute URL served by Yeet
    scale: float = 0.08       # Normalized size relative to canvas
    mass: float = 1.0         # Physics mass
    bounciness: float = 0.65  # Restitution
    rotational_speed: float = 1.0  # Torque/spin factor
    gravity_scale: float = 1.0     # Multiplier for world gravity
    lifetime: float = 8.0          # Seconds on screen before fading
    sound_effect: str = "bonk"     # "squish", "bonk", "thud", "pop", "clang" or custom URL
    sound_volume: float = 0.8      # [0.0 - 1.0]
    pitch_randomness: float = 0.2  # [0.0 - 0.5] pitch variation factor

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThrowableItem':
        return cls(
            id=data.get('id', 'item_1'),
            name=data.get('name', 'Item'),
            image_url=data.get('image_url', '/assets/items/tomato.svg'),
            scale=float(data.get('scale', 0.08)),
            mass=float(data.get('mass', 1.0)),
            bounciness=float(data.get('bounciness', 0.65)),
            rotational_speed=float(data.get('rotational_speed', 1.0)),
            gravity_scale=float(data.get('gravity_scale', 1.0)),
            lifetime=float(data.get('lifetime', 8.0)),
            sound_effect=data.get('sound_effect', 'bonk'),
            sound_volume=float(data.get('sound_volume', 0.8)),
            pitch_randomness=float(data.get('pitch_randomness', 0.2)),
        )

@dataclass
class PhysicsConfig:
    gravity: List[float] = field(default_factory=lambda: [0.0, 1.0])
    default_spawn_direction: str = "random"  # "left", "right", "top", "bottom", "random", "aimed", "rain", "spray"
    default_force: float = 1.0
    default_spread: float = 15.0             # Spread angle in degrees
    spawn_point: List[float] = field(default_factory=lambda: [0.0, 0.5])  # For spray
    spray_angle: float = 0.0                 # Degrees (0 = right)
    sound_debounce_ms: int = 50              # Minimum ms between impact sounds
    max_active_items: int = 120              # Max simultaneous items
    debug_boundaries: bool = False           # Render target wireframes in overlay

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhysicsConfig':
        return cls(
            gravity=data.get('gravity', [0.0, 1.0]),
            default_spawn_direction=data.get('default_spawn_direction', 'random'),
            default_force=float(data.get('default_force', 1.0)),
            default_spread=float(data.get('default_spread', 15.0)),
            spawn_point=data.get('spawn_point', [0.0, 0.5]),
            spray_angle=float(data.get('spray_angle', 0.0)),
            sound_debounce_ms=int(data.get('sound_debounce_ms', 50)),
            max_active_items=int(data.get('max_active_items', 120)),
            debug_boundaries=bool(data.get('debug_boundaries', False)),
        )

@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 49122

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        return cls(
            host=data.get('host', '127.0.0.1'),
            port=int(data.get('port', 49122)),
        )

def get_default_targets() -> List[Target]:
    return [
        Target(
            id="target_vtuber_body",
            name="VTuber Torso",
            type="capsule",
            x=0.50,
            y=0.62,
            width=0.22,
            height=0.38,
            rotation=0.0,
            bounciness=0.6,
            friction=0.15
        ),
        Target(
            id="target_vtuber_head",
            name="VTuber Head",
            type="circle",
            x=0.50,
            y=0.32,
            radius=0.12,
            rotation=0.0,
            bounciness=0.75,
            friction=0.1
        )
    ]

def get_default_items() -> Dict[str, ThrowableItem]:
    return {
        "tomato": ThrowableItem(
            id="tomato",
            name="Ripe Tomato",
            image_url="/assets/items/tomato.svg",
            scale=0.08,
            mass=0.8,
            bounciness=0.4,
            rotational_speed=1.5,
            gravity_scale=1.0,
            lifetime=8.0,
            sound_effect="squish",
            sound_volume=0.9,
            pitch_randomness=0.2
        ),
        "brick": ThrowableItem(
            id="brick",
            name="Red Brick",
            image_url="/assets/items/brick.svg",
            scale=0.09,
            mass=2.5,
            bounciness=0.25,
            rotational_speed=0.8,
            gravity_scale=1.3,
            lifetime=10.0,
            sound_effect="thud",
            sound_volume=1.0,
            pitch_randomness=0.15
        ),
        "pie": ThrowableItem(
            id="pie",
            name="Cream Pie",
            image_url="/assets/items/pie.svg",
            scale=0.10,
            mass=0.9,
            bounciness=0.3,
            rotational_speed=1.2,
            gravity_scale=0.9,
            lifetime=8.0,
            sound_effect="squish",
            sound_volume=0.95,
            pitch_randomness=0.25
        ),
        "rubber_duck": ThrowableItem(
            id="rubber_duck",
            name="Rubber Duck",
            image_url="/assets/items/rubber_duck.svg",
            scale=0.08,
            mass=0.5,
            bounciness=0.85,
            rotational_speed=2.0,
            gravity_scale=0.8,
            lifetime=12.0,
            sound_effect="bonk",
            sound_volume=0.85,
            pitch_randomness=0.3
        ),
        "water_balloon": ThrowableItem(
            id="water_balloon",
            name="Water Balloon",
            image_url="/assets/items/water_balloon.svg",
            scale=0.08,
            mass=0.7,
            bounciness=0.45,
            rotational_speed=1.3,
            gravity_scale=1.0,
            lifetime=7.0,
            sound_effect="squish",
            sound_volume=0.9,
            pitch_randomness=0.2
        ),
        "heart": ThrowableItem(
            id="heart",
            name="Heart Plushie",
            image_url="/assets/items/heart.svg",
            scale=0.09,
            mass=0.4,
            bounciness=0.7,
            rotational_speed=1.0,
            gravity_scale=0.7,
            lifetime=9.0,
            sound_effect="pop",
            sound_volume=0.8,
            pitch_randomness=0.25
        ),
        "beachball": ThrowableItem(
            id="beachball",
            name="Beach Ball",
            image_url="/assets/items/beachball.svg",
            scale=0.13,
            mass=0.25,
            bounciness=0.92,
            rotational_speed=1.5,
            gravity_scale=0.45,
            lifetime=14.0,
            sound_effect="pop",
            sound_volume=0.85,
            pitch_randomness=0.25
        )
    }
