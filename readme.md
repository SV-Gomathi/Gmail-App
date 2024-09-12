# Project Documentation

## Table of Contents

- [Introduction](#introduction)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Execution](#execution)

## Introduction

This project enables fetching emails from a Gmail account and applying custom rules to them. 

## Requirements

Refer to the [requirements.txt](requirements.txt) file for a list of required packages.

## Installation

To install the necessary packages, run the following command:

```
pip install -r requirements.txt
```

## CONFIGURATION

   1. Modify the username, password, host and port in config.json
      with your MYSQL DB details.
   2. Source the initial_schema.sql in the DB.
   3. Create your gmail oauth credentials 
      1. Go to the API Console.
      2. From the projects list, select a project or create a new one. 
      3. If the APIs & services page isn't already open, open the console left side menu and select APIs & services.
      4. On the left, click Credentials. 
      5. Click New Credentials, then select OAuth client ID.
      6. Select the application type as Desktop client and enter the additional information required.
      7. Click Create client ID
   4. Download your oauth credentials and replace that in the [existing one](credentials.json).
  
## EXECUTION

   1. Fetch Emails:

      Run the following command to fetch emails from your Gmail account and store them in the database. The script will only fetch emails received after the last timestamp recorded in the database.

```
python read_emails.py
```   
   2. Execute Rules:

      Execute the rules defined in your rules.json file against the emails stored in the database. The script will apply the necessary actions using the Gmail REST APIs based on the matching rules.
```
python execute_rules.py
```     
