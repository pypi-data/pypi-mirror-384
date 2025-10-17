<style type="text/css">
/* make sure we don't wrap first column of tables on this page */
table tr td:first-of-type {
    text-wrap: nowrap;
}
</style>

# Environment variables

If not already set elsewhere (e.g. `~/.bashrc`), copy `.env.template` to `.env`
and update the values of the shell variables. Essentially, the following
variables regarding the production database should be available

**Configuration settings**

| Name                 | Description                                    |
| -------------------- | ---------------------------------------------- |
| `INSTITUTION`        | institution code for your institution in ITkPD |
| `ITKDB_ACCESS_CODE1` | first access code for ITkDB                    |
| `ITKDB_ACCESS_CODE2` | second access code for ITkDB                   |

For example, to store these variables in your (bash) shell, one can add the
following lines to your `~/.bashrc`:

```bash title="~/.bashrc"
export INSTITUTION="LBNL_PIXEL_MODULES"
export ITKDB_ACCESS_CODE1="accesscode1"
export ITKDB_ACCESS_CODE2="accesscode2"
```

# Hardware Config

In addition to passing many things from the command-line, the hardware
configuration from
[module-qc-data-tools!64](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools/-/merge_requests/64)
can also be used to define the information you pass in to override defaults,
such as the localDB URI or additional tags to append to the default set of tags.

An example is presented below for SCIPP, UC Santa Cruz:

```json title="hw_config.json"
  "localdb": {
      "uri_ldb": "https://itkpix-srv.ucsc.edu:443/localdb",
      "uri_mdb": "mongodb://itkpix-srv.ucsc.edu:27017/localdb?ssl=True",
      "tags": ["alpha"],
      "institution": "UCSC",
      "userName": "pixdaq",
  }
```
