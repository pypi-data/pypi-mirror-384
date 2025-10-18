# Changelog

## 0.7.0 (2025-10-17)

Full Changelog: [v0.6.0...v0.7.0](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.6.0...v0.7.0)

### Features

* **api:** Add examples to integrations and events ([099feea](https://github.com/m3ter-com/m3ter-sdk-python/commit/099feeab5738656f8d33ef010c95e18377d8588f))
* improve future compat with pydantic v3 ([1996ec4](https://github.com/m3ter-com/m3ter-sdk-python/commit/1996ec48ff4536322cf9e2c472ec55020e820aa0))
* **types:** replace List[str] with SequenceNotStr in params ([15e1524](https://github.com/m3ter-com/m3ter-sdk-python/commit/15e152408c618ea346f2b38280d423cfad37fd78))


### Bug Fixes

* avoid newer type syntax ([cba95ba](https://github.com/m3ter-com/m3ter-sdk-python/commit/cba95bab4f30c95de1c1aee73ea23a5e98e2a536))


### Chores

* bump `httpx-aiohttp` version to 0.1.9 ([d10b4ef](https://github.com/m3ter-com/m3ter-sdk-python/commit/d10b4efcfedc4f2537a5d71ffa41ae2e6800cb9e))
* do not install brew dependencies in ./scripts/bootstrap by default ([bb9147b](https://github.com/m3ter-com/m3ter-sdk-python/commit/bb9147b097188453c20745126411b0310fd60df7))
* **internal:** add Sequence related utils ([23c2b7a](https://github.com/m3ter-com/m3ter-sdk-python/commit/23c2b7a423e79f8f86d828e9feff4d79ecb7e316))
* **internal:** change ci workflow machines ([1a56dff](https://github.com/m3ter-com/m3ter-sdk-python/commit/1a56dff78e573d029055c993e24a464d28cc8d09))
* **internal:** detect missing future annotations with ruff ([165c6e4](https://github.com/m3ter-com/m3ter-sdk-python/commit/165c6e47dabb84e73bd95e7860b59426063970cb))
* **internal:** fix ruff target version ([bf15d2f](https://github.com/m3ter-com/m3ter-sdk-python/commit/bf15d2f70321aa887acff92aa26dab49f019c0e6))
* **internal:** move mypy configurations to `pyproject.toml` file ([e8665c2](https://github.com/m3ter-com/m3ter-sdk-python/commit/e8665c2940935a84e3c7e4399734d06094668fbd))
* **internal:** update comment in script ([5daea5b](https://github.com/m3ter-com/m3ter-sdk-python/commit/5daea5be80b1e7503cfb17a1236fddb85be5374e))
* **internal:** update pydantic dependency ([e157197](https://github.com/m3ter-com/m3ter-sdk-python/commit/e157197788f8ebf8662d07b4158d6c9154ee5e09))
* **internal:** update pyright exclude list ([0200662](https://github.com/m3ter-com/m3ter-sdk-python/commit/020066272ddd2d2a52b751eedc9491b2dc9a199b))
* **tests:** simplify `get_platform` test ([a8cac9b](https://github.com/m3ter-com/m3ter-sdk-python/commit/a8cac9bb8c2b5be730e7bb491a49ef96b282aa9f))
* **types:** change optional parameter type from NotGiven to Omit ([714a76a](https://github.com/m3ter-com/m3ter-sdk-python/commit/714a76a83a89cda259cdc465f52032fade9665e7))
* update @stainless-api/prism-cli to v5.15.0 ([64023fe](https://github.com/m3ter-com/m3ter-sdk-python/commit/64023fe8e9fc700d2a3af5bd2da556708a939e9d))
* update github action ([3744158](https://github.com/m3ter-com/m3ter-sdk-python/commit/3744158773b98848f120ceeb309e4a0dd2164cb5))

## 0.6.0 (2025-08-01)

Full Changelog: [v0.5.0-alpha...v0.6.0](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.5.0-alpha...v0.6.0)

### Features

* **api:** add aggregationId query param to ListPricings ([e2bc74c](https://github.com/m3ter-com/m3ter-sdk-python/commit/e2bc74c04bf9f70d1365376767c0273f3eb1a06a))
* **api:** mark `version` attribute as computed in Terraform ([dd009d3](https://github.com/m3ter-com/m3ter-sdk-python/commit/dd009d365cfbc3928f12f2b4bbf85b00752459a9))
* **api:** OpenAPI spec update ([b4b696c](https://github.com/m3ter-com/m3ter-sdk-python/commit/b4b696c361883008320bf4472af3a59ea24c426c))
* **api:** remove audit fields from Terraform provider ([df51769](https://github.com/m3ter-com/m3ter-sdk-python/commit/df51769b17b8c50cc33f6bb670198d492b6353fc))
* **api:** Set "version" attribute to "computed_optional" in Terraform ([efb49d3](https://github.com/m3ter-com/m3ter-sdk-python/commit/efb49d3be31857b87b34f6a9d333e2b68f5db5d3))
* clean up environment call outs ([9699330](https://github.com/m3ter-com/m3ter-sdk-python/commit/9699330a0a8714090f3c7a91693b636491aac53b))
* **client:** add follow_redirects request option ([8d41e7f](https://github.com/m3ter-com/m3ter-sdk-python/commit/8d41e7fe9ffec54d76c1ba7486ad85f4bac9da86))
* **client:** add support for aiohttp ([3d4c3fa](https://github.com/m3ter-com/m3ter-sdk-python/commit/3d4c3fae40e201b8dc18cc66b9d3d3eda99dbb85))
* **client:** support file upload requests ([c47870b](https://github.com/m3ter-com/m3ter-sdk-python/commit/c47870b65f8500d23976f0e9184c892b0f0c2cb4))


### Bug Fixes

* **api:** terraform release readiness ([fad32e2](https://github.com/m3ter-com/m3ter-sdk-python/commit/fad32e22ec86d5697c6483f5bd4da835670c9d10))
* **api:** use WebhookDestinationResponse in webhook endpoint response schemas ([05fee13](https://github.com/m3ter-com/m3ter-sdk-python/commit/05fee13bb01a20782b2fd2ebcc255932e376ce70))
* **ci:** correct conditional ([0a7571b](https://github.com/m3ter-com/m3ter-sdk-python/commit/0a7571b668b181ed5b8cd9a0dde86ac1abef82f5))
* **ci:** release-doctor — report correct token name ([65031e3](https://github.com/m3ter-com/m3ter-sdk-python/commit/65031e3a9fefe1eac03230db925119e00d0e344b))
* **client:** correctly parse binary response | stream ([c34e3ac](https://github.com/m3ter-com/m3ter-sdk-python/commit/c34e3ac0c81a7623a326c68d84a2dd9f8a39fde5))
* **client:** don't send Content-Type header on GET requests ([670fb31](https://github.com/m3ter-com/m3ter-sdk-python/commit/670fb31efc94a40f0e8712f7b11ba065d6958314))
* **client:** handle .copy() with endpoint specific URLs ([84f9daa](https://github.com/m3ter-com/m3ter-sdk-python/commit/84f9daa987271a09c2f3833febc47fa1318fafb2))
* **parsing:** correctly handle nested discriminated unions ([7331ae7](https://github.com/m3ter-com/m3ter-sdk-python/commit/7331ae76377855f9c120c9111ec5bcd1d5f557b6))
* **parsing:** ignore empty metadata ([6fb7665](https://github.com/m3ter-com/m3ter-sdk-python/commit/6fb7665725c132e3c7ad92806233e2dca1c8d8a1))
* **parsing:** parse extra field types ([b044551](https://github.com/m3ter-com/m3ter-sdk-python/commit/b044551606ea9741fc53cafec888f8bf06ad06e3))


### Chores

* **ci:** change upload type ([c31508d](https://github.com/m3ter-com/m3ter-sdk-python/commit/c31508d284784f23715bac04bbbd24b703dd6cff))
* **ci:** enable for pull requests ([b06b080](https://github.com/m3ter-com/m3ter-sdk-python/commit/b06b080389d08f01c8a94ef7609b7c0a11140c21))
* **ci:** only run for pushes and fork pull requests ([e978320](https://github.com/m3ter-com/m3ter-sdk-python/commit/e9783202624d76e58f577e6396a3d32c7844e66c))
* **docs:** remove reference to rye shell ([15bb1b9](https://github.com/m3ter-com/m3ter-sdk-python/commit/15bb1b902dcdde20c223e55eba3e0fea0dab9c66))
* **docs:** remove unnecessary param examples ([0fed9e0](https://github.com/m3ter-com/m3ter-sdk-python/commit/0fed9e0cf8917385a6a8fd072ae7bd477e5a4b1c))
* **internal:** bump pinned h11 dep ([a1c713b](https://github.com/m3ter-com/m3ter-sdk-python/commit/a1c713b74423d29d4d71ffdd19952ffdc530dee6))
* **internal:** codegen related update ([76cf1a9](https://github.com/m3ter-com/m3ter-sdk-python/commit/76cf1a907421a5280c17a4be6c0ea3aac0021fb9))
* **internal:** codegen related update ([3f776ea](https://github.com/m3ter-com/m3ter-sdk-python/commit/3f776ea8e85b3c93e3b78013dd8b7c4119312b42))
* **internal:** update conftest.py ([410de35](https://github.com/m3ter-com/m3ter-sdk-python/commit/410de35bed396320b9f5cefe9ff6b2dc2d3b48c0))
* **package:** mark python 3.13 as supported ([1552969](https://github.com/m3ter-com/m3ter-sdk-python/commit/15529699bf6470266bc5206b93ca02644d95089a))
* **project:** add settings file for vscode ([9f269b9](https://github.com/m3ter-com/m3ter-sdk-python/commit/9f269b9eeff19d80d4850c2c1612b62a7d41f1b9))
* **readme:** fix version rendering on pypi ([e6bcc85](https://github.com/m3ter-com/m3ter-sdk-python/commit/e6bcc85a6328eca40d990222552452cf364b33d2))
* **readme:** update badges ([8ac2b31](https://github.com/m3ter-com/m3ter-sdk-python/commit/8ac2b315cc860dadfa2685b7a9a43c2bc22fd624))
* **tests:** add tests for httpx client instantiation & proxies ([093a35b](https://github.com/m3ter-com/m3ter-sdk-python/commit/093a35bbfb82777b811b1356344c9fa0b4efda15))
* **tests:** run tests in parallel ([4553836](https://github.com/m3ter-com/m3ter-sdk-python/commit/455383612e5ad99eb0064db7d1abac393506bfb2))
* **tests:** skip some failing tests on the latest python versions ([18708e7](https://github.com/m3ter-com/m3ter-sdk-python/commit/18708e7fe593b8db9003797feb1485ee39d18e11))


### Documentation

* **client:** fix httpx.Timeout documentation reference ([2522d49](https://github.com/m3ter-com/m3ter-sdk-python/commit/2522d496e983af7b5f135952e9953e7d49ea4ac8))

## 0.5.0-alpha (2025-05-29)

Full Changelog: [v0.4.0-alpha...v0.5.0-alpha](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.4.0-alpha...v0.5.0-alpha)

### Features

* **api:** add statements ([89dd6a3](https://github.com/m3ter-com/m3ter-sdk-python/commit/89dd6a3313e40cd6046fd3e17c3d6bc9630523ff))
* **client:** add support for endpoint-specific base URLs ([74cfda6](https://github.com/m3ter-com/m3ter-sdk-python/commit/74cfda67200730e7f6c43866145f416bad74ba0e))


### Bug Fixes

* **package:** support direct resource imports ([0203cd1](https://github.com/m3ter-com/m3ter-sdk-python/commit/0203cd17ed94baecc653011e9bb399e9da490b87))


### Chores

* **ci:** fix installation instructions ([0dd5ea0](https://github.com/m3ter-com/m3ter-sdk-python/commit/0dd5ea0a282f796c75fe4f9e4abd4d2d6419cfb0))
* **ci:** upload sdks to package manager ([69477c8](https://github.com/m3ter-com/m3ter-sdk-python/commit/69477c89744f2cf306ae8fa668447a198338150d))
* **ci:** use --pre flag for prerelease installation instructions ([1196818](https://github.com/m3ter-com/m3ter-sdk-python/commit/11968184f6767fd46b79019d551dab928fda6b16))
* **ci:** use --pre flag for prerelease installation instructions ([1e55bae](https://github.com/m3ter-com/m3ter-sdk-python/commit/1e55baed2c12ae8a7b6621a26be8abed3456c5f8))
* **docs:** grammar improvements ([0c5fd06](https://github.com/m3ter-com/m3ter-sdk-python/commit/0c5fd0682db20b137d17a8926b4280ac23bc66ad))
* **internal:** codegen related update ([1b117c6](https://github.com/m3ter-com/m3ter-sdk-python/commit/1b117c6e2559ee66ba8b6ff57be65b31280a2f46))
* **internal:** codegen related update ([db10922](https://github.com/m3ter-com/m3ter-sdk-python/commit/db10922b953a720a985b94abb74cffd4b6b08d4a))

## 0.4.0-alpha (2025-05-09)

Full Changelog: [v0.3.1-alpha...v0.4.0-alpha](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.3.1-alpha...v0.4.0-alpha)

### Features

* **api:** Introduce OrganizationConfigRequest model ([f00b7b1](https://github.com/m3ter-com/m3ter-sdk-python/commit/f00b7b1057736b694077efb4358f4ef12e212213))
* **api:** Spec fixes ([f0dfc1f](https://github.com/m3ter-com/m3ter-sdk-python/commit/f0dfc1fd7d3be6d6344d54cd60e6f97136180ce6))
* **api:** update open api spec ([f1d5dd3](https://github.com/m3ter-com/m3ter-sdk-python/commit/f1d5dd33d6656c625cd8299bef430bf458207b4d))
* **api:** update OpenAPI spec + associated fixes ([b4163ca](https://github.com/m3ter-com/m3ter-sdk-python/commit/b4163caef5396954739ee673a8a57302842f118a))


### Bug Fixes

* **perf:** optimize some hot paths ([58a0322](https://github.com/m3ter-com/m3ter-sdk-python/commit/58a03227a3d5b7e2f5644353376847ee5823fb91))
* **perf:** skip traversing types for NotGiven values ([e346612](https://github.com/m3ter-com/m3ter-sdk-python/commit/e3466121df216a0b5ec9233e610ec36c61ca8586))
* **pydantic v1:** more robust ModelField.annotation check ([c218f3f](https://github.com/m3ter-com/m3ter-sdk-python/commit/c218f3f23df66246805e4a15c46bea5b8b67a43b))


### Chores

* broadly detect json family of content-type headers ([a8f4032](https://github.com/m3ter-com/m3ter-sdk-python/commit/a8f403244392cba48e1574bbe112bee1e39dff7c))
* **ci:** add timeout thresholds for CI jobs ([7290e0b](https://github.com/m3ter-com/m3ter-sdk-python/commit/7290e0b714d9074e999c47551d6d207e2c2d2d60))
* **ci:** only use depot for staging repos ([a8944ec](https://github.com/m3ter-com/m3ter-sdk-python/commit/a8944ec4982cc15d897943306d4cf0ca797717ea))
* **ci:** run on more branches and use depot runners ([530e2c9](https://github.com/m3ter-com/m3ter-sdk-python/commit/530e2c9fbb2caa9e65d9efdbaf7f8694b265e65e))
* **client:** minor internal fixes ([53b7bed](https://github.com/m3ter-com/m3ter-sdk-python/commit/53b7bed095583f86fd45469d9157a194bd079c98))
* **internal:** avoid errors for isinstance checks on proxies ([70e0ce7](https://github.com/m3ter-com/m3ter-sdk-python/commit/70e0ce72bf9d8baa3f2e6320264317ae83908b2b))
* **internal:** base client updates ([fa2b6cc](https://github.com/m3ter-com/m3ter-sdk-python/commit/fa2b6cc5bde9b1fb11f09641f65e6d55108b1549))
* **internal:** bump pyright version ([869e1ee](https://github.com/m3ter-com/m3ter-sdk-python/commit/869e1eec241edefa84aee803dfbe1d69e84f959d))
* **internal:** codegen related update ([5656210](https://github.com/m3ter-com/m3ter-sdk-python/commit/56562105e7e41d339ffd761d7ca8f08313dca29c))
* **internal:** fix list file params ([1f0f063](https://github.com/m3ter-com/m3ter-sdk-python/commit/1f0f0634874b529dbf309e2205977b768f3196f2))
* **internal:** import reformatting ([5172027](https://github.com/m3ter-com/m3ter-sdk-python/commit/51720271bb9301fee016ca4c64c7655b1f6042a8))
* **internal:** minor formatting changes ([5986b32](https://github.com/m3ter-com/m3ter-sdk-python/commit/5986b32f796fbb2aa275a43de4f4ce24e1bb4a78))
* **internal:** refactor retries to not use recursion ([f50b690](https://github.com/m3ter-com/m3ter-sdk-python/commit/f50b690683f235ff32062932db587915405a4b6b))
* **internal:** update models test ([2d36eca](https://github.com/m3ter-com/m3ter-sdk-python/commit/2d36eca293d09bfd902dcfdaff240d30da343e18))
* **internal:** update pyright settings ([d1815da](https://github.com/m3ter-com/m3ter-sdk-python/commit/d1815da8f4db4f284515ab201df7535eef392dfe))
* **internal:** updates ([a72f1e2](https://github.com/m3ter-com/m3ter-sdk-python/commit/a72f1e293a2607866bba2d09514ede98a109e4b2))

## 0.3.1-alpha (2025-04-10)

Full Changelog: [v0.3.0-alpha...v0.3.1-alpha](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.3.0-alpha...v0.3.1-alpha)

### Bug Fixes

* use correct base url for client.usage.submit() ([#86](https://github.com/m3ter-com/m3ter-sdk-python/issues/86)) ([5bce3a4](https://github.com/m3ter-com/m3ter-sdk-python/commit/5bce3a46045deb9117984b4599806aef190b7473))

## 0.3.0-alpha (2025-04-10)

Full Changelog: [v0.2.0-alpha...v0.3.0-alpha](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.2.0-alpha...v0.3.0-alpha)

### Features

* **api:** add measurement request model ([ccaa85a](https://github.com/m3ter-com/m3ter-sdk-python/commit/ccaa85aafe2702dff827f90e494c001520887d60))

## 0.2.0-alpha (2025-04-10)

Full Changelog: [v0.1.1-alpha...v0.2.0-alpha](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.1-alpha...v0.2.0-alpha)

### Features

* **api:** rename DataFieldResponse to DataField and add DerivedField as a model ([3f6765b](https://github.com/m3ter-com/m3ter-sdk-python/commit/3f6765bf80ac31fa243ee5395221ba15172cfc03))


### Chores

* **internal:** expand CI branch coverage ([#84](https://github.com/m3ter-com/m3ter-sdk-python/issues/84)) ([9feb9b4](https://github.com/m3ter-com/m3ter-sdk-python/commit/9feb9b4041b67082ca5d13ade74ea3dc3027bd08))
* **internal:** reduce CI branch coverage ([46c3e28](https://github.com/m3ter-com/m3ter-sdk-python/commit/46c3e2889a2140b763c73873a86dd81d961c8e13))


### Documentation

* Use "My Org Id" in example requests ([#81](https://github.com/m3ter-com/m3ter-sdk-python/issues/81)) ([acd1d40](https://github.com/m3ter-com/m3ter-sdk-python/commit/acd1d4002f29041cd2518721d07200643fc7c004))

## 0.1.1-alpha (2025-04-08)

Full Changelog: [v0.1.0-alpha...v0.1.1-alpha](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha...v0.1.1-alpha)

### Chores

* **internal:** slight transform perf improvement ([#79](https://github.com/m3ter-com/m3ter-sdk-python/issues/79)) ([7117cc2](https://github.com/m3ter-com/m3ter-sdk-python/commit/7117cc2f005922440da310e54ec5a032917c34d9))

## 0.1.0-alpha (2025-04-08)

Full Changelog: [v0.1.0-alpha.11...v0.1.0-alpha](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.11...v0.1.0-alpha)

### Features

* **api:** update contact email and package name ([#77](https://github.com/m3ter-com/m3ter-sdk-python/issues/77)) ([92d901e](https://github.com/m3ter-com/m3ter-sdk-python/commit/92d901ec6877ffd987d87bc766463d789e5e123e))


### Chores

* **internal:** remove trailing character ([#75](https://github.com/m3ter-com/m3ter-sdk-python/issues/75)) ([36ad0e5](https://github.com/m3ter-com/m3ter-sdk-python/commit/36ad0e5ca0768dce21866641212f26d0bb6f63b8))

## 0.1.0-alpha.11 (2025-03-27)

Full Changelog: [v0.1.0-alpha.10...v0.1.0-alpha.11](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.10...v0.1.0-alpha.11)

### Bug Fixes

* **ci:** remove publishing patch ([#70](https://github.com/m3ter-com/m3ter-sdk-python/issues/70)) ([6fbbae5](https://github.com/m3ter-com/m3ter-sdk-python/commit/6fbbae5666b4ad473268e2e3a35b864093147ce6))
* **types:** add missing total=False ([#73](https://github.com/m3ter-com/m3ter-sdk-python/issues/73)) ([95c6736](https://github.com/m3ter-com/m3ter-sdk-python/commit/95c6736f6dd00e58c91948451395c72ce6d61aed))


### Chores

* fix typos ([#72](https://github.com/m3ter-com/m3ter-sdk-python/issues/72)) ([ef318ff](https://github.com/m3ter-com/m3ter-sdk-python/commit/ef318ffbd99ae2020a8ef36587be2b3efc02c2ea))

## 0.1.0-alpha.10 (2025-03-17)

Full Changelog: [v0.1.0-alpha.9...v0.1.0-alpha.10](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.9...v0.1.0-alpha.10)

### Bug Fixes

* **ci:** ensure pip is always available ([#68](https://github.com/m3ter-com/m3ter-sdk-python/issues/68)) ([78e0a39](https://github.com/m3ter-com/m3ter-sdk-python/commit/78e0a3959e83e38320f3aaa8c65e8400e37fa215))
* **types:** handle more discriminated union shapes ([#67](https://github.com/m3ter-com/m3ter-sdk-python/issues/67)) ([434c416](https://github.com/m3ter-com/m3ter-sdk-python/commit/434c416439f40c277b410f85d02d107578120b47))


### Chores

* **internal:** version bump ([#65](https://github.com/m3ter-com/m3ter-sdk-python/issues/65)) ([a3e7a93](https://github.com/m3ter-com/m3ter-sdk-python/commit/a3e7a93f97d70482e9063d81ea4595a36122e49c))

## 0.1.0-alpha.9 (2025-03-14)

Full Changelog: [v0.1.0-alpha.8...v0.1.0-alpha.9](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.8...v0.1.0-alpha.9)

### Chores

* **internal:** bump rye to 0.44.0 ([#64](https://github.com/m3ter-com/m3ter-sdk-python/issues/64)) ([38a19e3](https://github.com/m3ter-com/m3ter-sdk-python/commit/38a19e325a0717a7990c87bf32d8d3ac8aba7372))
* **internal:** remove extra empty newlines ([#62](https://github.com/m3ter-com/m3ter-sdk-python/issues/62)) ([5a8dea0](https://github.com/m3ter-com/m3ter-sdk-python/commit/5a8dea0d8d6622239f4a4f2844f1852e3cb5b7b0))

## 0.1.0-alpha.8 (2025-03-11)

Full Changelog: [v0.1.0-alpha.7...v0.1.0-alpha.8](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.7...v0.1.0-alpha.8)

## 0.1.0-alpha.7 (2025-03-09)

Full Changelog: [v0.1.0-alpha.6...v0.1.0-alpha.7](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.6...v0.1.0-alpha.7)

### Features

* **api:** make response model names explicit ([#55](https://github.com/m3ter-com/m3ter-sdk-python/issues/55)) ([183386e](https://github.com/m3ter-com/m3ter-sdk-python/commit/183386e6aedb8cb368868f16d8c3bb48e3baf4a9))


### Documentation

* revise readme docs about nested params ([#57](https://github.com/m3ter-com/m3ter-sdk-python/issues/57)) ([9671ceb](https://github.com/m3ter-com/m3ter-sdk-python/commit/9671cebe0d99b4728ca626ca6ea1b40961010aa4))

## 0.1.0-alpha.6 (2025-03-04)

Full Changelog: [v0.1.0-alpha.5...v0.1.0-alpha.6](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.5...v0.1.0-alpha.6)

### Features

* **api:** manual updates ([#52](https://github.com/m3ter-com/m3ter-sdk-python/issues/52)) ([3f2384f](https://github.com/m3ter-com/m3ter-sdk-python/commit/3f2384f288196411a3f4f32b6befa24f69a93e73))

## 0.1.0-alpha.5 (2025-03-04)

Full Changelog: [v0.1.0-alpha.4...v0.1.0-alpha.5](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.4...v0.1.0-alpha.5)

### Features

* **api:** fixing warnings ([#49](https://github.com/m3ter-com/m3ter-sdk-python/issues/49)) ([948cded](https://github.com/m3ter-com/m3ter-sdk-python/commit/948cdeddc4e66955196ec469aa6ff1f8133356e9))

## 0.1.0-alpha.4 (2025-03-03)

Full Changelog: [v0.1.0-alpha.3...v0.1.0-alpha.4](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.3...v0.1.0-alpha.4)

### Chores

* **internal:** remove unused http client options forwarding ([#46](https://github.com/m3ter-com/m3ter-sdk-python/issues/46)) ([7510f49](https://github.com/m3ter-com/m3ter-sdk-python/commit/7510f49c5d57c0e3b3f938ddcddbc4aee42fb942))

## 0.1.0-alpha.3 (2025-03-03)

Full Changelog: [v0.1.0-alpha.2...v0.1.0-alpha.3](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.2...v0.1.0-alpha.3)

### Bug Fixes

* remove invalid tests ([#44](https://github.com/m3ter-com/m3ter-sdk-python/issues/44)) ([cca6f33](https://github.com/m3ter-com/m3ter-sdk-python/commit/cca6f3385418f095033acc7f000f78c970c84e92))


### Chores

* org ID at the client level is required ([#43](https://github.com/m3ter-com/m3ter-sdk-python/issues/43)) ([d0606c5](https://github.com/m3ter-com/m3ter-sdk-python/commit/d0606c51b4179129e6bb38f2db4f0c3f0296aeb6))
* org ID client arg is optional ([#41](https://github.com/m3ter-com/m3ter-sdk-python/issues/41)) ([67a4aa8](https://github.com/m3ter-com/m3ter-sdk-python/commit/67a4aa88455030135638e3fe7a0db089b0eccc45))

## 0.1.0-alpha.2 (2025-03-03)

Full Changelog: [v0.1.0-alpha.1...v0.1.0-alpha.2](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.1.0-alpha.1...v0.1.0-alpha.2)

### Features

* **api:** add missing endpoints ([#35](https://github.com/m3ter-com/m3ter-sdk-python/issues/35)) ([1e960bf](https://github.com/m3ter-com/m3ter-sdk-python/commit/1e960bfa22cd90105ec4780512ac8287ffaa1b2f))
* **api:** add more endpoints ([#20](https://github.com/m3ter-com/m3ter-sdk-python/issues/20)) ([6445bde](https://github.com/m3ter-com/m3ter-sdk-python/commit/6445bdece1e396aee1a1499bc230dea3e2dd5497))
* **api:** add orgId path param to client settings ([#29](https://github.com/m3ter-com/m3ter-sdk-python/issues/29)) ([e7e5fcc](https://github.com/m3ter-com/m3ter-sdk-python/commit/e7e5fcc56f08db259d71a970037f705c9413b89d))
* **api:** Config update ([#14](https://github.com/m3ter-com/m3ter-sdk-python/issues/14)) ([4dfe290](https://github.com/m3ter-com/m3ter-sdk-python/commit/4dfe2903738e94b2be2f723c93675c9ac373fe57))
* **api:** create ad hoc data export endpoint ([#27](https://github.com/m3ter-com/m3ter-sdk-python/issues/27)) ([687d13f](https://github.com/m3ter-com/m3ter-sdk-python/commit/687d13fe3db079cce72cc54b9e6fb2744ecfff33))
* **api:** snake case method names ([#36](https://github.com/m3ter-com/m3ter-sdk-python/issues/36)) ([e6174e3](https://github.com/m3ter-com/m3ter-sdk-python/commit/e6174e3c31a1059ed6aa3d32b20e9ed535bf777a))
* **api:** Spec Update + Various Fixes ([#39](https://github.com/m3ter-com/m3ter-sdk-python/issues/39)) ([907becd](https://github.com/m3ter-com/m3ter-sdk-python/commit/907becd0bb31e1106a85775dde3ba48f106ef960))
* **api:** Update custom field type information ([#18](https://github.com/m3ter-com/m3ter-sdk-python/issues/18)) ([d0184e8](https://github.com/m3ter-com/m3ter-sdk-python/commit/d0184e89d3f8bb9a5a61cce4c37ce445d8625770))
* **api:** update open api spec ([#34](https://github.com/m3ter-com/m3ter-sdk-python/issues/34)) ([2b9e9db](https://github.com/m3ter-com/m3ter-sdk-python/commit/2b9e9db3f44ec446e46462a64d95e1cf12fd3c89))
* **client:** allow passing `NotGiven` for body ([#31](https://github.com/m3ter-com/m3ter-sdk-python/issues/31)) ([49db89f](https://github.com/m3ter-com/m3ter-sdk-python/commit/49db89f0436deb424fbbae40449dad8090db897a))
* **client:** send `X-Stainless-Read-Timeout` header ([#19](https://github.com/m3ter-com/m3ter-sdk-python/issues/19)) ([be43c57](https://github.com/m3ter-com/m3ter-sdk-python/commit/be43c578d57a15ce8dba423ee9709ecf6d13fa25))


### Bug Fixes

* **client:** mark some request bodies as optional ([49db89f](https://github.com/m3ter-com/m3ter-sdk-python/commit/49db89f0436deb424fbbae40449dad8090db897a))


### Chores

* **docs:** update client docstring ([#38](https://github.com/m3ter-com/m3ter-sdk-python/issues/38)) ([756d62b](https://github.com/m3ter-com/m3ter-sdk-python/commit/756d62bfbc234d813f830c35ae361286bf575e3b))
* **internal:** bummp ruff dependency ([#17](https://github.com/m3ter-com/m3ter-sdk-python/issues/17)) ([7d6c4b4](https://github.com/m3ter-com/m3ter-sdk-python/commit/7d6c4b468996a4f10225a2f24d3be4ac775555fa))
* **internal:** change default timeout to an int ([#16](https://github.com/m3ter-com/m3ter-sdk-python/issues/16)) ([f564f15](https://github.com/m3ter-com/m3ter-sdk-python/commit/f564f15a54458fa30f853b764fcd858f6f0dac99))
* **internal:** codegen related update ([#25](https://github.com/m3ter-com/m3ter-sdk-python/issues/25)) ([a9a56e8](https://github.com/m3ter-com/m3ter-sdk-python/commit/a9a56e8ce7e4c7d94152f44d5d667adc5db6d811))
* **internal:** codegen related update ([#26](https://github.com/m3ter-com/m3ter-sdk-python/issues/26)) ([402683e](https://github.com/m3ter-com/m3ter-sdk-python/commit/402683e171fa5de2449fba12a77a684a800e5a11))
* **internal:** codegen related update ([#28](https://github.com/m3ter-com/m3ter-sdk-python/issues/28)) ([29aef5f](https://github.com/m3ter-com/m3ter-sdk-python/commit/29aef5f14bfc356eb7814f4143e802ac5d109012))
* **internal:** fix devcontainers setup ([#32](https://github.com/m3ter-com/m3ter-sdk-python/issues/32)) ([4661fb8](https://github.com/m3ter-com/m3ter-sdk-python/commit/4661fb8375371ba45b44263a8e04adbfb0d9d1bf))
* **internal:** fix type traversing dictionary params ([#21](https://github.com/m3ter-com/m3ter-sdk-python/issues/21)) ([6d2212e](https://github.com/m3ter-com/m3ter-sdk-python/commit/6d2212e3be2131a52c3605481e1e2e053c00cf81))
* **internal:** minor type handling changes ([#22](https://github.com/m3ter-com/m3ter-sdk-python/issues/22)) ([a189c96](https://github.com/m3ter-com/m3ter-sdk-python/commit/a189c96fd80acdfdf7ea4ee0f11aabf821ec8e8d))
* **internal:** properly set __pydantic_private__ ([#33](https://github.com/m3ter-com/m3ter-sdk-python/issues/33)) ([4406825](https://github.com/m3ter-com/m3ter-sdk-python/commit/4406825ce820d297c3c26315d4df65568f49ef36))
* minor change to tests ([#23](https://github.com/m3ter-com/m3ter-sdk-python/issues/23)) ([46be5a4](https://github.com/m3ter-com/m3ter-sdk-python/commit/46be5a435cb560a17491cc9b45ed0724e45833a5))
* **tests:** skip problematic tests ([#9](https://github.com/m3ter-com/m3ter-sdk-python/issues/9)) ([9590855](https://github.com/m3ter-com/m3ter-sdk-python/commit/9590855c47d25e42172eedd3ce1aafe320416cc3))


### Documentation

* **readme:** update example snippets ([#24](https://github.com/m3ter-com/m3ter-sdk-python/issues/24)) ([62e35aa](https://github.com/m3ter-com/m3ter-sdk-python/commit/62e35aac8ca8bcf0fc9f1056b84a2905d3837945))
* update URLs from stainlessapi.com to stainless.com ([#37](https://github.com/m3ter-com/m3ter-sdk-python/issues/37)) ([c17dae2](https://github.com/m3ter-com/m3ter-sdk-python/commit/c17dae275b3824cdd294afbb031ca49dafedce3e))

## 0.1.0-alpha.1 (2025-01-30)

Full Changelog: [v0.0.1-alpha.0...v0.1.0-alpha.1](https://github.com/m3ter-com/m3ter-sdk-python/compare/v0.0.1-alpha.0...v0.1.0-alpha.1)

### Features

* **api:** add oauth token fetching ([7886fa9](https://github.com/m3ter-com/m3ter-sdk-python/commit/7886fa992f2f7aa5422447f4df99bce85cac245e))
* **api:** add oauth token fetching ([7886fa9](https://github.com/m3ter-com/m3ter-sdk-python/commit/7886fa992f2f7aa5422447f4df99bce85cac245e))
* **api:** add oauth token fetching ([a06c94b](https://github.com/m3ter-com/m3ter-sdk-python/commit/a06c94b7f889f73ac7908200f52147225ba659fc))
* **api:** update readme ([91bea30](https://github.com/m3ter-com/m3ter-sdk-python/commit/91bea30c85ae01cc39dcba995b915829fa99e570))
* **api:** update readme ([91bea30](https://github.com/m3ter-com/m3ter-sdk-python/commit/91bea30c85ae01cc39dcba995b915829fa99e570))
* **api:** update readme ([69817ab](https://github.com/m3ter-com/m3ter-sdk-python/commit/69817ab95899ea425730812b0227592bb94144e6))
* **api:** updated OpenAPI spec ([#11](https://github.com/m3ter-com/m3ter-sdk-python/issues/11)) ([7bd116e](https://github.com/m3ter-com/m3ter-sdk-python/commit/7bd116ee9a575d7c3abc734b142b1d0271c7b30b))


### Bug Fixes

* deduplicate unknown entries in union ([#10](https://github.com/m3ter-com/m3ter-sdk-python/issues/10)) ([31f5718](https://github.com/m3ter-com/m3ter-sdk-python/commit/31f5718193e838d7415163d0c914199c7e37b4ae))


### Chores

* go live ([687d711](https://github.com/m3ter-com/m3ter-sdk-python/commit/687d711164eaca2447a90b19ec67c4cc5b5283cd))
* **internal:** codegen related update ([#8](https://github.com/m3ter-com/m3ter-sdk-python/issues/8)) ([e3b357e](https://github.com/m3ter-com/m3ter-sdk-python/commit/e3b357e7e8c05ca24769dbf1b9327fd8f3a4f474))
* **internal:** minor formatting changes ([#6](https://github.com/m3ter-com/m3ter-sdk-python/issues/6)) ([344d6b2](https://github.com/m3ter-com/m3ter-sdk-python/commit/344d6b266aa90fe051c8c33a250d26dc1dc60fba))
* **internal:** minor style changes ([#4](https://github.com/m3ter-com/m3ter-sdk-python/issues/4)) ([f598842](https://github.com/m3ter-com/m3ter-sdk-python/commit/f598842f6b04a7137cd96a49c98f463fe23cbfde))
* **tests:** skip problematic tests ([#9](https://github.com/m3ter-com/m3ter-sdk-python/issues/9)) ([f21ca07](https://github.com/m3ter-com/m3ter-sdk-python/commit/f21ca07c3210e61ce32dd9b5de914faa56afddc6))
