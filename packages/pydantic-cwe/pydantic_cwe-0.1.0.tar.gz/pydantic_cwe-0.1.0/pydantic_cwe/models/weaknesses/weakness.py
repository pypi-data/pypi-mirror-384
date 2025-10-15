from pydantic import Field
from typing import Optional, Dict, Any, Set

from ..common import CommonBase


NOT_PLATFORM_SPECIFIC = {
    'Architecture': "Not Architecture-Specific",
    'Language': "Not Language-Specific",
    'Technology': "Not Technology-Specific",
    'Operating_System': "Not OS-Specific"
}


class RelatedWeakness(CommonBase):
    """A related weakness reference"""
    nature: str = Field(..., alias="Nature")
    cwe_id: str = Field(..., alias="CWE_ID")
    view_id: Optional[str] = Field(None, alias="View_ID")
    ordinal: Optional[str] = Field(None, alias="Ordinal")


class Weakness(CommonBase):
    """A CWE weakness entry"""
    id: int = Field(..., alias="ID")
    name: str = Field(..., alias="Name")
    abstraction: str = Field(..., alias="Abstraction")
    structure: str = Field(..., alias="Structure")
    status: str = Field(..., alias="Status")
    description: str = Field(..., alias="Description")

    # Optional fields - we don't model the full structure to keep it simple
    extended_description: Optional[str] = Field(None, alias="Extended_Description")
    likelihood_of_exploit: Optional[str] = Field(None, alias="Likelihood_Of_Exploit")

    # We'll store the raw data for these complex fields
    related_weaknesses: Optional[Dict[str, Any]] = Field(None, alias="Related_Weaknesses")
    applicable_platforms: Optional[Dict[str, Any]] = Field(None, alias="Applicable_Platforms")
    affected_resources: Optional[Dict[str, Any]] = Field(None, alias="Affected_Resources")
    ordinalities: Optional[Dict[str, Any]] = Field(None, alias="Weakness_Ordinalities")
    functional_areas: Optional[Dict[str, Any]] = Field(None, alias="Functional_Areas")
    background_details: Optional[Dict[str, Any]] = Field(None, alias="Background_Details")
    modes_of_introduction: Optional[Dict[str, Any]] = Field(None, alias="Modes_Of_Introduction")
    common_consequences: Optional[Dict[str, Any]] = Field(None, alias="Common_Consequences")
    detection_methods: Optional[Dict[str, Any]] = Field(None, alias="Detection_Methods")
    potential_mitigations: Optional[Dict[str, Any]] = Field(None, alias="Potential_Mitigations")
    demonstrative_examples: Optional[Dict[str, Any]] = Field(None, alias="Demonstrative_Examples")
    observed_examples: Optional[Dict[str, Any]] = Field(None, alias="Observed_Examples")
    references: Optional[Dict[str, Any]] = Field(None, alias="References")
    mapping_notes: Optional[Dict[str, Any]] = Field(None, alias="Mapping_Notes")
    related_attack_patterns: Optional[Dict[str, Any]] = Field(None, alias="Related_Attack_Patterns")
    content_history: Optional[Dict[str, Any]] = Field(None, alias="Content_History")

    def get_ordinalities(self) -> Set[str]:
        _ordinalities = set()

        if self.ordinalities:
            _ords = self.ordinalities["Weakness_Ordinality"]

            if isinstance(_ords, dict):
                _ordinalities.add(_ords["Ordinality"])
            else:
                for ordinality in _ords:
                    _ordinalities.add(ordinality["Ordinality"])

        return _ordinalities

    def get_consequences_scope(self) -> Set[str]:
        weakness_scope = set()

        if self.common_consequences:
            for key, values in self.common_consequences.items():
                if isinstance(values, dict):
                    values = [values]

                for value in values:
                    scope = value.get('Scope')

                    if isinstance(scope, str):
                        scope = [scope]

                    weakness_scope.update(scope)

        return weakness_scope

    def get_mitigations_phases(self) -> list:
        phases = set()

        if self.potential_mitigations:
            for _, mitigations in self.potential_mitigations.items():

                if isinstance(mitigations, dict):
                    mitigations = [mitigations]

                for mitigation in mitigations:
                    if "Phase" not in mitigation:
                        continue

                    m_phase = mitigation["Phase"]

                    if isinstance(m_phase, list):
                        phases.update(m_phase)
                    else:
                        phases.add(m_phase)

        return list(phases)

    def get_introduction_phases(self) -> list:
        _modes_of_introduction = set()

        if self.modes_of_introduction:
            for _, modes in self.modes_of_introduction.items():
                if isinstance(modes, dict):
                    modes = [modes]

                for mode in modes:
                    _modes_of_introduction.add(mode["Phase"])

        return list(_modes_of_introduction)

    def get_applicable_platforms(self) -> list:
        _applicable_platforms = set()

        if self.applicable_platforms:
            for category, platforms in self.applicable_platforms.items():

                if isinstance(platforms, dict):
                    platforms = [platforms]

                for platform in platforms:
                    if "Name" in platform:
                        if platform["Name"] == NOT_PLATFORM_SPECIFIC[category]:
                            continue

                        _applicable_platforms.add(platform["Name"])

                    else:
                        if platform["Class"] == NOT_PLATFORM_SPECIFIC[category]:
                            continue

                        _applicable_platforms.add(platform["Class"])

        return list(_applicable_platforms)

    def get_code_examples(self) -> Dict[str, Any]:
        _code_examples = {}

        if self.demonstrative_examples:
            for i, example in enumerate(self.demonstrative_examples.values()):
                if "Example_Code" in example:
                    # TODO: fix parsing in the Loader since the code of the examples is not available
                    _code_examples[i]= example["Example_Code"]

        return _code_examples

    def get_detection_methods(self) -> list:
        _detection_methods = set()

        if self.detection_methods:
            for name, methods in self.detection_methods.items():
                if isinstance(methods, dict):
                    methods = [methods]

                for method in methods:
                    _detection_methods.add(method["Method"])

        return list(_detection_methods)

    def get_related_attack_pattern_ids(self) -> list:
        _related_attack_patterns = set()

        if self.related_attack_patterns:
            for _, patterns in self.related_attack_patterns.items():
                if isinstance(patterns, dict):
                    patterns = [patterns]

                for pattern in patterns:
                    _related_attack_patterns.add(int(pattern["CAPEC_ID"]))

        return list(_related_attack_patterns)
