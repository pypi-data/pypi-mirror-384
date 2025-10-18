
<hr/>
<div align="center">
    <pre>
 _____ _   _ ____   ____ _   _  ___   ___  _     
|  ___| \ | / ___| / ___| | | |/ _ \ / _ \| |    
| |_  |  \| \___ \| |   | |_| | | | | | | | |    
|  _| | |\  |___) | |___|  _  | |_| | |_| | |___ 
|_|   |_| \_|____/ \____|_| |_|\___/ \___/|_____|
    </pre>
</div>
<p align="center">
    funingschool
</p>
<h4 align="center">
    NO Just some simple scripts for warehousing and consuming.
</h4>
<hr/>
<p align="center">
    <a href="https://gitee.com/larryw3i/funingschool/blob/master/Documentation/README/zh_CN.md">简体中文</a> •
    <a href="https://github.com/larryw3i/funingschool/blob/master/README.md">English</a>
</p>

<p align="center">
    <a href="#key-features">
        Key Features
    </a>
    •
    <a href="#how-to-use">
        How To Use
    </a>
    •
    <a href="#credits">
        Credits
    </a>
    •
    <a href="#support">
        Support
    </a>
    •
    <a href="#license">
        License
    </a>
</p>

![Screenshot](https://raw.githubusercontent.com/larryw3i/funingschool/master/Documentation/images/9432e132-f8cd-11ee-8ee6-f37309efa64b.png)

<h2 id="key-features">
    Key Features
</h2>

<h3>
    warehousing and consuming
</h3>

* Read food spreadsheets automatically.
* The simplest and most straightforward `consuming sheets`.
* Update sheets (warehousing, consuming, summing, etc) automatically.
* Reduce calculation errors.
* Effectively eliminate unit prices containing infinite decimals.
* Merge food sheets between spreadsheets.  
* Easy to use.

<h3>
    Test statistics
</h3>

* An easy-to-use "test score entry form".
* Clear test results at a glance, converting table data into Intuitive images.
* Display comments.
* Effectively assist testers, especially teachers and students.

<h2 id="how-to-use">
    How To Use
</h2>

<h3>
    Install Python3
</h3>
<p>

on `Ubuntu`:

```bash
sudo apt-get install python3 python3-pip python3-tk
```  
For `Windows 10` and `Windows 11`, you can install Python3 from https://www.python.org/getit/ . (`fnschool` requires Python 3.12 or later)
</p>

<h3>
    Install fnschool and run it
</h3>

<p>

Run the command line application:
* `Ubuntu`: `Ctrl+Alt+T`.  
* `Windows`: "`Win+R, powershell, Enter`".  

Enter the following commands:

</p>

```bash
# install fnschool.
pip install -U fnschool

# Making bill of "canteen" module.
fnschool-cli canteen mk_bill
# Merging food sheets of "canteen" module.
fnschool-cli canteen merge_foodsheets

# run `test statistics` module.
fnschool-cli exam enter
```

>Note: Read the information it prompts carefully, which is the key to using it well.

<h2 id="credits">
    Credits
</h2>
<p>
    This software uses the following open source packages:
    <ul>
        <li><a href="https://github.com/tartley/colorama">colorama</a></li>
        <li><a href="https://pandas.pydata.org/">pandas</a></li>
        <li><a href="https://numpy.org/">numpy</a></li>
        <li><a href="https://openpyxl.readthedocs.io/">openpyxl</a></li>
        <li><a href="http://github.com/ActiveState/appdirs">appdirs</a></li>
        <li><a href="https://matplotlib.org/">matplotlib</a></li>
        <li><a href="https://github.com/Miksus/red-mail">redmail</a></li>
    </ul>
</p>

<h2 id="support">
    Support
</h2>
<h3>
    Buy me a `coffee`:
</h3>  

![Buy me a "coffee".](https://raw.githubusercontent.com/larryw3i/funingschool/master/Documentation/images/9237879a-f8d5-11ee-8411-23057db0a773.jpeg)

<h2 id="license">
    License
</h2>

<a href="https://github.com/larryw3i/funingschool/blob/master/LICENSE">
    GNU LESSER GENERAL PUBLIC LICENSE Version 3
</a>
