# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->

## [v1.4.0](https://gitlab.com/solidipes/solidipes/tags/v1.4.0) - 2025-10-16

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v1.3.0...v1.4.0)</small>

### Added

- new logo!
- prepare integration in Renku 2.0
- add rclone mount, download, and upload

### Fixed

- automatic update of RO-Crate metadata
- stuck locked database

<!-- insertion marker -->

## [v1.3.0](https://gitlab.com/solidipes/solidipes/tags/v1.3.0) - 2025-05-27

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v1.2.0...v1.3.0)</small>

### Added

- add windows support
- add dspace 5/7 download and upload
- add plugin interface for scanners
- add `solidipes shell` command
- add `solidipes install-completion` command

### Fixed

- fix dtool uri prefix replacement

<!-- insertion marker -->

## [v1.2.0](https://gitlab.com/solidipes/solidipes/tags/v1.2.0) - 2025-04-09

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v1.1.0...v1.2.0)</small>

### Added

- add viewer selection in web report
- add tests with tagged plugin versions
- add validator infrastructure
- add dtool import/export or download/upload
- add RO-Crate metadata
- add plugin tests
- add tests on macos

### Fixed

- force utf8 encoding when opening files
- fix readthedocs pipeline
- fix huge font in web-report readme
- fix plugin reload
- fix zenodo upload in web report

### Changed

- add generic progress bars and spinners for CLI and web report
- convert python dependency groups into extras (_e.g._ installable with `pip install solidipes[dev]`)
- plugin interfaces for downloaders, reports, and uploaders
- switch from poetry to uv for dependency management

<!-- insertion marker -->

## [v1.1.0](https://gitlab.com/solidipes/solidipes/tags/v1.1.0) - 2024-11-08

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v1.0.1...v1.1.0)</small>

### Added

- add detection of solidipes plugins (metadata group `solidipes.plugins`)
- add loaders and viewers from plugins
- add plugin management interface in web report
- add core, solid-mech, and astro plugins as submodules
- add doc for writing plugins, loaders, and viewers
- create downloader class

### Changed

- move core and solid-mech loaders and viewers to plugins
- remove unused python dependencies
- move `utils.viewer_backends` to `viewers.backends`
- changed `solidipes report web_report` command to `solidipes report web-report`
- integrate zenodo download command into download subclass

<!-- insertion marker -->

## [v1.0.1](https://gitlab.com/solidipes/solidipes/tags/v1.0.1) - 2024-09-13

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v1.0.0...v1.0.1)</small>

### Added

- add file groups unfolding in web report
- add aggregation of file info in web report lists
- add curation fail for empty files

### Changed

- change specification of loaders supported mime-types and extensions

<!-- insertion marker -->

## [v1.0.0](https://gitlab.com/solidipes/solidipes/tags/v1.0.0) - 2024-08-29

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v0.1.9...v1.0.0)</small>

### Added

- added docker image support
- added documentation with videos
- added loaders/viewers for gnuplot, TIKZ
- added new pyvista support using trame

### Changed

- new web interface with acquisition/curation/metadata/export stages

### Fixed

- robust and fast cache system for scanners
- cached preferred loaders

<!-- insertion marker -->

## [v0.1.9](https://gitlab.com/solidipes/solidipes/tags/v0.1.9) - 2024-05-29

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v0.1.8...v0.1.9)</small>

### Added

- added support to lammps files
- added support for numpy files (npy, npz)
- adding support for paraview state files (as xml)

### Changed

- adding zip/unzip in default docker image
- default docker image will install packages in requirements.txt
- Decorator for cached_loadable entries forces a commit to database (fixes a bug in cache)

### Fixed

- jupyter notebook links in web report

<!-- insertion marker -->

## [v0.1.8](https://gitlab.com/solidipes/solidipes/tags/v0.1.8) - 2024-05-16

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v0.1.7...v0.1.8)</small>

### Added

- add linter to pyhton files
- add lazy loader to external modules
- add Dockerhub image automatic generation
- Abaqus loader
- Jupyter Notebook loader
- XDMF and XML loader and tests
- Scanner tests

### Changed

- decorator for loader properties
- decorator for cached properties
- cached metadata (speed improvement)

<!-- insertion marker -->

## [v0.1.7](https://gitlab.com/solidipes/solidipes/tags/v0.1.7) - 2023-12-20

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v0.1.6...v0.1.7)</small>

### Added

- add uploader class
- add renku uploader
- add "editable lists" in web report metadata edition
- add hdf5 support
- add dcsm mount (postgres + minio)

### Changed

- in web report metadata: changed affiliation separator to semicolon
- moved zenodo upload script to uploader class
- update documentation
- better manipulation of cache

### Fixed

- fix zenodo upload and download (api changed)

<!-- insertion marker -->

## [v0.1.6](https://gitlab.com/solidipes/solidipes/tags/v0.1.6) - 2023-11-10

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v0.1.5...v0.1.6)</small>

### Added

- add postgres mount

<!-- insertion marker -->

## [v0.1.5](https://gitlab.com/solidipes/solidipes/tags/v0.1.5) - 2023-10-13

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v0.1.4...v0.1.5)</small>

### Added

- add: sphinx documentation structure
- add: user documentation initial usable version

<!-- insertion marker -->

## [v0.1.4](https://gitlab.com/solidipes/solidipes/tags/v0.1.4) - 2023-10-13

