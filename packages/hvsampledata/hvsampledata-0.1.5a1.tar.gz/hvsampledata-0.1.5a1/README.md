# hvsampledata

<div style="border: 2px solid #f5c542; padding: 10px; border-radius: 5px; background-color: #fff8e1;">
  <strong>⚠️ Experimental ⚠️</strong>
  <p>hvsampledata is still in an experimental phase. Expect breaking changes, incomplete features, and potential bugs. Please do not use this in production environments.</p>
</div>

Shared datasets for the HoloViz projects

Datasets:

| Name               | Type    | Included |
| ------------------ | ------- | -------- |
| air_temperature    | Gridded | Yes      |
| apple_stocks       | Tabular | Yes      |
| earthquakes        | Tabular | Yes      |
| landsat_rgb        | Gridded | Yes      |
| nyc_taxi           | Tabular | Remote   |
| penguins           | Tabular | Yes      |
| penguins_rgba      | Gridded | Yes      |
| stocks             | Tabular | Yes      |
| synthetic_clusters | Tabular | Yes      |
| us_states          | Tabular | Yes      |

## Developer guide

- Install [pixi](https://pixi.sh)
- Run `pixi run setup-dev` to setup your developer environment
- Run `pixi run test-unit` to run the tests
