# AA Fleetcomp

[![release](https://img.shields.io/pypi/v/aa-fleetcomp?label=release)](https://pypi.org/project/aa-fleetcomp/)
[![python](https://img.shields.io/pypi/pyversions/aa-fleetcomp)](https://pypi.org/project/aa-fleetcomp/)
[![django](https://img.shields.io/pypi/djversions/aa-fleetcomp?label=django)](https://pypi.org/project/aa-fleetcomp/)
[![license](https://img.shields.io/badge/license-MIT-green)](https://gitlab.com/r0kym/aa-fleetcomp/-/blob/master/LICENSE)

Alliance auth application to monitor a fleet composition (ship numbers, multi-boxing, etc...)

## Features
- Snapshot your own fleets
  - Check how much members multibox and which roles
  - Check fleet mass (with and without capital ships)
- Possibility to snapshot fleets of other fleet commanders
- View snapshots history

The goal of this application isn't to be a fleet activity tracker (FAT).
It's only made to record who flies what and give FCs an overview of their fleet.

### Screenshots

![](images/fleet_window.png)

![](images/user_details.png)

## Installation

### Step 1 - Check prerequisites

The application requires the Eve Universe module: [django-eveuniverse](https://django-eveuniverse.readthedocs.io/en/latest/)

### Step 2 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

```bash
pip install aa-fleetcomp
```

### Step 3 - Configure Auth settings

Configure your Auth settings (`local.py`) as follows:

- Add `'fleetcomp'` to `INSTALLED_APPS`

### Step 4 - Finalize App installation

Run migrations & copy static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Restart your supervisor services for Auth.

### Step 5 - Optional - Add default ship groupings

The fleet snapshot view will by default only distinguish mainline ships and other ships.
Other groupings can be added to have a better view of the fleet.

Default groupings can be added by running
```bash
python manage.py populate_default_groupings
```

## Ship groupings

The fleet view can propose some grouping of ships to be tracked (logi, dread, faxes, ...).
A set of default groupings can be added with a management command.

If you want an additional grouping you can go in the admin menu and create a `CustomGrouping` object.

## Permissions

Permissions overview.

| Name           | Description                                                                                 |
|----------------|---------------------------------------------------------------------------------------------|
| `basic_access` | Allows to access the module, create snapshots of its own fleets and see own fleet snapshots |
| `view_all`     | Can view all recorded fleets and create snapshots of other FCs fleet                        |

## App settings

| Name                                   | Description                                                                                                     | Default |
|----------------------------------------|-----------------------------------------------------------------------------------------------------------------|---------|
| `FLEETCOMP_FLEET_CACHE_MINUTES`        | Time in minutes before a new scan of a known fleet is allowed.                                                  | 5       |
| `FLEETCOMP_DREADNOUGHT_WEIGHT_PENALTY` | Penality applied to all dreadnoughts when determining the main ship of a fleet. Can be set to 1 to be nullified | 5       |


## Management commands

| Name                         | Description                                               |
|------------------------------|-----------------------------------------------------------|
| `populate_default_groupings` | Populates the database with a default set of ShipGrouping |
