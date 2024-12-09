#!/bin/bash

# Change to the directory of the script
cd "$(dirname "$0")"

# Execute the Python module with arguments
python -m filechat.main "$@"
