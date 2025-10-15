# fdev-ids-python

Data from https://github.com/EDCD/FDevIDs bundled in Python data structures.

## Installation

    pip install fdev-ids

## Usage

Load a table by specifying the lowercase table name:

```pycon
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
```

Tables with a single value per ID return the value directly for each ID:

```pycon
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
```

Similarily when only the ID is defined:

```pycon
>>> dockingdeniedreasons = load_table("dockingdeniedreasons")
>>> pprint(dockingdeniedreasons)
{'ActiveFighter': 'ActiveFighter',
 'Distance': 'Distance',
 'Hostile': 'Hostile',
 'NoSpace': 'NoSpace',
 'Offences': 'Offences',
 'RestrictedAccess': 'RestrictedAccess',
 'TooLarge': 'TooLarge'}
```

## Terms of Use

The data contained in this package is based on publicly available information sourced from https://github.com/EDCD/FDevIDs and subject to the [Elite Dangerous EULA and Terms of Use](https://www.frontierstore.net/ed-eula/).

The MIT license applies to the code in this repository only.

## Issues & support

Report issues with the package itself at https://codeberg.org/jdlbt/fdev-ids-python/issues.

For issues with or updates to the data tables, refer to https://github.com/EDCD/FDevIDs/issues.


## Development

See [CONTRIBUTING](CONTRIBUTING.md).
