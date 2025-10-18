<a id="aea.package_manager.base"></a>

# aea.package`_`manager.base

Base manager class.

<a id="aea.package_manager.base.load_configuration"></a>

#### load`_`configuration

```python
def load_configuration(package_type: PackageType,
                       package_path: Path) -> PackageConfiguration
```

Load a configuration, knowing the type and the path to the package root.

**Arguments**:

- `package_type`: the package type.
- `package_path`: the path to the package root.

**Returns**:

the configuration object.

<a id="aea.package_manager.base.load_fetch_ipfs"></a>

#### load`_`fetch`_`ipfs

```python
def load_fetch_ipfs() -> Callable[[str, PublicId, str, bool], Optional[Path]]
```

Load fetch_ipfs method.

<a id="aea.package_manager.base.DepedencyMismatchErrors"></a>

## DepedencyMismatchErrors Objects

```python
class DepedencyMismatchErrors(Enum)
```

Dependency mismatch errors.

<a id="aea.package_manager.base.Cache"></a>

## Cache Objects

```python
class Cache()
```

Cache manager.

<a id="aea.package_manager.base.Cache.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Package cache helper.

<a id="aea.package_manager.base.Cache.exists"></a>

#### exists

```python
def exists(package_hash: str) -> bool
```

Check if package exists in the cache.

<a id="aea.package_manager.base.Cache.add"></a>

#### add

```python
def add(package_path: Path, package_hash: str) -> None
```

Add package to cache.

<a id="aea.package_manager.base.Cache.remove"></a>

#### remove

```python
def remove(package_hash: str) -> None
```

Remove package.

<a id="aea.package_manager.base.Cache.valid"></a>

#### valid

```python
def valid(package_hash: str) -> bool
```

Validate a package.

<a id="aea.package_manager.base.Cache.copy"></a>

#### copy

```python
def copy(package_hash: str, destination_path: Path) -> bool
```

Copy package from cache.

<a id="aea.package_manager.base.BasePackageManager"></a>

## BasePackageManager Objects

```python
class BasePackageManager(ABC)
```

AEA package manager

<a id="aea.package_manager.base.BasePackageManager.__init__"></a>

#### `__`init`__`

```python
def __init__(path: Path,
             config_loader: ConfigLoaderCallableType = load_configuration,
             logger: Optional[logging.Logger] = None) -> None
```

Initialize object.

<a id="aea.package_manager.base.BasePackageManager.iter_dependency_tree"></a>

#### iter`_`dependency`_`tree

```python
def iter_dependency_tree() -> Iterator[PackageId]
```

Iterate dependency tree.

<a id="aea.package_manager.base.BasePackageManager.check_dependencies"></a>

#### check`_`dependencies

```python
def check_dependencies(
    configuration: PackageConfiguration
) -> List[Tuple[PackageId, DepedencyMismatchErrors]]
```

Verify hashes for package dependecies againts the available hashes.

<a id="aea.package_manager.base.BasePackageManager.is_dependencies_hashes_match"></a>

#### is`_`dependencies`_`hashes`_`match

```python
def is_dependencies_hashes_match(
        package_id: PackageId,
        configuration_obj: PackageConfiguration) -> bool
```

Check dependecies hashes match and print errors

<a id="aea.package_manager.base.BasePackageManager.get_package_dependencies"></a>

#### get`_`package`_`dependencies

```python
def get_package_dependencies(package_id: PackageId) -> List[PackageId]
```

Get package dependencies by package_id.

<a id="aea.package_manager.base.BasePackageManager.update_public_id_hash"></a>

#### update`_`public`_`id`_`hash

```python
def update_public_id_hash(public_id_str: str, package_type: str) -> str
```

Update public id hash from the latest available hashes.

<a id="aea.package_manager.base.BasePackageManager.update_dependencies"></a>

#### update`_`dependencies

```python
def update_dependencies(package_id: PackageId) -> None
```

Update dependency hashes to latest for a package.

<a id="aea.package_manager.base.BasePackageManager.get_package_config_file"></a>

#### get`_`package`_`config`_`file

```python
def get_package_config_file(package_id: PackageId) -> Path
```

Get package config file path.

<a id="aea.package_manager.base.BasePackageManager.update_fingerprints"></a>

#### update`_`fingerprints

```python
def update_fingerprints(package_id: PackageId) -> None
```

Update fingerprints for a package.

<a id="aea.package_manager.base.BasePackageManager.add_package"></a>

#### add`_`package

