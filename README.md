This script calculates average performance of campaigns and classifies agents by their individual performance from a provided CSV file.

The script can be found in [solution.py](solution.py).

Script uses `argparse` for better flexibility and control. The following options are available:
```
usage: solution.py [-h] [--input INPUT] [--output OUTPUT] [--noprint]
  -h, --help           show this help message and exit
  --input, -i INPUT    Input CSV file path (default: calls.csv)
  --output, -o OUTPUT  Output statistic file path (default: no file output)
  --noprint            Disable console output printing (default: print to console)
  --single-pass        Compute every statistic in a single pass, increases RAM utilization, improves performance (default: compute statistics sequentially)
```

An example of the output produced by the script can be found in [output.txt](output.txt).

```
PERFORMANCE REPORT - 2025-05-12
==================================================

Campaign: 1000
	Average performance:
		0.950 number of sales per hour
		46.761 amount sold per hour
	Best agent by number of sales per hour:
		agent0279
	Best agent by amount sold per hour:
		agent0279

...

Campaign: 9000
	Average performance:
		2.216 number of sales per hour
		108.970 amount sold per hour
	Best agent by number of sales per hour:
		agent0835
	Best agent by amount sold per hour:
		agent0864

Underperforming agents by number of sales per hour (worst to best):
	agent0845
	...
	agent0182

Underperforming agents by amount sold per hour (worst to best):
	agent0845
	...
	agent0975

==================================================

...

PERFORMANCE REPORT - 2025-05-16
==================================================

Campaign: 1000
	Average performance:
		0.972 number of sales per hour
		47.560 amount sold per hour
	Best agent by number of sales per hour:
		agent0401
	Best agent by amount sold per hour:
		agent0992

...

Campaign: 9000
	Average performance:
		2.267 number of sales per hour
		112.256 amount sold per hour
	Best agent by number of sales per hour:
		agent0529
	Best agent by amount sold per hour:
		agent0529

Underperforming agents by number of sales per hour (worst to best):
	agent0552
	...
	agent0842

Underperforming agents by amount sold per hour (worst to best):
	agent0526
	...
	agent0427

==================================================
```

Script seems to use under 15MB of RAM and runs in under 10s (under 2s with `--single-pass`) on my machine with 1'000'000 lines CSV file.
