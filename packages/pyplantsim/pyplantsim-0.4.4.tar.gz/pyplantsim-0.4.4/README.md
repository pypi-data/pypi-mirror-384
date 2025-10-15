<h1 align="center">
pyplantsim
</h1>

<h4 align="center">A python wrapper for <a href="https://www.dex.siemens.com/plm/tecnomatix/plant-simulation" target="_blank">Siemens Tecnomatix Plant Simulation</a> COM Interface.</h4>

<p align="center">
  <a href="#setup">Setup</a> •
  <a href="#examples">Examples</a> •
  <a href="https://malun22.github.io/pyplantsim/" target="_blank">Further documentation</a> •
  <a href="#notice">Notice</a> •
  <a href="#license">License</a>
</p>

## Setup

Install via pip:

```
pip install pyplantsim
```

Find this package on [Pypi](https://pypi.org/project/pyplantsim/).

## Examples

```python
import pyplantsim

with Plantsim(license=PlantsimLicense.STUDENT, version=PlantsimVersion.V_MJ_22_MI_1,
                    visible=True, trusted=True, suppress_3d=False, show_msg_box=False) as plantsim:

        plantsim.new_model()

        plantsim.save_model(
            folder_path=r"C:\users\documents\plantsimmodels", file_name="MyNewModel")
```

There are further examples in the [example folder](https://github.com/malun22/pyplantsim/tree/main/examples).

## Further documentation

Here is the [documentation for pyplantsim](https://malun22.github.io/pyplantsim/)

Here is the official [COM Interface documentation](https://docs.sw.siemens.com/en-US/doc/297028302/PL20250108338137660.PlantSimulation/id47631)

## Notice

This package is not developed, endorsed, or maintained by Siemens AG.
The names "SimTalk" and "Plant Simulation" are trademarks of Siemens AG.

## License

This package is distributed under the MIT License.
