# Changelog

<!--next-version-placeholder-->

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
