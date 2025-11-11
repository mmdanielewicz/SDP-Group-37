This folder contains processed data files derived from the raw FEMA National Shelter System Facilities shapefile.

Notes:
- **fema_shelters_clean.csv**: cleaned, includes CT shelters only
- Columns include facility name, address, city, state, capacity, and other attributes.

**Purpose**: To make the raw FEMA data easier to view and understand using a simple CSV format. This CSV serves as the **primary data source for MVP development**.

**NOTE**: Since the MVP is being developed locally, each team member will have to setup the database on their own laptop's using the CSV file or use the CSV file directly.

## Steps To Setup Database Locally

**Start with saving "fema_shelters_clean.csv" from this repo, save it in a simple path to avoid any errors with PostgreSQL**

1: Install PostgreSQL: https://www.postgresql.org/download/
- Keep the default port (5432)
- If you setup a password for the default user save it!
- Make sure "pgAdmin 4" is checked 

2: Open "pgAdmin 4" from your start menu, expand "Local PostGreSQL"

3: Right click Databases -> Create -> Database, name it "ct_disaster_resilience" and click Save

4: Right click on your database, select "Query Tool", paste the following query and then click the play button at the top

```sql
CREATE TABLE ct_shelters (
    shelter_id TEXT,
    shelter_na TEXT,
    address_1 TEXT,
    city TEXT,
    county_par TEXT,
    fips_code TEXT,
    state TEXT,
    zip TEXT,
    mail_addr_ TEXT,
    mailing_ad TEXT,
    mailing__1 TEXT,
    mailing_ci TEXT,
    mailing_co TEXT,
    mailing_st TEXT,
    mailing_zi TEXT,
    facility_u TEXT,
    evacuation TEXT,
    post_impac TEXT,
    ada_compli TEXT,
    wheelchair TEXT,
    pet_accomm TEXT,
    pet_acco_1 TEXT,
    generator_ TEXT,
    self_suffi TEXT,
    latitude TEXT,
    longitude TEXT,
    in_100_yr_ TEXT,
    in_500_yr_ TEXT,
    in_surge_s TEXT,
    pre_landfa TEXT,
    shelter_co TEXT,
    org_organi TEXT,
    org_orga_1 TEXT,
    org_main_p TEXT,
    org_fax TEXT,
    org_email TEXT,
    org_hotlin TEXT,
    org_other_ TEXT,
    org_addres TEXT,
    org_city TEXT,
    org_state TEXT,
    org_zip TEXT,
    org_poc_na TEXT,
    org_poc_ph TEXT,
    org_poc_af TEXT,
    org_poc_em TEXT,
    org_hours_ TEXT,
    population TEXT,
    incident_i TEXT,
    shelter_st TEXT,
    shelter_op TEXT,
    shelter_cl TEXT,
    reporting_ TEXT,
    general_po TEXT,
    medical_ne TEXT,
    other_popu TEXT,
    other_po_1 TEXT,
    total_popu TEXT,
    pet_popula TEXT,
    incident_n TEXT,
    incident_1 TEXT,
    incident_c TEXT,
    objectid TEXT,
    score TEXT,
    status TEXT,
    match_type TEXT,
    loc_name TEXT,
    geox TEXT,
    geoy TEXT,
    facility_t TEXT,
    subfacilit TEXT,
    data_sourc TEXT,
    geometry TEXT
);
```

5: On the left under "ct_disaster_resilience" expand "Schemas", then expand "Tables", right click on "ct_shelters"
- If you don't see "ct_shelters", close the application and reopen

6: Right click on "ct_shelters", click "Import/Export data", put in the file path where the "fema_shelters_clean" is stored and click "OK"
- Make sure "Format: csv" and "Encoding: UTF8"

6: Right click on "ct_shelters", click "Query Tool" and test using this query:

```sql select * from ct_shelters ```

You should now be able to query from the shelter information.


