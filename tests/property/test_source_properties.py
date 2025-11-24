"""
Property-based tests for Source model.
Feature: operator-request-distribution
"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.models.source import Source
from app.core.database import Base


# Create a separate in-memory database for testing
test_engine = create_engine("sqlite:///:memory:", echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def setup_module():
    """Create database schema once for all tests in this module."""
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    """Drop database schema after all tests."""
    Base.metadata.drop_all(bind=test_engine)


@settings(max_examples=100, deadline=1000)
@given(
    identifier=st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
    name1=st.text(min_size=1, max_size=255).filter(lambda x: x.strip()),
    name2=st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
)
def test_source_identifier_uniqueness(identifier: str, name1: str, name2: str):
    """
    Feature: operator-request-distribution, Property 6: Source identifier uniqueness
    
    For any two sources, if they have the same identifier,
    the system should reject the creation of the second source.
    
    Validates: Requirements 2.3
    """
    session = TestSessionLocal()
    try:
        # Create first source with the identifier
        source1 = Source(
            name=name1,
            identifier=identifier
        )
        session.add(source1)
        session.commit()
        
        # Attempt to create second source with the same identifier
        source2 = Source(
            name=name2,
            identifier=identifier
        )
        session.add(source2)
        
        # This should raise an IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            session.commit()
        
        # Rollback the failed transaction
        session.rollback()
        
        # Verify only one source exists with this identifier
        sources = session.query(Source).filter(Source.identifier == identifier).all()
        assert len(sources) == 1, f"Expected 1 source with identifier '{identifier}', found {len(sources)}"
        assert sources[0].name == name1, f"Expected source name to be '{name1}', got '{sources[0].name}'"
        
    finally:
        session.query(Source).delete()
        session.commit()
        session.close()
