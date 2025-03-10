# Changelog

<!--next-version-placeholder-->

## v4.2.3 (2025-02-12)

### Fix

* Set log level once in processor and reporter ([`29ae481`](https://github.com/MozillaSecurity/bugmon-tc/commit/29ae4818d088423538c71d980d14882c23fe9219))

## v4.2.2 (2025-02-12)

### Fix

* Log level can only be set once ([`a7de51d`](https://github.com/MozillaSecurity/bugmon-tc/commit/a7de51d0c5d0032246c0fa9b4b8da7af82fa1973))

## v4.2.1 (2025-02-12)

### Fix

* Propagate debug parameter to sub tasks ([`7f25fd1`](https://github.com/MozillaSecurity/bugmon-tc/commit/7f25fd1216044a4129f8de49ad641cdb34b13cc5))
* Propagate debug parameter to sub tasks ([`3f35d73`](https://github.com/MozillaSecurity/bugmon-tc/commit/3f35d73855daae520aa398708bc7a4685ff5e304))

## v4.2.0 (2025-02-12)

### Feature

* Enable debug logging via task env ([`18940a7`](https://github.com/MozillaSecurity/bugmon-tc/commit/18940a7b75ee3753076193451ad2c40a33ad2bac))

## v4.1.0 (2025-02-11)

### Feature

* Allow setting debug logging via env variable ([`449cd1d`](https://github.com/MozillaSecurity/bugmon-tc/commit/449cd1d51153c48ebab94fd44a880c76bf1529c8))

## v4.0.1 (2025-01-06)

### Fix

* Ensure launch.sh is evaluated by bash ([`5c56974`](https://github.com/MozillaSecurity/bugmon-tc/commit/5c5697415f5963ddbcf797b773c449c1357b8ffd))

## v4.0.0 (2024-11-12)

### Feature

* Drop support for python 3.8 ([`3ddb139`](https://github.com/MozillaSecurity/bugmon-tc/commit/3ddb139d7414119589bc3dc4ebf692687a68be35))

### Breaking

* Sets minimum python to version 3.9. ([`3ddb139`](https://github.com/MozillaSecurity/bugmon-tc/commit/3ddb139d7414119589bc3dc4ebf692687a68be35))

## v3.3.2 (2024-07-22)

### Fix

* Ignore pernosco-keyword if pernosco-failed command is set ([`fe48bce`](https://github.com/MozillaSecurity/bugmon-tc/commit/fe48bce3221bb6e4bdaac3a02f751327f01c3733))

## v3.3.1 (2024-07-08)

### Fix

* Add scope docker-worker:capability:privileged to ReporterTask ([`91b2e4c`](https://github.com/MozillaSecurity/bugmon-tc/commit/91b2e4c12bd8aebe1449314ba0e6a3998163eb07))

## v3.3.0 (2024-07-02)

### Feature

* Increase bugmon-confirm deadline to 12 hours ([`f91cb39`](https://github.com/MozillaSecurity/bugmon-tc/commit/f91cb39d96bf5db18ca42cba5a36bca567b48c76))

## v3.2.1 (2024-06-10)

### Fix

* Increase deadline by 1 hour ([`1186f87`](https://github.com/MozillaSecurity/bugmon-tc/commit/1186f87a5baf9c3faadc12481a746dca465a71ca))

## v3.2.0 (2024-03-11)

### Feature

* Local sources are no longer required for pernosco traces ([`a494117`](https://github.com/MozillaSecurity/bugmon-tc/commit/a4941173dbe8483deae1a00cf53d08862fb64461))
* Local sources are no longer required for pernosco traces ([`8556e22`](https://github.com/MozillaSecurity/bugmon-tc/commit/8556e22a91cf03d432ff5d21691fcf2e2a1d58d4))

## v3.1.9 (2024-03-06)

### Fix

* Enable privileged mode on reporter tasks ([`cc6b82d`](https://github.com/MozillaSecurity/bugmon-tc/commit/cc6b82da5c6da2f0986870228756b77a186edc8d))

## v3.1.8 (2024-01-04)

### Fix

* Use indexed image ([`81e636d`](https://github.com/MozillaSecurity/bugmon-tc/commit/81e636d3d1b562cd72b5d62708b099204f8e3abb))

## v3.1.7 (2024-01-02)

### Fix

* Update bugmon ([`f00bbf8`](https://github.com/MozillaSecurity/bugmon-tc/commit/f00bbf8499c481d35822b6622ff2d6ffe6cf4144))

## v3.1.6 (2023-12-13)

### Fix

* Update bugmon ([`cf0109c`](https://github.com/MozillaSecurity/bugmon-tc/commit/cf0109c82235456f236fd70780e658128440e509))

## v3.1.5 (2023-12-09)

### Fix

* Only attempt to record pernosco sessions for linux x86_64 bugs ([`d116e5d`](https://github.com/MozillaSecurity/bugmon-tc/commit/d116e5d55513cfd6540f6bbeee9d3680e20ee583))
* Update bugmon ([`4bc91fa`](https://github.com/MozillaSecurity/bugmon-tc/commit/4bc91fa534a253f22873457bbb9d0fc510bfdaf5))
* Update bugmon ([`68eb3fe`](https://github.com/MozillaSecurity/bugmon-tc/commit/68eb3fef230e00b7b32a42ea4d1aff3db1fbb1e8))

## v3.1.4 (2023-12-05)

### Fix

* Convert path to posix str before building url ([`684d6fc`](https://github.com/MozillaSecurity/bugmon-tc/commit/684d6fcc2fe4f469b7bd7deeb4d8d71bf3f2d546))

## v3.1.3 (2023-12-05)

### Fix

* Sort all list output ([`07d8351`](https://github.com/MozillaSecurity/bugmon-tc/commit/07d83510b0f1a019da8a2eea1d16f618a506acd5))
* Only add get-artifact scope for trace if set ([`f121c86`](https://github.com/MozillaSecurity/bugmon-tc/commit/f121c861a6016a657eef3da50a274bb11d1eb44e))
* Only raise errors on unfound files when not in tc ([`9dfbede`](https://github.com/MozillaSecurity/bugmon-tc/commit/9dfbede5267de0dd3e43d9d9ab4778d5352e37f5))

## v3.1.2 (2023-12-05)

### Fix

* Generic-worker expects relative artifact paths ([`0e88573`](https://github.com/MozillaSecurity/bugmon-tc/commit/0e88573987d8d06009577c21b0018f970daabfd0))

## v3.1.1 (2023-12-04)

### Fix

* Cache and capabilities are not valid payload fields for windows ([`da1e21c`](https://github.com/MozillaSecurity/bugmon-tc/commit/da1e21cfdefeb7989de8f7f05930987674b49ffb))

### Documentation

* Fix link to codecov results ([`2350b9c`](https://github.com/MozillaSecurity/bugmon-tc/commit/2350b9c1b087ccf65a718cd2e5048e46599a91ea))

## v3.1.0 (2023-12-04)

### Feature

* Add support for windows processor tasks ([`8aef506`](https://github.com/MozillaSecurity/bugmon-tc/commit/8aef506d0137ba0bc8b26dfc4107dececdb428d8))
* Enable mypy and add type hints ([`9b54077`](https://github.com/MozillaSecurity/bugmon-tc/commit/9b54077b2c625d55692d2d2aadd4713c98d0c83f))
* Update bugmon and lockfile ([`8d637a8`](https://github.com/MozillaSecurity/bugmon-tc/commit/8d637a8603473032b253ef6da2aa5f6f0d0b2728))

### Fix

* Call orion launch script ([`d20edb6`](https://github.com/MozillaSecurity/bugmon-tc/commit/d20edb660789f89434a54050717f64b52d54adc3))
* Add more explicit type hints to main and parse_args ([`b43f9d6`](https://github.com/MozillaSecurity/bugmon-tc/commit/b43f9d6728f47ce4ea8dda1f9562ec9a81da04ab))
* Windows images are defined using the mounts key ([`fc4e223`](https://github.com/MozillaSecurity/bugmon-tc/commit/fc4e2231a0405bbe4a15a246d307f3ed3ef93fe8))
* Set bugmon-win image when processing a windows bug ([`adc0147`](https://github.com/MozillaSecurity/bugmon-tc/commit/adc0147010ac7ea7707d4c8f19c81ab30f4ff351))
* Raise parser error if path doesn't exist ([`d1ec33e`](https://github.com/MozillaSecurity/bugmon-tc/commit/d1ec33eb70aedc1bb92980f98445478fa8718d35))
* Fix argv typer hint ([`39dbb10`](https://github.com/MozillaSecurity/bugmon-tc/commit/39dbb10f10085e79891109a3f0f67c55322e2c31))
* Set type hint for argv to Any ([`437e34c`](https://github.com/MozillaSecurity/bugmon-tc/commit/437e34c96aa5bebe8db1cf92029a79df9614cebe))
* Set force_confirm arg to False by default ([`389ff78`](https://github.com/MozillaSecurity/bugmon-tc/commit/389ff7891e539f3c5827434b31e83ca626592c7f))
* Remove unnecessary call to open ([`8f4d2ac`](https://github.com/MozillaSecurity/bugmon-tc/commit/8f4d2ac4723935f848dda7e8fc56ec46dcbb83b3))
* Use Dict from typing ([`766a3d5`](https://github.com/MozillaSecurity/bugmon-tc/commit/766a3d531a9cf4c7efecdaf25ea14105bdc01df0))
* Address pylint warnings ([`d4ac65d`](https://github.com/MozillaSecurity/bugmon-tc/commit/d4ac65d4914a23a3fed375098475481e26e2169d))

### Documentation

* Fix minor typo ([`462dd04`](https://github.com/MozillaSecurity/bugmon-tc/commit/462dd04dbb1fb159007d4185f6d987d69e6c407f))

## v3.0.0 (2023-04-25)
### Breaking
* drop support for pythin 3.7 ([`c30146d`](https://github.com/MozillaSecurity/bugmon-tc/commit/c30146de4bda656cfdc77bf2b418c11527b5dd7b))

## v2.1.8 (2023-03-03)
### Fix
* Close unsupported bugs ([`d80374a`](https://github.com/MozillaSecurity/bugmon-tc/commit/d80374aaee75fc45ad047b3f45e05dd389eeed69))
* Use pernosco if pernosco-wanted keyword present ([`dd2cd38`](https://github.com/MozillaSecurity/bugmon-tc/commit/dd2cd38575ded61df3c65225ed110a5170e91fa7))

## v2.1.7 (2022-12-01)
### Fix
* TemporaryDirectory() returns a string ([`5d5f4ac`](https://github.com/MozillaSecurity/bugmon-tc/commit/5d5f4acb9d3dca6a40877f888b195db0f252fa4d))

## v2.1.6 (2022-12-01)
### Fix
* Binary artifacts are returned directly in tc ([`f525da3`](https://github.com/MozillaSecurity/bugmon-tc/commit/f525da3ce4e40dd40667b171f45957a2b66e5d28))

## v2.1.5 (2022-11-26)
### Fix
* Only update bug if submit_trace succeeds ([`aafa553`](https://github.com/MozillaSecurity/bugmon-tc/commit/aafa5530812aa09ec9e36956e9197b51c4bf5355))

## v2.1.4 (2022-11-23)
### Fix
* Convert trace_artifact path to str ([`a3b58d4`](https://github.com/MozillaSecurity/bugmon-tc/commit/a3b58d424d687578e7228cc889d6d10d48377fcb))

## v2.1.3 (2022-10-31)
### Fix
* Allow redirects when fetching artifacts ([#7](https://github.com/MozillaSecurity/bugmon-tc/issues/7)) ([`d49f137`](https://github.com/MozillaSecurity/bugmon-tc/commit/d49f1379b3cbe007072e152662cbdefc94567df4))

## v2.1.2 (2022-10-28)
### Fix
* Revert bug chfield value ([`ebf4958`](https://github.com/MozillaSecurity/bugmon-tc/commit/ebf49587f79981a0209ca7406fcad30cecbd541b))

## v2.1.1 (2022-10-28)
### Fix
* Wrap artifact path in str ([`7c57131`](https://github.com/MozillaSecurity/bugmon-tc/commit/7c57131d439e9e0ace94a329f8a6382ae428d280))

## v2.1.0 (2022-10-27)
### Feature
* Pass in task_id to fetch_artifact ([`31acc7e`](https://github.com/MozillaSecurity/bugmon-tc/commit/31acc7e323077795b47824bfce094bc358dbb335))

## v2.0.5 (2022-10-27)
### Fix
* Remove useless check for local artifacts ([`3f2df69`](https://github.com/MozillaSecurity/bugmon-tc/commit/3f2df69602615aecc44fed2906c364d6ac9316e8))

## v2.0.4 (2022-10-27)
### Fix
* Always include pernosco required scopes ([`c90944d`](https://github.com/MozillaSecurity/bugmon-tc/commit/c90944dd1e17177eecce1d7add42ed2ddde4058a))

## v2.0.3 (2022-10-27)
### Fix
* Remove unnecessary PERNOSCO check in reporter ([`5bc9661`](https://github.com/MozillaSecurity/bugmon-tc/commit/5bc9661fe694a039b2aec2f6c80db7e7bccf33fd))
* Use type(self) to get class name ([`70f206a`](https://github.com/MozillaSecurity/bugmon-tc/commit/70f206aaf90f8d0e47891e417f81282957181d1d))

## v2.0.2 (2022-10-24)
### Fix
* Only use pernosco if command present ([`29749c9`](https://github.com/MozillaSecurity/bugmon-tc/commit/29749c97e3b0c7f29533b86609f7eb15ffde8346))

## v2.0.1 (2022-10-20)
### Fix
* Add privileged and disableSeccomp capabilities to processor task ([`31d55aa`](https://github.com/MozillaSecurity/bugmon-tc/commit/31d55aa60d6d874fed96a2983bdc8280b5d4d59a))

## v2.0.0 (2022-10-20)
### Feature
* Add support for submitting pernosco traces ([#6](https://github.com/MozillaSecurity/bugmon-tc/issues/6)) ([`bdc052e`](https://github.com/MozillaSecurity/bugmon-tc/commit/bdc052ec51f4ecbdfb8f628c73e9be24178d8066))

### Breaking
* Makes significant changes to the exposed API ([`bdc052e`](https://github.com/MozillaSecurity/bugmon-tc/commit/bdc052ec51f4ecbdfb8f628c73e9be24178d8066))

## v1.0.1 (2021-11-18)
### Fix
* Expand search range to 2020-03-01 ([`5bb3427`](https://github.com/MozillaSecurity/bugmon-tc/commit/5bb3427e0e2b1585fd90b93c1c5d02b4bf569fe2))

### Documentation
* Fix path to taskcluster badge ([`86d479a`](https://github.com/MozillaSecurity/bugmon-tc/commit/86d479a404f35e94b391f78b7d87666ae7e5fb3f))

## v1.0.0 (2021-08-18)
### Feature
* Include bug ID in task name and artifacts ([#4](https://github.com/MozillaSecurity/bugmon-tc/issues/4)) ([`f282dff`](https://github.com/MozillaSecurity/bugmon-tc/commit/f282dff6f8ed8dc69e5bd1b010da23672dc833db))

### Breaking
* Makes changes to the Task init arguments ([`f282dff`](https://github.com/MozillaSecurity/bugmon-tc/commit/f282dff6f8ed8dc69e5bd1b010da23672dc833db))

## v0.1.0 (2021-08-17)
### Feature
* Add support for bugmom --force-confirm ([`38cc550`](https://github.com/MozillaSecurity/bugmon-tc/commit/38cc5503c88b034ab55f10ce377eaaa5318a8ba8))

### Fix
* Add support for forced confirmations to monitor task ([`adf3a08`](https://github.com/MozillaSecurity/bugmon-tc/commit/adf3a08acbf02c198ede2d3bb73b03970416c1e3))
* BugMonitor expects a Path ([`121198d`](https://github.com/MozillaSecurity/bugmon-tc/commit/121198d8dd93d2bc44377d8d38911244569ca9aa))
* Corrected force_confirm argument name ([`02b9bc7`](https://github.com/MozillaSecurity/bugmon-tc/commit/02b9bc70e8f95cd454f3b0f555d61fa331df3982))
* Use renamed BugmonException class ([`59b2d0a`](https://github.com/MozillaSecurity/bugmon-tc/commit/59b2d0a99ea252f10482c5ef41bf4dbaf1166acb))
* Pass FORCE_CONFIRM env variable from monitor to process ([`924e2bc`](https://github.com/MozillaSecurity/bugmon-tc/commit/924e2bcae3b22dfd9511101aed197e57db4e0c13))
