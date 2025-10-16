"""

Test Unified Data Generation System

Tests both old and new syntax for table generation and object-based responses.

License: BSD 3-Clause

"""

#
# IMPORTS
#
import pytest
from toy_api import dummy_data_generator


#
# TESTS - Object Generation
#
def test_generate_object_basic():
    """Test basic object generation."""
    user = dummy_data_generator.generate_object('core.user', row_idx=5)

    assert 'user_id' in user
    assert 'name' in user
    assert 'email' in user
    assert 'username' in user
    assert 'active' in user
    assert isinstance(user['active'], bool)


def test_generate_object_with_params():
    """Test object generation with parameter overrides."""
    user = dummy_data_generator.generate_object(
        'core.user',
        params={'user_id': '12345'},
        row_idx=5
    )

    assert user['user_id'] == '12345'  # Should be overridden
    assert 'name' in user


def test_generate_object_not_found():
    """Test error handling for non-existent object."""
    with pytest.raises(ValueError, match="Object 'fake.object' not found"):
        dummy_data_generator.generate_object('fake.object')


#
# TESTS - Old Table Syntax (Explicit Columns)
#
def test_old_syntax_basic():
    """Test old syntax with explicit column definitions."""
    config = {
        "config": {"NB_USERS": 3},
        "shared": {
            "user_id[[NB_USERS]]": "UNIQUE[int]"
        },
        "tables": {
            "users[[NB_USERS]]": {
                "user_id": "[[user_id]]",
                "name": "NAME",
                "email": "str",
                "active": "bool"
            }
        }
    }

    result = dummy_data_generator.create_table(config)

    assert len(result) == 3
    for user in result:
        assert 'user_id' in user
        assert 'name' in user
        assert 'email' in user
        assert 'active' in user
        assert isinstance(user['active'], bool)


def test_old_syntax_multiple_tables():
    """Test old syntax with multiple tables."""
    config = {
        "config": {"NB_USERS": 2, "NB_POSTS": 3},
        "shared": {
            "user_id[[NB_USERS]]": "UNIQUE[int]"
        },
        "tables": {
            "users[[NB_USERS]]": {
                "user_id": "[[user_id]]",
                "name": "NAME"
            },
            "posts[[NB_POSTS]]": {
                "post_id": "UNIQUE[int]",
                "user_id": "CHOOSE[[user_id]]",
                "title": "POST_TITLE"
            }
        }
    }

    result = dummy_data_generator.create_table(config)

    assert 'users' in result
    assert 'posts' in result
    assert len(result['users']) == 2
    assert len(result['posts']) == 3


#
# TESTS - New Table Syntax (Object References)
#
def test_new_syntax_basic():
    """Test new syntax with object reference."""
    config = {
        "config": {"NB_USERS": 3},
        "shared": {
            "user_id[[NB_USERS]]": "UNIQUE[int]"
        },
        "tables": {
            "users[[NB_USERS]]": {
                "object": "core.user",
                "user_id": "[[user_id]]"  # Override
            }
        }
    }

    result = dummy_data_generator.create_table(config)

    assert len(result) == 3
    for user in result:
        assert 'user_id' in user
        assert 'name' in user
        assert 'email' in user
        assert 'active' in user


def test_new_syntax_with_extension():
    """Test new syntax with object reference and field extension."""
    config = {
        "config": {"NB_USERS": 2},
        "shared": {
            "user_id[[NB_USERS]]": "UNIQUE[int]"
        },
        "tables": {
            "users[[NB_USERS]]": {
                "object": "core.user",
                "user_id": "[[user_id]]",
                "custom_field": "str",  # Add new field
                "is_premium": "bool"  # Add another field
            }
        }
    }

    result = dummy_data_generator.create_table(config)

    assert len(result) == 2
    for user in result:
        # Original object fields
        assert 'user_id' in user
        assert 'name' in user
        assert 'email' in user
        # Extended fields
        assert 'custom_field' in user
        assert 'is_premium' in user


def test_new_syntax_post_object():
    """Test new syntax with post object."""
    config = {
        "config": {"NB_POSTS": 5},
        "tables": {
            "posts[[NB_POSTS]]": {
                "object": "core.post"
            }
        }
    }

    result = dummy_data_generator.create_table(config)

    assert len(result) == 5
    for post in result:
        assert 'post_id' in post
        assert 'title' in post
        assert 'content' in post
        assert 'tags' in post


#
# TESTS - Mixed Syntax
#
def test_mixed_syntax():
    """Test mixing old and new syntax in same config."""
    config = {
        "config": {"NB_USERS": 2, "NB_POSTS": 3},
        "shared": {
            "user_id[[NB_USERS]]": "UNIQUE[int]"
        },
        "tables": {
            # Old syntax
            "users[[NB_USERS]]": {
                "user_id": "[[user_id]]",
                "name": "NAME",
                "email": "str"
            },
            # New syntax
            "posts[[NB_POSTS]]": {
                "object": "core.post"
            }
        }
    }

    result = dummy_data_generator.create_table(config)

    assert 'users' in result
    assert 'posts' in result
    assert len(result['users']) == 2
    assert len(result['posts']) == 3


#
# TESTS - Response Generator Integration
#
def test_response_generator_object_syntax():
    """Test response generator with object syntax."""
    from toy_api import response_generator

    # Object-based response
    response = response_generator.generate_response(
        'core.user',
        {'user_id': '123'},
        '/users/123'
    )

    assert 'user_id' in response
    assert 'name' in response


def test_response_generator_legacy_syntax():
    """Test response generator still supports legacy syntax."""
    from toy_api import response_generator

    # Legacy response type
    response = response_generator.generate_response(
        'user_detail',
        {'user_id': '123'},
        '/users/123'
    )

    assert 'id' in response
    assert response['id'] == '123'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
