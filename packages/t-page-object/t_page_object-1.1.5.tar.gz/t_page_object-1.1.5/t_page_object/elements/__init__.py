"""Module for all base ui components."""
from . import checkbox_element
import sys

# Provide backward compatibility for typo
sys.modules[__name__ + ".checkox_element"] = checkbox_element
