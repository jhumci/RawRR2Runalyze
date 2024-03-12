# Readme

A script that takes raw RR-data, computes HRV-metrics and pushes it to the Runalyze Personal API

- [x] Unpack zip from Elite HRV
- [x] Fix log with things that already have been pushed
- [x] Decide for Measurements to store
    - Store HR
    - Read what metric is best to evaluarte recovery -> rmssd seems correct for short term readings
    - https://www.marcoaltini.com/blog/a-look-at-a-few-months-of-hr-and-hrv-measurements
- [x] Push to API and store success
- [x] Loop files
- [ ] Optimize I/O Operations and use tinyDB
- [x] Add Resting HR
- [ ] Find way to automate rr-exports

## Know-How

[Runalzye API](https://runalyze.com/doc/personal)

`POST ​/api​/v1​/metrics​/hrv`

```JSON
{
  "date_time": "2020-10-01T12:00:00Z",
  "measurement_type": "asleep",
  "hrv": 55,
  "rmssd": 55,
  "sdnn": 12,
  "lnrmssd": 25
}
```
You can only push one value to the API

### HRV metrics

- rmssd - for longer readings
- sdnn - for short readings
- see: https://www.youtube.com/watch?v=h9_cwC-rxA0



## Setup

- Create API Token: https://runalyze.com/settings/personal-api
- Add File `configs/config.txt`

```
[configuration]
apitoken = 
zip_path = export.zip
default_measurement_state = awake
raw_data_path = data
```

Download all Elite HR data and store `export.zip` in the project repository
