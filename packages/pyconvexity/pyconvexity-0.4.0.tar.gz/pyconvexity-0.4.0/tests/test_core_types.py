"""
Tests for core types in PyConvexity.
"""

import pytest
from pyconvexity.core.types import StaticValue, TimeseriesPoint, AttributeValue


class TestStaticValue:
    """Test StaticValue functionality"""
    
    def test_float_value(self):
        value = StaticValue(123.45)
        assert value.data_type() == "float"
        assert value.as_f64() == 123.45
        assert value.value() == 123.45
    
    def test_int_value(self):
        value = StaticValue(42)
        assert value.data_type() == "int"
        assert value.as_f64() == 42.0
        assert value.value() == 42
    
    def test_bool_value(self):
        value = StaticValue(True)
        assert value.data_type() == "boolean"
        assert value.as_f64() == 1.0
        assert value.value() is True
        
        value_false = StaticValue(False)
        assert value_false.as_f64() == 0.0
        assert value_false.value() is False
    
    def test_string_value(self):
        value = StaticValue("hello")
        assert value.data_type() == "string"
        assert value.value() == "hello"
    
    def test_json_serialization(self):
        # Test that JSON serialization matches expected format
        float_val = StaticValue(123.45)
        assert float_val.to_json() == "123.45"
        
        int_val = StaticValue(42)
        assert int_val.to_json() == "42"
        
        bool_val = StaticValue(True)
        assert bool_val.to_json() == "true"
        
        str_val = StaticValue("hello")
        assert str_val.to_json() == '"hello"'
    
    def test_equality(self):
        val1 = StaticValue(123.45)
        val2 = StaticValue(123.45)
        val3 = StaticValue(67.89)
        
        assert val1 == val2
        assert val1 != val3
    
    def test_invalid_type(self):
        with pytest.raises(ValueError):
            StaticValue([1, 2, 3])  # List not supported


class TestTimeseriesPoint:
    """Test TimeseriesPoint functionality"""
    
    def test_creation(self):
        point = TimeseriesPoint(timestamp=1609459200, value=123.45, period_index=0)
        assert point.timestamp == 1609459200
        assert point.value == 123.45
        assert point.period_index == 0
    
    def test_type_conversion(self):
        # Test that types are properly converted
        point = TimeseriesPoint(timestamp="1609459200", value="123.45", period_index="0")
        assert isinstance(point.timestamp, int)
        assert isinstance(point.value, float)
        assert isinstance(point.period_index, int)


class TestAttributeValue:
    """Test AttributeValue functionality"""
    
    def test_static_attribute(self):
        static_val = StaticValue(123.45)
        attr = AttributeValue.static(static_val)
        
        assert attr.is_static()
        assert not attr.is_timeseries()
        assert attr.static_value == static_val
        assert attr.timeseries_value is None
    
    def test_timeseries_attribute(self):
        points = [
            TimeseriesPoint(0, 100.0, 0),
            TimeseriesPoint(3600, 150.0, 1),
            TimeseriesPoint(7200, 200.0, 2)
        ]
        attr = AttributeValue.timeseries(points)
        
        assert attr.is_timeseries()
        assert not attr.is_static()
        assert attr.timeseries_value == points
        assert attr.static_value is None
    
    def test_invalid_attribute_value(self):
        with pytest.raises(ValueError):
            AttributeValue("invalid")  # String not supported directly
