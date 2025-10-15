from buildzr.dsl.interfaces import (
    DslWorkspaceElement,
    DslElement,
    DslRelationship,
)

from buildzr.dsl.dsl import (
    Workspace,
    Person,
    SoftwareSystem,
    Container,
    Component,
    DeploymentNode,
    InfrastructureNode,
    SoftwareSystemInstance,
    ContainerInstance,
    TypedDynamicAttribute,
)

from buildzr.dsl.relations import _Relationship

import buildzr
from typing import Set, Union, Optional, List, Dict, Any, Callable, Tuple, Sequence, Iterable, cast, Type
from typing_extensions import TypeIs

def _has_technology_attribute(obj: DslElement) -> TypeIs[Union[Container, Component]]:
    if isinstance(obj, (Person, SoftwareSystem, Workspace, SoftwareSystemInstance, ContainerInstance)):
        return False
    return True

def _has_group_attribute(obj: DslElement) -> TypeIs[Union[Person, SoftwareSystem, Container, Component]]:
    if isinstance(obj, (Workspace, DeploymentNode, InfrastructureNode, SoftwareSystemInstance, ContainerInstance)):
        return False
    return True

def _has_name_attribute(obj: DslElement) -> TypeIs[Union[Person, SoftwareSystem, Container, Component, DeploymentNode, InfrastructureNode]]:
    if isinstance(obj, (Workspace, SoftwareSystemInstance, ContainerInstance)):
        return False
    return True

def _has_environment_attribute(obj: DslElement) -> TypeIs[Union[ContainerInstance, SoftwareSystemInstance]]:
    if isinstance(obj, (Workspace, Person, SoftwareSystem, Container, Component)):
        return False
    return True

class FlattenElement:

    def __init__(self, elements: Iterable[DslElement]):
        self._elements = elements

    @property
    def ids(self) -> Set[Union[str]]:
        # Note that the `element.model` can also be a `Workspace`, whose `id` is
        # of type `int`. But since we know that these are all `DslElements` (`id` of type `str`),
        # we can safely cast all the `id`s as `str` for the type checker to be happy.
        return set([str(element.model.id) for element in self._elements])

    @property
    def names(self) -> Set[Union[str]]:

        """
        Returns the names of the elements.

        If the element is a `SoftwareSystemInstance` or `ContainerInstance`,
        which has no name attribute, it will be excluded from the result.
        """

        name_set: Set[str] = set()
        for element in self._elements:
            if _has_name_attribute(element):
                name_set.add(str(element.model.name))
        return name_set

    @property
    def tags(self) -> Set[Union[str]]:
        all_tags: Set[str] = set()
        for element in self._elements:
            tags = element.tags
            all_tags = all_tags.union(tags)
        return all_tags

class WorkspaceExpression:

    """
    A class used to filter the allowable methods and properties of the
    `Structurizr DSL` workspace. This is used to filter the elements and
    relationships in the workspace.
    """

    def __init__(self, workspace: Workspace):
        self._workspace = workspace
        self._dynamic_attributes = self._workspace._dynamic_attrs

    def software_system(self) -> TypedDynamicAttribute['SoftwareSystem']:
        """
        Returns the software system of the workspace. This is used to filter the
        elements and relationships in the workspace.
        """
        return TypedDynamicAttribute['SoftwareSystem'](self._dynamic_attributes)

    def person(self) -> TypedDynamicAttribute['Person']:
        """
        Returns the person of the workspace. This is used to filter the elements
        and relationships in the workspace.
        """
        return TypedDynamicAttribute['Person'](self._dynamic_attributes)

class ElementExpression:

    def __init__(self, element: DslElement):
        self._element = element

    @property
    def id(self) -> str:
        return cast(str, self._element.model.id)

    @property
    def type(self) -> Type:
        return type(self._element)

    @property
    def tags(self) -> Set[str]:
        return self._element.tags

    @property
    def name(self) -> Optional[str]:
        """
        Returns the name of the element (if applicable).

        Elements like `SoftwareSystemInstance` and `ContainerInstance` don't have
        a name attribute and will return None.
        """
        if _has_name_attribute(self._element):
            return self._element.model.name
        return None

    @property
    def technology(self) -> Optional[str]:
        if _has_technology_attribute(self._element):
            return self._element.model.technology
        return None

    # TODO: Make a test for this in `tests/test_expression.py`
    @property
    def parent(self) -> Optional[Union[DslWorkspaceElement, DslElement]]:
        return self._element.parent

    @property
    def children(self) -> FlattenElement:
        return FlattenElement(self._element.children)

    @property
    def sources(self) -> FlattenElement:
        return FlattenElement(self._element.sources)

    @property
    def destinations(self) -> FlattenElement:
        return FlattenElement(self._element.destinations)

    @property
    def properties(self) -> Dict[str, Any]:
        if self._element.model.properties is not None:
            return self._element.model.properties
        return dict()

    @property
    def group(self) -> Optional[str]:

        """
        Returns the group of the element (if applicable). The group is a string that is used to
        group elements in the Structurizr DSL.
        """

        if _has_group_attribute(self._element):
            return self._element.model.group
        return None

    @property
    def environment(self) -> Optional[str]:

        """
        Returns the environment of the element (if applicable). The environment
        is a string that is used to group deployment nodes and instances in the
        Structurizr DSL.
        """

        if _has_environment_attribute(self._element):
            return self._element.model.environment
        return None

    def is_instance_of(self, other: DslElement) -> bool:

        """
        Returns `True` if the element is an instance of the other element.
        """

        if isinstance(self._element, SoftwareSystemInstance):
            return self._element.model.softwareSystemId == other.model.id
        elif isinstance(self._element, ContainerInstance):
            return self._element.model.containerId == other.model.id
        return False

    def __eq__(self, element: object) -> bool:
        return isinstance(element, type(self._element)) and\
               element.model.id == self._element.model.id

