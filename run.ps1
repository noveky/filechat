# Change to the directory of the script
Set-Location -Path $PSScriptRoot

# Execute the Python module with arguments
python -m filechat.main @Args
