from tc.schema import Composition


def select_thermocalc_database(composition: Composition) -> str:
    """
    Selects the most appropriate thermo-calc database based on composition
    """
    # Convert the Composition object to a dict and remove None values
    fractions = composition.fractions()

    if not fractions:
        return "PURE5"  # fallback if no elements are set

    # Find the element with the highest fraction
    top_el, top_x = max(fractions.items(), key=lambda kv: kv[1])

    # Count elements with fraction >= 0.15
    multi_principal = sum(1 for x in fractions.values() if x >= 0.15) >= 3

    if top_el == "Ti":
        return "TCTI6"
    if top_el == "Ni" or fractions.get("Ni", 0.0) >= 0.30:
        return "TCNI12"
    if top_el == "Fe":
        return "TCFE14"
    if top_el == "Al":
        return "TCAL9"
    if multi_principal:
        return "TCHEA7"
    return "PURE5"
