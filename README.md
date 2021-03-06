# flow-models: A framework for analysis and modeling of IP network flows

Packages like `flow-tools` or `nfdump` provide tools for filtering and calculating simple summary/top-N statistics
from network flow records. They lack, however, any capabilities for analysis and modeling of flow features (length,
size, duration, rate, etc.) distributions. The goal of this framework is to fill this gap.

## Provided tools

The framework currently includes the following tools:

- `merge` -- performs merge of flows which were split across multiple records due to *active timeout*
- `convert` -- converts supported flow records formats between each other
- `sort` -- sorts flow records according to specified key fields (requires `numpy`)
- `hist` -- calculates histograms of flows length, size, duration or rate
- `hist_np` -- calculates histograms using multiple threads (requires `numpy`, much faster, but uses more memory)
- `fit` -- creates General Mixture Models (GMMs) fitted to flow records (requires `scipy`)
- `plot` -- generates plots from flow records and fitted models (requires `pandas` and `scipy`)
- `summary` -- produces LaTeX tables containing summary statistics of flow records data (requires `scipy`)
- `generate` -- generates flow records in supported output formats from histograms data or distribution mixtures

Each tool is a separate Python program. Features provided by the tools are orthogonal and are tailored to be used together in data-processing pipelines.

## File formats

The framework currently supports the following flow records formats:

- `pipe` -- `nfdump` pipe format
- `nfcapd` -- `nfdump` binary format
- `csv_flow` -- comma-separated values text format (see below)
- `binary` -- separate binary array file for each field (see below)

Additionally, the framework currently supports the following flow histograms formats:

- `csv_hist` -- comma-separated values text format (see below)

### `csv_flow` file format

File contains the following fields:

    af, prot, inif, outif, sa0, sa1, sa2, sa3, da0, da1, da2, da3, sp, dp, first, first_ms, last, last_ms, packets, octets, aggs

- `af` -- address family
- `prot` -- IP protocol number
- `inif` -- input interface number
- `outif` -- output interface number
- `sa0:sa3` -- consecutive 32-bit words forming source IP address
- `da0:da3` -- consecutive 32-bit words forming destination IP address
- `sp` -- source transport layer port
- `dp` -- destination transport layer port
- `first` -- timestamp of first packet (seconds component)
- `first_ms` -- timestamp of first packet (milliseconds component)
- `last` -- timestamp of last packet (seconds component)
- `last_ms` -- timestamp of last packet (milliseconds component)
- `packets` -- number of packets (flow length)
- `octets` -- number of octets (bytes) (flow size)
- `aggs` -- number of aggregated flow records forming this record

### `binary` file format

The `binary` file format is used as an effective internal on-disk format to exchange data between tools included in the framework.
Each flows trace is a directory, which contains several binary files. Each binary file stores one
field as an array of binary values with a specified type.

File naming schema is the following:

    _{field_name}.{dtype}  -- key fields
    {field_name}.{dtype}   -- value fields

Suffix `dtype` specifies the type of binary object stored in file:

| Type code | C Type |
| - | - |
| `b`   | signed char |
| `B`   | unsigned char |
| `h`   | signed short |
| `H`   | unsigned short |
| `i`   | signed int |
| `I`   | unsigned int |
| `l`   | signed long |
| `L`   | unsigned long |
| `q`   | signed long long |
| `Q`   | unsigned long long |
| `f`   | float |
| `d`   | double |

Such a storage schema has several advantages:

- fields can be distributed independently (for example one can share flow records without `sa*` and `da*` address fields for privacy reasons)
- fields can be compressed/uncompressed selectively (important when processing data which barely fits on disks)
- additional or custom fields can be trivially added or removed
- supports storage of any field using any object type (signedness, precision)
- files can be memory-mapped as numerical arrays (unlike `IPFIX`, `nfcapd` or any other structured/TLV format)
- the format is so simple that files can be memory-mapped into any big data processing software and is future-proof
- memory-mapping is IO and cache efficient (columnar memory layout allows applications to avoid unnecessary IO and accelerate analytical processing performance on modern CPUs and GPUs)

