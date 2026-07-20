-- 00_account_setup.sql
-- Run once as ACCOUNTADMIN right after creating the Snowflake trial.
-- Creates the database, schema, and a project role so you are not
-- doing everything as ACCOUNTADMIN (a real interview talking point).

USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS ONCOLAKE_ENG;
CREATE DATABASE IF NOT EXISTS ONCOLAKE;
CREATE SCHEMA IF NOT EXISTS ONCOLAKE.RAW;      -- landing zone
CREATE SCHEMA IF NOT EXISTS ONCOLAKE.STAGING;  -- cleaned / typed
CREATE SCHEMA IF NOT EXISTS ONCOLAKE.MARTS;    -- dbt dimensional output

-- Grants so the project role can actually work.
GRANT USAGE ON DATABASE ONCOLAKE TO ROLE ONCOLAKE_ENG;
GRANT ALL ON SCHEMA ONCOLAKE.RAW     TO ROLE ONCOLAKE_ENG;
GRANT ALL ON SCHEMA ONCOLAKE.STAGING TO ROLE ONCOLAKE_ENG;
GRANT ALL ON SCHEMA ONCOLAKE.MARTS   TO ROLE ONCOLAKE_ENG;

-- Give your login the role (replace with your username).
GRANT ROLE ONCOLAKE_ENG TO USER <YOUR_USER>;
