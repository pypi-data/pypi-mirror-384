import re
from pyteomics.mass import Composition, calculate_mass
from mascope_tools.composition.models import (
    CompositionFinderException,
    IonizationMechanism,
    Atom,
)
from mascope_tools.composition.constants import ELECTRON_MASS


def combine_formula_and_ionization(
    formula: str, ionization_mechanism: IonizationMechanism
) -> str:
    """
    Combine a neutral formula and ionization into a single ion formula in Hill notation.
    """
    # Parse formula
    comp_formula = Composition(formula=formula)
    comp_ionization = (
        Composition(formula=ionization_mechanism.formula)
        if ionization_mechanism
        else Composition(formula="")
    )
    if ionization_mechanism.addition:
        combined_composition = comp_formula + comp_ionization
    else:
        combined_composition = comp_formula - comp_ionization

    charge_sign = (
        "+" if ionization_mechanism and ionization_mechanism.charge > 0 else "-"
    )
    ion_formula = to_hill_order(combined_composition) + charge_sign
    return ion_formula


def parse_composition(formula_string: str, multiplier: int = 1) -> Composition:
    """Recursevely parses formulas like "(CH3CH2)2NH", "((CH3CH2)2NH)H", "(C6H10O2)H", "CH4N2OH"
    into pyteomics.Composition

    :param formula_string: String containing the formula to parse.
    :type formula_string: str
    :param multiplier: Multiplier after brackets, defaults to 1
    :type multiplier: int, optional
    :return: Parsed composition as a pyteomics.Composition object.
    :rtype: Composition
    """
    pattern = r"(\([^\(\)]+\))(\d*)"
    elements = Composition(formula="")
    i = 0
    while i < len(formula_string):
        # Find next bracketed group
        match = re.search(pattern, formula_string[i:])
        if match:
            start = i + match.start()
            end = i + match.end()
            # Parse before bracket
            before = formula_string[i:start]
            elements = elements + parse_composition(before, 1)
            # Parse inside bracket
            group = match.group(1)[1:-1]
            group_mult = int(match.group(2)) if match.group(2) else 1
            elements = elements + parse_composition(group, group_mult)
            i = end
        else:
            # Parse remaining string (elements outside brackets)
            m = re.match(r"([A-Z][a-z]?)(\d*)", formula_string[i:])
            if m:
                elem = m.group(1)
                count = int(m.group(2)) if m.group(2) else 1
                elements[elem] += count * multiplier
                i += len(m.group(0))
            else:
                i += 1
    return elements


def to_hill_order(elements: dict) -> str:
    """Convert a dictionary of elements to Hill notation string."""
    # Filter out zero and negative counts (can be if -H- is the ionization mechanism)
    elements = {k: v for k, v in elements.items() if v > 0}
    atomic_symbols = list(elements.keys())
    atomic_symbols.sort(key=lambda x: (0 if x == "C" else 1 if x == "H" else 2, x))
    formula = "".join(
        f"{symbol}{elements[symbol] if elements[symbol] > 1 else ''}"
        for symbol in atomic_symbols
    )
    formula = remove_ones_from_formula(formula)
    return formula


def remove_ones_from_formula(formula: str) -> str:
    formula = re.sub(r"([A-Za-z]+)1(?![0-9])", r"\1", formula)
    return formula


def parse_ionization(ionization_string: str) -> IonizationMechanism:
    """Parse ionization mechanism string from Mascope format into an IonizationMechanism object.

    :param ionization_string: String representing the ionization mechanism.
    :type ionization_string: str
    :raises CompositionFinderException: If the ionization is unsupported.
    :return: Parsed IonizationMechanism object.
    :rtype: IonizationMechanism
    """
    ionization_string = ionization_string.strip()
    formula = ""
    mass = ELECTRON_MASS
    if ionization_string == "+":
        # Abstract electron being kicked out
        addition = False
        charge = 1
    elif ionization_string == "-":
        # Abstract electron being added
        addition = True
        charge = -1
    elif ionization_string == "-H-":
        # Deprotonation
        addition = False
        formula = "H"
        charge = -1
        mass = calculate_mass(formula="H")
    else:
        # Regex pattern: start charge, base, end charge
        pattern = r"^([+-])?(.*?)([+-])?$"

        match = re.match(pattern, ionization_string)
        if match:
            addition = match.group(1) == "+"
            composition = parse_composition(match.group(2))
            formula = to_hill_order(composition)
            charge = 1 if match.group(3) == "+" else -1
            mass = composition.mass() - ELECTRON_MASS * charge
        else:
            raise CompositionFinderException(
                f"Unsupported ionization mechanism: '{ionization_string}'"
            )

    ionization_mech = IonizationMechanism(
        mascope_notation=ionization_string,
        addition=addition,
        formula=formula,
        mass=mass,
        charge=charge,
    )

    return ionization_mech


def parse_bool(val):
    """Parse a value into a boolean."""
    return str(val).lower() in ("1", "true", "yes", "on")


def parse_atom_count_ranges(count_ranges: str) -> list:
    """Parse a string of element count ranges into a list of Atom objects.

    :param count_ranges: String containing element count ranges.
        e.g. "C0-30 H0-40 N0-3 O0-20 O[18]0-1 C[13]0-2"
    :type count_ranges: str
    :return: List of Atom objects.
    :rtype: list
    """
    pattern = r"([A-Z][a-z]?(?:\[\d+\])?)(\d+)-(\d+)"
    atoms = []
    for match in re.finditer(pattern, count_ranges):
        element, min_count, max_count = match.groups()
        atoms.append(
            Atom(
                symbol=element,
                min_count=int(min_count),
                max_count=int(max_count),
                mass=calculate_mass(formula=element, charge=0),
            )
        )
    return atoms
