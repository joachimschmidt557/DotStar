# DotStar

[![Build Status](https://travis-ci.org/joachimschmidt557/DotStar.svg?branch=master)](https://travis-ci.org/joachimschmidt557/DotStar)
[![Build status](https://ci.appveyor.com/api/projects/status/oocppvl6ct23p6q7?svg=true)](https://ci.appveyor.com/project/joachimschmidt557/dotstar)
[![CircleCI](https://circleci.com/gh/joachimschmidt557/DotStar.svg?style=svg)](https://circleci.com/gh/joachimschmidt557/DotStar)
[![Code Health](https://landscape.io/github/joachimschmidt557/DotStar/master/landscape.svg?style=flat)](https://landscape.io/github/joachimschmidt557/DotStar/master)

Imagine distributing apps for multiple platforms in just one package. Or sending
a Word and a Pages document in one file and automatically opening the file which
can be run on your PC? Ever felt the urge to send a `FileName.*` file? 

DotStar makes this possible by providing an open container format architecture.
It's structure is easy and completely transparent: `.star` files are just normal
ZIP-compressed files which include one `Package.json` file which explains the
whole content. 

## Package-management capability

In addition to being a Python script which can handle special ZIP Packages,
DotStar is also a simplistic package manager which supports installing,
removing and locking packages (.star files).

## Philosophy

DotStar should be as easy to use as possible. Therefore, it will be provided in
only **one** Python file called `DotStar.py`. This file can be run directly with
command-line arguments to manipulate packages or can be imported from any other
Python file and used. The API will be available soon.

## Creating your own .star files

For a starting point, clone or download
[the template package repository](https://github.com/joachimschmidt557/DotStarTemplatePackage).

## Installation

If you already have DotStar installed, upgrade it by using this command:

`dotstar -i dotstar`

If you don't have DotStar installed, download the installers from the GitHub
release page. Python is not required to operate DotStar.
