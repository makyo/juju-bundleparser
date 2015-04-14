import sys

import json
import yaml

from . import (
    parse,
    validate,
)


def main():
    bundle = yaml.safe_load(sys.stdin)

    errors = validate.validate_bundle(bundle)
    if errors:
        sys.exit(errors)

    print('[')
    for num, change in enumerate(parse.parse(bundle)):
        if num:
            print(',')
        print(json.dumps(change, indent=4))
    print(']')

if __name__ == '__main__':
    main()
