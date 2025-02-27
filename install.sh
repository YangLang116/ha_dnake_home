#!/bin/bash
set -e

# Check the number of input parameters.
if [ $# -ne 1 ]; then
    echo "usage: $0 [config_path]"
    exit 1
fi
# Get the config path.
config_path=$1
# Check if config path exists.
if [ ! -d "$config_path" ]; then
    echo "$config_path does not exist"
    exit 1
fi

# Get the script path.
script_path=$(dirname "$0")

# Set source and target
component_name=dnake_home
source_path="$script_path/custom_components/$component_name"
target_root="$config_path/custom_components"
target_path="$target_root/$component_name"

# Remove the old version.
rm -rf "$target_path"

# Copy the new version.
mkdir -p "$target_root"
cp -r "$source_path" "$target_path"

# Done.
echo "Dnake Home installation is completed. Please restart Home Assistant."
exit 0