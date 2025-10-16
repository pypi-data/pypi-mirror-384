# fsspec_dnanexus
[fsspec backend](https://filesystem-spec.readthedocs.io/en/latest/) for [DNAnexus](https://dnanexus.com)


## Installation

    pip install fsspec-dnanexus

## Usage

A URL for fsspec_dnanexus is constructed as follows. Paths have to be absolute paths with the leading forward slash

    f"dnanexus://{PROJECT_NAME_OR_ID}:/{PATH_TO_FILE}"

Supported fsspec commands are listed below:

    import fsspec
    dxfs = fsspec.filesystem("dnanexus")

    # Creating a directory
    dxfs.mkdir("dnanexus://my-dx-project:/my/new/folder", create_parents=True)

    # create_parents is True by default, but you can override it. In this case if the immedate parent does not exist
    # an exception will be thrown
    dxfs.mkdir("dnanexus://my-dx-project:/my/other/new/folder", create_parents=False)

    # Directory listing
    dxfs.ls("dnanexus://my-dx-project:/my/folder")

    # Directory listing with entity type, size, etc
    dxfs.ls("dnanexus://my-dx-project:/my/folder", detail=True)

DNAnexus entities are represented when listing a directory, but currently manipulation can only be done on files and folders

Libraries such as pandas and modin have fsspec support built-in, and you can use the dnanexus URL once fsspec_dnanexus is installed

## Examples
Reading a CSV or parquet in pandas using project name

    df = pd.read_csv("dnanexus://my-dx-project:/folder/data.csv")
    df = pd.read_parquet("dnanexus://my-dx-project:/folder/data.parquet")

Writing a pandas dataframe using project ID

    df.to_csv("dnanexus://project-XXXX:/folder/filename2.csv")

Reading using fsspec.open

    with fsspec.open("dnanexus://project-XXXX:/folder/filename2.csv", 'r') as fp:
        fp.read()

Reading the first 10 rows all CSV files in a folder

    results = dxfs.ls("dnanexus://my-dx-project:/my/folder", detail=True)
    # N.B. the 'type' attribute can be any DNAnexus entity type, such as 'file', 'directory', 'applet', 'record'
    files = [x for x in results if x['type'] == 'file' and x['name'].endswith('csv')]
    for f in files:
        url = f"dnanexus://{f['project']}:{f['name']}"
        df = pd.read_csv(url)
        print(df.iloc[:10])

When writing files by default it will create any intermediate directories if they do not exist.

## Handling of duplicate file paths
DNAnexus platform allows for duplicate filenames (but not folders)

When reading files, a file URL resolves only to the file with the latest creation date and ignore the rest.

When writing files, the default behaviour is to mimic POSIX file system such that there are no surprises from
users coming from other fsspec backends, but this can easily be overrided in storage_options:

* allow_duplicate_filenames: False - [default] removes existing file(s) with the same path and writes the new file (just like file:// s3:// and other backends would)
* allow_duplicate_filenames: True - writes the file at specified path disregarding existing files

If the user's token allows for file writing but does not allow for the removal of the file (e.g. protected projects), the behaviour falls
back to allow_duplicate_filenames: True to ensure no data loss.

## Modin and ray
### Required Initialization
When using fsspec_dnanexus under modin and ray, you'll need to invoke an initialization function.

For most users, the following function would perform the necessary initialization for fsspec_dnanexus to work under modin and ray

    import fsspec_dnanexus
    fsspec_dnanexus.init_for_modin_on_ray()

For advanced users, manually set the number of partitions. This impacts the number of chunks modin uses to process the dataframe in parallel and affects the number of files

    import fsspec_dnanexus
    fsspec_dnanexus.init_for_modin_on_ray(n_partitions=20)

### Parquet folder

Note that when using df.to_parquet, each partition will simultaneously write a part of the dataframe and the resultant output is
a folder containing many parts rather than a single file.

### Other modin engines

Other modin engines such as dask and unidist are currently not supported.

## Credentials
The credentials used by fsspec_dnanexus to access DNAnexus is determined by the following methods:

1. By default fsspec_dnanexus inherits the credentials currently used by dxpy. If you're using a DNAnexus workstation, this is a good place to start as you don't have to do anything.

        df = pd.read_csv("dnanexus://my-dx-project:/folder/filename1.csv")

2. If the FSSPEC_DNANEXUS_TOKEN environment variable is set, it will be used over dx-toolkit's credentials

        os.environ['FSSPEC_DNANEXUS_TOKEN'] = "YOUR_DNANEXUS_TOKEN"
        df = pd.read_csv("dnanexus://my-dx-project:/folder/filename1.csv")

3. If a DNAnexus token parameter passed in using storage_options, this takes priority over the two methods above

        # Option 1a
        dxfs = fsspec.filesystem("dnanexus", storage_options = {"token": "YOUR_DNANEXUS_TOKEN"})

        # Option 1b
        df = pd.read_csv("dnanexus://my-dx-project:/folder/filename1.csv", storage_options={
            "token": "YOUR_DNANEXUS_TOKEN",
        })


## Limitations

1. The following commands are currently unsupported:
    * dxfs.touch
    * dxfs.cat
    * dxfs.copy
    * dxfs.rm

2. No local caching, which means repeated reads of a file will incur repeated downloads
3. fsspec transactions (e.g. `with fs.transaction:`) are not supported.
4. Files not in 'closed' state on DNAnexus are not listed by ls() currently.


## Logging

You can override the logging level by setting the following environment variable
    os.environ["FSSPEC_DNANEXUS_LOGGING_LEVEL"] = "DEBUG"

Valid logging levels are listed here: https://docs.python.org/3/library/logging.html#levels


## Changelog

#### 0.2.7 (2025-10-16)
* Fixed: Relax dependencies version 

#### 0.2.6 (2024-09-25)
* Fixed: Packaging issue 

#### 0.2.5 (2024-09-24)
* Fixed: Error when using dxfs.upload() 

#### 0.2.4 (2024-05-10)
* Fixed: Dependencies conflicted with s3fs

#### 0.2.3 (2023-12-07)
* Fixed: reading and writing hidden files

#### 0.2.2 (2023-11-15)
* Fixed: using modin 0.24 no longer resulted in single node reads
* Fixed: resolved package conflicts

#### 0.2.1 (2023-10-27)
* Feature: Compatiblility with PyArrow FileSystem wrapper.
    * Added "size", "project", "full_url" properties to results returned by `dxfs.ls` and `dxfs.find` when the object is a directory
* Bumped dependencies versions:
    * dxpy==0.358.0, fsspec==2023.9.2, botocore

#### 0.2.0 (2023-09-13)
* modin + ray improvements
    * Use `fsspec_dnanexus.init_for_modin_on_ray()` to initialize the library for modin on ray
    * Significant increase in read performance + other optimizations
    * Fixed writing a small csv file using modin and ray

#### 0.1.0 (2023-08-04)
* Feature: Support for modin + ray
* Known issues:
    * Under modin and ray, when writing a small csv file would result in an exception. The workaround is to set n_partition mentioned above to a low number

#### 0.0.3 (2023-06-05)
* Fixed: When using PyArrow to read parquet, `pd.read_parquet` can be invoked directly, no longer requiring
  passing in file handler from `fsspec.open()`.

#### 0.0.2 (2023-05-29)
* Fixed: Project description in PyPi, corrected import statement in README

#### 0.0.1 (2023-05-29)
* Initial release
