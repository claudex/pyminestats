pyminestats
===========

A python script parsing Minecraft server log to generate nice charts

Requirement
===========

The script use the [pygal](http://pygal.org) library to draw the charts

Usage
=====

Change the server log file location and output directory in the variables *log_file_name* and *output_dir*

If display the page in HTTPS, you have to change the *js* variable to an HTTPS one

Then, run

```
python /path/to/stats.py
```
