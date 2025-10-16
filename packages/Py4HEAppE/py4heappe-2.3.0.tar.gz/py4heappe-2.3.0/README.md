<img align="right" width="35%" src="https://raw.githubusercontent.com/It4innovations/Py4HEAppE/refs/heads/master/docs/imgs/logo.png">

# Py4HEAppE (Python for HEAppE Middleware)

Py4HEAppE simplifies access to the [HEAppE](https://heappe.eu) features by providing a high-level Python interface that abstracts away the complexities of direct API interactions. This allows users to focus on their core tasks without worrying about the underlying details of API communication. It can be usable in <b>two modes</b> depends what the end-user needs:
- HEAppE CLI Commands
- HEAppE API Wrapper Library

## Key Benefits

### Ease of Use:
Py4HEAppE provides a straightforward and intuitive interface for interacting with the HEAppE API. Users can perform complex operations with simple function calls.

### Abstraction: 
The library abstracts the intricacies of the HEAppE API, allowing users to work with high-level concepts and operations.

### Efficiency: 
By using Py4HEAppE, users can quickly integrate HEAppE functionalities into their Python applications, reducing development time and effort.

### Consistency:
The library ensures consistent and reliable communication with the HEAppE API, handling errors and edge cases gracefully.

## Supported HEAppE versions
| Py4HEAppE      | HEAppE Version       |  Notes                             |
|:--------------:|:--------------------:|:-----------------------------------|
| 2.3.X          | 6.0.x, 5.0.X, 4.X.X  | W/O Admin/File sections in CLI     |
| 2.2.X          | 5.0.X, 4.3.X, 4.2.X  | W/O Admin/File sections in CLI     |
| 2.1.X          | 5.0.X, 4.3.X, 4.2.X  | W/O Admin/Job/File sections in CLI |
| 2.0.X          | 5.0.X                | W/O Admin/Job/File sections in CLI |
| 1.X.X          | 4.3.X, 4.2.X         | W/O Admin/Job/File sections in CLI |

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

* Python (version 3.11)
* Pip (package installer)
* Access to Deployed HEAppE instance (HEAppE instance URL and HPC project identificator)

### Installation

```
pip install Py4HEAppE
 ```

<b>Note:</b> In some cases, you can obtain a warning message like this <b>"WARNING: The script py4heappe.exe is installed in 'C:\Users\user\AppData\Roaming\Python\Python311\Scripts' which is not on PATH.</b>" If you obtained a similar warning message, it is necessary to add the mentioned path into your operation system <b>PATH</b> variable or use a path with an executable file (i.e. C:\Users\user\AppData\Roaming\Python\Python311\Scripts\py4heappe.exe).


## HEAppE CLI

The HEAppE CLI (Command Line Interface) provides a convenient way to interact with the HEAppE Middleware directly from your terminal. It allows users to perform various operations such as authentication, job management, and information retrieval without needing to write any code. This makes it an ideal tool for end-users who need to manage HEAppE Instance efficiently.

### Usage
For using HEAppE CLI it is neeaded to initializing Py4HEAppE for usage with a specific HEAppE Instance (It is necessary to call for the first usage). Command requires <b>HPC project accounting string</b> and <b>HEAppE Instance URL</b>.

```shell
# Initial Setup
py4heappe Conf Init
```

All mentioned functions are aggregated to CLI's specific <b>commands groups (commands aggregations)</b>. To do so, type the following to provide help on how to use managers via CLI.

```shell
# List of commands groups (commands aggregations)
py4heappe --help 
```

Available Commands Groups (commands aggregations): 

```shell
# Authentication commands group
py4heappe Auth --help 

# Command Template Management commands group
py4heappe CmdTemp --help 

# Information commands group
py4heappe Info --help 

# Job Management commands group
py4heappe Job --help

# Report commands group
py4heappe Report --help 
```

<b>Note:</b> On Windows operation system need to use <b>"py4heappe.exe"</b> instead of <b>"py4heappe"</b>.
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## HEAppE API Wrapper Library

In this mode, the Py4HEAppE package is used as a wrapper for HEAppE API specification. It allows users to perform various operations from <b>HEAppE API</b>, such as authentication, job management, and information retrieval, without needing to write their API wrapper code. It can be easily integrated with internal <b>Python</b> projects that HEAppE Middleware wants to be used. More information about usability can be found in the section below.
 
### Usage
 
It is required to specify following modules in "requirements.txt" file.
 
```text
paramiko==4.0.0
scp==0.15.0
urllib3==2.5.0
```

The code snapshot illustrated an example of "how to" obtain cluster information from the HEAppE Instance. For more detailed examples of basic HPC workflow, please refer to the [example.py](https://github.com/It4innovations/Py4HEAppE/blob/master/docs/examples/example.py) file.

```python
import json
import os
import time
from io import StringIO
from pathlib import Path
 
import py4heappe.core as hp
 
print("\nFetching cluster info...")
lac_body = {
    "_preload_content": False
}
 
ciEndpoint = hp.ClusterInformationApi(api_instance)
r = ciEndpoint.heappe_cluster_information_list_available_clusters_get(**lac_body)
r_data = json.loads(r.data)
print(json.dumps(r_data, indent = 3))
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Acknowledgement

e-Infra CZ
This work was supported by the Ministry of Education, Youth and Sports of the Czech Republic through the e-INFRA CZ (ID:90254)

<p align="right">(<a href="#readme-top">back to top</a>)</p>