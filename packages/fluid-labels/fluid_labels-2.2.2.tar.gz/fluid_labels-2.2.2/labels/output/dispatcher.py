import logging
from collections.abc import Callable

from labels.model.core import OutputFormat, SbomConfig
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.resolver import Resolver
from labels.output.cyclonedx.output_handler import format_cyclonedx_sbom
from labels.output.fluid.output_handler import format_fluid_sbom
from labels.output.spdx.output_handler import format_spdx_sbom

LOGGER = logging.getLogger(__name__)
_FORMAT_HANDLERS: dict[OutputFormat, Callable] = {
    OutputFormat.FLUID_JSON: format_fluid_sbom,
    OutputFormat.CYCLONEDX_JSON: format_cyclonedx_sbom,
    OutputFormat.CYCLONEDX_XML: format_cyclonedx_sbom,
    OutputFormat.SPDX_JSON: format_spdx_sbom,
    OutputFormat.SPDX_XML: format_spdx_sbom,
}


def dispatch_sbom_output(
    *,
    packages: list[Package],
    relationships: list[Relationship],
    config: SbomConfig,
    resolver: Resolver,
) -> None:
    handler = _FORMAT_HANDLERS[config.output_format]
    handler(
        packages=packages,
        relationships=relationships,
        config=config,
        resolver=resolver,
    )
