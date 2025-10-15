from pydantic import BaseModel
from pathlib import Path


class Composition(BaseModel):
    name: str

    # Base elements
    Fe: float | None = None
    C: float | None = None

    # TCFe alloys
    H: float | None = None
    Mg: float | None = None
    Ca: float | None = None
    Y: float | None = None
    Ti: float | None = None
    Zr: float | None = None
    V: float | None = None
    Nb: float | None = None
    Ta: float | None = None
    Cr: float | None = None
    Mo: float | None = None
    W: float | None = None
    Mn: float | None = None
    Ru: float | None = None
    Co: float | None = None
    Ni: float | None = None
    Cu: float | None = None
    Zn: float | None = None
    B: float | None = None
    Al: float | None = None
    Si: float | None = None
    N: float | None = None
    P: float | None = None
    O: float | None = None
    S: float | None = None
    Ar: float | None = None
    Ce: float | None = None

    # TCNi12 extra elements
    Hf: float | None = None
    Re: float | None = None
    Pd: float | None = None
    Pt: float | None = None

    # TCAl9 extra elements
    Li: float | None = None
    Na: float | None = None
    K: float | None = None
    Be: float | None = None
    Sr: float | None = None
    Ba: float | None = None
    Sc: float | None = None
    Ga: float | None = None
    Ge: float | None = None
    Ag: float | None = None
    In: float | None = None
    Cd: float | None = None
    Sn: float | None = None
    Sb: float | None = None
    Te: float | None = None
    Se: float | None = None
    Pb: float | None = None
    Bi: float | None = None
    La: float | None = None
    Pr: float | None = None
    Nd: float | None = None
    Er: float | None = None

    # TCHEA7
    Ir: float | None = None

    def save(self, path: Path) -> Path:
        """Save model to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "Composition":
        """Load model from a JSON file."""
        return cls.model_validate_json(path.read_text())

    def elements(self) -> list[str]:
        """Return a list of elements that have non-None values."""
        return [k for k, v in self if k != "name" and v is not None]

    def fractions(self) -> dict[str, float]:
        """Return a dict of element → value (excluding 'name')."""
        return {k: v for k, v in self if k != "name" and v is not None}
