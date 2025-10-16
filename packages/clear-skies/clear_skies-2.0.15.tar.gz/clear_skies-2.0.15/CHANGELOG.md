# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.15] - 2025-10-16

### Removed
- Remove unused imports by @tnijboer in [#29](https://github.com/clearskies-py/clearskies/pull/29)

## [2.0.14] - 2025-10-16

### Added
- Add auto guess for akeyless secrets by @tnijboer in [#27](https://github.com/clearskies-py/clearskies/pull/27)

### Changed
- Bump version to v2.0.14 by @github-actions[bot]

## [2.0.13] - 2025-10-10

### Changed
- Bump version to v2.0.13 by @github-actions[bot]
- Broken imports by @cmancone in [#25](https://github.com/clearskies-py/clearskies/pull/25)
- Broken imports by @cmancone

### Fixed
- Callable be none by @cmancone in [#26](https://github.com/clearskies-py/clearskies/pull/26)
- Callable be none

## [2.0.12] - 2025-10-09

### Changed
- Bump version to v2.0.12 by @github-actions[bot]
- Use dict for Header class by @cmancone in [#23](https://github.com/clearskies-py/clearskies/pull/23)
- Make headers a dict

## [2.0.11] - 2025-10-09

### Changed
- Bump version to v2.0.11 by @github-actions[bot]
- Typos by @cmancone in [#24](https://github.com/clearskies-py/clearskies/pull/24)
- Input Output reorg by @cmancone

## [2.0.10] - 2025-10-06

### Changed
- Bump version to v2.0.10 by @github-actions[bot]
- Include injectable props for base secret class, and detection of… by @cmancone in [#22](https://github.com/clearskies-py/clearskies/pull/22)
- Black by @cmancone
- Include injectable props for base secret class, and detection of missing class by @cmancone

## [2.0.9] - 2025-10-01

### Added
- Add email configs by @tnijboer in [#21](https://github.com/clearskies-py/clearskies/pull/21)
- Add regex to string_list/string_list_callable and reuse them
- Add email configs

### Changed
- Bump version to v2.0.9 by @github-actions[bot]

### Removed
- Remove extra call, token is already in credentials json in [#20](https://github.com/clearskies-py/clearskies/pull/20)

## [2.0.8] - 2025-09-22

### Changed
- Bump version to v2.0.8 by @github-actions[bot]
- Move typing import to IF TYPE_CHECKING by @cmancone in [#19](https://github.com/clearskies-py/clearskies/pull/19)
- Move typing import to IF TYPE_CHECKING:

### Fixed
- Importing reorder

## [2.0.7] - 2025-09-16

### Added
- Add secrets: inherit

### Changed
- Bump version to v2.0.7 by @github-actions[bot]
- Pull latest changes from repo

### Fixed
- Uv.lock
- Import of di modules

## [2.0.6] - 2025-09-09

### Changed
- Bump version to v2.0.6 by @github-actions[bot]
- Undo local dep

### Fixed
- Fix local dependencies
- Fix docs dependency
- Fix docs use latest changelog;

## [2.0.5] - 2025-09-09

### Added
- Add changelog.md
- Add uv and release workflow
- Add uv and release workflow

### Changed
- Bump version to v2.0.5 by @github-actions[bot]
- Switch build to uv by @tnijboer in [#18](https://github.com/clearskies-py/clearskies/pull/18)
- Reuse readme.md
- Switch build to uv by @cmancone
- Workflows by @cmancone in [#17](https://github.com/clearskies-py/clearskies/pull/17)
- Merge pull request #14 from clearskies-py/docs-switch by @cmancone in [#14](https://github.com/clearskies-py/clearskies/pull/14)
- R2G? by @cmancone
- Moving along by @cmancone
- Bug fix for error message by @cmancone

### Fixed
- Allow list for json default and setable by @cmancone in [#16](https://github.com/clearskies-py/clearskies/pull/16)
- Set default and setable for json column to any config
- Allow list for json default and setable
- Right include for readme
- Docs missing folder
- Pyproject.toml
- Set input/output schema to type[Schema] by @cmancone in [#15](https://github.com/clearskies-py/clearskies/pull/15)
- Set input/output schema to type[Schema]

### Removed
- Remove dupes by @cmancone

## New Contributors
* @github-actions[bot] made their first contribution
## [2.0.4] - 2025-08-27

### Added
- Add input_outputs to the __init__.py

### Changed
- Merge pull request #13 from clearskies-py/fix/endpointgroup by @cmancone in [#13](https://github.com/clearskies-py/clearskies/pull/13)
- Merge pull request #12 from clearskies-py/autodoc by @cmancone in [#12](https://github.com/clearskies-py/clearskies/pull/12)
- Tooling fixes by @cmancone
- Url prefix ignored by endpoint group, example fixes by @cmancone
- Merge pull request #11 from clearskies-py/autodoc by @cmancone in [#11](https://github.com/clearskies-py/clearskies/pull/11)
- Schema by @cmancone
- Merge pull request #10 from clearskies-py/fix/import by @cmancone in [#10](https://github.com/clearskies-py/clearskies/pull/10)

### Fixed
- Bug in endpoint group for 404s by @cmancone
- Bug in endpoint group for 404s by @cmancone

## [2.0.3] - 2025-07-29

### Changed
- Merge pull request #9 from clearskies-py/moar-moar-docs by @cmancone in [#9](https://github.com/clearskies-py/clearskies/pull/9)
- Make the tooling happy by @cmancone
- Context docs by @cmancone

## [2.0.2] - 2025-07-24

### Changed
- Merge pull request #8 from clearskies-py/fix/decorators by @cmancone in [#8](https://github.com/clearskies-py/clearskies/pull/8)
- Merge pull request #6 from clearskies-py/moar-docs by @cmancone in [#6](https://github.com/clearskies-py/clearskies/pull/6)
- Tooling by @cmancone
- Merge branch 'main' into moar-docs by @cmancone

### Fixed
- Rename parameters_to_properties.py to decorators.py

## [2.0.1] - 2025-07-24

### Changed
- Merge pull request #7 from clearskies-py/hotfix by @cmancone in [#7](https://github.com/clearskies-py/clearskies/pull/7)
- Merge pull request #5 from clearskies-py/moar-docs by @cmancone in [#5](https://github.com/clearskies-py/clearskies/pull/5)
- ENDLESS TESTSgit add .git add . by @cmancone
- NEVER ENDING DOCSgit add .! by @cmancone
- MOAR docs by @cmancone
- MOAR documentation by @cmancone
- MOAR docs by @cmancone
- Merge pull request #4 from clearskies-py/docs by @cmancone in [#4](https://github.com/clearskies-py/clearskies/pull/4)
- Docs only on main by @cmancone
- Pre-commit by @cmancone
- And push to S3? by @cmancone
- Sigh by @cmancone
- Sigh by @cmancone
- Sudo? by @cmancone
- Ruby? by @cmancone
- The lazy way by @cmancone
- Triggers help by @cmancone
- Playing with doc building by @cmancone
- Wheee! by @cmancone
- Moving along by @cmancone
- Merge branch 'main' into docs by @cmancone

### Fixed
- Wrong key, missing types by @cmancone

## [2.0.0] - 2025-07-05

### Added
- Add black ruff check
- Add code formatting
- Add ruff, remove black, add github actions
- Added create endpoint and continuing to document column by @cmancone
- Support 3.12 and 3.11 by @cmancone
- Add some more typecasting for self
- Add timezone to test + assertEquals is deprected in favor of asserEqual
- Add configurable timezone
- Add backend to __init__.py
- Add optional deps
- Add extensions module
- Add new secret bearer flags to decorator by @cmancone
- Add issuer to JWKS check by @cmancone
- Add profile for saml auth in Akeyless
- Adding a 'mixin' like functionality to DI configuration by @cmancone
- Adding more helpers to the handler baser by @cmancone

### Changed
- Merge pull request #3 from clearskies-py/publish by @cmancone in [#3](https://github.com/clearskies-py/clearskies/pull/3)
- New version by @cmancone
- Load version via plugin by @cmancone
- Fixes per comments by @cmancone
- Re-enable tests by @cmancone
- Release test 2 by @cmancone
- Release strategy? by @cmancone
- Test out switch to tag version by @cmancone
- Try a differnt action just for kicks by @cmancone
- S/var/action by @cmancone
- Test basic pypi publishing by @cmancone
- Merge pull request #2 from clearskies-py/cleanup by @cmancone in [#2](https://github.com/clearskies-py/clearskies/pull/2)
- Happy tooling? by @cmancone
- Merge main by @cmancone
- Merge pull request #1 from tnijboer/feat/secrets-backend by @cmancone in [#1](https://github.com/clearskies-py/clearskies/pull/1)
- Move secrets backend to v2
- Mypy cleanup by @cmancone
- MOAR docs by @cmancone
- Good progress on autodocs by @cmancone
- Tweaks while documenting by @cmancone
- Lock update by @cmancone
- Minor fixes by @cmancone
- Merge pull request #31 from tnijboer/v2 by @cmancone
- Update secrets backend to v2
- Merge pull request #30 from tnijboer/v2 by @cmancone
- Merge branch 'cmancone:v2' into v2 by @tnijboer
- Merge pull request #29 from tnijboer/v2 by @cmancone
- Allow test to fail for now
- Disable older python versions
- Enable black again
- Linter fixes
- Ruff format
- Ruff linter
- Merge pull request #28 from tnijboer/v2 by @cmancone
- Mypy + pytest by @cmancone
- MOAR mypy cleanup by @cmancone
- Mypy by @cmancone
- MOAR test cleanup by @cmancone
- Cleanup by @cmancone
- Cleanup by @cmancone
- Restful API by @cmancone
- Endpoint Groups by @cmancone
- Advanced search, finally by @cmancone
- More endpoints by @cmancone
- More endpoints by @cmancone
- More endpoints and tweaks by @cmancone
- The last columns! by @cmancone
- MOAR columns by @cmancone
- MOAR columns by @cmancone
- More column docs and tests by @cmancone
- Base column docs and tests by @cmancone
- Starting on base column by @cmancone
- Belongs to docs+tests by @cmancone
- API backend tests by @cmancone
- More backends! by @cmancone
- Working API Backend by @cmancone
- Test for cursor backend by @cmancone
- Cursor Backend by @cmancone
- Working through examples by @cmancone
- More tests for endpoints by @cmancone
- Callable docs by @cmancone
- Docs on endpoint by @cmancone
- Input validation callable by @cmancone
- ... by @cmancone
- Working through validators by @cmancone
- Wheee! by @cmancone
- Some first working endpoints by @cmancone
- It's probably coming together by @cmancone
- Wheee! by @cmancone
- Base endpoint by @cmancone
- Making this up as I go by @cmancone
- Some progress on default endpoint by @cmancone
- Working through supporting stuff for endpoint base by @cmancone
- Starting on endpoints by @cmancone
- Security headers by @cmancone
- MOAR fixes by @cmancone
- Column cleanup by @cmancone
- Working through more columns by @cmancone
- Bringing in autodocs and filling out more columns by @cmancone
- Moving aong by @cmancone
- Working on the backend reorg by @cmancone
- Saving so I can change branches by @cmancone
- Merging models into model and separating out the query by @cmancone
- Filling out some columns by @cmancone
- Docs and test by @cmancone
- Just need some docs? by @cmancone
- Endless overhauls... by @cmancone
- To/from backend for columns by @cmancone
- Mypy cleanup by @cmancone
- More cleanup for configs by @cmancone
- Moving through our tests quicker now... by @cmancone
- Starting up tests for examples by @cmancone
- DI documentation and typing by @cmancone
- Whee! by @cmancone
- Importable! by @cmancone
- Continuing to polish the column definitions by @cmancone
- Slowly filling out all the columns by @cmancone
- MOAR columns by @cmancone
- Save my work! by @cmancone
- Starting to make sense by @cmancone
- A quick rundown by @cmancone
- Duh by @cmancone
- Just testing by @cmancone
- Finding a new org by @cmancone
- Saving some work by @cmancone
- Pytest in pre-commit by @cmancone
- DI via type hinting and switch to pytest by @cmancone
- Minor bugfix by @cmancone
- HasMany always overrides parent id column name by @cmancone
- Better handling of 'where' in HasMany by @cmancone
- Cache control for additional configs by @cmancone
- Update for has many by @cmancone
- A fix for the children of HasMany by @cmancone
- Finalize the ApiGetOnlyBackend by @cmancone
- Small bug fix by @cmancone
- Bug fix by @cmancone
- Missed a param by @cmancone
- Where for belong to + has many by @cmancone
- Auth pass through by @cmancone
- More flexible URL scheme for API backend by @cmancone
- And better by @cmancone
- Early test on some changes to the category tree by @cmancone
- Version bump, python-dependent python-extensions by @cmancone
- Merge pull request #19 from tnijboer/master by @cmancone
- Version bump, timestamp update, system-wide timezone by @cmancone
- Merge pull request #18 from tnijboer/master by @cmancone
- Fine then! :p by @cmancone
- And the lock by @cmancone
- Version bump by @cmancone
- Merge pull request #16 from tnijboer/master by @cmancone
- Update akeyless
- Has one column type by @cmancone
- Timestamp column type by @cmancone
- Version bump by @cmancone
- Merge pull request #15 from tnijboer/master by @cmancone
- Fix an edge case in the audit system by @cmancone
- Phone column by @cmancone
- CLI should have authorization data, even if it will always be empty by @cmancone
- Min/max value input requirements by @cmancone
- Minor updates by @cmancone
- Catch more errors by @cmancone
- Better audience check by @cmancone
- Ancient bug in autodocs for non-Auth0 JWKS by @cmancone
- JWCrypto for those who prefer it by @cmancone
- Rename dependency before we get too far by @cmancone
- Version bump by @cmancone
- Merge pull request #14 from tnijboer/optional-deps by @cmancone
- Minor updates by @cmancone
- Always include table name in where conditions by @cmancone
- A little date/string helper by @cmancone
- Created by only on create by @cmancone
- Edge case! by @cmancone
- Mix created by sources with different types by @cmancone
- Misc fixes, allow group on another table by @cmancone
- Some edge cases in auditing by @cmancone
- Audit needs masking and excludes by @cmancone
- Need another option for audit field by @cmancone
- Forgot to expose the new requirements by @cmancone
- More date-related input requirements by @cmancone
- Time-related input requirements by @cmancone
- Email validation was too strict by @cmancone
- Update get to match update in terms of fetching id via hook by @cmancone
- Didn't properly support fall-back routes by @cmancone
- Check where_for_request when checking belongs to input values by @cmancone
- Provide default status code for consistency by @cmancone
- Really shouldn't cache now by @cmancone
- Date formats and microsecond column types by @cmancone
- Make context specifics reachable for test context by @cmancone
- Sigh by @cmancone
- And the import by @cmancone
- Missed a change by @cmancone
- More ways to set values for columns by @cmancone
- Allow DI names on output map by @cmancone
- Minor addition by @cmancone
- Fixes/improvements for exposing belongs to via list/search handlers by @cmancone
- Don't drop the table by @cmancone
- Rotated secrets by @cmancone
- Version bump by @cmancone
- Proper handling of input errors by @cmancone
- Better string comparison by @cmancone
- Bugfix for list folders by @cmancone
- Merge pull request #12 from tnijboer/master by @cmancone
- Args for dynamic secrets by @cmancone
- Fix for repeating cors by @cmancone
- Ability to turn off greedy matching by @cmancone
- Strict email not required when fuzzy searching, list sub folders for secrets by @cmancone
- Better kwarg handling when calling functions through DI by @cmancone
- Version bump by @cmancone
- Death to backticks by @cmancone
- Audit headers by @cmancone
- Minor bug fi by @cmancone
- Minor bug fix by @cmancone
- A bit more flexibility by @cmancone
- Version bump by @cmancone
- A bit of flexibility for descendents by @cmancone
- Minor bug fix by @cmancone
- Minor tweak by @cmancone
- Route debugging by @cmancone
- Misc updates and fixes by @cmancone
- Version bump by @cmancone
- Auto import configs for modules by @cmancone
- Oops by @cmancone
- Working through the edge cases by @cmancone
- More minor updates/fixes by @cmancone
- Misc bugfixes by @cmancone
- Misc bug fixes by @cmancone
- Handler hooks by @cmancone
- Bug for an edge case by @cmancone
- Getting base caught up with the rest by @cmancone
- Columns for auditing by @conormancone-cimpress
- Don't need that import by @conormancone-cimpress
- No more json body for GET requests to search by @cmancone
- Version bump by @cmancone
- Extra input columns for validators by @cmancone
- Normalize the return value of to_json by @cmancone
- Allow authn|z to return 404 by @cmancone
- Fix for url quoting in lambdas... by @cmancone
- One more small tweak by @cmancone
- Better support for stand alone update handlers by @cmancone
- And test updates by @cmancone
- Need slightly different behavior by @cmancone
- Bugfix by @cmancone
- Misc bugfixes + minor reorg by @cmancone
- Minor bugfix + minor audit reorg by @cmancone
- Play nice by @cmancone
- Default by @cmancone
- Merge pull request #11 from cmancone/reformat by @cmancone
- Black by @cmancone
- Black by @cmancone
- Preparing for black by @cmancone
- Bug fixes for audit by @cmancone
- Audit by @cmancone
- Context-specifics by @cmancone
- Switch to poetry by @cmancone
- Ruff? by @cmancone
- S/yapf/ruff by @cmancone
- Use 0 for an example of pagination params by @cmancone
- More cleanup by @cmancone
- Deprecations... by @cmancone
- The ability to mock out classes from binding configs by @cmancone
- No more implicit readable ids, bugs regarding inconsistent autodoc path params by @cmancone
- Null dates FTW by @cmancone
- :( by @cmancone
- Version bump by @cmancone
- Forward/backward support for requests 2 by @cmancone
- Separate out schema by @cmancone
- Src/clearskies/ by @cmancone
- Triggers! by @cmancone
- Separate out schema helper as it will be needed elsewhere by @cmancone
- Better support for sub-routing in callables by @cmancone
- Misc bug fixes by @cmancone
- Expose the silent flag by @cmancone
- Bump by @cmancone
- Input validation hook by @cmancone
- Allow names for authz by @cmancone
- Search endpoint should accept GET for simple search by @cmancone
- Another oldie by @cmancone
- Oldest bug ever by @cmancone
- Tiny bit of logging by @cmancone
- Missing datetime as an injectable by @cmancone
- Better Handling for missing secrets by @cmancone
- Upsert by @cmancone
- Missing options for secret bearer by @cmancone
- Optionally convert to date by @cmancone
- Minor bug fixes by @cmancone
- Bugfix by @cmancone
- Merge pull request #10 from cmancone/decorators by @cmancone
- Version bump by @cmancone
- Finishing touches for now by @cmancone
- Handle DI config by @cmancone
- Starting on decorator usage by @cmancone
- Basic decorators done by @cmancone
- Working down the list by @cmancone
- Moving along by @cmancone
- Getting started by @cmancone
- Misc updates by @cmancone
- Misc bug fixes by @cmancone
- That bug was hiding for a while by @cmancone
- Return actual JSON by @cmancone
- Silent by default by @cmancone
- File backends by @cmancone
- Misc bug fixes by @cmancone
- Version bump by @cmancone
- Merge pull request #8 from tnijboer/akeyless-saml-profiles by @cmancone
- Levels and docs were backwards by @cmancone
- Boolean type by @cmancone
- Input output for converting models by @cmancone
- Category tree! by @cmancone
- Extend wheres to other operations by @cmancone
- Filter functions for list/search handlers by @cmancone
- Final authn/z tests by @cmancone
- More robust authz but needs more tests by @cmancone
- Official support for nested simple routers by @cmancone
- Better handling of relationship columns for docs by @cmancone
- Configurable model column name by @cmancone
- Clearly needs tests by @cmancone
- Minor bug by @cmancone
- Better type control by @cmancone
- Client side by @cmancone
- Related search by @cmancone
- Searching on parents via API by @cmancone
- Regrets by @cmancone
- Version bump by @cmancone
- And done by @cmancone
- N plus one done? by @cmancone
- Ground work for N+1 by @cmancone
- Cache some stuff for performance by @cmancone
- Logging by @cmancone
- Better column transformations and backend control by @cmancone
- Updates for autodocs and callables by @cmancone
- Minor fixes by @cmancone
- Give control to the handler by @cmancone
- Types! by @cmancone
- Security headers for hosted schema endpoint by @cmancone
- CLI routing data by @cmancone
- My shame is complete by @cmancone
- Better CORS routing by @cmancone
- Some missing CORS automation by @cmancone
- Misc fixes by @cmancone
- Slightly different expansion for child columns by @cmancone
- Include route parameters in autodocs by @cmancone
- Merge pull request #7 from cmancone/security-headers by @cmancone
- G2G? by @cmancone
- Merge branch 'master' into security-headers by @cmancone
- Resource routing for callables by @cmancone
- Couple more minor fixes by @cmancone
- Missing import for readable columns by @cmancone
- Minor tweak by @cmancone
- Stop hiding downstream errors by @cmancone
- And tests by @cmancone
- Return of the auto-integration by @cmancone
- 3.10 support by @cmancone
- Gt-lt could not compare non-numbers by @cmancone
- Merge pull request #6 from cmancone/many-to-many-with-data by @cmancone
- Excellent by @cmancone
- First go, needs tests by @cmancone
- Simplify routing for callables by @cmancone
- Better error handling for callables by @cmancone
- Better cooperation between simple routing and CLI by @cmancone
- Need base_url in callables to use with routing by @cmancone
- Make auth data more generally available by @cmancone
- Starting on CORS by @cmancone
- Working through the list by @cmancone
- Skeleton for a better approach to security headers by @cmancone
- No need for a security scheme for public auth by @cmancone
- Extra call by @cmancone
- Proper OAPI3.0 support, more flexible components for future by @cmancone
- Wasn't including root parameters in request doc by @cmancone
- Properly pass response headers through simple routing handler by @cmancone
- Version bump by @cmancone
- Schema bug, include respond headers on schema by @cmancone
- Properly pass through response header config by @cmancone
- More fine-tuning of routing by @cmancone
- Health Check handler by @cmancone
- Minor routing bug in schema endpoint by @cmancone
- Fix routing inconsistencies by @cmancone
- Forgot to set default value by @cmancone
- Bug fix with test by @cmancone
- Sigh by @cmancone
- Forgot to hook new backend up in DI by @cmancone
- More secrets by @cmancone
- More flexibility from datetime column by @cmancone
- Version bump, id column name bug by @cmancone
- Fixed memory backend to work with autoincrementing ids by @cmancone
- Minor bugs by @cmancone
- Test fix by @cmancone
- Minor bug fix by @cmancone
- Upstream changes in mygrations by @cmancone
- Version bump by @cmancone
- Various bug fixes/updates by @cmancone
- Minor bug fixes by @cmancone
- Version bump by @cmancone
- Minor tweaks by @cmancone
- Making use of additional configs by @cmancone
- New build process by @cmancone
- Merge pull request #5 from cmancone/moar_aws by @cmancone
- Ready for real-world testing by @cmancone
- Basic mygrations integration by @cmancone
- Pre-commit and another yapf round by @cmancone
- Doc updates by @cmancone
- Final details for callable schema and docs by @cmancone
- Tests for callable handler by @cmancone
- Starting on callable+schema, needs more tests by @cmancone
- Starting on schema for CLI handler by @cmancone
- Moving pagination to backend is complete (hopefully)! by @cmancone
- Next level of overhaul to move pagination into backends by @cmancone
- Moving pagination to backends by @cmancone
- Update one last test for auto case by @cmancone
- Done with autocasing by @cmancone
- Read cleanup, start on case swapping by @cmancone
- Final overhaul of handler separation by @cmancone
- New restful API by @cmancone
- Get handler by @cmancone
- Advanced search + tests by @cmancone
- Starting advanced search by @cmancone
- Simple search done! by @cmancone
- Slowly working through things... by @cmancone
- Finalizing details of simple search by @cmancone
- Test overhaul and separating list and search by @cmancone
- Updating tests for latest overhaul by @cmancone
- Separating out read controllers and finishing transition to single model class by @cmancone
- Combine model and models by @cmancone
- Start reorg of model/models to combine by @cmancone
- Tests! by @cmancone
- Start of dynamodb tests by @cmancone
- DynamoDB! (needs tests) by @cmancone
- DynamoDB backend that needs lots of tests by @cmancone
- String IDs, configurable id column name, and start of AWS by @cmancone
- Test docs by @cmancone
- One more silly bug by @cmancone
- Forgot to return on success by @cmancone
- Subtle logic error by @cmancone
- Version bump by @cmancone
- Fix an issue with auto import by @cmancone
- Debug mode? by @cmancone
- Searching with in operator by @cmancone
- Simple tweaks by @cmancone
- Moar docs! by @cmancone
- More docs and declare di_class at application level by @cmancone
- No periods in links by @cmancone
- Documentation updates and new DI priorities by @cmancone
- Lots more docs by @cmancone
- API backends by @cmancone
- Docs and optional memory backend replacement on tests by @cmancone
- Docs, docs, docs by @cmancone
- Docs, docs, docs by @cmancone
- Obnoxious bug fix by @cmancone
- Docs, docs, more docs by @cmancone
- Normalization and version bump by @cmancone
- More flexible context input by @cmancone
- Version bump by @cmancone
- Misc bug fixes by @cmancone
- MOAR documentation by @cmancone
- More docs by @cmancone
- Version bump by @cmancone
- Auth method documentation fixes by @cmancone
- Updates by @cmancone
- Cleanup and documentation by @cmancone
- Fixes by @cmancone
- Models by @cmancone
- Clarification and typos by @cmancone
- Nav by @cmancone
- SRP by @cmancone
- More docs! by @cmancone
- Outline of next steps by @cmancone
- Less is more by @cmancone
- Now with schema endpoint! by @cmancone
- OAI3! by @cmancone
- Very close to functional OAI3 autodoc by @cmancone
- Docs with routing by @cmancone
- Basic autodocs for the 'root' handlers by @cmancone
- Working through autodoc by @cmancone
- Version bump by @cmancone
- Starting on autodoc by @cmancone
- Version bump by @cmancone
- Another bug by @cmancone
- Bug fix by @cmancone
- Version bump by @cmancone
- Minor tweak and G2G by @cmancone
- Starting on docs, small adjustment to backend by @cmancone
- Update README.md by @cmancone
- README update by @cmancone
- Searching many-to-many (untested) by @cmancone
- Search by query parameters by @cmancone
- Some (almost) e2e tests by @cmancone
- Less caching, more input checking by @cmancone
- Tests look good by @cmancone
- First tests and minor bug fixes by @cmancone
- Untested attempt at joins by @cmancone
- JOIN parsing by @cmancone
- Working on join parsing by @cmancone
- Various fixes by @cmancone
- Minor improvements by @cmancone
- Misc bug fixes by @cmancone
- Also cache for function calls by @cmancone
- Bug fixes by @cmancone
- Missed the bind method on context by @cmancone
- Various bug fixes by @cmancone
- Untested ManyToMany by @cmancone
- Version bump by @cmancone
- AWS Contexts by @cmancone
- Tweak for config info by @cmancone
- Switching to pymysql because it is pure python and works on a lambda by @cmancone
- Minor bug is swallowing errors by @cmancone
- Authorization? by @cmancone
- Auth0 JWKs auth by @cmancone
- Untested attempt to add routing to CLI by @cmancone
- Minor updates after some production use by @cmancone
- Merge pull request #4 from cmancone/feature/native_di by @cmancone
- Pinject is dead by @cmancone
- Ditch pinject by @cmancone
- Starting on tests for DI by @cmancone
- Just laying some basic thoughts by @cmancone
- Minor fixes by @cmancone
- Version bump by @cmancone
- Merge pull request #3 from cmancone/feature/callable-cli by @cmancone
- Cli, secrets, and API backend overhaul by @cmancone
- Untested callable handler by @cmancone
- Version bump by @cmancone
- Merge pull request #2 from cmancone/feature/relationships by @cmancone
- Final changes after tests by @cmancone
- Test context (needs tests) by @cmancone
- Separate application configuration from execution context by @cmancone
- Input output is now passed in at call time rather than a singleton by @cmancone
- Load backend results in memory to avoid cursor confusion by @cmancone
- Working but issues with a shared cursor by @cmancone
- Simple routing + tests by @cmancone
- Simple routing, needs more tests by @cmancone
- WIP by @cmancone
- Column overrides by @cmancone
- Output map by @cmancone
- Better way of setting input requirements by @cmancone
- Final HasMany + tests by @cmancone
- WIP but want to save by @cmancone
- Rolling this back: this feature will cause more confusion then it will solve problems by @cmancone
- Working out just how crazy I want to get with this feature by @cmancone
- Working on can_create functionality for belongs_to by @cmancone
- Updates per codereview answers by @cmancone
- Version bump by @cmancone
- Merge pull request #1 from cmancone/feature/configurable_auth by @cmancone
- Cleanup by @cmancone
- Verified changes for auth-in-handler-config by @cmancone
- Finished tweaks and tests for auth in configuration by @cmancone
- Flow seems to work but haven't updated all the tests by @cmancone
- Finished with tests by @cmancone
- Version bump by @cmancone
- Working changes for integration testing, needs a double check by @cmancone
- Final touches and tests by @cmancone
- Testing by @cmancone
- Working filtering by @cmancone
- All operators covered by @cmancone
- Possibly the most ridiculous python I've ever written by @cmancone
- Version bump by @cmancone
- Minor tweaks by @cmancone
- Version bump by @cmancone
- Latest changes working by @cmancone
- Some more tweaks for new config method by @cmancone
- Experimenting with a new way of managing DI config by @cmancone
- Bumping version for new release by @cmancone
- Restful API with basic tests by @cmancone
- Restful API - needs tests by @cmancone
- Last changes for working example by @cmancone
- Working through changes for a fully functional example by @cmancone
- Reorg for input checking, easier column generation, and email column type by @cmancone
- Sigh by @cmancone
- Routed handlers and CRUD by @cmancone
- Basics and one working test for routing handlers by @cmancone
- Working on some basic routing by @cmancone
- Updated everything to use InputOutput by @cmancone
- Convert handlers to use new InputOutput object by @cmancone
- First public release by @cmancone
- Preparing for packaging by @cmancone
- WSGI ready? by @cmancone
- Done with column types for now by @cmancone
- Select column and more input checks/tests by @cmancone
- Tested belongs to by @cmancone
- BelongsTo - needs tests by @cmancone
- Tests for created and updated by @cmancone
- Forgot to update init.py by @cmancone
- Starting on created and updated columns - need tests by @cmancone
- Better consistency and concept of writeable column types by @cmancone
- Rename + add a brief overview of the project by @cmancone
- Fill in some tests by @cmancone
- Filling out search helpers by @cmancone
- Close to finishing up read handler by @cmancone
- Starting on read by @cmancone
- Delete functionality by @cmancone
- Auth tests + update + update tests by @cmancone
- Create handler working and tested by @cmancone
- First test on create handler: needs more! by @cmancone
- Ready to test create handler, but need some mocks by @cmancone
- Updating columns for some better config checking and adding in input checks by @cmancone
- Tests for input requirements by @cmancone
- Starting up on organization for input requirements/checking by @cmancone
- JSON conversion? by @cmancone
- Starting to fill out create handler by @cmancone
- Finished tests for handler base by @cmancone
- Couple more quick tests by @cmancone
- Start on handlers by @cmancone
- SecretBearer authentication by @cmancone
- Finished tests for api backend by @cmancone
- Small reorg, working on cursor backend tests by @cmancone
- Finished test on new models class by @cmancone
- Working on tests for models by @cmancone
- Tests on new cursor backend by @cmancone
- Moved searching to backend - needs tests everywhere by @cmancone
- Switching model to backend system by @cmancone
- JSON column type by @cmancone
- Tests for environment file by @cmancone
- Working through tests and final details by @cmancone
- More details on environment and secret configuration: needs tests by @cmancone
- Working models, some tests, starting up on environment/secrets by @cmancone
- Working on model and columns by @cmancone
- Filling out model, needs tests by @cmancone
- Len for models by @cmancone
- Query building by @cmancone
- Building out query builder by @cmancone
- Working condition parser by @cmancone
- Models and model base in progress by @cmancone

### Fixed
- Exit 1 on pytest error
- Github actions
- Pre-commit fail on poetry
- Use built-in function for non count backend
- Fix workflow black
- Fix tests
- Fix workflow
- Fix workflow
- Timestamp issue
- Fix list_sub_folders
- Tests for WSGI input/output by @cmancone

### Removed
- Remove old handlers by @cmancone
- Remove auto dependency loading by @cmancone

## New Contributors
* @cmancone made their first contribution in [#3](https://github.com/clearskies-py/clearskies/pull/3)
* @ made their first contribution
* @tnijboer made their first contribution
* @conormancone-cimpress made their first contribution
[2.0.15]: https://github.com/clearskies-py/clearskies/compare/v2.0.14..v2.0.15
[2.0.14]: https://github.com/clearskies-py/clearskies/compare/v2.0.13..v2.0.14
[2.0.13]: https://github.com/clearskies-py/clearskies/compare/v2.0.12..v2.0.13
[2.0.12]: https://github.com/clearskies-py/clearskies/compare/v2.0.11..v2.0.12
[2.0.11]: https://github.com/clearskies-py/clearskies/compare/v2.0.10..v2.0.11
[2.0.10]: https://github.com/clearskies-py/clearskies/compare/v2.0.9..v2.0.10
[2.0.9]: https://github.com/clearskies-py/clearskies/compare/v2.0.8..v2.0.9
[2.0.8]: https://github.com/clearskies-py/clearskies/compare/v2.0.7..v2.0.8
[2.0.7]: https://github.com/clearskies-py/clearskies/compare/v2.0.6..v2.0.7
[2.0.6]: https://github.com/clearskies-py/clearskies/compare/v2.0.5..v2.0.6
[2.0.5]: https://github.com/clearskies-py/clearskies/compare/v2.0.4..v2.0.5
[2.0.4]: https://github.com/clearskies-py/clearskies/compare/v2.0.3..v2.0.4
[2.0.3]: https://github.com/clearskies-py/clearskies/compare/v2.0.2..v2.0.3
[2.0.2]: https://github.com/clearskies-py/clearskies/compare/v2.0.1..v2.0.2
[2.0.1]: https://github.com/clearskies-py/clearskies/compare/v2.0.0..v2.0.1

<!-- generated by git-cliff -->
