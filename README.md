# Corporate Analyst Agent

## Purpose

Given a ticker symbol, this agent downloads the most recent 10-K report from the
SEC and corporate data from Zoominfo. 
It generates a report after analyzing all the information about the company from 
these sources.

## Prerequisites
* Generate an API key from sec-api.io for yourself and add it to the .env file
`SEC_API_KEY= YOUR_API_KEY`
* Add your Zoominfo credentials to the .env file as
`ZOOMINFO_USERNAME=YOUR_ZOOMINFO_USERNAME`
`ZOOMINFO_PASSWORD=YOUR_ZOOMINFO_PASSWORD`
* Check requirements.txt for python dependencies