"""
Tests for logging and error handling
"""

import pytest
import logging
import time

from pvdata.utils.exceptions import (
    PVDataError,
    ConfigurationError,
    ValidationError,
    FileError,
    FileNotFoundError as PVDataFileNotFoundError,
)
from pvdata.utils.logger import setup_logger, get_logger, set_log_level
from pvdata.utils.decorators import (
    handle_errors,
    log_execution,
    measure_time,
    validate_args,
    retry,
)


class TestExceptions:
    """Tests for custom exceptions"""

    def test_base_exception(self):
        """Test base PVDataError"""
        error = PVDataError("test error")
        assert str(error) == "test error"
        assert isinstance(error, Exception)

    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("config issue")
        assert isinstance(error, PVDataError)
        assert str(error) == "config issue"

    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("validation failed")
        assert isinstance(error, PVDataError)

    def test_file_error_hierarchy(self):
        """Test FileError hierarchy"""
        error = PVDataFileNotFoundError("file not found")
        assert isinstance(error, FileError)
        assert isinstance(error, PVDataError)

    def test_exception_raising(self):
        """Test that exceptions can be raised and caught"""
        with pytest.raises(ValidationError):
            raise ValidationError("test")


class TestLogger:
    """Tests for logger utilities"""

    def test_setup_logger_default(self):
        """Test default logger setup"""
        logger = setup_logger("test_default")
        assert logger.name == "test_default"
        assert logger.level == logging.INFO

    def test_setup_logger_custom_level(self):
        """Test logger with custom level"""
        logger = setup_logger("test_debug", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logger_no_console(self):
        """Test logger without console output"""
        logger = setup_logger("test_no_console", console=False)
        # Should have no stream handlers
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) == 0

    def test_setup_logger_with_file(self, tmp_path):
        """Test logger with file output"""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_file", log_file=log_file)

        logger.info("Test message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_get_logger(self):
        """Test getting logger"""
        logger = get_logger("test_get")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_get"

    def test_set_log_level(self):
        """Test setting log level"""
        logger = setup_logger("test_level", level="INFO")
        assert logger.level == logging.INFO

        set_log_level("DEBUG", "test_level")
        assert logger.level == logging.DEBUG


class TestHandleErrorsDecorator:
    """Tests for handle_errors decorator"""

    def test_handle_errors_catches_exception(self):
        """Test that decorator catches exceptions"""

        @handle_errors(ValueError, reraise=False, default_return="error")
        def failing_func():
            raise ValueError("test error")

        result = failing_func()
        assert result == "error"

    def test_handle_errors_reraises(self):
        """Test that decorator can re-raise exceptions"""

        @handle_errors(ValueError)
        def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            failing_func()

    def test_handle_errors_success(self):
        """Test that decorator doesn't interfere with success"""

        @handle_errors()
        def working_func():
            return "success"

        result = working_func()
        assert result == "success"


class TestLogExecutionDecorator:
    """Tests for log_execution decorator"""

    def test_log_execution(self, caplog):
        """Test basic logging"""
        with caplog.at_level(logging.INFO):

            @log_execution()
            def test_func():
                return "result"

            result = test_func()
            assert result == "result"
            assert "Calling test_func" in caplog.text
            assert "Finished test_func" in caplog.text

    def test_log_execution_with_args(self, caplog):
        """Test logging with arguments"""
        with caplog.at_level(logging.INFO):

            @log_execution(include_args=True)
            def test_func(x, y=10):
                return x + y

            result = test_func(5, y=15)
            assert result == 20
            assert "test_func" in caplog.text


class TestMeasureTimeDecorator:
    """Tests for measure_time decorator"""

    def test_measure_time(self, caplog):
        """Test time measurement"""
        with caplog.at_level(logging.INFO):

            @measure_time()
            def slow_func():
                time.sleep(0.1)
                return "done"

            result = slow_func()
            assert result == "done"
            assert "slow_func took" in caplog.text
            # Check that time is recorded
            assert "0." in caplog.text  # Should show decimal seconds

    def test_measure_time_custom_template(self, caplog):
        """Test custom message template"""
        with caplog.at_level(logging.INFO):

            @measure_time(message_template="{name}: completed in {elapsed:.2f}s")
            def test_func():
                return "done"

            test_func()
            assert "test_func: completed in" in caplog.text


class TestValidateArgsDecorator:
    """Tests for validate_args decorator"""

    def test_validate_args_success(self):
        """Test successful validation"""

        @validate_args(x=lambda x: x > 0, y=lambda y: isinstance(y, str))
        def test_func(x, y):
            return f"{y}: {x}"

        result = test_func(10, "value")
        assert result == "value: 10"

    def test_validate_args_failure(self):
        """Test validation failure"""

        @validate_args(x=lambda x: x > 0)
        def test_func(x):
            return x

        with pytest.raises(ValueError, match="Validation failed"):
            test_func(-5)

    def test_validate_args_multiple(self):
        """Test multiple validators"""

        @validate_args(
            x=lambda x: x > 0,
            y=lambda y: isinstance(y, str),
            z=lambda z: len(z) > 0,
        )
        def test_func(x, y, z):
            return (x, y, z)

        result = test_func(10, "test", [1, 2])
        assert result == (10, "test", [1, 2])

        with pytest.raises(ValueError):
            test_func(10, "test", [])  # Empty list fails validation


class TestRetryDecorator:
    """Tests for retry decorator"""

    def test_retry_success_first_attempt(self):
        """Test successful first attempt"""
        call_count = [0]

        @retry(max_attempts=3)
        def test_func():
            call_count[0] += 1
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count[0] == 1

    def test_retry_success_after_failures(self):
        """Test success after some failures"""
        call_count = [0]

        @retry(max_attempts=3, delay=0.01)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("fail")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count[0] == 3

    def test_retry_all_attempts_fail(self):
        """Test all attempts failing"""

        @retry(max_attempts=3, delay=0.01)
        def test_func():
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            test_func()

    def test_retry_specific_exception(self):
        """Test retry with specific exception type"""
        call_count = [0]

        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("retry this")
            return "success"

        result = test_func()
        assert result == "success"

        # Different exception should not be retried
        @retry(exceptions=(ValueError,))
        def test_func2():
            raise TypeError("don't retry this")

        with pytest.raises(TypeError):
            test_func2()
