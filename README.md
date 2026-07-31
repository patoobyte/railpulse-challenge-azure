
# 🚅  RailPulse - Belgian Transit SQL Analysis 🚋

Made with

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

## 🚄 Project Context

RailPulse is the first sprint of RailwayPulse, a transit data engineering and analytics platform developed during the AI & Data Science Bootcamp at BeCode.

The wider RailwayPulse project builds a modern hybrid data architecture that ingests, cleans, and transforms both historical schedules (GTFS Static) and live operational streams (GTFS Real-time) from the Belgian National Railway (SNCB/NMBS), De Lijn, and TEC. The platform is deployed on Microsoft Azure, visualized with Power BI, and exposes transit insights through a conversational Generative AI interface.

This repository focuses exclusively on Sprint 1, which lays the project's data foundation. It covers the ingestion of the official SNCB/NMBS GTFS Static feed, the construction of a local SQLite relational database, and SQL analysis of Belgian rail operations.

The goal of this sprint is to answer operational questions about train schedules, station activity, route patterns, service frequency, and other network characteristics using SQL.

The SQLite database file itself is not included in this repository because of its size. Instructions for building it from the official GTFS source files are provided later in this README.
