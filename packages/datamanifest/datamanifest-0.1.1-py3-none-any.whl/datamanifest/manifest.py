import logging
from typing import Optional
from pathlib import Path
from dataclasses import dataclass
import importlib.resources as ires
import rdfhelpers
import rdflib
from xmptools import makeFileURI

log = logging.getLogger(__name__)

@dataclass
class SourceSpec:
    uri:            Optional[rdflib.URIRef]  = None
    prefix:         Optional[rdflib.Literal] = None
    from_url:       Optional[rdflib.URIRef]  = None
    alt_uri:        Optional[rdflib.URIRef]  = None
    classification: Optional[rdflib.URIRef]  = None
    title:          Optional[rdflib.Literal] = None
    is_dir:         Optional[rdflib.Literal] = None
    period:         Optional[rdflib.Literal] = None
    config_url:     Optional[rdflib.URIRef]  = None
    shacl:          Optional[rdflib.URIRef]  = None
    mapping:        Optional[rdflib.URIRef]  = None
    context:        Optional[rdflib.URIRef]  = None
    declared_uri:   Optional[rdflib.URIRef]  = None

class SourceManager:
    def __init__(self, default_sources=None, shapes: rdflib.Graph = None):
        self.default_sources = default_sources
        self.data_dir = ires.files(__package__ + ".data") if __package__ else Path("data")
        if shapes:
            self.manifest_shapes = shapes
        else:
            self.manifest_shapes = rdflib.Graph()
            with self.data_dir.joinpath("manifest-shapes.ttl").open('rb') as sh:
                self.manifest_shapes.parse(sh)

    def getManifestURI(self):
        return makeFileURI(self.data_dir.joinpath("manifest.ttl"))

    def readSources(self, url, try_default=True, graph=None) -> rdfhelpers.Composable:
        graph = rdfhelpers.Composable(graph)
        log.debug("Reading source configuration from {}".format(url))
        try:
            graph.parse(url, publicID=url)
            return graph
        except FileNotFoundError as e:
            if try_default and self.default_sources:
                log.warning("No source configuration found, trying default sources only")
                return self.readSources(makeFileURI(self.default_sources),
                                        try_default=False, graph=graph)
            else:
                log.error("No source configuration found")
                raise e

    def collectSources(self, url, try_default=True, validate=True) -> list[SourceSpec]:
        graph = self.readSources(url, try_default=try_default)
        if validate:
            try:
                graph.validate(self.manifest_shapes, fail_if_necessary=True)  # , allow_infos=True)
            except rdfhelpers.templated.ValidationFailure as e:
                log.error("SHACL validation failed for {}".format(url))
                log.error(e)
                return list()
        sources = [SourceSpec(*values) for values
                   in graph.query(self.QS_LOAD_SOURCES, source=rdflib.URIRef(url))]
        if log.isEnabledFor(logging.DEBUG):
            for ss in sources:
                log.debug("Source: {}".format(ss.from_url or ss.uri))
        for source, in graph.query(self.QS_IMPORT_SOURCES, source=rdflib.URIRef(url)):
            new_sources = self.collectSources(source, try_default=False, validate=validate)
            sources += new_sources
        if len(sources) == 0:
            log.warning("No sources found in {}".format(url))
        return sources

    def collectNamespaces(self, url, namespaces=None) -> dict[str, rdflib.URIRef]:
        graph = self.readSources(url, try_default=False)
        if namespaces is None:
            namespaces = dict()
        for prefix, uri in graph.query(self.QS_HARVEST_NAMESPACES):
            namespaces[str(prefix)] = uri
        for source, in graph.query(self.QS_IMPORT_SOURCES, source=rdflib.URIRef(url)):
            self.collectNamespaces(source, namespaces=namespaces)
        return namespaces

    def collectManifests(self, url, try_default=False, validate=False):
        return list(set([s.config_url for s
                         in self.collectSources(url, try_default=try_default, validate=validate)]))

    QS_IMPORT_SOURCES = """
        SELECT DISTINCT ?source {
            $source dcat:catalog ?source
        }
    """

    QS_LOAD_SOURCES = """
        PREFIX manifest: <https://somanyaircraft.com/data/schema/manifest#>
        SELECT ?uri ?prefix ?from_url ?alt_uri ?classification ?title ?is_dir ?period ?config_url
               ?shacl ?mapping ?context ?declared_uri {
            ?catalog a dcat:Catalog ;
                dcat:dataset/(^dcat:inSeries)* ?uri .
            ?uri a dcat:Dataset .
            OPTIONAL { ?uri dcterms:title ?title }
            OPTIONAL { ?uri dcat:theme ?classification }
            OPTIONAL { ?uri sh:declare/sh:namespace ?declared_uri }
            OPTIONAL { ?uri sh:declare/sh:prefix ?prefix }
            OPTIONAL { ?uri sh:declare/manifest:alternateNamespace ?alt_uri }
            OPTIONAL {
                ?uri dcat:distribution ?dist .
                ?dist a dcat:Distribution ;
                    dcat:downloadURL ?from_url
                OPTIONAL { ?dist dcat:packageFormat ?format }
                OPTIONAL { ?dist manifest:mapping ?mapping }
                OPTIONAL { ?dist manifest:context ?context }
            }
            OPTIONAL { ?uri sh:shapesGraph ?shacl }
            BIND ((?format = manifest:Directory) as ?is_dir)
            VALUES ?period { UNDEF }
            BIND ($source AS ?config_url)
    }
    """

    QS_HARVEST_NAMESPACES = """
        SELECT DISTINCT ?prefix ?uri {
            ?catalog a dcat:Catalog ;
                dcat:dataset/(^dcat:inSeries)* ?dataset_uri .
            ?dataset_uri a dcat:Dataset ;
                sh:declare/sh:namespace ?uri ;
                sh:declare/sh:prefix ?prefix
        }
    """
