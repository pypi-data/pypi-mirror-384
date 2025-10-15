import pytest
from jancodegen import jan


class TestJANCodeGenerator:
    """Test suite for JAN code generation functions."""

    def test_get_last_jan_digit(self):
        """Test the check digit calculation function."""
        # Test cases with known valid codes
        test_cases = [
            ("12345678901", 2),  # GTIN-12 example
            ("01234567890", 5),  # Another example
            ("99999999999", 3),  # Edge case with 9s
            ("00000000000", 0),  # Edge case with 0s
        ]

        for code, expected_check in test_cases:
            assert jan._get_last_jan_digit(code) == expected_check

    def test_random_gtin_13(self):
        """Test GTIN-13 code generation."""
        code = jan.random_gtin_13()

        # Check length
        assert len(code) == 13

        # Check all characters are digits
        assert code.isdigit()

        # Check check digit is valid
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Check randomness (generate multiple and ensure they're different)
        codes = [jan.random_gtin_13() for _ in range(10)]
        assert len(set(codes)) > 1  # At least some should be different

    def test_random_gtin_8(self):
        """Test GTIN-8 code generation."""
        code = jan.random_gtin_8()

        # Check length
        assert len(code) == 8

        # Check all characters are digits
        assert code.isdigit()

        # Check check digit is valid
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

    def test_random_gtin_14(self):
        """Test GTIN-14 code generation."""
        code = jan.random_gtin_14()

        # Check length
        assert len(code) == 14

        # Check all characters are digits
        assert code.isdigit()

        # Check starts with '1'
        assert code.startswith('1')

        # Check check digit is valid
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

    def test_random_upc_12(self):
        """Test UPC-12 code generation."""
        code = jan.random_upc_12()

        # Check length
        assert len(code) == 12

        # Check all characters are digits
        assert code.isdigit()

        # Check check digit is valid
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

    def test_random_sscc_18(self):
        """Test SSCC-18 code generation."""
        code = jan.random_sscc_18()

        # Check length
        assert len(code) == 18

        # Check all characters are digits
        assert code.isdigit()

        # Check starts with '0'
        assert code.startswith('0')

        # Check check digit is valid
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

    def test_random_grai_14(self):
        """Test GRAI-14 code generation."""
        code = jan.random_grai_14()

        # Check length
        assert len(code) == 14

        # Check all characters are digits
        assert code.isdigit()

        # Check starts with '0'
        assert code.startswith('0')

        # Check check digit is valid
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

    @pytest.mark.parametrize("func,expected_length,prefix", [
        (jan.random_gtin_13, 13, None),
        (jan.random_gtin_8, 8, None),
        (jan.random_gtin_14, 14, '1'),
        (jan.random_upc_12, 12, None),
        (jan.random_sscc_18, 18, '0'),
        (jan.random_grai_14, 14, '0'),
    ])
    def test_all_functions_return_valid_codes(self, func, expected_length, prefix):
        """Parameterized test for all generation functions."""
        code = func()

        # Check length
        assert len(code) == expected_length

        # Check all characters are digits
        assert code.isdigit()

        # Check prefix if specified
        if prefix:
            assert code.startswith(prefix)

        # Check check digit is valid
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

    def test_is_valid(self):
        """Test the is_valid function."""
        valid_codes = [
            jan.random_gtin_13(),
            jan.random_gtin_8(),
            jan.random_gtin_14(),
            jan.random_upc_12(),
            jan.random_sscc_18(),
            jan.random_grai_14(),
        ]

        for code in valid_codes:
            assert jan.is_valid(code) is True

        invalid_codes = [
            "1234567",          # Too short
            "12345678901234",   # Too long
            "ABCDEFGHIJKLM",    # Non-digit characters
            "1234567890123X",   # Invalid check digit
            "1234567890133",    # Valid length but invalid check digit
            "64312914",
            "08705308058149",
            "08705308058140",
        ]

        for code in invalid_codes:
            assert jan.is_valid(code) is False

    def test_random_gtin_13_with_prefix(self):
        """Test GTIN-13 generation with custom prefix."""
        # Test with empty prefix (default behavior)
        code = jan.random_gtin_13("")
        assert len(code) == 13
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with valid prefix
        code = jan.random_gtin_13("123")
        assert len(code) == 13
        assert code.startswith("123")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with invalid prefix (non-digit)
        with pytest.raises(ValueError, match="Prefix must be digits"):
            jan.random_gtin_13("abc")

        # Test with invalid prefix (too long)
        with pytest.raises(ValueError, match="Prefix must be digits and less than or equal 12 characters"):
            jan.random_gtin_13("1234567890123")

    def test_random_gtin_8_with_prefix(self):
        """Test GTIN-8 generation with custom prefix."""
        # Test with empty prefix
        code = jan.random_gtin_8("")
        assert len(code) == 8
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with valid prefix
        code = jan.random_gtin_8("12")
        assert len(code) == 8
        assert code.startswith("12")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with invalid prefix
        with pytest.raises(ValueError, match="Prefix must be digits and less than or equal 7 characters"):
            jan.random_gtin_8("12345678")

    def test_random_gtin_14_with_prefix(self):
        """Test GTIN-14 generation with custom prefix."""
        # Test with empty prefix (should default to '1')
        code = jan.random_gtin_14("")
        assert len(code) == 14
        assert code.startswith("1")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with custom prefix
        code = jan.random_gtin_14("45")
        assert len(code) == 14
        assert code.startswith("45")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with invalid prefix
        with pytest.raises(ValueError, match="Prefix must be digits and less than or equal 13 characters"):
            jan.random_gtin_14("12345678901234")

    def test_random_upc_12_with_prefix(self):
        """Test UPC-12 generation with custom prefix."""
        # Test with empty prefix
        code = jan.random_upc_12("")
        assert len(code) == 12
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with valid prefix
        code = jan.random_upc_12("123")
        assert len(code) == 12
        assert code.startswith("123")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with invalid prefix
        with pytest.raises(ValueError, match="Prefix must be digits and less than or equal 11 characters"):
            jan.random_upc_12("123456789012")

    def test_random_sscc_18_with_prefix(self):
        """Test SSCC-18 generation with custom prefix."""
        # Test with empty prefix (should default to '0')
        code = jan.random_sscc_18("")
        assert len(code) == 18
        assert code.startswith("0")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with custom prefix
        code = jan.random_sscc_18("12")
        assert len(code) == 18
        assert code.startswith("12")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with invalid prefix
        with pytest.raises(ValueError, match="Prefix must be digits and less than or equal 17 characters"):
            jan.random_sscc_18("123456789012345678")

    def test_random_grai_14_with_prefix(self):
        """Test GRAI-14 generation with custom prefix."""
        # Test with empty prefix (should default to '0')
        code = jan.random_grai_14("")
        assert len(code) == 14
        assert code.startswith("0")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with custom prefix
        code = jan.random_grai_14("45")
        assert len(code) == 14
        assert code.startswith("45")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with invalid prefix
        with pytest.raises(ValueError, match="Prefix must be digits and less than or equal 13 characters"):
            jan.random_grai_14("12345678901234")

    def test_random_jan_code(self):
        """Test custom length JAN code generation."""
        # Test with minimum length (4)
        code = jan.random_jan_code(4)
        assert len(code) == 4
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with maximum length (32)
        code = jan.random_jan_code(32)
        assert len(code) == 32
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with custom length and empty prefix
        code = jan.random_jan_code(10, "")
        assert len(code) == 10
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test with custom length and prefix
        code = jan.random_jan_code(15, "123")
        assert len(code) == 15
        assert code.startswith("123")
        assert code.isdigit()
        base_code = code[:-1]
        expected_check = jan._get_last_jan_digit(base_code)
        assert int(code[-1]) == expected_check

        # Test invalid length (too small)
        with pytest.raises(ValueError):
            jan.random_jan_code(3)

        # Test invalid length (too large)
        with pytest.raises(ValueError):
            jan.random_jan_code(33)

        # Test invalid length (not integer)
        with pytest.raises(ValueError):
            jan.random_jan_code("10")

        # Test invalid prefix (non-digit)
        with pytest.raises(ValueError):
            jan.random_jan_code(10, "abc")

        # Test invalid prefix (too long)
        with pytest.raises(ValueError):
            jan.random_jan_code(10, "1234567890")
