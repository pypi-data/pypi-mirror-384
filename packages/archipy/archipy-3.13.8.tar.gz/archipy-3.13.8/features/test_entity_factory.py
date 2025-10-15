import uuid
from datetime import datetime
from typing import Any

from features.test_entity import RelatedTestEntity, TestAdminEntity, TestEntity, TestManagerEntity


class TestEntityFactory:
    """Factory class for creating test entities.

    This factory provides methods to create different types of test entities with
    default values for testing purposes. This simplifies the creation of test
    entities in test scenarios.
    """

    @staticmethod
    def create_test_entity(
        test_uuid: uuid.UUID | None = None,
        created_at: datetime | None = None,
        description: str | None = None,
        updated_at: datetime | None = None,
        is_deleted: bool = False,
        **kwargs: Any,
    ) -> TestEntity:
        """Create a TestEntity with default or provided values.

        Args:
            test_uuid: UUID serving as primary key, defaults to a new UUID
            created_at: Creation timestamp, defaults to current datetime
            description: Optional description field
            updated_at: Optional update timestamp
            is_deleted: Whether the entity is soft-deleted, defaults to False
            **kwargs: Additional keyword arguments to pass to TestEntity

        Returns:
            TestEntity: A new TestEntity instance
        """
        if test_uuid is None:
            test_uuid = uuid.uuid4()

        if created_at is None:
            created_at = datetime.now()

        return TestEntity(
            test_uuid=test_uuid,
            created_at=created_at,
            description=description,
            updated_at=updated_at,
            is_deleted=is_deleted,
            **kwargs,
        )

    @staticmethod
    def create_test_manager_entity(
        test_uuid: uuid.UUID | None = None,
        created_at: datetime | None = None,
        created_by_uuid: uuid.UUID | None = None,
        description: str | None = None,
        updated_at: datetime | None = None,
        updated_by_uuid: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> TestManagerEntity:
        """Create a TestManagerEntity with default or provided values.

        Args:
            test_uuid: UUID serving as primary key, defaults to a new UUID
            created_at: Creation timestamp, defaults to current datetime
            created_by_uuid: UUID of the manager who created this entity, defaults to a new UUID
            description: Optional description field
            updated_at: Optional update timestamp
            updated_by_uuid: UUID of the manager who last updated this entity
            **kwargs: Additional keyword arguments to pass to TestManagerEntity

        Returns:
            TestManagerEntity: A new TestManagerEntity instance
        """
        if test_uuid is None:
            test_uuid = uuid.uuid4()

        if created_at is None:
            created_at = datetime.now()

        if created_by_uuid is None:
            created_by_uuid = uuid.uuid4()

        return TestManagerEntity(
            test_uuid=test_uuid,
            created_at=created_at,
            created_by_uuid=created_by_uuid,
            description=description,
            updated_at=updated_at,
            updated_by_uuid=updated_by_uuid,
            **kwargs,
        )

    @staticmethod
    def create_test_admin_entity(
        test_uuid: uuid.UUID | None = None,
        created_at: datetime | None = None,
        created_by_admin_uuid: uuid.UUID | None = None,
        description: str | None = None,
        updated_at: datetime | None = None,
        updated_by_admin_uuid: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> TestAdminEntity:
        """Create a TestAdminEntity with default or provided values.

        Args:
            test_uuid: UUID serving as primary key, defaults to a new UUID
            created_at: Creation timestamp, defaults to current datetime
            created_by_admin_uuid: UUID of the admin who created this entity, defaults to a new UUID
            description: Optional description field
            updated_at: Optional update timestamp
            updated_by_admin_uuid: UUID of the admin who last updated this entity
            **kwargs: Additional keyword arguments to pass to TestAdminEntity

        Returns:
            TestAdminEntity: A new TestAdminEntity instance
        """
        if test_uuid is None:
            test_uuid = uuid.uuid4()

        if created_at is None:
            created_at = datetime.now()

        if created_by_admin_uuid is None:
            created_by_admin_uuid = uuid.uuid4()

        return TestAdminEntity(
            test_uuid=test_uuid,
            created_at=created_at,
            created_by_admin_uuid=created_by_admin_uuid,
            description=description,
            updated_at=updated_at,
            updated_by_admin_uuid=updated_by_admin_uuid,
            **kwargs,
        )

    @staticmethod
    def create_related_test_entity(
        name: str = None,
        parent_id: uuid.UUID | None = None,
        parent_entity: TestEntity | None = None,
        related_uuid: uuid.UUID | None = None,
        created_at: datetime | None = None,
        value: str | None = None,
        **kwargs: Any,
    ) -> RelatedTestEntity:
        """Create a RelatedTestEntity with default or provided values.

        Either parent_id or parent_entity must be provided.

        Args:
            name: Name of the related entity, defaults to "Related Entity" with a unique suffix
            parent_id: Foreign key to parent TestEntity
            parent_entity: Parent TestEntity object (alternative to parent_id)
            related_uuid: UUID serving as primary key, defaults to a new UUID
            created_at: Creation timestamp, defaults to current datetime
            value: Optional value field
            **kwargs: Additional keyword arguments to pass to RelatedTestEntity

        Returns:
            RelatedTestEntity: A new RelatedTestEntity instance

        Raises:
            ValueError: If neither parent_id nor parent_entity is provided
        """
        if parent_id is None and parent_entity is None:
            raise ValueError("Either parent_id or parent_entity must be provided")

        if parent_entity is not None:
            parent_id = parent_entity.test_uuid  # Use test_uuid as pk_uuid is now a synonym

        if name is None:
            name = f"Related Entity {uuid.uuid4().hex[:8]}"

        if created_at is None:
            created_at = datetime.now()

        return RelatedTestEntity(
            name=name,
            parent_id=parent_id,
            related_uuid=related_uuid,
            created_at=created_at,
            value=value,
            **kwargs,
        )

    @staticmethod
    def create_entity_with_relationships(
        num_related: int = 3,
        entity_kwargs: dict[str, Any] | None = None,
        related_kwargs_list: list[dict[str, Any]] | None = None,
    ) -> tuple[TestEntity, list[RelatedTestEntity]]:
        """Create a TestEntity with a specified number of related entities.

        Args:
            num_related: Number of related entities to create, defaults to 3
            entity_kwargs: Keyword arguments for the main entity
            related_kwargs_list: List of keyword arguments for each related entity,
                                must have the same length as num_related if provided

        Returns:
            tuple: A tuple containing (TestEntity, List[RelatedTestEntity])
        """
        # Create the main entity
        entity_kwargs = entity_kwargs or {}
        entity = TestEntityFactory.create_test_entity(**entity_kwargs)

        # Create related entities
        related_entities = []
        related_kwargs_list = related_kwargs_list or [{} for _ in range(num_related)]

        if len(related_kwargs_list) != num_related:
            raise ValueError(
                f"related_kwargs_list length ({len(related_kwargs_list)}) must match num_related ({num_related})",
            )

        for i, kwargs in enumerate(related_kwargs_list):
            # Ensure we don't override parent_entity if explicitly set
            if "parent_entity" not in kwargs and "parent_id" not in kwargs:
                kwargs["parent_entity"] = entity

            if "name" not in kwargs:
                kwargs["name"] = f"Related Entity {i + 1}"

            related_entity = TestEntityFactory.create_related_test_entity(**kwargs)
            related_entities.append(related_entity)

        return entity, related_entities
