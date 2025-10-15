# Testing Guide for aiogram-cmds

## Overview

The `aiogram-cmds` library includes a comprehensive test suite with **236 tests** achieving **97% code coverage**. The test suite is organized into three categories:

- **Unit Tests** (212 tests): Test individual components in isolation
- **Integration Tests** (14 tests): Test complete workflows and component interactions  
- **Performance Tests** (10 tests): Test performance characteristics and scalability

## Test Structure

```
tests/
├── unit/                    # Unit tests (212 tests)
│   ├── test_apply.py       # Configuration application tests (27 tests)
│   ├── test_auto_setup.py  # Auto-setup functionality tests (28 tests)
│   ├── test_builder.py     # Command builder tests (20 tests)
│   ├── test_manager.py     # Manager tests (31 tests)
│   ├── test_policy.py      # Policy tests (24 tests)
│   ├── test_registry.py    # Registry tests (15 tests)
│   ├── test_setters.py     # Setters tests (26 tests)
│   ├── test_settings.py    # Settings tests (24 tests)
│   └── test_translator.py  # Translator tests (17 tests)
├── integration/            # Integration tests (14 tests)
│   ├── conftest.py        # Shared integration fixtures
│   └── test_full_workflow.py  # Complete workflow tests
└── perf/                   # Performance tests (10 tests)
    ├── conftest.py        # Performance test fixtures
    └── test_benchmarks.py # Performance benchmarks
```

## Running Tests

### Run All Tests
```bash
uv run pytest tests/
```

### Run Specific Test Categories
```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests only  
uv run pytest tests/integration/

# Performance tests only
uv run pytest tests/perf/
```

### Run with Coverage
```bash
uv run pytest tests/ --cov=src/aiogram_cmds --cov-report=term-missing
```

### Run Specific Test Files
```bash
uv run pytest tests/unit/test_manager.py
uv run pytest tests/integration/test_full_workflow.py
```

## Test Categories

### Unit Tests

Unit tests verify individual components work correctly in isolation:

- **`test_apply.py`**: Tests configuration application, scope creation, and command setup
- **`test_auto_setup.py`**: Tests auto-setup convenience functions and default configurations
- **`test_builder.py`**: Tests command building, name validation, and i18n integration
- **`test_manager.py`**: Tests the main CommandScopeManager class and its methods
- **`test_policy.py`**: Tests command policies, flags, and profile resolution
- **`test_registry.py`**: Tests command registry and profile resolution logic
- **`test_setters.py`**: Tests command setting, clearing, and scope management
- **`test_settings.py`**: Tests settings loading, validation, and configuration
- **`test_translator.py`**: Tests translation functionality and i18n integration

### Integration Tests

Integration tests verify complete workflows and component interactions:

- **Full Workflow Tests**: Test complete setup-to-usage workflows
- **Multi-Language Integration**: Test multi-language support across components
- **Profile System Integration**: Test complex profile hierarchies and resolution
- **Scope Hierarchy Integration**: Test scope precedence and application order
- **Real-World Scenarios**: Test e-commerce and support bot scenarios
- **Error Handling Integration**: Test error handling across component boundaries

### Performance Tests

Performance tests measure scalability and efficiency:

- **Setup Performance**: Test setup time with various configuration sizes
- **User Update Performance**: Test user command update performance
- **Profile Resolution Performance**: Test profile resolution speed
- **Memory Usage Scaling**: Test memory usage with large configurations
- **Concurrent Operations**: Test performance under concurrent load
- **Large-Scale Integration**: Test performance with realistic large-scale usage
- **Scalability Limits**: Test behavior at Telegram API limits

## Coverage Report

Current test coverage: **97%**

| Module | Coverage | Status |
|--------|----------|---------|
| `__init__.py` | 100% | ✅ Perfect |
| `apply.py` | 100% | ✅ Perfect |
| `auto_setup.py` | 100% | ✅ Perfect |
| `translator.py` | 100% | ✅ Perfect |
| `registry.py` | 100% | ✅ Perfect |
| `setters.py` | 100% | ✅ Perfect |
| `customize.py` | 100% | ✅ Perfect |
| `dynamic.py` | 100% | ✅ Perfect |
| `policy.py` | 100% | ✅ Perfect |
| `manager.py` | 98% | ✅ Excellent |
| `builder.py` | 97% | ✅ Excellent |
| `settings.py` | 97% | ✅ Excellent |
| `builders_configured.py` | 83% | ✅ Good |
| `version.py` | 0% | ⚠️ Minor (just version string) |

