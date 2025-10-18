"""Data models for AGR Curation API Client."""

import os
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict, model_validator
from datetime import datetime, timedelta


class APIConfig(BaseModel):
    """Configuration for AGR Curation API client."""

    base_url: HttpUrl = Field(
        default_factory=lambda: HttpUrl(
            os.getenv("ATEAM_API_URL", "https://curation.alliancegenome.org/api")
        ),
        description="Base URL for the A-Team Curation API"
    )
    okta_token: Optional[str] = Field(None, description="Okta bearer token for authentication")
    timeout: timedelta = Field(
        default=timedelta(seconds=30),
        description="Request timeout"
    )
    max_retries: int = Field(3, ge=0, description="Maximum number of retry attempts")
    retry_delay: timedelta = Field(
        default=timedelta(seconds=1),
        description="Delay between retry attempts"
    )
    verify_ssl: bool = Field(True, description="Whether to verify SSL certificates")
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional headers to include in requests"
    )

    @field_validator('timeout', 'retry_delay')
    def validate_timedelta(cls, v: timedelta) -> timedelta:
        """Ensure timedelta is positive."""
        if v.total_seconds() <= 0:
            raise ValueError("Timeout and retry_delay must be positive")
        return v

    class Config:
        """Pydantic config."""

        json_encoders = {
            timedelta: lambda v: v.total_seconds()
        }


