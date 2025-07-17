#!/bin/bash
#
# API Documentation Auto-generation Script
#
# Features:
# 1. Auto-generate Python module API docs using sphinx-apidoc
# 2. Support specifying ignored files/directories via .docignore
# 3. Auto-generate module index
#
# Usage:
# 1. Run in the `docs` folder of the project root
# 2. Add ignore patterns in `.docignore` (similar to `.gitignore` syntax)
# 3. Generated docs will be located in `source/api` after running

# Documentation output directory
SOURCE_DIR="source/api"
# Module index file path
INDEX_FILE="source/api/index.md"

# Module list to generate docs (can add multiple)
MODULES=("argoproxy")

# Source code root directory (relative to script location)
ROOT_DIR="../src"

# Ensure the output directory exists
mkdir -p "$SOURCE_DIR"

# Regenerate API References for each module
for module in "${MODULES[@]}"; do
    module_dir="$ROOT_DIR/$module"
    if [[ -d "$module_dir" ]]; then
        echo "Regenerating API References for $module..."
        sphinx-apidoc -o "$SOURCE_DIR" "$module_dir" -f -e --module-first --remove-old
    else
        echo "Warning: Module directory $module_dir does not exist. Skipping."
    fi
done

# Remove modules.rst after execution if it exists
if [[ -f "${SOURCE_DIR}/modules.rst" ]]; then
    rm ${SOURCE_DIR}/modules.rst
fi

# # Regenerate index.md with {toctree} directive
# echo "Regenerating index.md..."
# {
#     echo "# API References"
#     echo ""
#     echo "Welcome to the API references for the project. Below is a list of available modules:"
#     echo ""
#     echo "\`\`\`{toctree}"
#     echo ":maxdepth: 2"
#     echo ":caption: 'Contents:'"
#     echo ""
# } >"$INDEX_FILE"

# # Add module entries to the {toctree} directive
# for module in "${MODULES[@]}"; do
#     module_name=$(basename "$module")
#     if [[ -f "$SOURCE_DIR/${module_name}.rst" ]]; then
#         echo "${module_name}" >>"$INDEX_FILE"
#     fi
# done

# # Close the {toctree} directive
# echo "\`\`\`" >>"$INDEX_FILE"

# echo "API References and index.md regeneration complete. Files are located in $SOURCE_DIR and $INDEX_FILE."
