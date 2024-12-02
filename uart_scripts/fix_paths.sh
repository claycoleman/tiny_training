#!/bin/bash

# Define the paths
OLD_PATH="/Users/ccoleman/Developer/harvard/tinyml/tiny_training"
NEW_PATH="/Users/kennethchen/Desktop/HBS GSAS/MIT Tiny ML/tiny_training"

# Find all subdir.mk files and update the paths
find "../Debug" -name "subdir.mk" -type f -exec sed -i '' "s|${OLD_PATH}|${NEW_PATH}|g" {} +
