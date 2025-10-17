# Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.

# Version of the project - please follow semantic versioning 2.0: https://semver.org/
MAJOR = 0
MINOR = 1
PATCH = 10
PRE_RELEASE = ''

# Use the following formatting: major.minor.patch[-pre_release]
# Examples: 23.0.123 | 1.0.22-alpha5
__version__ = str(MAJOR) + "." + str(MINOR) + "." + str(PATCH) + ("-" + PRE_RELEASE if PRE_RELEASE != "" else "")

# Other package info.
__package_name__ = "nvidia-eff-tao-encryption"
__description__ = "NVIDIA Exchange File Format - Encryption for TAO"
__keywords__ = "nvidia, eff, tao, encryption"

__contact_names__ = "Tomasz Kornuta, Varun Praveen"
__contact_emails__ = "tkornuta@nvidia.com, vpraveen@nvidia.com"

__license__ = "NVIDIA Proprietary Software"
