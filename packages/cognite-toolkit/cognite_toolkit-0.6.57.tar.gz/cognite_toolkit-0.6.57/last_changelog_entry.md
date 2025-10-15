## cdf 

### Changed

- [alpha] The `cdf download` command has new output structure. The
default output directory is now `data` not `tmp` and the downloaded raw
tables/assets, are now organized into a group with resources adjacent to
the downloaded data. See below for an example with assets. Note that
configurations such as DataSets/Labels for assets, and RawTables and
Databases are put into the resources folder. The `.Manifest.yaml` stores
information about how the data was downloaded and how is should be
uploaded.
   ```bash
   📁 data
   ├── 📁 MyDataSetA
   │    ├── 📁 resources
   │    ├── 📄 assets.Manifest.yaml
   │    ├── 📄 assets-part-0000.Assets.csv
   │    └── 📄 assets-part-0001.Assets.csv
   └── 📁 MyDataSetB
        ├── 📁 resources
        ├── 📄 assets.Manifest.yaml
        ├── 📄 assets-part-0000.Assets.csv
        └── 📄 assets-part-0001.Assets.csv
  ```
 
### Improved

- [alpha] In the `cdf download` command, if for example a raw table
already has been downloaded, it will be skipped instead of overwritten.

### Added

- [alpha] A new `cdf upload` command. This takes a directory as input
expected to match the format of the output of the download command.

### Removed

- [alpha] The commands `cdf upload assets/raw` have been replaced by the
`cdf upload` command.

## templates

No changes.