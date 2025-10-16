# Example Usage
Below, we'll show you how to display the keywords from each source, how to bypass using the `threshold` decorator entirely, then walk through examples that build on each other to show how arguments are overwritten.

## Tracing
We added the ability to trace the source of each keyword argument. We set this using `threshold`'s kwarg `trace_level`. `trace_level` uses the [`loguru` package for logging](https://github.com/Delgan/loguru) and accepts the following arguments (case insenitive): 

- `"critical"`
- `"warning"`
- `"success"`
- `"info"`
- `"debug"`

We will see how this is used by trying out different log levels in the next set of examples.

## Developer-Provided Arguments (Highest Level)
If you need to debug something _really_ quickly and don't want to fuss around with files or CLI, you can pass the values in **as keywords**. This bypasses any external values provided from files, environment variables, or the CLI.
```py
# main.py
from argmerge import threshold


@threshold(trace_level="DEBUG")
def main(first, second, third: float = 3.0, fourth: float = 4.0, fifth: int = 5):
    pass


if __name__ == "__main__":
    main(first=1, second="second")
```
Outputs a list of keyword arguments with their sources listed in ascending priority order
```sh
$ uv run main.py
Parameter Name  | Location Set           
=======================================
third   | Python Function default
fourth  | Python Function default
fifth   | Python Function default
first   | developer-provided     
second  | developer-provided
```


## Default Function Values (Lowest Level)
```py
# main.py
from argmerge import threshold


@threshold(trace_level="DEBUG")
def main(
    first: int = 1,
    second: str = "second",
    third: float = 3.0,
    fourth: float = 4.0,
    fifth: int = 5,
):
    pass


if __name__ == "__main__":
    main()
```
Output
```sh
2025-10-13 23:58:14.901 | DEBUG    | argmerge.trace:_write_trace:27 - 
Parameter Name  | Location Set           
=======================================
first   | Python Function default
second  | Python Function default
third   | Python Function default
fourth  | Python Function default
fifth   | Python Function default
```

## JSON (Second Lowest)
JSON Config
```json
// threshold.json
{
    "first": 100,
    "second": "Python"
}
```
```py
# main.py
from argmerge import threshold


@threshold(fpath_json="threshold.json", trace_level="DEBUG")
def main(
    first: int,
    second: str,
    third: float = 3.0,
    fourth: float = 4.0,
    fifth: int = 5,
):
    pass


if __name__ == "__main__":
    main()
```
Outputs
```sh
2025-10-13 23:59:54.057 | DEBUG    | argmerge.trace:_write_trace:27 - 
Parameter Name  | Location Set           
=======================================
third   | Python Function default
fourth  | Python Function default
fifth   | Python Function default
first   | JSON (threshold.json)  
second  | JSON (threshold.json)  
```


## YAML (Third Lowest)
```yaml
# threshold.yaml
third: -3.333
```
```py
# main.py
from argmerge import threshold


@threshold(
    fpath_json="threshold.json", fpath_yaml="threshold.yaml", trace_level="DEBUG"
)
def main(
    first: int,
    second: str,
    third: float = 3.0,
    fourth: float = 4.0,
    fifth: int = 5,
):
    pass


if __name__ == "__main__":
    main()
```
Output
```sh
2025-10-14 00:02:32.892 | DEBUG    | argmerge.trace:_write_trace:27 - 
Parameter Name  | Location Set           
=======================================
fourth  | Python Function default
fifth   | Python Function default
first   | JSON (threshold.json)  
second  | JSON (threshold.json)  
third   | YAML (threshold.yaml)  
```

## Environment Variables (Third Highest)
```sh
$ export EXAMPLE_THRESH_FOURTH=-14.0
```
```py
# main.py
from argmerge import threshold


@threshold(
    fpath_json="threshold.json",
    fpath_yaml="threshold.yaml",
    env_prefix="EXAMPLE_THRESH",
    trace_level="WARNING",
)
def main(
    first: int,
    second: str,
    third: float = 3.0,
    fourth: float = 4.0,
    fifth: int = 5,
):
    pass


if __name__ == "__main__":
    main()
```
Outputs
```sh
2025-10-14 00:05:26.171 | WARNING  | argmerge.trace:_write_trace:27 - 
Parameter Name  | Location Set           
=======================================
fifth   | Python Function default
first   | JSON (threshold.json)  
second  | JSON (threshold.json)  
third   | YAML (threshold.yaml)  
fourth  | Environment Variable   
```

## Command-Line Arguments (Second Highest)

```py
# main.py
from argmerge import threshold


@threshold(
    fpath_json="threshold.json",
    fpath_yaml="threshold.yaml",
    env_prefix="EXAMPLE_THRESH",
    cli_pattern=r"--([A-Za-z_-]+)=([0-9A-Za-z_-\.]+)",  # the default pattern
    trace_level="WARNING",
)
def main(
    first: int,
    second: str,
    third: float = 3.0,
    fourth: float = 4.0,
    fifth: int = 5,
):
    pass


if __name__ == "__main__":
    main()
```

Output
```sh
$ uv run main.py -- --fifth=3.14
$ # you can also run
$ # python main.py --fifth=3.14
2025-10-14 00:07:09.683 | WARNING  | argmerge.trace:_write_trace:27 - 
Parameter Name  | Location Set         
=====================================
first   | JSON (threshold.json)
second  | JSON (threshold.json)
third   | YAML (threshold.yaml)
fourth  | Environment Variable 
fifth   | CLI      
```