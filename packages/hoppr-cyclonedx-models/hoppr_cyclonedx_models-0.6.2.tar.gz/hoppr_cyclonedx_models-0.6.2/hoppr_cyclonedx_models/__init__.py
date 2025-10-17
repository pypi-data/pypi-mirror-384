"""
Hoppr package to generate Pydantic models for CycloneDX schema

--------------------------------------------------------------------------------
SPDX-FileCopyrightText: Copyright © 2023 Lockheed Martin <open.source@lmco.com>
SPDX-FileName: hoppr_cyclonedx_models/__init__.py
SPDX-FileType: SOURCE
SPDX-License-Identifier: MIT
--------------------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
--------------------------------------------------------------------------------
"""
from __future__ import annotations

from typing import Any

from pydantic import Extra, Field, root_validator
from typing_extensions import Annotated, Literal

from hoppr_cyclonedx_models.base import CycloneDXBaseModel
from hoppr_cyclonedx_models.cyclonedx_1_3 import CyclonedxSoftwareBillOfMaterialSpecification as Sbom_1_3
from hoppr_cyclonedx_models.cyclonedx_1_4 import CyclonedxSoftwareBillOfMaterialsStandard as Sbom_1_4
from hoppr_cyclonedx_models.cyclonedx_1_5 import CyclonedxSoftwareBillOfMaterialsStandard as Sbom_1_5


class Sbom(Sbom_1_5, Sbom_1_4, Sbom_1_3):  # pylint: disable=too-few-public-methods
    """
    Convenience class to parse SBOM as latest spec version
    """

    class Config(CycloneDXBaseModel.Config):
        """
        Config options for Sbom
        """

        extra = Extra.forbid

    field_schema: Annotated[
        Literal[
            "http://cyclonedx.org/schema/bom-1.3.schema.json",
            "http://cyclonedx.org/schema/bom-1.4.schema.json",
            "http://cyclonedx.org/schema/bom-1.5.schema.json",
        ],
        Field(alias="$schema"),
    ] = "http://cyclonedx.org/schema/bom-1.5.schema.json"

    specVersion: Annotated[
        Literal["1.3", "1.4", "1.5"],
        Field(
            description="The version of the CycloneDX specification a BOM conforms to (starting at version 1.2).",
            examples=["1.3", "1.4", "1.5"],
            title="CycloneDX Specification Version",
        ),
    ] = "1.5"

    @root_validator(allow_reuse=True, pre=True)
    @classmethod
    def validate_sbom(cls, sbom: dict[str, Any]) -> dict[str, Any]:
        """
        Parse SBOM as latest CycloneDX spec release
        """
        sbom["$schema"] = "http://cyclonedx.org/schema/bom-1.5.schema.json"
        sbom["specVersion"] = "1.5"

        return Sbom_1_5(**sbom).dict(exclude_none=True, exclude_unset=True)


__version__ = "0.6.2"