```python
def add_package(package_id: PackageId,
                with_dependencies: bool = False,
                allow_update: bool = False) -> "BasePackageManager"
```

Add package.

<a id="aea.package_manager.base.BasePackageManager.add_dependencies_for_package"></a>

#### add`_`dependencies`_`for`_`package

```python
def add_dependencies_for_package(package_id: PackageId,
                                 allow_update: bool = False) -> None
```

Add dependencies for the package specified.

<a id="aea.package_manager.base.BasePackageManager.get_package_version_with_hash"></a>

#### get`_`package`_`version`_`with`_`hash

```python
def get_package_version_with_hash(package_id: PackageId) -> PackageId
```

Add package_id with hash for the package presents in registry.

<a id="aea.package_manager.base.BasePackageManager.is_package_files_exist"></a>

#### is`_`package`_`files`_`exist

```python
def is_package_files_exist(package_id: PackageId) -> bool
```

Check package exists in the filesystem by checking it's config file exists.

<a id="aea.package_manager.base.BasePackageManager.package_path_from_package_id"></a>

#### package`_`path`_`from`_`package`_`id

```python
def package_path_from_package_id(package_id: PackageId) -> Path
```

Get package path from the package id.

<a id="aea.package_manager.base.BasePackageManager.calculate_hash_from_package_id"></a>

#### calculate`_`hash`_`from`_`package`_`id

```python
def calculate_hash_from_package_id(package_id: PackageId) -> str
```

Calculate package hash from package id.

<a id="aea.package_manager.base.BasePackageManager.update_package"></a>

#### update`_`package

```python
def update_package(package_id: PackageId) -> "BasePackageManager"
```

Update package.

<a id="aea.package_manager.base.BasePackageManager.register"></a>

#### register

```python
@abstractmethod
def register(
        package_path: Path,
        package_type: Optional[PackageType] = None) -> "BasePackageManager"
```

Add package to the index.

<a id="aea.package_manager.base.BasePackageManager.get_package_hash"></a>

#### get`_`package`_`hash

```python
@abstractmethod
def get_package_hash(package_id: PackageId) -> Optional[str]
```

Return hash for the given package id.

<a id="aea.package_manager.base.BasePackageManager.sync"></a>

#### sync

```python
@abstractmethod
def sync(dev: bool = False,
         third_party: bool = True,
         update_packages: bool = False,
         update_hashes: bool = False) -> "BasePackageManager"
```

Sync local packages to the remote registry.

<a id="aea.package_manager.base.BasePackageManager.update_package_hashes"></a>

#### update`_`package`_`hashes

```python
@abstractmethod
def update_package_hashes(selector_prompt: Optional[Callable[[], str]] = None,
                          skip_missing: bool = False) -> "BasePackageManager"
```

Update package.json file.

<a id="aea.package_manager.base.BasePackageManager.verify"></a>

#### verify

```python
@abstractmethod
def verify() -> int
```

Verify fingerprints and outer hash of all available packages.

<a id="aea.package_manager.base.BasePackageManager.json"></a>

#### json

```python
@property
@abstractmethod
def json() -> OrderedDictType
```

Json representation

<a id="aea.package_manager.base.BasePackageManager.dump"></a>

#### dump

```python
def dump(file: Optional[Path] = None) -> None
```

Dump package data to file.

<a id="aea.package_manager.base.BasePackageManager.from_dir"></a>

#### from`_`dir

```python
@classmethod
@abstractmethod
def from_dir(
    cls,
    packages_dir: Path,
    config_loader: ConfigLoaderCallableType = load_configuration
) -> "BasePackageManager"
```

Initialize from packages directory.

<a id="aea.package_manager.base.PackageHashDoesNotMatch"></a>

## PackageHashDoesNotMatch Objects

```python
class PackageHashDoesNotMatch(Exception)
```

Package hash does not match error.

<a id="aea.package_manager.base.PackageUpdateError"></a>

## PackageUpdateError Objects

```python
class PackageUpdateError(Exception)
```

Package update error.

<a id="aea.package_manager.base.PackageNotValid"></a>

## PackageNotValid Objects

```python
class PackageNotValid(Exception)
```

Package not valid.

<a id="aea.package_manager.base.PackageFileNotValid"></a>

## PackageFileNotValid Objects

```python
class PackageFileNotValid(Exception)
```

Package file not valid.

<a id="aea.package_manager.base.PackagesSourceNotValid"></a>

## PackagesSourceNotValid Objects

```python
class PackagesSourceNotValid(Exception)
```

Packages source not valid.

