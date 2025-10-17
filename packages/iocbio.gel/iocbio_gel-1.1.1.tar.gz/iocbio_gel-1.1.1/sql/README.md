# Example SQL scripts

Scripts in this directory can be used to fetch the data from the
database. Provided scripts assume that you have IOCBIO Gel data stored
in PostgreSQL using schema `gel`. If you store it using some other
schema, just replace table names with the other schema name as in
`gel.measurement_lane` -> `other.measurement_lane` . If you use SQLite
then just remove `gel.` prefix.

Currently provided scripts:

- Fetching measurement values normalized to the reference lane
  values: [gel_relative_data.sql](gel_relative_data.sql)

- Fetching raw measurement values without normalization:
  [gel_raw_data.sql](gel_raw_data.sql)
