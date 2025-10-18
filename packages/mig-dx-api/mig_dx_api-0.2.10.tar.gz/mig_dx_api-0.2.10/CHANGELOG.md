# Changelog

## [0.2.9] - 2025-09-19
### Added
- MIT License
### Changed
- `workspace_key` passed into dx.installation instead of on DX object.
- `installation` searchable by `workspace_id`
### Fixed
- N/A

## [0.2.8] - 2025-09-11
### Added
- N/A
### Changed
- N/A
### Fixed
- Bug in file type validation that prevented using signed urls

## [0.2.7] - 2025-09-11
### Added
- N/A
### Changed
- Requires `workspace_key` to be provided by user
- `find` datasets can find by `dataset_id`
### Fixed
- N/A

## [0.2.6] - 2025-08-25
### Added
- Support for `tsv` and `json` files 
### Changed
- Informative error for unsupported file types
### Fixed
- N/A

## [0.2.5] - 2025-08-19
### Added
- Support for `workpace_keys` in auth 
### Changed
- N/A
### Fixed
- N/A

## [0.2.4] - 2025-08-13
### Added
- N/A
### Changed
- `get` datasets method accepts a UUID
### Fixed
- `upload_file_to_url` sends required `Content-Type` headers in request

## [0.2.3] - 2025-08-11
### Added
- Added support for `/jobs` endpoints and tagging for datasets
### Changed
- N/A
### Fixed
- N/A

## [0.2.0] - 2025-08-08
### Added
- Commiting DIY test file that implements readme steps

### Changed
- Updated Readme
- Supporting passing BaseURL as an argument
- Get intall ID dynamically

### Fixed
- e2e fixes
- Changes to models.py to reflect tenancy changes

### Removed
- Deleting 'working example' as seemingly a PoC that doesnt use actual methods