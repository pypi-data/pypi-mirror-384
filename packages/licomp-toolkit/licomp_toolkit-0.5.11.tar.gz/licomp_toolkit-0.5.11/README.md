# Licomp Toolkit

Licomp toolkit is a license compatiblity tool using miscellaneous
available compatibility resources and provides replies from all
resources.

## Introduction 

Licomp can be used to help determine if a license is compatible with
an outbound license. These compatibility checks needs context which is
often missing. The context above must be provided to
licomp-toolkit. In short the context is:

* use case - how you use the licensed component
* provisioning - how you provide the component to your user
* modification - if you have modified the component

Licomp toolkit is using the [Licomp](https://github.com/hesa/licomp) api to communicate with the Licomp resources. For a better understanding of Licomp we suggest you read:

* [Licomp basic concepts](https://github.com/hesa/licomp/#licomp-concepts)
* [Licomp reply format](https://github.com/hesa/licomp/blob/main/docs/reply-format.md)

## Licomp resources

Licomp toolkit uses the following compatibility resources using the [Licomp](https://github.com/hesa/licomp) api: [licomp-hermione](https://github.com/hesa/licomp-hermione), [licomp-osadl](https://github.com/hesa/licomp-osadl), [licomp-proprietary](https://github.com/hesa/licomp-proprietary), [licomp-reclicense](https://github.com/hesa/licomp-reclicense), [licomp-dwheeler](https://github.com/hesa/licomp-dwheeler) and [licomp-gnuguide](https://github.com/hesa/licomp-gnuguide).

# Using Licomp Toolkit

## Command line interface (brief intro)

If you want to check if the following is compatible:
* outbound license "MIT"
* inbound license "LGPL-2.0-or-later"

```
$ licomp-toolkit verify -il MIT -ol LGPL-2.0-or-later | jq .summary.results
{
  "nr_valid": "1",
  "yes": {
    "count": 1,
    "percent": 100.0
  }
}
```

In the above example, `licomp-toolkit` by default chose:
* usecase `library`- i.e. the licenses component is used as a library (e.g. linking to it)
* provisioning `binary-distribution`
* modification is not yet implemented

For more detailed guides to `licomp-toolkit`, please check out:
* [Licomp Toolkit - Command Line Guide](docs/cli-guide.md)
* [Licomp Toolkit - Reply Format](docs/reply-format.md)

## Python module

If you want to check if the following is compatible:
* outbound license "MIT"
* inbound license "LGPL-2.0-or-later"

```
>>> from licomp_toolkit.toolkit import LicompToolkit
>>> licomp_toolkit = LicompToolkit()
>>> compatibilities = licomp_toolkit.outbound_inbound_compatibility("MIT", "LGPL-2.0-or-later", "library", "binary-distribution")
>>> print(str(compatibilities['summary']['results']))
{'nr_valid': '1', 'yes': {'count': 1, 'percent': 100.0}}
```

For a more detailed guide to the `licomp-toolkit` Python api, please check out: [Licomp Toolkit - Python module](docs/python-api.md)

# Installing Licomp Toolkit

## From pypi.org

Licomp Toolkit is available via [pypi.org](https://pypi.org/) at: [https://pypi.org/project/licomp-toolkit/](https://pypi.org/project/licomp-toolkit/). To install, simply do the following:

```
$ pip install licomp-toolkit
```

## From github

Installing from github assumes you already have `pip` installed.

```
$ git clone https://github.com/hesa/licomp-toolkit
$ pip install -r requirements.txt
$ pip install -r requirements-dev.txt
$ pip install .
```
