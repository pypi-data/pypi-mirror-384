class ConfigurationError(Exception):
    pass


class ConfigurationParsingError(ConfigurationError):
    def __init__(self, message: str, file_path: str = None):
        self.file_path = file_path
        error_location = f" in {file_path}" if file_path else ""
        super().__init__(f"Configuration parsing error{error_location}: {message}")


class ConfigurationValidationError(ConfigurationError):
    def __init__(self, message: str, validation_errors: list = None):
        self.validation_errors = validation_errors or []
        super().__init__(f"Configuration validation error: {message}")


class ConfigurationFileNotFoundError(ConfigurationError):
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"Configuration file not found: {file_path}")


class ConfigurationSchemaError(ConfigurationError):
    def __init__(self, message: str, schema_path: str = None):
        self.schema_path = schema_path
        error_location = f" at {schema_path}" if schema_path else ""
        super().__init__(f"Configuration schema error{error_location}: {message}")


# Backward compatibility aliases - will be removed in future version
ConfigurationParsingException = ConfigurationParsingError
ConfigurationValidationException = ConfigurationValidationError
ConfigurationFileNotFoundException = ConfigurationFileNotFoundError
ConfigurationSchemaException = ConfigurationSchemaError
