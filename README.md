# 🎧 Sparkify Data Warehouse (AWS Redshift ETL Pipeline)

## 📌 Project Overview

Sparkify, a growing music streaming startup, wants to transition its data infrastructure to the cloud to support scalable analytics. Their data currently resides in JSON logs stored in Amazon S3, containing:

- User activity logs from the music streaming app
- Song metadata from the Million Song Dataset

The goal of this project is to build an ETL pipeline that extracts data from S3, stages it in Amazon Redshift, and transforms it into a star schema optimized for analytical queries.

This enables Sparkify’s analytics team to efficiently analyze user behavior, song popularity, and listening trends.

## ❓ Project Discussion Question

### Question

1. Discuss the purpose of this database in the context of the startup, Sparkify, and their analytical goals.

### Answer

The purpose of this database is to support Sparkify’s transition from a file-based storage system (JSON logs in S3) to a scalable cloud data warehouse using Amazon Redshift.

As Sparkify’s user base and song catalog grow, querying raw JSON files becomes inefficient and does not support complex analytical queries. This data warehouse solves that problem by:

- Centralizing data from multiple sources (user activity logs and song metadata)
- Structuring raw data into analytics-ready tables using a star schema
- Enabling fast, scalable SQL queries for business intelligence

The database allows Sparkify to transform raw event data into meaningful insights that support decision-making and product growth.
