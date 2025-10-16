# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Import the necessary modules and classes for the package
import logging
import os

# Configure logging at the package level to ensure all nvidia_rag modules inherit correct levels
# This must happen before any other nvidia_rag module imports
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper(), force=True)

logger = logging.getLogger(__name__)
try:
    from .rag_server.main import NvidiaRAG
except ModuleNotFoundError as e:
    logger.debug(f"Error importing NvidiaRAG: {e}")

try:
    from .ingestor_server.main import NvidiaRAGIngestor
except ModuleNotFoundError as e:
    logger.debug(f"Error importing NvidiaRAGIngestor: {e}")
