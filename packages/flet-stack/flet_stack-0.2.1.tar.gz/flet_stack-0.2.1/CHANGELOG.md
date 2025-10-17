# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-10-16

### Added
- Support for custom initial routes via `page.route`
- `initialize_with_route()` method in `AppModel` for explicit route initialization
- `initialized` flag to track route initialization state
- Better support for authentication flows and deep linking

### Fixed
- Initial route was always defaulting to `/` regardless of `page.route` setting
- Routes list initialization now respects the page's initial route
- Proper `on_load` trigger for custom initial routes

### Improved
- Documentation updated with examples for setting initial routes
- Enhanced initialization logic to prevent route duplication on startup

## [0.2.0] - 2025-10-16

### 🚨 Breaking Changes
- **Complete architecture rewrite** to use Flet's new component system
- Requires **Flet >= 0.70.0.dev6281** (new component architecture)
- Views must now use `@ft.component` decorator
- State classes must use `@ft.observable` and `@dataclass`
- Navigation changed from `page.go()` to `ft.context.page.push_route()`
- Main app initialization changed from `ft.run(main)` to using `page.render_views(FletStack)`
- Removed automatic `ft.run()` patching - now uses explicit `FletStack` component

### Added
- `FletStack` component for managing view stack and routing
- Integration with Flet's `@ft.observable` for reactive state management
- Integration with Flet's `@ft.component` decorator
- `AppModel` class for managing routing state
- Support for `ft.context.page` in view components
- Better view stack management with proper back navigation
- Improved route state persistence across navigation
- Enhanced 404 handling with component architecture
- `render_view_for_route()` helper function for view rendering

### Changed
- View functions now return lists of controls instead of Column/Container
- State management now uses observable dataclasses
- Navigation now uses `asyncio.create_task(ft.context.page.push_route())`
- Loading indicators now properly integrate with component lifecycle
- Route matching improved for better performance
- View registration simplified with cleaner decorator pattern
- State initialization moved to observable dataclass defaults

### Improved
- Performance improvements with component-based rendering
- Better separation of concerns between routing and view logic
- More predictable state management with observables
- Cleaner API surface with explicit `FletStack` component
- Enhanced type hints and documentation

## [0.1.0] - 2025-10-06

### Added
- Initial release of flet-stack
- `@view()` decorator for route definition
- Automatic view stacking from URL paths
- State management with `state_class` parameter
- Async loading support with `on_load` parameter
- URL parameter extraction (e.g., `/user/{id}`)
- Automatic loading indicators during async operations
- Support for custom view properties via `**view_kwargs`
- Automatic routing via patched `ft.run()`
- 404 handling for undefined routes
- Prevention of duplicate route processing

### Features
- Decorator-based routing
- Automatic view stack creation from nested paths
- Built-in state management
- Support for both sync and async `on_load` functions
- Flexible parameter injection for view functions
- Regex-based route matching with named groups

[0.2.1]: https://github.com/fasilwdr/flet-stack/releases/tag/v0.2.1
[0.2.0]: https://github.com/fasilwdr/flet-stack/releases/tag/v0.2.0
[0.1.0]: https://github.com/fasilwdr/flet-stack/releases/tag/v0.1.0