class RelationshipExpression:

    def __init__(self, relationship: DslRelationship):
        self._relationship = relationship

    # TODO: Make a test for this in `tests/test_expression.py`
    @property
    def id(self) -> str:
        return cast(str, self._relationship.model.id)

    @property
    def tags(self) -> Set[str]:
        return self._relationship.tags

    @property
    def technology(self) -> Optional[str]:
        return self._relationship.model.technology

    @property
    def source(self) -> ElementExpression:
        return ElementExpression(self._relationship.source)

    @property
    def destination(self) -> ElementExpression:
        return ElementExpression(self._relationship.destination)

    @property
    def properties(self) -> Dict[str, Any]:
        if self._relationship.model.properties is not None:
            return self._relationship.model.properties
        return dict()

class Expression:

    """
    A class used to filter the elements and the relationships in the workspace.
    To be used when defining views.

    In the Structurizr DSL, these are called "Expressions". See the Structurizr docs here:
    https://docs.structurizr.com/dsl/expressions
    """

    def __init__(
        self,
        include_elements: Iterable[Union[DslElement, Callable[[WorkspaceExpression, ElementExpression], bool]]]=[lambda w, e: True],
        exclude_elements: Iterable[Union[DslElement, Callable[[WorkspaceExpression, ElementExpression], bool]]]=[],
        include_relationships: Iterable[Union[DslElement, Callable[[WorkspaceExpression, RelationshipExpression], bool]]]=[lambda w, e: True],
        exclude_relationships: Iterable[Union[DslElement, Callable[[WorkspaceExpression, RelationshipExpression], bool]]]=[],
    ) -> 'None':
        self._include_elements = include_elements
        self._exclude_elements = exclude_elements
        self._include_relationships = include_relationships
        self._exclude_relationships = exclude_relationships

    def elements(
        self,
        workspace: Workspace,
    ) -> List[DslElement]:

        filtered_elements: List[DslElement] = []

        workspace_elements = buildzr.dsl.Explorer(workspace).walk_elements()
        for element in workspace_elements:
            includes: List[bool] = []
            excludes: List[bool] = []
            for f in self._include_elements:
                if isinstance(f, DslElement):
                    includes.append(f == element)
                else:
                    includes.append(f(WorkspaceExpression(workspace), ElementExpression(element)))
            for f in self._exclude_elements:
                if isinstance(f, DslElement):
                    excludes.append(f == element)
                else:
                    excludes.append(f(WorkspaceExpression(workspace), ElementExpression(element)))
            if any(includes) and not any(excludes):
                filtered_elements.append(element)

        return filtered_elements

    def relationships(
        self,
        workspace: Workspace
    ) -> List[DslRelationship]:

        """
        Returns the relationships that are included as defined in
        `include_relationships` and excludes those that are defined in
        `exclude_relationships`. Any relationships that directly works on
        elements that are excluded as defined in `exclude_elements` will also be
        excluded.
        """

        filtered_relationships: List[DslRelationship] = []

        def _is_relationship_of_excluded_elements(
            workspace: WorkspaceExpression,
            relationship: RelationshipExpression,
            exclude_element_predicates: Iterable[Union[DslElement, Callable[[WorkspaceExpression, ElementExpression], bool]]],
        ) -> bool:
            for f in exclude_element_predicates:
                if isinstance(f, DslElement):
                    if f == relationship.source or f == relationship.destination:
                        return True
                else:
                    if f(workspace, relationship.source) or f(workspace, relationship.destination):
                        return True
            return False

        workspace_relationships = buildzr.dsl.Explorer(workspace).walk_relationships()

        for relationship in workspace_relationships:

            includes: List[bool] = []
            excludes: List[bool] = []

            for f in self._include_relationships:
                if isinstance(f, DslElement):
                    includes.append(f == relationship)
                else:
                    includes.append(f(WorkspaceExpression(workspace), RelationshipExpression(relationship)))

            for f in self._exclude_relationships:
                if isinstance(f, DslElement):
                    excludes.append(f == relationship)
                else:
                    excludes.append(f(WorkspaceExpression(workspace), RelationshipExpression(relationship)))

            # Also exclude relationships whose source or destination elements
            # are excluded.
            excludes.append(
                _is_relationship_of_excluded_elements(
                    WorkspaceExpression(workspace),
                    RelationshipExpression(relationship),
                    self._exclude_elements,
                )
            )

            if any(includes) and not any(excludes):
                filtered_relationships.append(relationship)

        return filtered_relationships