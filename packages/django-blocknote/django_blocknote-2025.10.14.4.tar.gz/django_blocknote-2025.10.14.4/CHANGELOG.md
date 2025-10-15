# CHANGELOG

<!--next-version-placeholder-->

## [2025.10.14.4]

### Maintenance
- Add min-width for visual consistancy (menu) [#74](https://github.com/Dunwright-dev/django-blocknote/pull/74)


## [2025.10.14.3]

### Bug Fixes
- Prevent group header accumulation in submenu filtering (Menu) [#56](https://github.com/Dunwright-dev/django-blocknote/pull/56)


## [2025.10.14.2]

### Bug Fixes
- Fix menu min-height and recalc max-height (menu) [#71](https://github.com/Dunwright-dev/django-blocknote/pull/71)


## [2025.10.14.1]

### Maintenance
- Removed redundant config and used shortcut value (menu) [#69](https://github.com/Dunwright-dev/django-blocknote/pull/69)


## [2025.10.13.2]

### Maintenance
- Upgrade BlockNote and all dependencies to latest versions (deps) [#64](https://github.com/Dunwright-dev/django-blocknote/pull/64)


## [2025.10.13.1]

### Maintenance
- Upgrade BlockNote and all dependencies to latest versions (deps) [#64](https://github.com/Dunwright-dev/django-blocknote/pull/64)
- Move the debug info to the bottom of the page (example) [#67](https://github.com/Dunwright-dev/django-blocknote/pull/67)


## [2025.10.10.2]

### Bug Fixes
- Alias list is properly built for filtering (menu) [#61](https://github.com/Dunwright-dev/django-blocknote/pull/61)


## [2025.10.10.1]

### Bug Fixes
- Alias list is properly built for filtering (menu) [#61](https://github.com/Dunwright-dev/django-blocknote/pull/61)
- Update base and template menus for consistency with blocks (menu) [#59](https://github.com/Dunwright-dev/django-blocknote/pull/59)
- Updated css so selected menu hover is aligned correctly (menu) [#59](https://github.com/Dunwright-dev/django-blocknote/pull/59)


## [2025.07.08.1]

### Maintenance
- Add debug logging to change log script (git) [#52](https://github.com/Dunwright-dev/django-blocknote/pull/52)
- Update packages (deps) [#52](https://github.com/Dunwright-dev/django-blocknote/pull/52)

### Bug Fixes
- Remove + sidebar & refactor (menu) [#52](https://github.com/Dunwright-dev/django-blocknote/pull/52)
  > - Major refactor getting ready to add working `+` for mouse menu navigation.
- Remove memory leaks from widget manager.
- Remove unnecessary editor create/destroy behavior.
- Remove editor flicker when transition read-only/edit.
- Add error handling and user notifications for template load errors.


## [2025.07.05.2]

### Maintenance
- Fix typo in yaml file (git) [#48](https://github.com/Dunwright-dev/django-blocknote/pull/48)
- Remove version from script, GHA and README (version) [#48](https://github.com/Dunwright-dev/django-blocknote/pull/48)


## [2025.07.05.1]

### Features
- Add fuzzy find and improve ui (menu) [#49](https://github.com/Dunwright-dev/django-blocknote/pull/49)


## [2025.07.03.3]

### Maintenance
- Remove commented out code (app) [#46](https://github.com/Dunwright-dev/django-blocknote/pull/46)


## [2025.07.03.2]

### Maintenance
- Remove redundant template preview (admin) [#41](https://github.com/Dunwright-dev/django-blocknote/pull/41)

### Documentation
- Update info (README) [#41](https://github.com/Dunwright-dev/django-blocknote/pull/41)
- Update to correct readme path (readme) [#41](https://github.com/Dunwright-dev/django-blocknote/pull/41)


## [2025.07.03.1]

### Documentation
- Add template max size config (template) [#43](https://github.com/Dunwright-dev/django-blocknote/pull/43)

### Bug Fixes
- Add template config (frontend) [#43](https://github.com/Dunwright-dev/django-blocknote/pull/43)
- Add template config (template) [#43](https://github.com/Dunwright-dev/django-blocknote/pull/43)


## [2025.07.02.1]

### Maintenance
- Update doc template place holder (model) [#40](https://github.com/Dunwright-dev/django-blocknote/pull/40)

### Bug Fixes
- Typo in pyproject link (changelog) [#39](https://github.com/Dunwright-dev/django-blocknote/pull/39)


## [2025.07.01.1]

### Maintenance
- Update import paths (example) [#37](https://github.com/Dunwright-dev/django-blocknote/pull/37)

### Documentation
- Add/update for breaking changes (quickstart) [#37](https://github.com/Dunwright-dev/django-blocknote/pull/37)


## [2025.06.30.1]

### Maintenance
- Add back/front end machinery for templates (template) [#35](https://github.com/Dunwright-dev/django-blocknote/pull/35)

### Documentation
- Add quickstart guide (how-to) [#35](https://github.com/Dunwright-dev/django-blocknote/pull/35)

### Bug Fixes
- Replace readonly context constant (readonly) [#33](https://github.com/Dunwright-dev/django-blocknote/pull/33)


## [2025.06.24.1]

### Maintenance
- Add basic document template machinery (template) [#32](https://github.com/Dunwright-dev/django-blocknote/pull/32)

### Documentation
- Add doc templates management (how-to) [#32](https://github.com/Dunwright-dev/django-blocknote/pull/32)
- Add reference and explanation documents (template) [#32](https://github.com/Dunwright-dev/django-blocknote/pull/32)

### Features
- Add user template model and admin (template) [#32](https://github.com/Dunwright-dev/django-blocknote/pull/32)


## [2025.06.23.1]

### Maintenance
- Add slash menu and context passing (template) [#30](https://github.com/Dunwright-dev/django-blocknote/pull/30)

### Documentation
- Add template data flow reference (template) [#30](https://github.com/Dunwright-dev/django-blocknote/pull/30)

### Features
- Add default document templates (template) [#30](https://github.com/Dunwright-dev/django-blocknote/pull/30)


## [2025.06.08.2]

### Maintenance
- Simplify template and css layouts (ui) [#28](https://github.com/Dunwright-dev/django-blocknote/pull/28)


## [2025.06.08.1]

### Maintenance
- Consolidate templates and css into single files (widget) [#26](https://github.com/Dunwright-dev/django-blocknote/pull/26)


## [2025.06.07.3]

### Bug Fixes
- Typo in widget breaking config (editor) [#24](https://github.com/Dunwright-dev/django-blocknote/pull/24)


## [2025.06.07.2]

### Maintenance
- Add media and read only for admin (widget) [#22](https://github.com/Dunwright-dev/django-blocknote/pull/22)


## [2025.06.07.1]

### Code Refactoring
- Config falls back to settings (widget) [#17](https://github.com/Dunwright-dev/django-blocknote/pull/17)


## [2025.06.06.4]

### Bug Fixes
- Increase url max_length (url) [#19](https://github.com/Dunwright-dev/django-blocknote/pull/19)


## [2025.06.06.3]

### Maintenance
- Register and Admin for UnusedImageURLS (admin) [#16](https://github.com/Dunwright-dev/django-blocknote/pull/16)


## [2025.06.06.2]

### Maintenance
- Add configurable slash menu (menu) [#14](https://github.com/Dunwright-dev/django-blocknote/pull/14)
- Expose react globally, update example setup (conf) [#14](https://github.com/Dunwright-dev/django-blocknote/pull/14)


## [2025.06.06.1]

### Maintenance
- Add front-end machinery for image removal handling (image) [#12](https://github.com/Dunwright-dev/django-blocknote/pull/12)
- Add image deletion machinery (img) [#12](https://github.com/Dunwright-dev/django-blocknote/pull/12)
- Improve dev experience with builds and setup (dev) [#12](https://github.com/Dunwright-dev/django-blocknote/pull/12)
- Update setup and test coverage (dev) [#12](https://github.com/Dunwright-dev/django-blocknote/pull/12)


## [2025.06.04.1]

### Maintenance
- Add custom image handling through config (image) [#10](https://github.com/Dunwright-dev/django-blocknote/pull/10)
- Add deps, update setup.sh (deps) [#10](https://github.com/Dunwright-dev/django-blocknote/pull/10)
- Update image upload handling (image) [#10](https://github.com/Dunwright-dev/django-blocknote/pull/10)
- Update scripts and image handling (image) [#10](https://github.com/Dunwright-dev/django-blocknote/pull/10)


## [2025.05.31.2]

### Maintenance
- Add pyproject to version updater (version) [#8](https://github.com/Dunwright-dev/django-blocknote/pull/8)


## [2025.05.31.1]

### Maintenance
- Update deps, example setup shell (conf) #5

### Bug Fixes
- Add valid json if none exists on form save (editor) #5


## [2025.05.30.1]

### Maintenance
- Add machinery for image uploads, not connected (backend) #3
- Additions for image upload (frontend) #3
- Update asset name check (assets) #3
- Update example project and deps (setup) #3

### Testing
- Update for js to ts refactor (fields) #3


## [2025.05.29.1]

### Maintenance
- Update getting assets and conf (config) #1
- Update workflows (git) #1

### Documentation
- Update config and extensions (conf) #1

### Testing
- Add test infra and tests (assets) #1


