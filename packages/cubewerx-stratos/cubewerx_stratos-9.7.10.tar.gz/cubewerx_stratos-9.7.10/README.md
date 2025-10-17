# CubeWerx Stratos Administration Interface

This API allows a Stratos Geospatial Data Server to be set up and
maintained remotely.  Once installed, it can be invoked with the
following Python code:

```
from cubewerx.stratos import *
stratos = Stratos(deploymentUrl, username, password)
```

where ```deploymentUrl``` is the URL of a CubeWerx Stratos deployment
(e.g., "https://somewhere.com/cubewerx/"), ```username``` is the username
(with an Administrator role) to log in as, and ```password``` is the
password of the specified username.

The documentation for this API can be found
[here](https://www.cubewerx.com/documentation/9.7/pythonApi/stratos.html).