<small>[Compare with latest](https://gitlab.com/solidipes/solidipes/compare/v0.1.3...v0.1.4)</small>

### Features

- feat: new logging system
- feat: stabilize file sequences info
- feat: separate window view for opened file
- feat: use exif to fetch image metadata

### Added

- add: discussions possible and stored in metadata
- add: symbolic link in datasets

### Changed

- change: refactor the utils module

<!-- insertion marker -->

## [v0.1.3](https://gitlab.com/solidipes/solidipes/tags/v0.1.3) - 2023-09-14

<small>[Compare with v0.1.2](https://gitlab.com/solidipes/solidipes/compare/v0.1.2...v0.1.3)</small>

### Added

- add download of nested zenodo files ([e44ae23](https://gitlab.com/solidipes/solidipes/commit/e44ae23b97022dc00628ca2637f53ab1a5fe508f) by Son Pham-Ba).
- adding comments on the curation part ([c24f13e](https://gitlab.com/solidipes/solidipes/commit/c24f13e3ae17a9ca84481a6e7a0ac741f6017b6b) by Guillaume Anciaux).
- add default keyword list in metadata ([0e3ad37](https://gitlab.com/solidipes/solidipes/commit/0e3ad372802a11925edb62f46da24806575b5543) by Son Pham-Ba).
- add more representative default metadata authors ([67fc6fe](https://gitlab.com/solidipes/solidipes/commit/67fc6fee13fa683de444317621ba9ad519f8e985) by Son Pham-Ba).
- added to doc tree ([0ce18ae](https://gitlab.com/solidipes/solidipes/commit/0ce18ae1e0c9844d8ea087da0d3c6878e69c0e10) by LaetiMS).
- adding images and new structure ([dcff86b](https://gitlab.com/solidipes/solidipes/commit/dcff86bca91b0d286af1501ec25baa344e4ed2c4) by LaetiMS).
- add tests for loader sequences and metadata ([7dc86c5](https://gitlab.com/solidipes/solidipes/commit/7dc86c5a4e341a27c561c91fa26360ef78c7f057) by Son Pham-Ba).
- add "question" issue template ([1f0638b](https://gitlab.com/solidipes/solidipes/commit/1f0638b389d2746bc283b763fd8dcda7f426ccdb) by Son Pham-Ba).
- add cached metadata to file sequences ([fd725f4](https://gitlab.com/solidipes/solidipes/commit/fd725f4bd0a7d2f5a4f4cdad5f5d6e4f2d3c946b) by Son Pham-Ba).
- add cached metadata for files ([03abd74](https://gitlab.com/solidipes/solidipes/commit/03abd74f953bd78501cc5dd60a166475885f507c) by Son Pham-Ba).
- adding a spinner ([d088870](https://gitlab.com/solidipes/solidipes/commit/d0888702aef79d9e01b86a0591d9c2caa9aba1fc) by Guillaume Anciaux).
- add a delay before mounting ([675b831](https://gitlab.com/solidipes/solidipes/commit/675b831c4b50201d2ff78ca6bc988c1e515e1901) by Guillaume Anciaux).
- add public_keys in cloud test ([967630e](https://gitlab.com/solidipes/solidipes/commit/967630e90f918add6f54326fb08b99c777f5e974) by Son Pham-Ba).
- add option to save mount keys publicly ([5289981](https://gitlab.com/solidipes/solidipes/commit/52899814dfa9c617479681212e4fa68386aefe50) by Son Pham-Ba).
- add mount all in web report ([e04be2e](https://gitlab.com/solidipes/solidipes/commit/e04be2ee365ef407f4cf987ef4d9bbef3ad6cb7d) by Son Pham-Ba).
- add unmount_all python function ([59435f5](https://gitlab.com/solidipes/solidipes/commit/59435f5b2aad9e66efe4d972963266e0da4e965f) by Son Pham-Ba).
- adding loader type, viewer type guides ([1d0ddc3](https://gitlab.com/solidipes/solidipes/commit/1d0ddc3897401242dcf7fc6d5a7638c7959cbf0d) by LaetiMS).
- add sudo explanation for mount command ([89c496b](https://gitlab.com/solidipes/solidipes/commit/89c496bf788505d9e9e4ff23ce9e108d7eb91eee) by Son Pham-Ba).
- add mount options for smb (username, password, domain) ([31c5a36](https://gitlab.com/solidipes/solidipes/commit/31c5a3662faa4eb927bbbd7e7d45fa6ee0d60b28) by Son Pham-Ba).
- adding option to pdf catch exception for userdef mimes ([ab8766c](https://gitlab.com/solidipes/solidipes/commit/ab8766cf8a3284de6b944c4c76a8087e05ad9420) by Guillaume Anciaux).
- adding possibility to warp a field ([c086d96](https://gitlab.com/solidipes/solidipes/commit/c086d96850752ca9c91bedce40b7f42f52fad5f1) by Guillaume Anciaux).
- add sequence's element selection in web report ([8e62f13](https://gitlab.com/solidipes/solidipes/commit/8e62f1310d1d8e165dd46b296a5cccf8c8a7ec64) by Son Pham-Ba).
- add sequence loader, base of file_sequence ([884a20a](https://gitlab.com/solidipes/solidipes/commit/884a20ae048970de93551006f09474bb0f61ed6d) by Son Pham-Ba).
- adding possibility to view a field ([02169a8](https://gitlab.com/solidipes/solidipes/commit/02169a81981fcef410050a3b20bd0abc4fd180c2) by Guillaume Anciaux).
- add image_sequence frame selection ([9018e4c](https://gitlab.com/solidipes/solidipes/commit/9018e4c934cb38fee436edf7a05b72d528b30a4c) by Son Pham-Ba).
- add frame loading for image sequence ([6d3f315](https://gitlab.com/solidipes/solidipes/commit/6d3f3150869ce8df3c1cd90786cc63e75e17fdb8) by Son Pham-Ba).
- add image_sequence loader and detection ([8021bfd](https://gitlab.com/solidipes/solidipes/commit/8021bfddf48e9566d8c743a11715d30a36f672ea) by Son Pham-Ba).
- add soft fails in mount all command ([28014d7](https://gitlab.com/solidipes/solidipes/commit/28014d7450c4b86e309064bc3371fb56153c6734) by Son Pham-Ba).
- add exception when private credentials missing ([0a17f21](https://gitlab.com/solidipes/solidipes/commit/0a17f21b101c7bf7212a2ce7b7fc2a090688cac4) by Son Pham-Ba).
- add spelling precommit and fix typos ([be15ef9](https://gitlab.com/solidipes/solidipes/commit/be15ef98138b15ea0c49dbf79519681b240a3014) by Son Pham-Ba).
- add command to mount all ([8aa92e9](https://gitlab.com/solidipes/solidipes/commit/8aa92e93c308455782955c29123644081ee94ed9) by Son Pham-Ba).
- add nfs and smb mounts ([82e0a74](https://gitlab.com/solidipes/solidipes/commit/82e0a74abf6c0dd06a078745b3a5730d6ad09837) by Son Pham-Ba).
- add mount ssh with sshfs ([d752926](https://gitlab.com/solidipes/solidipes/commit/d752926a403726ddbcabd2b957c7730f7d9b1145) by Son Pham-Ba).
- add pdf generation for readthedocs ([73c85bb](https://gitlab.com/solidipes/solidipes/commit/73c85bb5abb84c317f23ac815c026e908e3c440b) by Son Pham-Ba).
- add 'code documentation' section in doc ([bcbe20c](https://gitlab.com/solidipes/solidipes/commit/bcbe20cbcaf18a7a2e22693cf37330c1730a06b6) by Son Pham-Ba).
- add readthedocs python version specification ([fc5e990](https://gitlab.com/solidipes/solidipes/commit/fc5e9901e3745cb703cd695ee3abe25608f0938f) by Son Pham-Ba).
- add pre-commit hook to update doc deps for rtd ([e13f381](https://gitlab.com/solidipes/solidipes/commit/e13f381faf957cbe66dfb10ef54b5555dd8462ec) by Son Pham-Ba).
- add "doc" build dependency group ([5cae686](https://gitlab.com/solidipes/solidipes/commit/5cae6869d1416b719368f7c9a587874ac1871292) by Son Pham-Ba).
- add short cloud mount doc ([7fc38ec](https://gitlab.com/solidipes/solidipes/commit/7fc38ec1223c9e6193b7ce9613c59ea1370ef32b) by Son Pham-Ba).
- add test file for metadata ([bcd042a](https://gitlab.com/solidipes/solidipes/commit/bcd042a602c39dc4488a49bc6ffcba0f346e2f6d) by Son Pham-Ba).
- add tests for DESCRIPTION and README ([d35aa1b](https://gitlab.com/solidipes/solidipes/commit/d35aa1bec76c587b28199ed3d53162bb648c2926) by Son Pham-Ba).
- add method for listing mounted dirs ([e4fbc3f](https://gitlab.com/solidipes/solidipes/commit/e4fbc3f599d67fcda931a5d03bef0e4f88ad8c0b) by Son Pham-Ba).
- add trailing "/" removal in path in mount commands ([046b8ba](https://gitlab.com/solidipes/solidipes/commit/046b8ba7524f264f364c203f0b74e3691297d34e) by Son Pham-Ba).
- add test for mount convert command ([63a2cb9](https://gitlab.com/solidipes/solidipes/commit/63a2cb92a12479037e7df8ac89f9c47933cb9878) by Son Pham-Ba).
- add s3 conversion command ([3b203a1](https://gitlab.com/solidipes/solidipes/commit/3b203a17263665929870002cc8e60c1906105f7c) by Son Pham-Ba).
- add simple way of mounting s3fs subdirectory ([bc1a5c3](https://gitlab.com/solidipes/solidipes/commit/bc1a5c3fc3080d36101e22154954c13b47837574) by Son Pham-Ba).
- add juicefs mount implementation ([0b88e56](https://gitlab.com/solidipes/solidipes/commit/0b88e56128262087288babbb7805eef1f9000917) by Son Pham-Ba).
- add .solidipes directory in user's home ([45dfea8](https://gitlab.com/solidipes/solidipes/commit/45dfea8f4e7dbf664958d1324c61c96a8163ef31) by Son Pham-Ba).
- add s3 mounting system selection ([c9639ee](https://gitlab.com/solidipes/solidipes/commit/c9639ee9fafc428a251cf3aa930562b919124e64) by Son Pham-Ba).
- add list mount points command ([6300e27](https://gitlab.com/solidipes/solidipes/commit/6300e27ff6aa754a49cf4fa5e1ac89fba11113d9) by Son Pham-Ba).
- adding eth and solidipes info ([8d91e99](https://gitlab.com/solidipes/solidipes/commit/8d91e9967b0be77bad18d53d23d6c7310d813dc3) by Guillaume Anciaux).
- add a link to edit DESCRIPTION.md in gitlab ([e046fa8](https://gitlab.com/solidipes/solidipes/commit/e046fa81d1b90fa4c78c86490e1a2da00f83360d) by Guillaume Anciaux).
- add pdf view and visible git push button ([faabee5](https://gitlab.com/solidipes/solidipes/commit/faabee5fb8844a154ed703a3105953eba6305b40) by Guillaume Anciaux).
- add direct link to gitlab ([a90af83](https://gitlab.com/solidipes/solidipes/commit/a90af8398e839bc7936635b4ff5679a8ac2f18ad) by Guillaume Anciaux).
- adding a missing package ([1e3dbbd](https://gitlab.com/solidipes/solidipes/commit/1e3dbbd6990e5b49374b64c92c013c1014f9d955) by Guillaume Anciaux).
- adding the generation of the readme ([5784c6c](https://gitlab.com/solidipes/solidipes/commit/5784c6c9018e4ea459c96a820030aa46f5ca4586) by Guillaume Anciaux).
- adding prog editor ([623f816](https://gitlab.com/solidipes/solidipes/commit/623f8163b5e44a951e552abc531d3157eeeb1150) by Guillaume Anciaux).
- adding widget for the editing ([f1e6d1d](https://gitlab.com/solidipes/solidipes/commit/f1e6d1dd4d06d8d5870ed878785da0221f442d51) by Guillaume Anciaux).
- add DESCRIPTION.md file for Zenodo metadata ([c666e48](https://gitlab.com/solidipes/solidipes/commit/c666e487e957b7f4103ab1e5a0af1fd932a18de4) by Son Pham-Ba).
- add widget dependencies ([51c0289](https://gitlab.com/solidipes/solidipes/commit/51c0289051b335832cb99ce04eed3e61ae65ace4) by Son Pham-Ba).
- add expanders for nicer view ([2a3157c](https://gitlab.com/solidipes/solidipes/commit/2a3157c52200eaed0960bba4eed521987d435ae1) by Guillaume Anciaux).
- adding options ([0fb0782](https://gitlab.com/solidipes/solidipes/commit/0fb0782b3d8900972261c32ec4217c6099b79b11) by Guillaume Anciaux).
- add checkbox in web report to create new deposit ([3f8a2d3](https://gitlab.com/solidipes/solidipes/commit/3f8a2d31bd84721924f14a2f0d9883f8a2d7ab24) by Son Pham-Ba).
- adding back the description stuff ([81685bd](https://gitlab.com/solidipes/solidipes/commit/81685bdc703374d1c5ac5988093a5272fdd496d2) by Guillaume Anciaux).
- add pypi badge to readme ([5f8c42d](https://gitlab.com/solidipes/solidipes/commit/5f8c42d37443b424799f78eb5c87f4b60f9f3db2) by Son Pham-Ba).
- add tests for mount and unmount commands ([9e72e70](https://gitlab.com/solidipes/solidipes/commit/9e72e7010f5d3cf4b7e2778da4d2914c9cbcc567) by Son Pham-Ba).
- add test for commands ([d394aa3](https://gitlab.com/solidipes/solidipes/commit/d394aa36b13be616a34ac1be6000ef1de8be8756) by Son Pham-Ba).
- add tests for cloud_utils ([e972555](https://gitlab.com/solidipes/solidipes/commit/e9725559391406dd5fc90b1bbdf05e9c6bd8fc97) by Son Pham-Ba).
- add commands to mount and unmount s3 ([e906d0e](https://gitlab.com/solidipes/solidipes/commit/e906d0e578073849a6a02f437693098c67a315df) by Son Pham-Ba).
- add method to remove saved cloud info ([c707444](https://gitlab.com/solidipes/solidipes/commit/c707444cb7191e82502046eddaa976eb51aab3b4) by Son Pham-Ba).
- add s3 mount methods ([8317927](https://gitlab.com/solidipes/solidipes/commit/8317927e9ec183ce12598a3377c819d4d9878d91) by Son Pham-Ba).

### Fixed

- Fix the problem of invalid yaml when filling authors ([88c86d3](https://gitlab.com/solidipes/solidipes/commit/88c86d306b0e412c9fb6cb874d7a7d1ac6025e6b) by Guillaume Anciaux).
- fixing the the curation in terminal ([4ac5af9](https://gitlab.com/solidipes/solidipes/commit/4ac5af91159aa59120971e1df772fa04eaae29ec) by Guillaume Anciaux).
- fix regression bug for the geof loader ([3c22409](https://gitlab.com/solidipes/solidipes/commit/3c2240901c02506aba7dac161b2a6d40d32db95d) by Guillaume Anciaux).
- fix: add cached metadata class file ([e71fe00](https://gitlab.com/solidipes/solidipes/commit/e71fe00a13c3f9b5ecf98da28cb89ceca6634391) by Son Pham-Ba).
- fix cloud test waiting for mount ([188b751](https://gitlab.com/solidipes/solidipes/commit/188b751d112a3540de2d3c4a09e826540b37238f) by Son Pham-Ba).
- fix a keyerror problem ([8014d8e](https://gitlab.com/solidipes/solidipes/commit/8014d8e8c4467cd878a223a63a0188e281df92df) by Guillaume Anciaux).
- fix cloud key replacement ([a994340](https://gitlab.com/solidipes/solidipes/commit/a994340bb65468b0076c41b31f5fc71ac29fba36) by Son Pham-Ba).
- fix sequences in web report ([b3dd07f](https://gitlab.com/solidipes/solidipes/commit/b3dd07f20225859d8e1823176bc02d1d4e4c1abe) by Son Pham-Ba).
- fix full execution of web report on File.view error ([c2bac1d](https://gitlab.com/solidipes/solidipes/commit/c2bac1dfdb6b24c4010c7136e422ada2bfa9dd70) by Son Pham-Ba).
- fix 16 bit images in streamlit ([0be4f8e](https://gitlab.com/solidipes/solidipes/commit/0be4f8e8a4a9732360b1e904c781a85b53806602) by Son Pham-Ba).
- fix exception type on missing data_container attribute ([0e4c604](https://gitlab.com/solidipes/solidipes/commit/0e4c604fda99a1f226781ff540437f6bf1e8314d) by Son Pham-Ba).
- fix juicefs mount by creating .solidipes/cloud/ ([4c25165](https://gitlab.com/solidipes/solidipes/commit/4c25165fc42eb976a19540bae2939612b0db0276) by Son Pham-Ba).
- fix typos in cloud test comments ([11770d4](https://gitlab.com/solidipes/solidipes/commit/11770d44e452a412ac2c8d8754483ab126de44e9) by Son Pham-Ba).
- fix cloud arguments in test ([1883cc2](https://gitlab.com/solidipes/solidipes/commit/1883cc263285cbdcdfe327431c73b1b5268bb7c7) by Son Pham-Ba).
- fix solidipes init behavior with home directory ([c234272](https://gitlab.com/solidipes/solidipes/commit/c234272ff8e38e38cad3ee08f8901a9184698f05) by Son Pham-Ba).
- fix .readthedocs jobs ([6a2d7cf](https://gitlab.com/solidipes/solidipes/commit/6a2d7cf7705eab7e8ecc56c729cb2b7d2c52727e) by Son Pham-Ba).
- fix zenodo upload-download compatibility ([e88fa91](https://gitlab.com/solidipes/solidipes/commit/e88fa919bbf04b3f1cf10af83f021952d136e6c0) by Son Pham-Ba).
- fix wrong DESCRIPTION updated when uploading ([8302ae6](https://gitlab.com/solidipes/solidipes/commit/8302ae6de9796d014da19333d2c84d7a264946c4) by Son Pham-Ba).
- fix tests involving user's home dir ([776199f](https://gitlab.com/solidipes/solidipes/commit/776199f7fd7de347bfa9ab968f4dd66272fec3de) by Son Pham-Ba).
- fix cloud tests (command arguments) ([9e287df](https://gitlab.com/solidipes/solidipes/commit/9e287df028ca01e7c9dd67f8b44a6d5fcb48285f) by Son Pham-Ba).
- fix utils methods kwargs ([85712fa](https://gitlab.com/solidipes/solidipes/commit/85712fa3c9b131502b76b7e18bc863075c73785f) by Son Pham-Ba).
- fix metadata web_report tests ([64ef448](https://gitlab.com/solidipes/solidipes/commit/64ef4489b6628d33ee57f83b64c1e661a487131e) by Son Pham-Ba).
- fix web_report saving description ([dc45c35](https://gitlab.com/solidipes/solidipes/commit/dc45c354a2334cc909633a3c03e4b6e8211bffa4) by Son Pham-Ba).
- fix a not passing test ([c9755be](https://gitlab.com/solidipes/solidipes/commit/c9755be69d31bf7a5c710935f50b1d519590245c) by Guillaume Anciaux).
- fix zenodo metadata in upload test ([ef065fa](https://gitlab.com/solidipes/solidipes/commit/ef065fa0a793f882e19cc69d748313178d260377) by Son Pham-Ba).
- fix web report in non-git directory ([7e23c8f](https://gitlab.com/solidipes/solidipes/commit/7e23c8f5ab913a48833682af8523ae7f6a972264) by Son Pham-Ba).
- fix typo in upload argument ([f3928c2](https://gitlab.com/solidipes/solidipes/commit/f3928c2d047ac327b535ee5a1bc4614e0a7e586e) by Son Pham-Ba).

### Changed

- change back the interface ([fe16e10](https://gitlab.com/solidipes/solidipes/commit/fe16e1016c9b798f6846945b2c0acb13e9056ef3) by Guillaume Anciaux).
- change a bad call ([bdba9e5](https://gitlab.com/solidipes/solidipes/commit/bdba9e57c190965a9a03f014ba14a2b96db7c239) by Guillaume Anciaux).
- change edit button ([4622a59](https://gitlab.com/solidipes/solidipes/commit/4622a596368293f780a63613ed87ffe3fe7a7df3) by Guillaume Anciaux).
- change the automatic mount ([5e0d985](https://gitlab.com/solidipes/solidipes/commit/5e0d985ea016fe3debc8e5c71ec4443f92679431) by Guillaume Anciaux).

### Removed

- remove useless things ([cfe8925](https://gitlab.com/solidipes/solidipes/commit/cfe89258539646d85be4ad4e0e26451d6c659b23) by Guillaume Anciaux).
- remove keys from juicefs database ([b3407c3](https://gitlab.com/solidipes/solidipes/commit/b3407c3008ef8eeef938c06778dd6a58814d03bc) by Son Pham-Ba).
- remove mount warning when keys in project ([18b26c0](https://gitlab.com/solidipes/solidipes/commit/18b26c02482bbcbeac39e5eb5292a890a12af1a6) by Son Pham-Ba).
- remove error when mount with missing private credential ([c86ef34](https://gitlab.com/solidipes/solidipes/commit/c86ef3410eeaddbb81d370f6dd71444b5b8428be) by Son Pham-Ba).
- remove unused docs/requirements.txt ([1f30245](https://gitlab.com/solidipes/solidipes/commit/1f302450c2534c722745764d94454ef49f8aa132) by Son Pham-Ba).
- remove unused cloud info setting methods ([1c3acf4](https://gitlab.com/solidipes/solidipes/commit/1c3acf40bbb303cb61d1cb68211ef8c11f65b860) by Son Pham-Ba).
- remove unused file ([a5dffa9](https://gitlab.com/solidipes/solidipes/commit/a5dffa91d33a78612c7ece502dece473025d6d6e) by Son Pham-Ba).

## [v0.1.2](https://gitlab.com/solidipes/solidipes/tags/v0.1.2) - 2023-05-17

<small>[Compare with v0.1.1](https://gitlab.com/solidipes/solidipes/compare/v0.1.1...v0.1.2)</small>

### Fixed

- fix ci "/" in branch name ([ee6301b](https://gitlab.com/solidipes/solidipes/commit/ee6301b94ddfdf078666d3192d25122acf94b8e6) by Son Pham-Ba).

## [v0.1.1](https://gitlab.com/solidipes/solidipes/tags/v0.1.1) - 2023-05-12

<small>[Compare with v0.1.0](https://gitlab.com/solidipes/solidipes/compare/v0.1.0...v0.1.1)</small>

### Added

- add changelog in Makefile ([ff994dc](https://gitlab.com/solidipes/solidipes/commit/ff994dc24eba882f8bb3310763542e1a5e1c9757) by Son Pham-Ba).
- add tests for web_report with different settings ([8137676](https://gitlab.com/solidipes/solidipes/commit/8137676b32dc7619bd21c7bc1ebc7adc95ad9be1) by Son Pham-Ba).
- add test zenodo upload ([492a611](https://gitlab.com/solidipes/solidipes/commit/492a6118d1a54563c01b59f264f85dbc9d1b7271) by Son Pham-Ba).
- add zenodo download test ([1301fda](https://gitlab.com/solidipes/solidipes/commit/1301fda05add957f482a7760b4cf573ff476ea31) by Son Pham-Ba).
- add web_report test to ci ([72ac480](https://gitlab.com/solidipes/solidipes/commit/72ac480f3b24214537aec7e4778ddb4be26c9e49) by Son Pham-Ba).
- add web_report test with selenium ([50a0d06](https://gitlab.com/solidipes/solidipes/commit/50a0d061e83e8b11a7bbac46956d81bd4ede6240) by Son Pham-Ba).
- add branch name to test docker image tags ([57de22b](https://gitlab.com/solidipes/solidipes/commit/57de22bac90774e9241a44669c8086ebc6438473) by Son Pham-Ba).
- add logo in readme ([11665f4](https://gitlab.com/solidipes/solidipes/commit/11665f4b934bbde56cc242cfe674c3cbee00795e) by Son Pham-Ba).
- add test requirement before publishing in ci ([e6dbafb](https://gitlab.com/solidipes/solidipes/commit/e6dbafb05fa357debf1679a9d35e51a7c70906b4) by Son Pham-Ba).

### Fixed

- fix: allow tests ci to run if ci_commit_branch is null ([dec845f](https://gitlab.com/solidipes/solidipes/commit/dec845f8a40afd3060359e13adc92e0108598c7c) by Son Pham-Ba).
- fix tests ci to run on branches' commits ([b299bbd](https://gitlab.com/solidipes/solidipes/commit/b299bbd7da8bec8ed2652383f45afd4d37b9d747) by Son Pham-Ba).
- fix docker image fetch in ci tests triggered by tag ([e9c0d4e](https://gitlab.com/solidipes/solidipes/commit/e9c0d4ea133974505b0acbddcbc353db6fc8c393) by Son Pham-Ba).
- fix docs requirements ([917c553](https://gitlab.com/solidipes/solidipes/commit/917c553d6ebd1076ee31dd10677cc2526b561e68) by Son Pham-Ba).
- fix import in web_report ([4690a38](https://gitlab.com/solidipes/solidipes/commit/4690a38a17281e5422b2190736b0b3d32b82bb21) by Son Pham-Ba).

### Changed

- change logo size ([c2eb0fb](https://gitlab.com/solidipes/solidipes/commit/c2eb0fb2130da2af8516798d1c6e6e2997c3baf0) by Son Pham-Ba).

### Removed

- remove commented lines from Dockerfile ([c4aedaa](https://gitlab.com/solidipes/solidipes/commit/c4aedaa2d6e80afa46d0e573a45bc6a875535956) by Son Pham-Ba).

## [v0.1.0](https://gitlab.com/solidipes/solidipes/tags/v0.1.0) - 2023-04-26

<small>[Compare with v0.0.1](https://gitlab.com/solidipes/solidipes/compare/v0.0.1...v0.1.0)</small>

### Added

- add reference to Getting started (doc) in Readme ([7c8ed6a](https://gitlab.com/solidipes/solidipes/commit/7c8ed6a46485c7d31e225d26565fae4a79834e1f) by Son Pham-Ba).
- add "Getting started" section in doc ([85e349b](https://gitlab.com/solidipes/solidipes/commit/85e349b9180a4e8c55ecc05e29541043dfb83e3a) by Son Pham-Ba).
- add python 3.8 compatibility ([f8d2573](https://gitlab.com/solidipes/solidipes/commit/f8d25731b5beeee7e8048ab7421a5b14891b7043) by Son Pham-Ba).
- adding a separator ([377edf1](https://gitlab.com/solidipes/solidipes/commit/377edf12b869a428bcfd49a7bec384e4f3111bf3) by Guillaume Anciaux).
- adding issues to the report ([6547a42](https://gitlab.com/solidipes/solidipes/commit/6547a4200f5f005830550326c735378cc08723ee) by Guillaume Anciaux).
- add python deps to tests' docker image ([d36759a](https://gitlab.com/solidipes/solidipes/commit/d36759a09c014a2bd221e9270c139e02b1f24a80) by Son Pham-Ba).
- add tests' docker image build in ci ([4992a2d](https://gitlab.com/solidipes/solidipes/commit/4992a2daf358257d4bb4ca8fb538ffc1d9c78d62) by Son Pham-Ba).
- add Dockerfile for tests' image ([242854c](https://gitlab.com/solidipes/solidipes/commit/242854c0d62bde204f7f5d77510d559b65bcb18c) by Son Pham-Ba).
- add list of ignored paths ([b912679](https://gitlab.com/solidipes/solidipes/commit/b9126791303c06239a6e3b9def6b1b92aa3c9e79) by Son Pham-Ba).
- adding matlab in loaders and fix the default viewer ([bc53e11](https://gitlab.com/solidipes/solidipes/commit/bc53e11df55e3c5f51a0195613ec52ca53cdd452) by Guillaume Anciaux).
- adding mimes config ([328376c](https://gitlab.com/solidipes/solidipes/commit/328376cff7df597d159c8c83c0b988793751dea4) by Guillaume Anciaux).
- add excluded patterns (instead of files) in scanner ([47ee8e9](https://gitlab.com/solidipes/solidipes/commit/47ee8e92cb5234f1d55916713470b1b2cd0065c6) by Son Pham-Ba).
- adding information for the zenodo dataset ([22bdee7](https://gitlab.com/solidipes/solidipes/commit/22bdee7c14c619bdb11419fca07a1e227013265c) by Guillaume Anciaux).
- add "solidipes init" command (empty .solidipes) ([ca884e8](https://gitlab.com/solidipes/solidipes/commit/ca884e846c97c8c8cff28c1de42b2e9bfd539fe2) by Son Pham-Ba).
- add zenodo upload to existing diposit ([cf800d4](https://gitlab.com/solidipes/solidipes/commit/cf800d45f33ec181b7ced6c581f583364ae9d8ad) by Son Pham-Ba).
- add zenodo_utils module for commands ([b7e22c3](https://gitlab.com/solidipes/solidipes/commit/b7e22c33172cadd61d3e9086e2bb2d45ac61678a) by Son Pham-Ba).
- add argcomplete for TAB completion in CLI ([aba4517](https://gitlab.com/solidipes/solidipes/commit/aba45174c3517b8d4f3e3f4185e634b085fd85ec) by Son Pham-Ba).
- add list of report types to report command ([fd37202](https://gitlab.com/solidipes/solidipes/commit/fd37202fbdae0205c030a5b9a50c86220b0bb729) by Son Pham-Ba).
- add option to only download metadata ([525487a](https://gitlab.com/solidipes/solidipes/commit/525487a3fa7cf04512cbc1c9b7e7b496f698cd99) by Son Pham-Ba).
- add metadata processing of download and upload ([2584183](https://gitlab.com/solidipes/solidipes/commit/258418366b2969b580140483030fba35d23cf697) by Son Pham-Ba).
- add progress bar when uploading to Zenodo ([8c758d0](https://gitlab.com/solidipes/solidipes/commit/8c758d0bf265b5c2969868759939f5acfbe120a6) by Son Pham-Ba).
- Add command to upload directory to Zenodo ([19afaba](https://gitlab.com/solidipes/solidipes/commit/19afabaa96a01ec55abe8e4948ad8351d86e3447) by Son Pham-Ba).
- add progress bars when downloading from Zenodo ([bed179a](https://gitlab.com/solidipes/solidipes/commit/bed179a0dbc4361da91e4758ae9bed8bee073521) by Son Pham-Ba).
- add command to download from Zenodo ([8a66014](https://gitlab.com/solidipes/solidipes/commit/8a660140038e918dbd5eca6fdf0cfa27dcd8f9e0) by Son Pham-Ba).
- add files to ignore ([d41a785](https://gitlab.com/solidipes/solidipes/commit/d41a785f747f9c5a945983fab528fce9fbcb7a20) by Guillaume Anciaux).
- adding link to jupyterlab ([3d0fc2b](https://gitlab.com/solidipes/solidipes/commit/3d0fc2bfa64ee140a1b29ee0f4cd9b2b73c8a4ea) by Guillaume Anciaux).
- adding a dep ([5b11473](https://gitlab.com/solidipes/solidipes/commit/5b11473b35f2dab84d376af094c60abb8d04d579) by Guillaume Anciaux).
- add review and icons ([ec1c2d8](https://gitlab.com/solidipes/solidipes/commit/ec1c2d813bda5ea45170d68c2b510a3bb9b8ed0d) by Guillaume Anciaux).
- add a key to checkbox ([4e3217d](https://gitlab.com/solidipes/solidipes/commit/4e3217d39d58fba99c11947a0be07b1cc235936c) by Guillaume Anciaux).
- add a key to duplicate button ([af1208f](https://gitlab.com/solidipes/solidipes/commit/af1208fc5cd04ba8878bba2404c9325b79321f88) by Guillaume Anciaux).
- add possibility to launch xvfb ([3e49e57](https://gitlab.com/solidipes/solidipes/commit/3e49e57ae7dd60177ff65bdb3d4f8d87cd585550) by Guillaume Anciaux).
- adding options for the curation ([03704b3](https://gitlab.com/solidipes/solidipes/commit/03704b3dff58e7c3c3a60f3527e346425fa200d5) by Guillaume Anciaux).
- adding edition possibility through gitlab ([1b249a3](https://gitlab.com/solidipes/solidipes/commit/1b249a3ff06dcf1bdb5d146e852d1ab23cfb29e4) by Guillaume Anciaux).
- adding possibility to report errors ([cd9e795](https://gitlab.com/solidipes/solidipes/commit/cd9e795512e412d8e87dc3ac9964f249e8cdb0e0) by Guillaume Anciaux).
- adding keys to csv viewer component ([cdd6554](https://gitlab.com/solidipes/solidipes/commit/cdd6554adf025be206d3312265a43d73ea157e10) by Guillaume Anciaux).
- adding a report ([03e9af3](https://gitlab.com/solidipes/solidipes/commit/03e9af3809addac8512d2630a55ed653b5eda8f8) by Guillaume Anciaux).
- add image support ([2bc7334](https://gitlab.com/solidipes/solidipes/commit/2bc73341c064cd38c45edea5d044acc8d44a8a78) by Son Pham-Ba).
- add markdown to mime detection ([5880146](https://gitlab.com/solidipes/solidipes/commit/588014697a0224142fd27b0c16cb9e669c49847b) by Guillaume Anciaux).
- add supported extensions and mime types in File loaders ([41c4557](https://gitlab.com/solidipes/solidipes/commit/41c45572075b77f7f5328aaeefde2edc6ffd279c) by Son Pham-Ba).
- add data type check in viewers ([04ab931](https://gitlab.com/solidipes/solidipes/commit/04ab93174244dc7d013879e3784eb7b2132c10d0) by Son Pham-Ba).
- add optional "data" argument in viewer constructor ([84ed117](https://gitlab.com/solidipes/solidipes/commit/84ed117bedb0136f7222273600f0d086e87379d2) by Son Pham-Ba).
- addind a dependency ([f16586e](https://gitlab.com/solidipes/solidipes/commit/f16586e9b26d3b869cbb360f5bf27d828b1791f2) by Guillaume Anciaux).
- add virtual frame buffer for pyvista plotter test ([052b567](https://gitlab.com/solidipes/solidipes/commit/052b567e310614cdf7bccfe56439bb8713bf4618) by Son Pham-Ba).
- add test requirements to gitlab ci ([d69211f](https://gitlab.com/solidipes/solidipes/commit/d69211f1472e01fb3e0b7c45787c23959ecc4cf9) by Son Pham-Ba).
- add short docstrings to all ([f950ef3](https://gitlab.com/solidipes/solidipes/commit/f950ef336b424b4edb7abff67367024d94df41d9) by Son Pham-Ba).
- add test for PyvistaPlotter screenshot save ([3341b3e](https://gitlab.com/solidipes/solidipes/commit/3341b3e23e1d66c2b5b133bedc921e12424fce33) by Son Pham-Ba).
- add scripts directory to doc ([ee466c1](https://gitlab.com/solidipes/solidipes/commit/ee466c1068750f04e24b0b0b0eb3ea82a3a06402) by Son Pham-Ba).
- add more file metadata ([77919f3](https://gitlab.com/solidipes/solidipes/commit/77919f34977db489d5680def3b99b2c752ab16d1) by Son Pham-Ba).
- add detection of filetype for files without extension ([fdf03f3](https://gitlab.com/solidipes/solidipes/commit/fdf03f37b44ec25324328f490045ca4fee4b575f) by Son Pham-Ba).
- add tests for common files (binary, text, table) ([8f8a8c7](https://gitlab.com/solidipes/solidipes/commit/8f8a8c72c54904fd9adc0d0899b4b4da8921f056) by Son Pham-Ba).
- add support for binary (unknown) files ([75de2a5](https://gitlab.com/solidipes/solidipes/commit/75de2a558614aacf2948d03b8a9c139fe31d1977) by Son Pham-Ba).
- add tests for PyvistaMesh wrap and set_values ([481db45](https://gitlab.com/solidipes/solidipes/commit/481db45e4b7353c17b04b458a92695d664e57a5c) by Son Pham-Ba).
- add coverage in Makefile ([0e0aa0e](https://gitlab.com/solidipes/solidipes/commit/0e0aa0ee237feebc66bbe1811ddc5e2ee299703a) by Son Pham-Ba).
- add tests for PyvistaMesh file and data ([738f794](https://gitlab.com/solidipes/solidipes/commit/738f7941b520ab355658e2cacd1cd509500af74d) by Son Pham-Ba).
- added "solidipes" command entry-point ([c078688](https://gitlab.com/solidipes/solidipes/commit/c078688b00768507d8da208d3f096663dcc2258c) by Son Pham-Ba).
- added "save" method to viewers ([d8531cf](https://gitlab.com/solidipes/solidipes/commit/d8531cf67689c2fd41fa1d3c2648baf3e54a99f7) by Son Pham-Ba).
- added support for tables (csv, excel) ([925c094](https://gitlab.com/solidipes/solidipes/commit/925c094a684916ac9993824424146ef19bbd2af8) by Son Pham-Ba).
- added support for formated text files ([1f2ab41](https://gitlab.com/solidipes/solidipes/commit/1f2ab41761490997ed1a56a57137f0f7a0a68182) by Son Pham-Ba).
- added publishing to PyPI in CI ([0442032](https://gitlab.com/solidipes/solidipes/commit/0442032cfb3050232603a0dc0c099ac7450745df) by Son Pham-Ba).
- added documentation ([7e968cc](https://gitlab.com/solidipes/solidipes/commit/7e968cccba2ff5b084e6a473516533e003f3b2cd) by Son Pham-Ba).
- added base classes and examples ([cdcc734](https://gitlab.com/solidipes/solidipes/commit/cdcc7346b43572b657d35736f1a49ad8e514d331) by Son Pham-Ba).
- added instruction to install with pip ([b0f0426](https://gitlab.com/solidipes/solidipes/commit/b0f0426e48432fb2444e253f715ab1ac1331ba1d) by Son Pham-Ba).
- added pyright to pre-commit checks ([0069ad5](https://gitlab.com/solidipes/solidipes/commit/0069ad58eb4f47affce8646406c882112abee4ae) by Son Pham-Ba).

### Fixed

- fix typo in .gitlab-ci.yaml ([72d6727](https://gitlab.com/solidipes/solidipes/commit/72d6727d152ea5142e05850e39ce900938e73421) by Son Pham-Ba).
- fix ci dependency ([f562fff](https://gitlab.com/solidipes/solidipes/commit/f562fff9f6e4aea667505b2bba1463f8046be021) by Son Pham-Ba).
- fix doc generation (move scripts dir) ([745ad51](https://gitlab.com/solidipes/solidipes/commit/745ad51e07942f930e7cd7481d3366eb96844283) by Son Pham-Ba).
- fix .gitlab-ci.yml ([fd61fa7](https://gitlab.com/solidipes/solidipes/commit/fd61fa7c573dc0496649f7272ed698dd67797d17) by Son Pham-Ba).
- fix a little problem ([13a6202](https://gitlab.com/solidipes/solidipes/commit/13a6202a601049970a48dd74426b5f969dc5bdac) by Guillaume Anciaux).
- fix a little regression ([0222a94](https://gitlab.com/solidipes/solidipes/commit/0222a948bc10ce19f9a2a421683f56228bcb4f35) by Guillaume Anciaux).
- fix missing error messages in upload command ([1ca3686](https://gitlab.com/solidipes/solidipes/commit/1ca36868bc1dcc23e144d7a2237953570e62108f) by Son Pham-Ba).
- fix Markdown rendering ([778c71b](https://gitlab.com/solidipes/solidipes/commit/778c71bc1ec354f9e172cb625a6ab0606c374b97) by Son Pham-Ba).
- fix test (remove hanging pdb expressions) ([acb7cf3](https://gitlab.com/solidipes/solidipes/commit/acb7cf3269541698bd8483d0bc1be4efa4e5ed9a) by Son Pham-Ba).
- fix text test (end of line) ([fec7414](https://gitlab.com/solidipes/solidipes/commit/fec741457f108b736b1bb47e1b16e0b3e3c9d11e) by Son Pham-Ba).
- fixed meshio data convertion to viewable ([10b9998](https://gitlab.com/solidipes/solidipes/commit/10b999861601ca580253fe583bd7ee7fadf72db7) by Son Pham-Ba).
- fixed ci versioning and rdt ([d9aec99](https://gitlab.com/solidipes/solidipes/commit/d9aec999b4876cd24a904f65f130fb4f38b5237b) by Son Pham-Ba).
- fixed pyproject version number for auto numbering ([e1a75ed](https://gitlab.com/solidipes/solidipes/commit/e1a75edcbf6675dd9e3e7b43a164b37839039fe2) by Son Pham-Ba).
- fix missing libGL.so.1 in gitlab ci ([d802e9d](https://gitlab.com/solidipes/solidipes/commit/d802e9d2b5c3ed579a9afbd697a39683fcfe26f0) by Son Pham-Ba).

### Changed

- change appearance ([ceace7a](https://gitlab.com/solidipes/solidipes/commit/ceace7a2ce6db88ccd1e18dd77cc1c743e4e59c2) by Guillaume Anciaux).
- change PyvistaMesh File structure to match pyvista ([e6b6eb9](https://gitlab.com/solidipes/solidipes/commit/e6b6eb9684789eaf9a5bb77e40a52e02499a9a0a) by Son Pham-Ba).
- changed example vtu to plate_hole FEM ([ad5b189](https://gitlab.com/solidipes/solidipes/commit/ad5b189b1a0a40008d0460256f2df5f33d3ecdc3) by Son Pham-Ba).
- changed warp_by_scalar to warp_by_vector in PyvistaMesh ([5b84f26](https://gitlab.com/solidipes/solidipes/commit/5b84f267482333b40e5ff10ea06826a606df36d3) by Son Pham-Ba).

### Removed

- remove ci test "needs" to wait for whole build ([f237ec2](https://gitlab.com/solidipes/solidipes/commit/f237ec2a7dd828c8598abb95e960b323dd515f17) by Son Pham-Ba).
- remove unnecessary deps installation in ci tests ([289588d](https://gitlab.com/solidipes/solidipes/commit/289588dabb0e50f88e20f19fb1399e085601a02f) by Son Pham-Ba).
- remove TODOs ([1f43fde](https://gitlab.com/solidipes/solidipes/commit/1f43fde6dec484f9f1eec456438635cc306f5aa2) by Son Pham-Ba).
- remove "." from Zenodo archive ([79f58d3](https://gitlab.com/solidipes/solidipes/commit/79f58d3e333bdb322c151f23cf0e47f7fefae0cc) by Son Pham-Ba).
- remove root path from Zenodo archive upload ([02826a3](https://gitlab.com/solidipes/solidipes/commit/02826a3538011361bf5e0b800c1003036a7d43b3) by Son Pham-Ba).
- remove Zenodo metadata file from pulication ([41c6e3d](https://gitlab.com/solidipes/solidipes/commit/41c6e3de6f64080364df040345460302d6c5a69e) by Son Pham-Ba).
- remove a match ([104bda3](https://gitlab.com/solidipes/solidipes/commit/104bda3a3d711517a52eb224d2aca8cd71353a2d) by Guillaume Anciaux).
- remove viewers' default data key ([b2d0416](https://gitlab.com/solidipes/solidipes/commit/b2d0416cb6da1aa409eb87ab32d4e0384a645c51) by Son Pham-Ba).
- remove a obsolete test ([e0508e3](https://gitlab.com/solidipes/solidipes/commit/e0508e31541fce8b2f734f0e4b41d4e1fd20a86c) by Guillaume Anciaux).
- remove useless import ([048dc1c](https://gitlab.com/solidipes/solidipes/commit/048dc1c231a2b178f846742b3636379e16ce0449) by Guillaume Anciaux).
- remove unused singleton class ([9e7b5ab](https://gitlab.com/solidipes/solidipes/commit/9e7b5ab1ccd0aee49516cedd2d3d49bc07fb5aa3) by Son Pham-Ba).
- remove unnecessary stpyvista imports ([8382fcd](https://gitlab.com/solidipes/solidipes/commit/8382fcdb3e1f31260e1447af3e81fe839f30fbf3) by Son Pham-Ba).

## [v0.0.1](https://gitlab.com/solidipes/solidipes/tags/v0.0.1) - 2023-01-13

<small>[Compare with first commit](https://gitlab.com/solidipes/solidipes/compare/2beb87b0602a4769bfb72b4494e18aa70d0745ff...v0.0.1)</small>

### Added

- added artifacts in CI to keep build directory ([494bc51](https://gitlab.com/solidipes/solidipes/commit/494bc51116fcc798383148abece417105fe8ba04) by Son Pham-Ba).
- added test ([ca4d8f6](https://gitlab.com/solidipes/solidipes/commit/ca4d8f676a468e29a2b036de4d75f929b6697355) by Son Pham-Ba).
- added empty package and test.PyPI upload ([2e520bd](https://gitlab.com/solidipes/solidipes/commit/2e520bdbbb5b92d85ac3c2aa9bf2d83f90c138bd) by Son Pham-Ba).
- added README ([2beb87b](https://gitlab.com/solidipes/solidipes/commit/2beb87b0602a4769bfb72b4494e18aa70d0745ff) by Son Pham-Ba).

### Fixed

- fixed .gitlab-ci.yml name ([20f2872](https://gitlab.com/solidipes/solidipes/commit/20f2872d4168e074e9eae3fc20c63197299546ec) by Son Pham-Ba).

### Changed

- changed package name to something available ([62523d3](https://gitlab.com/solidipes/solidipes/commit/62523d3da49184cb4fb516e69ac9aaf89626d0b9) by Son Pham-Ba).