Example:

    agh_2015/
    └── day-01
        ├── _af.B            ─┐
        ├── _da0.I            │
        ├── _da1.I            │
        ├── _da2.I            │
        ├── _da3.I            │
        ├── _dp.H             │
        ├── _inif.H           │ key
        ├── _outif.H          │ fields
        ├── _prot.B           │
        ├── _sa0.I            │
        ├── _sa1.I            │
        ├── _sa2.I            │
        ├── _sa3.I            │
        ├── _sp.H            ─┘
        ├── first.I          ─┐
        ├── first_ms.H        │
        ├── last.I            │ value
        ├── last_ms.H         │ fields
        ├── octets.Q          │
        └── packets.Q        ─┘

### `csv_hist` file format

File contains the following fields:

    bin_lo, bin_hi, flows_sum, packets_sum, octets_sum, duration_sum, rate_sum, aggs_sum

- `bin_lo` -- lower edge of a bin (inclusive)
- `bin_hi` -- upper edge of a bin (exclusive)
- `flows_sum` -- number of flows within a particular bin
- `packets_sum` -- sum of packets of all flows within a bin
- `octets_sum` -- sum of octets of all flows within a bin
- `duration_sum` -- sum of duration of all flows within a bin (in milliseconds)
- `rate_sum` -- sum of rates of all flows within a bin (in bps)
- `aggs_sum` -- sum of aggregated flows of all flows within a bin

Histograms can be calculated using `hist` or `hist_np` modules. The former is a pure Python implementation which can take advantage of unlimited width integer support in Python in order to perform more accurate calculations. The latter uses the `numpy` package to perform binning, which can utilise SIMD instructions and multiple threads and is therefore many orders of magnitude faster but requires more memory and can introduce rounding errors due to the operation on doubles having limited precision. Both tools output a CSV file which can be directly used to plot a histogram, CDF or PDF of a particular flow feature.

The framework user can specify a parameter *b*, which is a power-of-two defining starting point for logarithmic binning. For example, *b = 12* means that bin widths will start increasing for values *> 4096* (for lower values bin width will be equal to one). Therefore, values between 4096-8192 would be binned into bins of width 2, between 8192-16384 into bins of width 4, etc.


## Models repository

The `data` directory contains histogram CSV files, fitted mixture models and plots. It does not include full flow records.

### agh_2015

P. Jurkiewicz, G. Rzym and P. Boryło, "Flow length and size distributions in campus Internet traffic", arXiv:1809.03486, 2018. Available: http://arxiv.org/abs/1809.03486

Based on NetFlow records collected on the Internet-facing interface of the AGH University of Science and Technology network during the consecutive period of 30 days.

Dormitories, populated with nearly 8000 students, generated 69% of the traffic. The rest of the university (over 4000 employees) generated 31%. In the case of dormitories, 91% of traffic was downstream traffic (from the Internet).
In the case of rest of the university, downstream traffic made up 73% of the total traffic. Therefore, this model can also be considered as representative of residential traffic.

| Parameter | Value | Unit |
| - | -: | -: |
| Dataset name | agh_2015 | |
| Flow definition | 5-tuple | |
| Exporter | Cisco router | (NetFlow) |
| L2 technology | Ethernet | |
| Sampling rate | none | |
| Active timeout | 300 | seconds |
| Inactive timeout | 15 | seconds|
| | | |
| Number of flows | 4 032 376 751 | flows |
| Number of packets | 316 857 594 090 | packets |
| Number of bytes | 275 858 498 994 998 | bytes |
| Average flow length | 78.578370 | packets |
| Average flow size | 68410.894128 | octets |
| Average packet size | 870.607188 | bytes |


|    | TCP | UDP | Other |
| :- | -:  | -:  | -:    |
| Flows | 53.85% | 43.09% | 3.06% |
| Packets | 83.51% | 16.01% | 0.48% |
| Octets | 88.57% | 11.27% | 0.1% |
