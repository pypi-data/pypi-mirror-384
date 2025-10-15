import pytest
from unittest.mock import MagicMock, patch
from tee import Model, Int, Str, set_default_db


class TestUser(Model):
    id = Int()
    name = Str()
    email = Str()


@pytest.fixture
def mock_db():
    """Mock database setup for testing"""
    with patch('tee.connection.pymysql.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Setup database configuration
        set_default_db(
            host="localhost",
            port=3306,
            user="test",
            password="test",
            database="test_db"
        )
        
        yield {
            'connection': mock_conn,
            'cursor': mock_cursor,
            'connect': mock_connect
        }


class TestModel:
    def test_model_creation(self):
        """Test basic model creation and field access"""
        user = TestUser(id=1, name="张三", email="test@example.com")
        
        assert user.id == 1
        assert user.name == "张三"
        assert user.email == "test@example.com"
    
    def test_to_dict(self):
        """Test model to_dict method"""
        user = TestUser(id=1, name="张三", email="test@example.com")
        user_dict = user.to_dict()
        
        expected = {
            "id": 1,
            "name": "张三", 
            "email": "test@example.com"
        }
        assert user_dict == expected
    
    def test_get_table_name(self):
        """Test table name generation"""
        assert TestUser.get_table_name() == "test_user"
    
    def test_get_field_names(self):
        """Test field names retrieval"""
        field_names = TestUser.get_field_names()
        assert set(field_names) == {"id", "name", "email"}


class TestSelect:
    def test_select_query_building(self, mock_db):
        """Test select query building"""
        mock_db['cursor'].fetchall.return_value = [
            {"id": 1, "name": "张三", "email": "test@example.com"}
        ]
        
        users = TestUser.select().list()
        
        # Verify SQL was called
        mock_db['cursor'].execute.assert_called()
        call_args = mock_db['cursor'].execute.call_args[0]
        assert "SELECT" in call_args[0]
        assert "test_user" in call_args[0]
    
    def test_select_with_conditions(self, mock_db):
        """Test select with WHERE conditions"""
        mock_db['cursor'].fetchall.return_value = []
        
        TestUser.select().eq(TestUser.id, 1).list()
        
        mock_db['cursor'].execute.assert_called()
        call_args = mock_db['cursor'].execute.call_args
        sql = call_args[0][0]
        args = call_args[0][1]
        
        assert "WHERE" in sql
        assert "id = %s" in sql
        assert 1 in args


class TestInsert:
    def test_insert_execute(self, mock_db):
        """Test insert operation"""
        mock_db['cursor'].execute.return_value = 1
        
        result = TestUser.insert().execute({
            "name": "张三",
            "email": "test@example.com"
        })
        
        mock_db['cursor'].execute.assert_called()
        call_args = mock_db['cursor'].execute.call_args[0]
        assert "INSERT INTO" in call_args[0]
        assert "test_user" in call_args[0]


class TestUpdate:
    def test_update_execute(self, mock_db):
        """Test update operation"""
        mock_db['cursor'].execute.return_value = 1
        
        TestUser.update().eq(TestUser.id, 1).set(name="李四").execute()
        
        mock_db['cursor'].execute.assert_called()
        call_args = mock_db['cursor'].execute.call_args[0]
        assert "UPDATE" in call_args[0]
        assert "test_user" in call_args[0]
        assert "WHERE" in call_args[0]


class TestDelete:
    def test_delete_execute(self, mock_db):
        """Test delete operation"""
        mock_db['cursor'].execute.return_value = 1
        
        TestUser.delete().eq(TestUser.id, 1).execute()
        
        mock_db['cursor'].execute.assert_called()
        call_args = mock_db['cursor'].execute.call_args[0]
        assert "DELETE FROM" in call_args[0]
        assert "test_user" in call_args[0]
        assert "WHERE" in call_args[0]
    
    def test_delete_without_condition_raises_error(self):
        """Test that delete without conditions raises an error"""
        with pytest.raises(ValueError, match="Delete operation requires at least one condition"):
            TestUser.delete().execute()


if __name__ == "__main__":
    pytest.main([__file__])