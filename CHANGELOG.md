# Changelog

<!--next-version-placeholder-->

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