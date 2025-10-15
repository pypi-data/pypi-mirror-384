from typing import get_args, Literal

from ._loader import _list_to_index
from ._loader import _load_csv
from ._loader import _tables_index

__version__ = "1.0.0"

TableName = Literal[
    "bundles",
    "combatrank",
    "commodity",
    "cqcrank",
    "crimes",
    "dockingdeniedreasons",
    "economy",
    "empirerank",
    "engineers",
    "explorationrank",
    "factionids",
    "factionstate",
    "federationrank",
    "government",
    "happiness",
    "material",
    "microresources",
    "outfitting",
    "passengers",
    "rare_commodity",
    "rings",
    "security",
    "shipyard",
    "sku",
    "systemallegiance",
    "terraformingstate",
    "traderank",
]

tables: tuple[str] = tuple(get_args(TableName))


def load_table(table: TableName) -> dict[str | dict]:
    """Load a table of FDev IDs into a dictionary.

    Parameters
    ----------
    table
        Name of the table corresponding to the name of the csv file, in lower case and
        without suffix.

    Returns
    -------
    :
        A dictionary where the keys correspond to the values in the first column of the
        table and the values are dictionaries representing each row.

    Examples
    --------
    Load a table by specifying the table name:

    >>> from pprint import pprint
    >>> from fdev_ids import load_table
    >>> bundles = load_table("bundles")
    >>> pprint(bundles)
    {129030471: {'id': 129030471,
                'name': 'AX COMBAT JUMPSTART ALLIANCE CHIEFTAIN',
                'sku': 'FORC_FDEV_V_CHIEFTAIN_BUNDLE_001'},
    129030472: {'id': 129030472,
                'name': 'LASER MINING JUMPSTART TYPE-6',
                'sku': 'FORC_FDEV_V_TYPE6_BUNDLE_001'},
    129030473: {'id': 129030473,
                'name': 'EXPLORATION JUMPSTART DIAMONDBACK EXPLORER',
                'sku': 'FORC_FDEV_V_DIAMOND_EXPLORER_BUNDLE_001'},
    129030512: {'id': 129030512,
                'name': 'PYTHON MK II STELLAR',
                'sku': 'FORC_FDEV_V_PYTHON_MKII_BUNDLE_001'},
    129030519: {'id': 129030519,
                'name': 'PYTHON MK II STANDARD',
                'sku': 'FORC_FDEV_V_PYTHON_MKII_BUNDLE_002'}}

    Table with a single value per ID return the value directly for each ID:

    >>> factionids = load_table("factionids")
    >>> pprint(factionids)
    {'$faction_Alliance;': 'Alliance',
     '$faction_Empire;': 'Empire',
     '$faction_Federation;': 'Federation',
     '$faction_FrontlineSolutions;': 'Frontline Solutions',
     '$faction_Independent;': 'Independent',
     '$faction_Pirate;': 'Pirate',
     '$faction_Thargoid;': 'Thargoid',
     '$faction_none;': 'None'}

    Similarily when only the ID is defined:

    >>> dockingdeniedreasons = load_table("dockingdeniedreasons")
    >>> pprint(dockingdeniedreasons)
    {'ActiveFighter': 'ActiveFighter',
     'Distance': 'Distance',
     'Hostile': 'Hostile',
     'NoSpace': 'NoSpace',
     'Offences': 'Offences',
     'RestrictedAccess': 'RestrictedAccess',
     'TooLarge': 'TooLarge'}
    """
    return _list_to_index(_load_csv(_tables_index()[table]))
