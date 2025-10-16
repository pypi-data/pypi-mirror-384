# apstrim
Logger and extractor of time-series data (e.g. EPICS PVs).

- Data are objects, indexed in time order.
- Supported Control Infrastructures: EPICS ChannelAccess+PVAccess, ADO, LITE. Easy extendable.
- Wide range of data objects: strings, lists, maps, numpy arrays, custom.
- Data objects could be inhomogeneous and have arbitrary frequency.
- Self-describing data format, no schema required.
- Data objects are binary-serialized using MessagePack.
- Fast online compression.
- Fast random-access retrieval of data objects for selected time interval.
- Simultaneous writing and reading.
- Typical speed of compressed serialization to a logbook file is 80 MB/s.
- De-serialization speed is up to 1200 MB/s when the logbook is cached in memory.
- Basic plotting of the logged data.

<img src='/docs/apstrim_file_format.png' width='400'>

## Installation
Dependencies: **msgpack, caproto, p4p, lz4framed**. 
These packages will be installed using pip:

    pip3 install apstrim

The example program for deserialization and plotting **apstrim.view**,
requires additional package: **pyqtgraph**.

## API refrerence

[apstrim](https://htmlpreview.github.io/?https://github.com/ASukhanov/apstrim/blob/main/docs/apstrim.html)

[scan](https://htmlpreview.github.io/?https://github.com/ASukhanov/apstrim/blob/main/docs/scan.html)

## Examples

## Serialization

	# Serialization of one float64 parameter from an EPICS simulated scope IOC:
	:python -m apstrim -nEPICS -T59 testAPD:scope1:MeanValue_RBV
	Logging finished for 1 sections, 1 parLists, 7.263 KB.
	...

    # The same with compression:
	:python -m apstrim -nEPICS -T59 testAPD:scope1:MeanValue_RBV --compress
    Logging finished for 1 sections, 1 parLists, 6.101 KB. Compression ratio:1.19
	...

    # Serialization 1000-element array and one scalar of floats:
    :python -m apstrim -nEPICS -T59 testAPD:scope1:MeanValue_RBV,Waveform_RBV --compress
    Logging finished for 1 sections, 2 parLists, 2405.354 KB. Compression ratio:1.0
	...
	# Note, Compression is poor for floating point arrays with high entropy.

	# Serialization of an incrementing integer parameter:
	:python -m apstrim -nLITE --compress liteHost:dev1:cycle
    Logging finished for 1 sections, 1 parLists, 56.526 KB. Compression ratio:1.25
	...
	# In this case the normalized compressed volume is 9.3 bytes per entry.
	# Each entry consist of an int64 timestamp and an int64 value, which would 
	# occupy 16 bytes per entry using standard writing.

### De-serialization
Example of deserialization and plotting of all parameters from several logbooks.

    python -m apstrim.view -i all -p *.aps

Python code snippet to extract items 1,2 and 3 from a logbook
for 20 seconds interval starting on 2021-08-12 at 23:31:31.

```python
from apstrim.scan import APScan
apscan = APScan('aLogbook.aps')
headers = apscan.get_headers()
print(f'{headers["Index"]}')
extracted = apscan.extract_objects(span=20, items=[1,2,3], startTime='210812_233131')
print(f'{extracted[3]}')# print the extracted data for item[3]
# returned:
{'par': 'liteBridge.peakSimulator:rps',           # object (PV) name of the item[3]
'times': [1628825500.8938403, 1628825510.898658], # list of the item[3] timestamps
'values': [95.675125, 95.55396]}                  # list of the item[3] values
```

