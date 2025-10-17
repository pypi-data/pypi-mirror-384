# Entropica Labs Loom API Client

A frontend API for generating QEC Loom Experiments. Use of this client requires a valid API token and API URL.

If you would like access to the Loom APIs, get in touch with us at [Entropica Labs](https://entropicalabs.com/contact).

## Configuration

The client reads the configuration required to establish successful connections from (in order of precedence): inline **constructor arguments**, **environment variables**, **environment variables from an `.env` file**, the **configuration file** located in the user's home folder at `~/.loom/config.json`. There are no default values for the configuration options, so you must provide them in one of the ways described below.

**We don't recommend** passing the configuration options directly to the client constructor,
unless you know what you are doing and understand the security implications of exposing your API token in code that may be committed to a repository or shared.

Example:

```python
from el_loom_api_client import LoomClient

# Will read from environment variables or configuration file, if they exist, in that order
client = LoomClient()

# Will use the provided values, overriding any environment variables or configuration file
client = LoomClient(api_url="https://api.example.com", api_token="**********")

# Override only the API token if `api_url` is already set in environment variables or configuration file
client = LoomClient(api_token="********")
```

### Using a configuration file `[RECOMMENDED]`

File location: `~/.loom/config.json`

```json
{
    "api_url": "https://api.example.com",
    "api_token": "**********"
}
```

You can create the configuration file in your user's home folder with the following commands:

**MacOS/Linux**:

```bash
mkdir -p ~/.loom && echo '{"api_url": "https://api.example.com", "api_token": "**********"}' > ~/.loom/config.json
```

**Windows**:

```powershell
New-Item -Path "$HOME\.loom" -ItemType Directory -Force
Set-Content -Path "$HOME\.loom\config.json" -Value '{"api_url": "https://api.example.com", "api_token": "**********"}'
```

Edit the files to replace the example values with your actual API URL and API token.

Create the client without passing any arguments to the constructor:

```python
from el_loom_api_client import LoomClient

client = LoomClient()
```

### From environment variables or `.env` file

```shell
export LOOM_API_URL="https://api.example.com"
export LOOM_API_TOKEN="**********"
```

These variables can also be set in a `.env` file in the current working directory, which will be automatically loaded by the client, without the `export` statement.

**NOTE**: if only one of the two variables is set, the client will try reading the missing variable from the configuration file.

Create the client without passing any arguments to the constructor:

```python
from el_loom_api_client import LoomClient

client = LoomClient()
```

## Using the client

In order to use the client, you should have already obtained a valid API token and the API URL and configured the client as described before.

To create a client to interact with the Loom APIs, you can use the `LoomClient` or the `AsyncLoomClient` classes.

The client implements the context-manager protocol. Use `with` (or `async with` for the async client) to automatically close connections when the block exits. Alternatively, close it explicitly with `close()` (sync) or `aclose()` (async).

Once closed, the client instance cannot be used again and a new instance must be created.

### Synchronous client example:

```python
from el_loom_api_client import LoomClient

# Recommended: use the client as a context manager
with LoomClient() as client:
    # Use the client here
    pass
# Connection is automatically closed here

# Alternative: manually close the client
client = LoomClient()
try:
    # Use the client here
    pass
finally:
    # Manually close the client when done
    client.close()
```

### Asynchronous client example:

```python
from el_loom_api_client import AsyncLoomClient

# Recommended: use the client as a context manager
async with AsyncLoomClient() as client:
    # Use the client here
    pass
# Connection is automatically closed here

# Alternative: manually close the client
client = AsyncLoomClient()
try:
    # Use the client here, with the `await` keyword as needed
    pass
finally:
    # Manually close the client when done (note: this is an async `aclose` method)
    await client.aclose()
```

## Run a QEC experiment

Using the provided models and the client, you can build and run a QEC experiment.

The following example shows how to create a simple QEC memory experiment using the `MemoryExperiment` model and submit it to the Loom API.

```python
from el_loom_api_client import LoomClient
from el_loom_api_client.models import (
    Code,
    Decoder,
    MemoryExperiment,
    NoiseParameters,
)

# Create client using context manager (recommended)
with LoomClient() as client:
    # Build the experiment model
    experiment = MemoryExperiment(
        qec_code=Code.ROTATEDSURFACECODE,
        distance=3,
        num_rounds=[3, 5, 7],
        memory_type="Z",
        decoder=Decoder.PYMATCHING,
        noise_parameters=[
            NoiseParameters(depolarizing=0.01, measurement=0.01, reset=0.01),
            NoiseParameters(depolarizing=0.05, measurement=0.05, reset=0.05),
        ],
        gate_durations={"x": 3e-8, "cx": 2e-7},
    )

    # Submit the experiment to the Loom API
    run_id = client.experiment_run(experiment)

    # Check the status of the experiment
    status = client.get_experiment_run_status(run_id)

    # Wait for the result
    # Will poll the API for the status until the experiment is complete and fetch the result
    result = client.wait_for_experiment_run_result(run_id)

    # Print the result
    print(result)
```
