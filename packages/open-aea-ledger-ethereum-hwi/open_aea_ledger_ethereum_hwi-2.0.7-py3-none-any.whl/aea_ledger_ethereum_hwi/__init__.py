# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Python package wrapping the public and private key cryptography and support for hardware wallet interactions."""

import os


if os.environ.get("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", None) != "python":
    print(
        (
            'Please export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="python" '
            "to use the hardware wallet without any issues"
        )
    )

from aea_ledger_ethereum_hwi.hwi import (  # noqa: F401
    EthereumHWIApi,
    EthereumHWICrypto,
    EthereumHWIFaucetApi,
    EthereumHWIHelper,
)
