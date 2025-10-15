# CHANGELOG

<!-- version list -->

## v0.1.4 (2025-10-14)

### Bug Fixes

- Update known-first-party package and change build system to hatchling to be able to configure
  package setup
  ([`13e450b`](https://github.com/dimanu-py/sindri/commit/13e450bee1d01334001c3d75d420d3ee700e068d))


## v0.1.3 (2025-10-14)

### Bug Fixes

- Update import paths to remove 'src' prefix
  ([`3a94d51`](https://github.com/dimanu-py/sindri/commit/3a94d5121c493b7ecb17082fcdff5701643902a4))


## v0.1.2 (2025-10-14)

### Bug Fixes

- Correct urls to contributing guide in readme
  ([`440eb86`](https://github.com/dimanu-py/sindri/commit/440eb86911d386d49b43d5c726454ca3d6686743))


## v0.1.1 (2025-10-14)

### Bug Fixes

- Update project name for pypi
  ([`63d765c`](https://github.com/dimanu-py/sindri/commit/63d765c6b8ec379d7fd6628f35bd1f33e6157593))

### Build System

- Update Python version classifiers in pyproject.toml
  ([`8abc14a`](https://github.com/dimanu-py/sindri/commit/8abc14a8d2ba0308e8ad3c52ac7081fe6b3e2e51))

### Refactoring

- Rename source folder to sindripy
  ([`83a3dd5`](https://github.com/dimanu-py/sindri/commit/83a3dd5661420d9460e11785780db785b65cedf7))


## v0.1.0 (2025-10-13)

### Bug Fixes

- Update version variables in pyproject.toml
  ([`146fbb3`](https://github.com/dimanu-py/sindri/commit/146fbb35ad2849343fabf5b1689cbf79de1c4366))

- Use previous template issues
  ([`bf8de02`](https://github.com/dimanu-py/sindri/commit/bf8de02c0cd2f86313831e40c210aff6be5241e5))

- **primitives**: Correct wrong types in list tests
  ([`e09f4c0`](https://github.com/dimanu-py/sindri/commit/e09f4c0cc37b680e6e4ccd2a876146ec01b7d15a))

- **primitives**: Remove unreachable branch reported by mypy
  ([`903b05d`](https://github.com/dimanu-py/sindri/commit/903b05da913dc8f2532cb8cceb95e52047e8144c))

- **validation**: Improve type checking for validation order
  ([`f040416`](https://github.com/dimanu-py/sindri/commit/f040416874413bbca8ad5527ef447fcf00c13256))

- **value-object**: Correct imports after moving 'mother' folder to 'src'
  ([`ca2c4c2`](https://github.com/dimanu-py/sindri/commit/ca2c4c2d63ff27508cbc928f4cc99be7ee44e630))

- **value-objects**: Pass expected type to IncorrectValueTypeError to send correct message
  ([`01dbdc1`](https://github.com/dimanu-py/sindri/commit/01dbdc12df56d5e23299eae857697d64317866f5))

- **value-objects**: Raise TypeError when comparing two value objects that are not of the same type
  ([`2efa331`](https://github.com/dimanu-py/sindri/commit/2efa3313d41f24bcb590788a71102ff4755865e7))

### Build System

- Add build backend using uv default system
  ([`be6166d`](https://github.com/dimanu-py/sindri/commit/be6166df7ab3c0baca642b05700be3bc0fa6f6d8))

- Add missing commands in makefile
  ([`b00a081`](https://github.com/dimanu-py/sindri/commit/b00a081957cafc082b2215973dc4432e80efb632))

- Add mypy configuration
  ([`57833b4`](https://github.com/dimanu-py/sindri/commit/57833b4e4520e9aa51ad7c2dd180e55b37f37c72))

- Add packages for documentation
  ([`8f5ff91`](https://github.com/dimanu-py/sindri/commit/8f5ff914772773e277b26712b16125ea65f446e7))

- Add pytest configuration for test markers and paths to pyproject.toml instead of separated
  pytest.ini file
  ([`ba13a2d`](https://github.com/dimanu-py/sindri/commit/ba13a2df885ee39d5ef6875334f36b1a919d587c))

- Add version variable for semantic release
  ([`41d48b4`](https://github.com/dimanu-py/sindri/commit/41d48b4a4227f5eeb18df154c39859984e49ad94))

- Correct error in 'search' make command
  ([`7f1a47d`](https://github.com/dimanu-py/sindri/commit/7f1a47daf944fa122389d703d8e11e73cc25f6e0))

- Fix error in build-system section
  ([`de600e3`](https://github.com/dimanu-py/sindri/commit/de600e3bc63ae2a90a3b3d6db4813cc3c3829bde))

- Fix main package name in config file
  ([`ee33f75`](https://github.com/dimanu-py/sindri/commit/ee33f75a294ae00030d4fda9894410981d8d27d2))

- Ignore pip audit vulnerability due to pip audit bug
  ([`65d15d6`](https://github.com/dimanu-py/sindri/commit/65d15d64b8fa66f48d808b20a4d3009f73c9cc00))

- Ignore rule E501
  ([`8b05274`](https://github.com/dimanu-py/sindri/commit/8b05274f3dd0b563582a9f7d57814662c92faf9f))

- Remove unnecessary project.scripts section as the library will not be a cli application
  ([`cb5e9ac`](https://github.com/dimanu-py/sindri/commit/cb5e9ac50b08e1631fb6a31ece49085420daa590))

- Update known-first-party to include 'src' and 'test'
  ([`1aca0d3`](https://github.com/dimanu-py/sindri/commit/1aca0d31aedfd5e11014692eb6767b6d6c0d8a68))

- Update package name in uv.lock file
  ([`2bf433b`](https://github.com/dimanu-py/sindri/commit/2bf433b8e86069b79d3873a92abb979a7cca5715))

- Update project name metadata
  ([`e5f91bf`](https://github.com/dimanu-py/sindri/commit/e5f91bf3b3329a4f72e974af034f6872ddb54ef9))

- Update Python version requirement to support 3.10 and 3.13
  ([`4ecf034`](https://github.com/dimanu-py/sindri/commit/4ecf0343b9679c248fa31e424e074857f5980b43))

### Features

- Add Buy Me a Coffee funding option
  ([`333c6ce`](https://github.com/dimanu-py/sindri/commit/333c6ce7761a31b5f78c7144d5e60f37b0c16e91))

- Add compatibility helpers for typing features across Python versions
  ([`c134554`](https://github.com/dimanu-py/sindri/commit/c134554316dfc274098af8dc4e0805dc02615df5))

- **errors**: Remove unused error
  ([`dc8d6ee`](https://github.com/dimanu-py/sindri/commit/dc8d6ee23e909d2157a1238feb8e9d4c2efb5cb8))

- **list**: Add validation for list element types
  ([`55049f1`](https://github.com/dimanu-py/sindri/commit/55049f13f1115dbe286fd0942926973d64c3aace))

- **mothers**: Remove unused random generator
  ([`bd80dd7`](https://github.com/dimanu-py/sindri/commit/bd80dd782590e8c314e0ae7cf05784d81b790d96))

- **primitives**: Add __eq__ method to list value object
  ([`8f820b0`](https://github.com/dimanu-py/sindri/commit/8f820b07d84091d86bc2ee9ca9382ba562e9c551))

- **primitives**: Add Boolean value object with validation and testing utilities
  ([`f26a738`](https://github.com/dimanu-py/sindri/commit/f26a738163bb417de2af0a2c6a73e01009d0f98e))

- **primitives**: Add FloatValueObject and FloatPrimitivesMother for float value handling
  ([`eaa7d8a`](https://github.com/dimanu-py/sindri/commit/eaa7d8a64b2ce9fd09ef899deff7f5bc7120d76a))

- **primitives**: Create List value object class
  ([`6dc97ea`](https://github.com/dimanu-py/sindri/commit/6dc97ea007011fe59391bedbf5aedf79914c9156))

- **primitives**: Implement methods to be able to iterate, check containing, length, reversed
  iteration over a List value object and named constructor method to be able to construct the class
  directly from primitives
  ([`ad1c6d3`](https://github.com/dimanu-py/sindri/commit/ad1c6d37c4e3f78df492593ee4f1c11ce4531fa3))

- **value-crafter**: Expose public API for value-crafter library
  ([`7ce8357`](https://github.com/dimanu-py/sindri/commit/7ce83570218654754a765f6ec684465db919329e))

- **value-objects**: Raise error when comparing value objects of different types
  ([`32f6ffb`](https://github.com/dimanu-py/sindri/commit/32f6ffbb7b1581a3909d1cffda507b4b5c73d34d))

- **value-objects**: Return False by default when comparing two different types of value objects
  ([`4965184`](https://github.com/dimanu-py/sindri/commit/4965184890b4f6565c6fa118c255c273693e1711))

### Refactoring

- Move back value_crafters folder to src to be able to use uv build system directly
  ([`7e01712`](https://github.com/dimanu-py/sindri/commit/7e01712c162b62f0da98fdd85361184f5d2dbe9c))

- Rename main module to src
  ([`826dc57`](https://github.com/dimanu-py/sindri/commit/826dc576938fa7efe6b42bc1e46e6ccaab8fc006))

- Rename package from value-crafter to sindri
  ([`4aceb6d`](https://github.com/dimanu-py/sindri/commit/4aceb6ddccd3b353cd022852606dca840ef9ec66))

- Rename source folder to 'value_crafter'
  ([`3e6ee81`](https://github.com/dimanu-py/sindri/commit/3e6ee81d6b883d75359bf4140ea1f5285ae093c3))

- **errors**: Migrate domain errors to validation errors
  ([`5c217bc`](https://github.com/dimanu-py/sindri/commit/5c217bcb33460764995b0d158a1a5f23bf9519da))

- **errors**: Move errors to value_object folder
  ([`2c59bc6`](https://github.com/dimanu-py/sindri/commit/2c59bc632c77d2e0a5a41db029b88213df1ecb75))

- **errors**: Remove ValidationError class to be abstract to allow using it directly in custom value
  objects
  ([`2f11cf3`](https://github.com/dimanu-py/sindri/commit/2f11cf34f66e86869d6e6915125d9a9ab9500f88))

- **errors**: Rename ValidationError to ValueObjectValidationError to avoid colliding with
  pydantic's ValidationError
  ([`5d33786`](https://github.com/dimanu-py/sindri/commit/5d33786a670be1d601b6dfda4461b84f35030254))

- **mothers**: Modify ObjectMother to not be abstract as it does not have any abstractmethod
  ([`0e4efaf`](https://github.com/dimanu-py/sindri/commit/0e4efafba7e43dab1a04ee017ae010ff9a24ef8c))

- **mothers**: Move mothers folder to src as it would be part of the public library usage
  ([`9f02acd`](https://github.com/dimanu-py/sindri/commit/9f02acd47de5f4037dca1eddac8831a5b45e376a))

- **mothers**: Optimize faker usage with lru_cache in object mother
  ([`1917c75`](https://github.com/dimanu-py/sindri/commit/1917c7511e3c18c624cbe3f9a2cf494da3c7985e))

- **mothers**: Organized in modules object mothers
  ([`daa2ac9`](https://github.com/dimanu-py/sindri/commit/daa2ac9a25975e9503d8bc7ceadf43fd4891fbce))

- **mothers**: Update object mothers to new base class and implement additional methods
  ([`0d07f74`](https://github.com/dimanu-py/sindri/commit/0d07f74e9546eaeeca408bbd0d088db4845bec20))

- **primitives**: Add type hint to __iter__ and __reversed__ methods
  ([`004bffd`](https://github.com/dimanu-py/sindri/commit/004bffd8d509e36392c9d60f39bfcd439a1700e0))

- **primitives**: Clean up tests for list value object removing unnecessary classes and tests
  ([`c00f18b`](https://github.com/dimanu-py/sindri/commit/c00f18b58b6d4da595375085c15fe73c392e6cc0))

- **primitives**: Extract semantic methods when subclassing List value object to make validation
  more readable
  ([`16d3e9a`](https://github.com/dimanu-py/sindri/commit/16d3e9aad8e2d55caaa696be7531558e890525be))

- **primitives**: Remove unreachable bool verification in integer validation
  ([`dc786ac`](https://github.com/dimanu-py/sindri/commit/dc786ac617d1aad1f38d7b0002f4098195ce95c7))

- **primitives**: Remove validation for negative values in IntValueObject
  ([`ba1cd6f`](https://github.com/dimanu-py/sindri/commit/ba1cd6f28be725b47ce9ffab57cced96c204542c))

- **primitives**: Rename IntValueObject to Integer and update references
  ([`569a81e`](https://github.com/dimanu-py/sindri/commit/569a81ee19b28b07fe1cb07467238fb23704bdca))

- **primitives**: Rename StringValueObject to String and update references
  ([`a70e9d5`](https://github.com/dimanu-py/sindri/commit/a70e9d5a9def91d85f9f13ef80cdfc17b9e861cb))

- **primitives**: Rename Uuid to StringUuid and update references
  ([`db4ae12`](https://github.com/dimanu-py/sindri/commit/db4ae123560dfbd4eed54c9a0382cd5fc1b7ae3b))

- **primitives**: Reorganize string_uuid module and update references
  ([`7bc15fa`](https://github.com/dimanu-py/sindri/commit/7bc15fa80e011d1f2d0f1edcbfa379e4c26df6d3))

- **value-objects**: Allow value object class to handle order of validation
  ([`dfbd825`](https://github.com/dimanu-py/sindri/commit/dfbd8258156c34178943c734e2e29869bf7dba6b))

- **value-objects**: Modify message error when constructor parameters mismatch
  ([`0bbfccd`](https://github.com/dimanu-py/sindri/commit/0bbfccd5f0cb80175e2c0185c9438a9d95ff4fe8))

- **value-objects**: Modify validate decorator to allow order of validation
  ([`be930f6`](https://github.com/dimanu-py/sindri/commit/be930f63a0ddd03b2734ba802de828c79b2087dd))

- **value-objects**: Raise InvalidIdFormatError from ValueError on uuid vo
  ([`56f933a`](https://github.com/dimanu-py/sindri/commit/56f933ae12bc2c427cc7f36f0f643f1da445f0b7))

- **value-objects**: Remove sorting attributes in Aggregate class
  ([`4d2e430`](https://github.com/dimanu-py/sindri/commit/4d2e4307108a53b5f50404a07ec17c64db054dfa))

- **value-objects**: Rename 'usables' module to 'primitives'
  ([`c6e5200`](https://github.com/dimanu-py/sindri/commit/c6e52009717731fe7ecac0e73adb4dc9eb438dec))
