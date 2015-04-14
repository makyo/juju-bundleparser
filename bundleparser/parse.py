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


class ChangeSet(object):
    services_added = {}
    machines_added = {}

    def __init__(self, bundle):
        self.bundle = bundle
        self._changeset = []
        self._counter = itertools.count()

    def send(self, change):
        self._changeset.append(change)

    def recv(self):
        changeset = self._changeset
        self._changeset = []
        return changeset

    def next_action(self):
        return self._counter.next()


def parse(bundle):
    changeset = ChangeSet(bundle)
    handler = handle_services
    while True:
        handler = handler(changeset)
        for change in changeset.recv():
            yield change
        if handler is None:
            break


def handle_services(changeset):
    charms = {}
    for service_name, service in changeset.bundle['services'].items():
        # Add the addCharm record if one hasn't been added yet.
        if service['charm'] not in charms:
            record_id = 'addCharm-{}'.format(changeset.next_action())
            changeset.send({
                'id': record_id,
                'method': 'addCharm',
                'args': [service['charm']],
                'requires': [],
            })
            charms[service['charm']] = record_id

        # Add the deploy record for this service.
        record_id = 'addService-{}'.format(changeset.next_action())
        changeset.send({
            'id': record_id,
            'method': 'deploy',
            'args': [
                service['charm'],
                service_name,
                service.get('options', {})
            ],
            'requires': [charms[service['charm']]],
        })
        changeset.services_added[service_name] = record_id
    return handle_machines


def handle_machines(changeset):
    for machine_name, machine in changeset.bundle.get('machines', {}).items():
        record_id = 'addMachine-{}'.format(changeset.next_action())
        changeset.send({
            'id': record_id,
            'method': 'addMachine',
            'args': [],  # TODO
            'requires': [],
        })
        changeset.machines_added[machine_name] = record_id
    return handle_units


def handle_units(changeset):
    units, records = {}, {}
    for service_name, service in changeset.bundle['services'].items():
        for i in range(service['num_units']):
            record_id = 'addUnit-{}'.format(changeset.next_action())
            unit_name = '{}/{}'.format(service_name, i)
            records[record_id] = {
                'id': record_id,
                'method': 'addUnit',
                'args': [
                    '${}'.format(changeset.services_added[service_name]),
                    1,
                    None,
                ],
                'requires': [],
            }
            units[unit_name] = {
                'record': record_id,
                'service': service_name,
                'unit': i,
            }
    # Second pass, ensure that requires and placement directives are taken into account.
    for service_name, service in changeset.bundle['services'].items():
        # Add the addUnits record for each unit.
        placement_directives = service.get('to', [])
        if isinstance(placement_directives, basestring):
            placement_directives = [placement_directives]
        if placement_directives and 'machines' in changeset.bundle:
            placement_directives += placement_directives[-1:] * \
                (service['num_units'] - len(placement_directives))
        for i in range(service['num_units']):
            unit = units['{}/{}'.format(service_name, i)]
            record = records[unit['record']]
            if i < len(placement_directives):
                if 'machines' in changeset.bundle:
                    placement = _parse_v4_unit_placement(placement_directives[i])
                    if placement['machine']:
                        machine_id = changeset.machines_added[
                            placement['machine']]
                        record['requires'].append(machine_id)
                        record['args'][2] = '${}'.format(machine_id)
                else:
                    placement = _parse_v3_unit_placement(placement_directives[i])
            changeset.send(record)