## Test Fixtures

### Unit Test Fixtures
- `mock_bot`: Mock Bot instance for testing
- `sample_config`: Sample CmdsConfig for testing
- `sample_settings`: Sample CmdsSettings for testing

### Integration Test Fixtures
- `mock_bot`: AsyncMock Bot instance
- `mock_i18n`: Mock i18n instance with translation support
- `sample_config`: Comprehensive sample configuration
- `sample_settings`: Sample settings configuration

### Performance Test Fixtures
- `mock_bot`: Fast mock Bot instance
- `large_config`: Large configuration for performance testing

## Writing New Tests

### Unit Test Guidelines

1. **Test one component at a time**
2. **Use mocks for external dependencies**
3. **Test both success and error cases**
4. **Include edge cases and boundary conditions**
5. **Use descriptive test names**

Example:
```python
def test_command_builder_with_translator(self, mock_bot):
    """Test command building with translator integration."""
    mock_translator = Mock()
    mock_translator.return_value = "Translated command"
    
    commands = build_bot_commands(
        ["start"], 
        lang="en", 
        translator=mock_translator
    )
    
    assert len(commands) == 1
    assert commands[0].command == "start"
    mock_translator.assert_called()
```

### Integration Test Guidelines

1. **Test complete workflows**
2. **Use realistic scenarios**
3. **Test component interactions**
4. **Verify end-to-end functionality**

Example:
```python
@pytest.mark.asyncio
async def test_full_setup_workflow(self, mock_bot):
    """Test complete setup workflow."""
    manager = CommandScopeManager(bot=mock_bot)
    await manager.setup_all()
    
    await manager.update_user_commands(
        user_id=12345,
        is_registered=True,
        has_vehicle=False,
        is_during_registration=False,
    )
    
    assert mock_bot.set_my_commands.call_count >= 1
```

### Performance Test Guidelines

1. **Measure actual performance metrics**
2. **Test with realistic data sizes**
3. **Verify scalability characteristics**
4. **Set reasonable performance expectations**

Example:
```python
@pytest.mark.asyncio
async def test_setup_performance(self, mock_bot):
    """Test setup performance with large config."""
    config = create_large_config()
    
    start_time = time.time()
    manager = CommandScopeManager(bot=mock_bot, config=config)
    await manager.setup_all()
    setup_time = time.time() - start_time
    
    assert setup_time < 5.0  # Should complete in reasonable time
```

## Continuous Integration

Tests run automatically on:
- **Pull Requests**: All tests must pass
- **Main Branch**: All tests must pass
- **Releases**: All tests must pass with 97%+ coverage

## Test Maintenance

- **Regular Updates**: Tests are updated with new features
- **Coverage Monitoring**: Maintain 97%+ coverage
- **Performance Monitoring**: Ensure performance tests pass
- **Documentation**: Keep test documentation current

## Debugging Tests

### Common Issues

1. **Async Test Failures**: Ensure `@pytest.mark.asyncio` is used
2. **Mock Issues**: Verify mock setup and assertions
3. **Import Errors**: Check test imports and module paths
4. **Coverage Gaps**: Add tests for uncovered code paths

### Debug Commands

```bash
# Run with verbose output
uv run pytest tests/ -v

# Run specific test with debugging
uv run pytest tests/unit/test_manager.py::TestCommandScopeManager::test_basic_setup -v -s

# Run with coverage and show missing lines
uv run pytest tests/ --cov=src/aiogram_cmds --cov-report=term-missing
```

## Best Practices

1. **Test Coverage**: Maintain high test coverage (97%+)
2. **Test Quality**: Write meaningful, maintainable tests
3. **Performance**: Ensure tests run quickly
4. **Documentation**: Document test purpose and scenarios
5. **CI/CD**: Integrate tests into development workflow

The comprehensive test suite ensures `aiogram-cmds` is reliable, maintainable, and ready for production use.
