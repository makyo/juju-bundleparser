import itertools

from collections import namedtuple

UnitPlacement = namedtuple(
    'UnitPlacement', [
        'container_type',
        'machine',
        'service',
        'unit',
    ]
)


def _parse_v3_unit_placement(placement):
    container = machine = service = unit = ''
    if ':' in placement:
        contaner, placement = placement.split(':')
    if '=' in placement:
        placement, unit = placement.split('=')
    if placement.is_digit():
        machine = placement
    else:
        service = placement
    return UnitPlacement(container, machine, service, unit)

def _parse_v4_unit_placement(placement):
    container = machine = service = unit = ''
    if ':' in placement:
        contaner, placement = placement.split(':')
    if '/' in placement:
        placement, unit = placement.split('/')
    if placement.is_digit():
        machine = placement
    else:
        service = placement
    return UnitPlacement(container, machine, service, unit)

def parse(bundle):
    changeset = []
    unit_records = {}
    action_index = itertools.count()
    charms_added = {}
    services_added = {}
    machines_added = {}
    units_added = {}

    # machines -> charm -> service -> units -> relations
    for service_name, service in bundle['services'].items():
        # Add the addCharm record if one hasn't been added yet.
        if service['charm'] not in charms_added:
            record_id = 'addCharm-{}'.format(action_index.next())
            changeset.append({
                'id': record_id,
                'method': 'addCharm',
                'args': [service['charm']],
                'requires': [],
            })
            charms_added[service['charm']] = record_id

        # Add the deploy record for this service.
        record_id = 'addService-{}'.format(action_index.next())
        changeset.append({
            'id': record_id,
            'method': 'deploy',
            'args': [service['charm'], service_name, service.get('options', {})],
            'requires': [charms_added[service['charm']]],
        })
        services_added[service_name] = record_id

    for machine_name, machine in bundle.get('machines', {}).items():
        record_id = 'addMachine-{}'.format(action_index.next())
        changeset.append({
            'id': record_id,
            'method': 'addMachine',
            'args': [], # TODO
            'requires': [],
        })
        machines_added[machine_name] = record_id

    # First pass, add the unit records so that we can refer to them later.
    for service_name, service in bundle['services'].items():
        for i in range(service['num_units']):
            record_id = 'addUnit-{}'.format(action_index.next())
            unit_name = '{}/{}'.format(service_name, i)
            unit_records[record_id] = {
                'id': record_id,
                'method': 'addUnit',
                'args': ['${}'.format(services_added[service_name]), 1, None],
                'requires': [],
            }
            units_added[unit_name] = {
                'record': record_id,
                'service': service_name,
                'unit': i,
            }
    # Second pass, ensure that requires and placement directives are taken into account.
    for service_name, service in bundle['services'].items():
        # Add the addUnits record for each unit.
        placement_directives = service.get('to', [])
        if isinstance(placement_directives, basestring):
            placement_directives = [placement_directives]
        if placement_directives and 'machines' in bundle:
            placement_directives += placement_directives[-1:] * \
                (service['num_units'] - len(placement_directives))
        for i in range(service['num_units']):
            unit = units_added['{}/{}'.format(service_name, i)]
            record = unit_records[unit['record']]
            if i < len(placement_directives):
                if 'machines' in bundle:
                    placement = _parse_v4_unit_placement(placement_directives[i])
                    if placement['machine']:
                        machine_id = machines_added[placement['machine']]
                        record['requires'].append(machine_id)
                        record['args'][2] = '${}'.format(machine_id)
                else:
                    placement = _parse_v3_unit_placement(placement_directives[i])

    return changeset + unit_records.values()