class APIResponse(BaseModel):
    """Generic API response model."""

    total_results: Optional[int] = Field(None, alias="totalResults")
    returned_records: Optional[int] = Field(None, alias="returnedRecords")
    results: Optional[List[Dict[str, Any]]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    aggregations: Optional[Dict[str, Any]] = None


# API Response Models that match actual AGR Curation API responses

class Person(BaseModel):
    """Person model for createdBy/updatedBy fields."""

    id: Optional[int] = None
    uniqueId: Optional[str] = None
    dateCreated: Optional[datetime] = None
    dateUpdated: Optional[datetime] = None

    model_config = ConfigDict(extra='allow')


class ResourceDescriptorPage(BaseModel):
    """Resource descriptor page model."""

    id: Optional[int] = None
    internal: Optional[bool] = None
    obsolete: Optional[bool] = None
    name: Optional[str] = None
    url: Optional[str] = None

    model_config = ConfigDict(extra='allow')


class CrossReference(BaseModel):
    """Cross reference model that matches API response."""

    id: Optional[int] = None
    createdBy: Optional[Union[str, Person]] = None
    updatedBy: Optional[Union[str, Person]] = None
    internal: Optional[bool] = None
    obsolete: Optional[bool] = None
    dbDateCreated: Optional[datetime] = None
    dbDateUpdated: Optional[datetime] = None
    resourceDescriptorPage: Optional[ResourceDescriptorPage] = None

    # Original CrossReference fields
    displayName: Optional[str] = None
    pageArea: Optional[str] = None
    prefix: Optional[str] = None
    referencedCurie: Optional[str] = None
    url: Optional[str] = None

    model_config = ConfigDict(extra='allow')


class DataProvider(BaseModel):
    """Data provider model that matches API response."""

    type: Optional[str] = None
    id: Optional[int] = None
    internal: Optional[bool] = None
    obsolete: Optional[bool] = None
    abbreviation: Optional[str] = None
    fullName: Optional[str] = None
    homepageResourceDescriptorPage: Optional[ResourceDescriptorPage] = None
    sourceOrganization: Optional[str] = None
    crossReference: Optional[CrossReference] = None

    model_config = ConfigDict(extra='allow')

    @model_validator(mode='before')
    @classmethod
    def extract_source_organization(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sourceOrganization from abbreviation if not present."""
        if 'sourceOrganization' not in values and 'abbreviation' in values:
            values['sourceOrganization'] = values['abbreviation']
        return values


class NameType(BaseModel):
    """Name type model."""

    id: Optional[int] = None
    internal: Optional[bool] = None
    obsolete: Optional[bool] = None
    name: Optional[str] = None
    definition: Optional[str] = None

    model_config = ConfigDict(extra='allow')


class SynonymScope(BaseModel):
    """Synonym scope model."""

    id: Optional[int] = None
    internal: Optional[bool] = None
    obsolete: Optional[bool] = None
    name: Optional[str] = None

    model_config = ConfigDict(extra='allow')


class SlotAnnotation(BaseModel):
    """Slot annotation model that matches API response."""

    id: Optional[int] = None
    createdBy: Optional[Union[str, Person]] = None
    updatedBy: Optional[Union[str, Person]] = None
    dbDateCreated: Optional[datetime] = None
    dbDateUpdated: Optional[datetime] = None

    displayText: Optional[str] = None
    formatText: Optional[str] = None
    nameType: Optional[Union[str, NameType]] = None
    synonymScope: Optional[Union[str, SynonymScope]] = None

    model_config = ConfigDict(extra='allow')


class SecondaryId(BaseModel):
    """Secondary ID model."""

    id: Optional[int] = None
    createdBy: Optional[Union[str, Person]] = None
    updatedBy: Optional[Union[str, Person]] = None
    dbDateCreated: Optional[datetime] = None
    dbDateUpdated: Optional[datetime] = None
    secondaryId: Optional[str] = None

    model_config = ConfigDict(extra='allow')


class Gene(BaseModel):
    """Gene model that matches the actual API response structure."""

    # Primary fields that may differ from schema
    type: Optional[str] = None
    id: Optional[int] = None
    primaryExternalId: Optional[str] = None  # This is often used instead of curie
    curie: Optional[str] = None  # May be missing, use primaryExternalId as fallback

    # Audit fields that can be objects or strings
    createdBy: Optional[Union[str, Person]] = None
    updatedBy: Optional[Union[str, Person]] = None
    dateCreated: Optional[datetime] = None
    dateUpdated: Optional[datetime] = None

    # Gene-specific fields
    geneSymbol: Optional[SlotAnnotation] = None
    geneFullName: Optional[SlotAnnotation] = None
    geneSystematicName: Optional[SlotAnnotation] = None
    geneSynonyms: Optional[List[SlotAnnotation]] = None
    geneSecondaryIds: Optional[List[Union[str, SecondaryId]]] = None
    geneType: Optional[Any] = None  # Can be string or object

    # Related entities
    crossReferences: Optional[List[CrossReference]] = None
    dataProvider: Optional[DataProvider] = None
    taxon: Optional[Any] = None  # Can be string or object

    # Status fields
    obsolete: Optional[bool] = None
    internal: Optional[bool] = None

    model_config = ConfigDict(extra='allow')

    @model_validator(mode='before')
    @classmethod
    def handle_curie(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Use primaryExternalId as curie if curie is missing."""
        if 'curie' not in values and 'primaryExternalId' in values:
            values['curie'] = values['primaryExternalId']
        return values


class Allele(BaseModel):
    """Allele model that matches API response."""

    type: Optional[str] = None
    id: Optional[int] = None
    primaryExternalId: Optional[str] = None
    curie: Optional[str] = None

    createdBy: Optional[Union[str, Person]] = None
    updatedBy: Optional[Union[str, Person]] = None
    dateCreated: Optional[datetime] = None
    dateUpdated: Optional[datetime] = None

    alleleSymbol: Optional[SlotAnnotation] = None
    alleleFullName: Optional[SlotAnnotation] = None
    alleleSynonyms: Optional[List[SlotAnnotation]] = None

    crossReferences: Optional[List[CrossReference]] = None
    dataProvider: Optional[DataProvider] = None
    taxon: Optional[Any] = None

    obsolete: Optional[bool] = None
    internal: Optional[bool] = None
    isExtinct: Optional[bool] = None
    isExtrachromosomal: Optional[bool] = None
    isIntegrated: Optional[bool] = None
    laboratoryOfOrigin: Optional[Any] = None
    references: Optional[List[Any]] = None

    model_config = ConfigDict(extra='allow')

    @model_validator(mode='before')
    @classmethod
    def handle_curie(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Use primaryExternalId as curie if curie is missing."""
        if 'curie' not in values and 'primaryExternalId' in values:
            values['curie'] = values['primaryExternalId']
        return values


class Species(BaseModel):
    """Species model that matches API response."""

    type: Optional[str] = None
    id: Optional[int] = None
    curie: Optional[str] = None

    name: Optional[str] = None
    displayName: Optional[str] = None
    abbreviation: Optional[str] = None
    commonNames: Optional[List[str]] = None
    genomeAssembly: Optional[str] = None
    phylogeneticOrder: Optional[int] = None

    taxon: Optional[Any] = None

    obsolete: Optional[bool] = None
    internal: Optional[bool] = None

    model_config = ConfigDict(extra='allow')


class NCBITaxonTerm(BaseModel):
    """NCBI Taxon term model that matches API response.

    NCBITaxonTerm inherits from OntologyTerm in the AGR schema.
    This represents taxonomic species from the NCBI Taxonomy database.
    """

    type: Optional[str] = None
    id: Optional[int] = None
    curie: Optional[str] = None

    name: Optional[str] = None
    definition: Optional[str] = None
    namespace: Optional[str] = None

    # Additional fields from OntologyTerm
    dbkey: Optional[str] = None
    definitionUrls: Optional[List[str]] = None
    crossReferences: Optional[List[CrossReference]] = None
    synonyms: Optional[List[str]] = None
    subsets: Optional[List[str]] = None
    secondaryIdentifiers: Optional[List[str]] = None

    # Hierarchy fields
    ancestors: Optional[List[str]] = None
    descendants: Optional[List[str]] = None
    childCount: Optional[int] = None
    descendantCount: Optional[int] = None

    obsolete: Optional[bool] = None
    internal: Optional[bool] = None

    model_config = ConfigDict(extra='allow')


class OntologyTerm(BaseModel):
    """Ontology term model that matches API response."""

    type: Optional[str] = None
    id: Optional[int] = None
    curie: Optional[str] = None

    name: Optional[str] = None
    definition: Optional[str] = None
    namespace: Optional[str] = None

    obsolete: Optional[bool] = None
    internal: Optional[bool] = None

    childCount: Optional[int] = None
    descendantCount: Optional[int] = None
    ancestors: Optional[List[str]] = None

    model_config = ConfigDict(extra='allow')


class ExpressionAnnotation(BaseModel):
    """Expression annotation model from A-Team curation API."""

    curie: Optional[str] = Field(None, description="Compact URI")
    expressionAnnotationSubject: Optional[dict] = Field(
        None,
        description="Expression annotation subject"
    )
    expressionPattern: Optional[dict] = Field(
        None,
        description="Expression pattern"
    )
    whenExpressedStageName: Optional[str] = Field(
        None,
        description="Human-readable stage name"
    )
    whereExpressedStatement: Optional[str] = Field(
        None,
        description="Where expressed statement"
    )

    model_config = ConfigDict(extra='allow')


class AffectedGenomicModel(BaseModel):
    """Affected Genomic Model (AGM) for fish and other organisms from A-Team curation API."""

    id: Optional[int] = None
    curie: Optional[str] = Field(None, description="Compact URI")
    uniqueId: Optional[str] = None
    modEntityId: Optional[str] = None
    modInternalId: Optional[str] = None
    agmFullName: Optional[SlotAnnotation] = None
    dataProvider: Optional[DataProvider] = None
    taxon: Optional[Union[str, Dict[str, Any]]] = None
    species: Optional[Union[str, Species, Dict[str, Any]]] = None
    subtype: Optional[Union[str, Dict[str, Any]]] = None
    internal: Optional[bool] = None
    obsolete: Optional[bool] = None
    createdBy: Optional[Union[str, Person]] = None
    updatedBy: Optional[Union[str, Person]] = None
    dateCreated: Optional[datetime] = None
    dateUpdated: Optional[datetime] = None
    dbDateCreated: Optional[datetime] = None
    dbDateUpdated: Optional[datetime] = None
    crossReferences: Optional[List[CrossReference]] = None
    alleles: Optional[List[Union[str, Allele, Dict[str, Any]]]] = None
    affectedGenomicModelComponents: Optional[List[Dict[str, Any]]] = None
    parentalPopulations: Optional[List[Dict[str, Any]]] = None
    sequenceTargetingReagents: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(extra='allow')
