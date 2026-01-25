# Contributing to LUXusb

Thank you for your interest in contributing! We welcome contributions from everyone.

## Code of Conduct

Be respectful, inclusive, and considerate of others.

## How to Contribute

### Reporting Bugs

1. Check if bug already reported in [Issues](https://github.com/solon/luxusb/issues)
2. Create new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (distro, version)
   - Relevant logs

### Suggesting Features

1. Check existing feature requests
2. Create new issue with `enhancement` label
3. Describe feature and use case
4. Discuss implementation approach

### Submitting Code

1. **Fork** the repository
2. **Clone** your fork
3. **Create branch**: `git checkout -b feature/my-feature`
4. **Make changes**:
   - Follow code style guide
   - Add tests if applicable
   - Update documentation
5. **Test**: Run `pytest` and manual tests
6. **Commit**: Use clear commit messages
7. **Push**: `git push origin feature/my-feature`
8. **Pull Request**: Create PR with description

## Development Setup

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## Code Style

- Follow PEP 8 for Python
- Use Black for formatting: `black luxusb/`
- Type hints for all functions
- Docstrings for public APIs
- Maximum line length: 100 characters

## Testing

- Write unit tests for new features
- Test USB operations with caution (destructive!)
- Test on multiple distributions if possible
- Include test cases in PR description

## Documentation

- Update docs for user-facing changes
- Add docstrings for new functions
- Update README if needed
- Include comments for complex logic

## Pull Request Process

1. Update README.md with interface changes
2. Add entry to CHANGELOG.md (if exists)
3. Ensure tests pass
4. Update documentation
5. Request review from maintainers

## Areas for Contribution

### High Priority

- [ ] Add more Linux distributions
- [ ] Improve error handling
- [ ] Add resume capability for downloads
- [ ] Better progress reporting
- [ ] Unit test coverage

### Medium Priority

- [ ] Support for multiple ISOs
- [ ] Custom ISO support
- [ ] Persistent storage partition
- [ ] Mirror selection
- [ ] Torrent downloads

### Low Priority

- [ ] Themes/customization
- [ ] Localization (i18n)
- [ ] CLI interface
- [ ] Legacy BIOS support

## Questions?

Feel free to ask questions in:
- GitHub Issues
- Discussions section
- Development chat (if available)

Thank you for contributing! 🎉
