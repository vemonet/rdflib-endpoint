# 📜 Changelog

All notable changes to this project will be documented in this file.

## [0.6.0](https://github.com/vemonet/rdflib-endpoint/compare/v0.5.5..v0.6.0) - 2026-02-17

### ⚙️ Continuous Integration

- Add py 3.14 to test workflow, fix some params in tests - ([5536430](https://github.com/vemonet/rdflib-endpoint/commit/553643030a629e74dda1c8c78ef3758eab434289))
- Fix docker gateway host for github action federated queries tests - ([5fcf336](https://github.com/vemonet/rdflib-endpoint/commit/5fcf33618c94c7dd757b05bb2fe5c005565e358d))
- Fix federated query in gh action, somehow failing only for oxigraph when function running in gh action (custom function works when running locally) - ([9490786](https://github.com/vemonet/rdflib-endpoint/commit/94907861c41ad799ab0f85c4e86ed913e5c19def))

### ⛰️ Features

- Add `DatasetExt` class, to enable easily defining custom pattern and extension functions that resolves to python functions using pythonic decorated functions - ([59ff1f0](https://github.com/vemonet/rdflib-endpoint/commit/59ff1f0b40907975206334e8626a2d123197abee))
- Auto generate example_queries from functions docstring if not provided, deprecate `example_query` to use the 1st key of `example_queries` as YASGUI default tab. Update the example to use custom decorated functions - ([d9bf67a](https://github.com/vemonet/rdflib-endpoint/commit/d9bf67a8519d952b9e7a3beb34b8e4747d47e78b))
- Provide a default namespace for all decorator functions - ([444382c](https://github.com/vemonet/rdflib-endpoint/commit/444382ce901e1200f5c9d01cca6a7f0705b9ed53))
- Handle when `FILTER` = is used to define a variable value (instead of `VALUES`), which is done by virtuoso when transfering `SERVICE` calls - ([687fe16](https://github.com/vemonet/rdflib-endpoint/commit/687fe163e4960859533b93e7d7369060f40b1d83))
- Add `use_subject` arg to `type_function` to enable to use the triples subject as input arg - ([ee39318](https://github.com/vemonet/rdflib-endpoint/commit/ee3931865281f145f40c8a4534becc32c34d66ee))

### 🐛 Bug Fixes

- Fix types for py3.8 - ([d1e7354](https://github.com/vemonet/rdflib-endpoint/commit/d1e7354b94321c161cc56a7cf8fc71106f9698eb))

### 📚 Documentation

- Improve readme, example and add `.python-version` file - ([f6d6f14](https://github.com/vemonet/rdflib-endpoint/commit/f6d6f14cfc2855659c5d2f52f138e4665dbd8c88))
- Readme, fix py3.8 typing - ([5235f2a](https://github.com/vemonet/rdflib-endpoint/commit/5235f2a72e101de661d4f696de1c11026a9395b1))
- Fix readme - ([b7c1ae4](https://github.com/vemonet/rdflib-endpoint/commit/b7c1ae4bb75e7a3e29b68d6dff840e05ac516ba3))
- Fix contributing - ([c895c59](https://github.com/vemonet/rdflib-endpoint/commit/c895c595c5069395a97575fa29d9eefaeae0bba0))

### 🚜 Refactor

- Change default function namespace from https://w3id.org/sparql-functions/ to urn:sparql-function: - ([9bb9741](https://github.com/vemonet/rdflib-endpoint/commit/9bb974139f81f98b14c902e501160a07b14aac68))

### 🧪 Testing

- Add tests for federated `SERVICE` call from other triplestores to rdflib-endpoint: graphdb, fuseki, blazegraph, oxigraph, rdf4j - ([43e94df](https://github.com/vemonet/rdflib-endpoint/commit/43e94df61773362b116d5cb72ae9e960f6c9a12c))

## [0.5.5](https://github.com/vemonet/rdflib-endpoint/compare/v0.5.4..v0.5.5) - 2026-02-03

### ⚙️ Continuous Integration

- Remove py3.14 from test workflow since pyo3 (for oxigraph) does not support it - ([1c0d5df](https://github.com/vemonet/rdflib-endpoint/commit/1c0d5df7880e3113b9be929aa56aef38093d526e))

### 🐛 Bug Fixes

- Remove `application/sparql-results+csv` mime type and just use `text/csv` as precognized by the specs, stop converting miume type, just use the one sent in the request, to avoid breaking stuff - ([3e4cf81](https://github.com/vemonet/rdflib-endpoint/commit/3e4cf815fd22fa689b9154a993a8fce8a453c7c5))

### 🛠️ Miscellaneous Tasks

- Bump to v0.5.4 - ([b107438](https://github.com/vemonet/rdflib-endpoint/commit/b107438de0950bed3eef11c68c158ec5b026e094))
- Bump to v0.5.5 - ([4141627](https://github.com/vemonet/rdflib-endpoint/commit/41416279435ea0aceedf1d5a0fd74005b47f15a5))

## [0.5.4](https://github.com/vemonet/rdflib-endpoint/compare/v0.5.3..v0.5.4) - 2025-12-19

### ⚙️ Continuous Integration

- Update the release process, generate changelog with git cliff, and publish locally - ([b110147](https://github.com/vemonet/rdflib-endpoint/commit/b110147138529301728fd294a07da9e97946c9d8))

### ⛰️ Features

- Improve conversion of generic mime types to more specific ones for construct, describe, select and ask queries - ([6cfded1](https://github.com/vemonet/rdflib-endpoint/commit/6cfded16d73e6cc7ba607bba96e1b70b56a512f3))

### 🐛 Bug Fixes

- Fix coverage ignore and update dependencies - ([a82797d](https://github.com/vemonet/rdflib-endpoint/commit/a82797decfc0bbbf0ccf86ef0bb605470eeeeebd))

### 🚜 Refactor

- Rename `GENERAL_CONTENT_TYPE_TO_RDFLIB_FORMAT` to `GENERIC_CONTENT_TYPE_TO_RDFLIB_FORMAT` - ([e8da312](https://github.com/vemonet/rdflib-endpoint/commit/e8da31264043da1c53c5f9af187615dbdaadc922))
- Remove `__all__` from `sparql_endpoint.py` and `sparql_router.py` since they are now exported from `__main__.py`, improve imports in router - ([90c7804](https://github.com/vemonet/rdflib-endpoint/commit/90c780410308e35d76e2f58a044718f275393803))

### 🧪 Testing

- Fix test for select query with accept header `text/turtle` - ([5a54907](https://github.com/vemonet/rdflib-endpoint/commit/5a549070a7e0d20a3194ec76bb9536d7e713c256))

## [0.5.1](https://github.com/vemonet/rdflib-endpoint/compare/v0.5.0..v0.5.1) - 2024-05-24

### ⛰️ Features

- Add support for JSON-LD, n3, n-triples, n-quads, trix and trig return types on CONSTRUCT queries - ([16a47c6](https://github.com/vemonet/rdflib-endpoint/commit/16a47c69f730a6216994ff0f666fbd61031ff02d))

### 🐛 Bug Fixes

- Fix hatch build - ([a6c0208](https://github.com/vemonet/rdflib-endpoint/commit/a6c0208872e99a92e932a70662898b2cfb8b9419))

## [0.4.3](https://github.com/vemonet/rdflib-endpoint/compare/0.4.2..v0.4.3) - 2023-11-28

### 🐛 Bug Fixes

- Fix black - ([d4aa273](https://github.com/vemonet/rdflib-endpoint/commit/d4aa2736dd7ce59684460f8fa71320dcc046d5e4))

## [0.4.1](https://github.com/vemonet/rdflib-endpoint/compare/0.4.0..0.4.1) - 2023-10-02

### 🐛 Bug Fixes

- Fix sonar scan in workflow - ([be9595e](https://github.com/vemonet/rdflib-endpoint/commit/be9595e3894d61a3a5ee0d8b53e8abb75d17baa3))
- Fix workflow - ([aca4278](https://github.com/vemonet/rdflib-endpoint/commit/aca427871882e1b3f05688a2c5178face39eff4d))
- Fix sonar anal - ([0876ace](https://github.com/vemonet/rdflib-endpoint/commit/0876acec6bea4b825bf4b5b9c9bb1bd647d2b504))
- Fix sonar - ([e2163b9](https://github.com/vemonet/rdflib-endpoint/commit/e2163b9fde90ee73b247f96a9b3e79a38d612ce6))
- Fix sonar - ([195a5dd](https://github.com/vemonet/rdflib-endpoint/commit/195a5dd3cd3848b51f89c2e9b5349e32fec26b82))
- Fix sonar - ([32de19b](https://github.com/vemonet/rdflib-endpoint/commit/32de19b99f8438b60654837f75ae947bad9752ab))
- Fix sonar - ([b8b89eb](https://github.com/vemonet/rdflib-endpoint/commit/b8b89eb02d3b713c3f69973bc0516cd002513fc2))
- Fix codecov - ([4d2d1fd](https://github.com/vemonet/rdflib-endpoint/commit/4d2d1fd6a8de24b767f3f31c499062a6c1e9cbc7))
- Fix cov - ([ff89c52](https://github.com/vemonet/rdflib-endpoint/commit/ff89c52a0585bd1ca4b83c9bc68c806dd587d9f1))
- Fix cov - ([a419a22](https://github.com/vemonet/rdflib-endpoint/commit/a419a22c7caf17e3fd1672428083acb6322acf58))
- Fix cov - ([ff9d746](https://github.com/vemonet/rdflib-endpoint/commit/ff9d74627659ba47f86518c58ec2b9250f3cde2a))
- Fix cov - ([b8f23a8](https://github.com/vemonet/rdflib-endpoint/commit/b8f23a8b4995d38e06acae7836dccc4781a8809a))
- Fix args - ([ecc11a2](https://github.com/vemonet/rdflib-endpoint/commit/ecc11a211f5b4499d6259bea43823f6e0d1208a0))
- Fix description in test - ([feabe87](https://github.com/vemonet/rdflib-endpoint/commit/feabe87a500ac30afd9e17f60dbaf3e50c5feb9b))
- Fix missing rdf+xml mime type - ([fb15964](https://github.com/vemonet/rdflib-endpoint/commit/fb159644eb5adaa3928f58233f00cf99f7b29ac7))
- Fix httpx test calls - ([e340581](https://github.com/vemonet/rdflib-endpoint/commit/e3405810a225bb88441c3d56e49db5c7a80d0789))
- Fix test workflow - ([074c2f6](https://github.com/vemonet/rdflib-endpoint/commit/074c2f6b54e0d5adc661e1f63ba304135f3f9250))
- Fix precommit - ([b2fe7e6](https://github.com/vemonet/rdflib-endpoint/commit/b2fe7e6509339ccdb62f7095d9cce6530859fc82))
- Fix tests - ([dc01499](https://github.com/vemonet/rdflib-endpoint/commit/dc01499d56842fed13a4040d019f8969ec9da303))

## [0.4.0](https://github.com/vemonet/rdflib-endpoint/compare/0.3.0..0.4.0) - 2023-03-21

### 🐛 Bug Fixes

- Fix Processor import - ([d29aba8](https://github.com/vemonet/rdflib-endpoint/commit/d29aba870d48034faeb47d874d81657dc52e69fd))

## [0.3.0](https://github.com/vemonet/rdflib-endpoint/compare/0.2.7..0.3.0) - 2023-03-18

### 🐛 Bug Fixes

- Fix mypy - ([603d334](https://github.com/vemonet/rdflib-endpoint/commit/603d334d7a036e85c4a6682d0bcb727f8ab416cf))
- Fix tests - ([5b1b4f1](https://github.com/vemonet/rdflib-endpoint/commit/5b1b4f1d0d47006cb56652bd9cb13142fd47ed98))

## [0.2.7](https://github.com/vemonet/rdflib-endpoint/compare/0.2.6..0.2.7) - 2023-01-21

### 🐛 Bug Fixes

- Fix ruff checks - ([3fd6a09](https://github.com/vemonet/rdflib-endpoint/commit/3fd6a09fe20c9ed30159ad43afdaece0749df8a7))

## [0.2.3](https://github.com/vemonet/rdflib-endpoint/compare/0.2.2..0.2.3) - 2022-12-19

### 🐛 Bug Fixes

- Fix publish workflow again - ([cc5f0cd](https://github.com/vemonet/rdflib-endpoint/commit/cc5f0cd9204728894eafc413442839306ca444e3))

## [0.2.2](https://github.com/vemonet/rdflib-endpoint/compare/0.2.1..0.2.2) - 2022-12-19

### 🐛 Bug Fixes

- Fix publish workflow - ([2535422](https://github.com/vemonet/rdflib-endpoint/commit/25354229250e49f250177ddadb77ed2ea49ed978))

## [0.2.1](https://github.com/vemonet/rdflib-endpoint/compare/0.2.0..0.2.1) - 2022-12-19

### 🐛 Bug Fixes

- Fix publish workflow - ([5625732](https://github.com/vemonet/rdflib-endpoint/commit/5625732be3be42c39e5cfcb347e2998b7f5ceb6e))

## [0.2.0](https://github.com/vemonet/rdflib-endpoint/compare/0.1.6..0.2.0) - 2022-12-19

### 🐛 Bug Fixes

- Fix indent - ([c76c821](https://github.com/vemonet/rdflib-endpoint/commit/c76c821c9c21de7beac9ba6804b271b6b414c781))
- Fix flake8 dep - ([72263ac](https://github.com/vemonet/rdflib-endpoint/commit/72263ac479722eb285016be5c06bac8a4fe34753))
- Fix autoflake dep for py3.7 - ([5c27a1e](https://github.com/vemonet/rdflib-endpoint/commit/5c27a1e118fdebcc4c84da41b6fb0da6a4e73fa2))

### 🚜 Refactor

- Refactor comments - ([5aba1b0](https://github.com/vemonet/rdflib-endpoint/commit/5aba1b0510837452716c71a7f1c672c74996e85a))

## [0.1.6](https://github.com/vemonet/rdflib-endpoint/compare/0.1.5..0.1.6) - 2022-02-14

### 🐛 Bug Fixes

- Fix yasgui import html - ([f66b86a](https://github.com/vemonet/rdflib-endpoint/commit/f66b86a9497768b190b7893149c4b1fe845535f0))
- Fixing dumb setup.py package data - ([448ba49](https://github.com/vemonet/rdflib-endpoint/commit/448ba49bec7ada06935213cd34f205d209d268ba))

## [0.1.3](https://github.com/vemonet/rdflib-endpoint/compare/0.1.2..0.1.3) - 2021-12-14

### 🐛 Bug Fixes

- Fix codeql workflow triggers - ([bde6461](https://github.com/vemonet/rdflib-endpoint/commit/bde64611f4e5351ea6160d86f8e031ce155d0959))

## [0.1.0](https://github.com/vemonet/rdflib-endpoint/tree/0.1.0) - 2021-12-07

### 🐛 Bug Fixes

- Fix docker-compose - ([28d7884](https://github.com/vemonet/rdflib-endpoint/commit/28d788496d2cbbe3cc1965d6aee460f9dcaa5507))
- Fix docker-compose - ([01ae44f](https://github.com/vemonet/rdflib-endpoint/commit/01ae44f17e87efbd3a208b51e8ac5c52a7f2801f))
- Fix response content type - ([ecf6e8b](https://github.com/vemonet/rdflib-endpoint/commit/ecf6e8b35168c8ebace851c9f28b27e369a9577c))
- Fix service desc - ([9e646ce](https://github.com/vemonet/rdflib-endpoint/commit/9e646ce1c97822d80d8ce678c270a39cd973fcd8))
- Fix deploy script - ([dc38095](https://github.com/vemonet/rdflib-endpoint/commit/dc38095947828da7a9077b5d1f61dae5ca3f81c4))
- Fix import - ([5846c58](https://github.com/vemonet/rdflib-endpoint/commit/5846c5839d7762248333f4e303c01b5bee3016b0))
- Fix import - ([798352f](https://github.com/vemonet/rdflib-endpoint/commit/798352f678ead9d5d7ab7da94b03ddd8f072811c))
- Fix tests - ([4838ef2](https://github.com/vemonet/rdflib-endpoint/commit/4838ef2bdc50976f97f96e08b2ec94a798e1b1e7))
- Fix tests - ([34bca2b](https://github.com/vemonet/rdflib-endpoint/commit/34bca2bdaa95d5b83416ba154cf3f7db4b458846))
- Fix tests - ([b019792](https://github.com/vemonet/rdflib-endpoint/commit/b019792a5346fffc10f317438dff2fbc73e48803))
- Fix tests - ([a6184db](https://github.com/vemonet/rdflib-endpoint/commit/a6184db79fd5ec110e703c18a7499e16f6cbcfd4))
- Fix async post - ([af6f07a](https://github.com/vemonet/rdflib-endpoint/commit/af6f07adf6d2c27b2c828a49aaddcdfbab5a7aa1))
- Fix exception - ([badc9be](https://github.com/vemonet/rdflib-endpoint/commit/badc9be790b3c8e4bb35499f1cd6975b578ca04c))
- Fix apikey feature for update - ([a3f3825](https://github.com/vemonet/rdflib-endpoint/commit/a3f38256392aab6a4ea6969771dd59b868aaa470))
- Fix apikey for POST request - ([5d94d1e](https://github.com/vemonet/rdflib-endpoint/commit/5d94d1e07602cb51efc635375a6ca7d57b8e29a6))
- Fix error by increasing rdflib to 6 - ([42b8b20](https://github.com/vemonet/rdflib-endpoint/commit/42b8b206c920a58b4bffbc6e79b15e9a51dc2fe4))
- Fix publish workflow - ([9cd0901](https://github.com/vemonet/rdflib-endpoint/commit/9cd0901089e95ac3d5caf54f0fec75659214a9e7))
- Fix workflow - ([da5f274](https://github.com/vemonet/rdflib-endpoint/commit/da5f2744d9e2a7e67059d20a681b5d76ba82a9b2))
- Fix tests - ([7aafb39](https://github.com/vemonet/rdflib-endpoint/commit/7aafb39f2e8eead4d3db1b4bf5044e7832476e1e))

### 🚜 Refactor

- Refactor comments - ([f84175e](https://github.com/vemonet/rdflib-endpoint/commit/f84175e43f229ec36d2c3741905bf3d2a124cb71))
- Refactor - ([322817b](https://github.com/vemonet/rdflib-endpoint/commit/322817bcc12c13159f310180c041151319c1c78e))
- Refactor - ([a58a8a0](https://github.com/vemonet/rdflib-endpoint/commit/a58a8a0af83475c8840cb5bc39d17beb7d049391))
- Refactor - ([d0e7835](https://github.com/vemonet/rdflib-endpoint/commit/d0e7835cc8a5b74e469dc634b7e7a65c6f96877b))
- Refactor readme - ([d34db0b](https://github.com/vemonet/rdflib-endpoint/commit/d34db0b79658d4563bd2bcb9e21df3253250c59e))

<!-- generated by git-cliff -->
