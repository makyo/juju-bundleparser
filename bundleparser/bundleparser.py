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

    print(json.dumps(parse.parse(bundle), indent=4))


if __name__ == '__main__':
    main()
