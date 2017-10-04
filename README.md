# DotStar

[![Build Status](https://travis-ci.org/joachimschmidt557/DotStar.svg?branch=master)](https://travis-ci.org/joachimschmidt557/DotStar)
[![Build status](https://ci.appveyor.com/api/projects/status/oocppvl6ct23p6q7?svg=true)](https://ci.appveyor.com/project/joachimschmidt557/dotstar)
[![CircleCI](https://circleci.com/gh/joachimschmidt557/DotStar.svg?style=svg)](https://circleci.com/gh/joachimschmidt557/DotStar)

Imagine distributing apps for multiple platforms in just one package. Or sending a Word and a Pages document in one file and automatically opening the file which can be run on your PC? Ever felt the urge to send a `FileName.*` file? 

DotStar makes this possible by providing an open container format architecture. It's structure is easy and completely transparent: `.star` files are just normal ZIP-compressed files which include one `Package.json` file which explains the whole content. 
