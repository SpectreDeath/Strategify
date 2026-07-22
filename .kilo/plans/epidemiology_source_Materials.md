To parameterize epidemiological models (such as estimating transmission rates $\beta$, recovery rates $\gamma$, or the basic reproduction number $R_0$) using real-world public health surveillance data, epidemiologists and computational modelers rely on several open-access government, institutional, and academic data repositories.

The primary public databases and APIs frequently used for parameter fitting, time-series calibration, and real-time disease modeling include:

---

### 1. Primary U.S. Federal Surveillance & Open Data

* **CDC WONDER (Wide-ranging OnLine Data for Epidemiologic Research)**
* **What it provides:** Comprehensive mortality, morbidity, population census, and chronic/infectious disease surveillance data across state and county levels.
* **Use case:** Ground-truth baseline mortality rates, population demographic denominators, and historical incidence data for model calibration.
* **Access:** [wonder.cdc.gov](https://wonder.cdc.gov/)


* **CDC NNDSS (National Notifiable Diseases Surveillance System)**
* **What it provides:** Weekly provisional and finalized annual case surveillance counts for nationally reportable infectious diseases (e.g., measles, salmonellosis, hepatitis, respiratory viruses).
* **Use case:** Extracting weekly time-series incidence curves to estimate reproduction numbers ($R_t$) and time-varying transmission dynamics.
* **Access:** Available via [data.cdc.gov](https://data.cdc.gov/) or CDC Stacks.


* **CDC Center for Forecasting and Outbreak Analytics (CFA)**
* **What it provides:** Open datasets containing weekly $R_t$ estimates, trend probabilities, and nowcasting metrics for respiratory viruses (influenza, COVID-19).
* **Use case:** Benchmarking model predictions against official federal $R_t$ estimates and ensemble forecasts.
* **Access:** Search "CDC Epidemic Trends and Rt" on [data.cdc.gov](https://data.cdc.gov/).


* **HealthData.gov (U.S. HHS Open Data)**
* **What it provides:** Federal open datasets covering hospital bed capacity, emergency department visit percentages, and regional health metrics across the Department of Health and Human Services.
* **Access:** [healthdata.gov](https://healthdata.gov/)



---

### 2. Global & Academic Repositories

* **WHO Global Health Observatory (GHO) API**
* **What it provides:** Global mortality, disease prevalence, immunization coverage, and health system capacity metrics across 194 member states.
* **Use case:** Parameterizing global or multi-country compartmental models with age-stratified and region-specific baseline data.
* **Access:** Open OData API via [who.int/data/gho](https://www.who.int/data/gho).


* **Nextstrain (Genomic Epidemiology)**
* **What it provides:** Real-time tracking of pathogen evolution, phylogenetic trees, and spatial spread maps derived from open genomic sequencing data (e.g., GISAID, NCBI GenBank).
* **Use case:** Parameterizing multi-strain evolutionary game models or estimating mutation rates and clade competitiveness.
* **Access:** [nextstrain.org](https://nextstrain.org/)


* **Google Health & Johns Hopkins CSSE Archives**
* **What it provides:** Aggregated historical time-series datasets of global case counts, hospitalizations, testing rates, and mobility indicators across thousands of administrative regions worldwide.
* **Use case:** Benchmarking ODE systems against fine-grained historical outbreak curves.



---

### 3. How Models Extract Parameters from Surveillance Data

When feeding these datasets to a simulation framework or coding agent, standard mathematical techniques are used to translate raw surveillance counts into model parameters:

| Model Parameter | Definition | How It Is Derived from Public Data |
| --- | --- | --- |
| **Recovery Rate ($\gamma$)** | Rate at which infected individuals recover ($1/\text{infectious duration}$). | Derived from clinical study literature or hospital discharge duration metrics in CDC NCHS surveys. |
| **Transmission Rate ($\beta$)** | Effective contact/transmission rate per unit time. | Estimated by fitting ODE solver trajectories (`scipy.integrate.solve_ivp`) to weekly NNDSS incidence time-series via nonlinear least squares or Maximum Likelihood. |
| **Effective Reproduction Number ($R_t$)** | Time-varying mean number of secondary infections per infected case. | Calculated from daily/weekly case series using renewal equation models (e.g., the `EpiNow2` methodology used by CDC CFA). |
| **Population Denominators ($N, S_0$)** | Total population and initial susceptible pool size. | Ingested directly from CDC WONDER / U.S. Census Bureau population counts. |

### update 11:20
Both the **CDC** and the **NIH** maintain robust, open-access public APIs and developer portals. Combined with OpenFDA, they form the core ecosystem for federal health, surveillance, grant, and biomedical data.

Here is a breakdown of the primary developer APIs available across both agencies:

---

## 1. Centers for Disease Control and Prevention (CDC)

The CDC hosts its open data primarily through **Socrata-backed data portals** and specialized REST endpoints.

### 🏛️ CDC Socrata Open Data API (SODA)

* **What it provides:** Direct RESTful programmatic querying over tens of thousands of CDC datasets (including NNDSS surveillance counts, state-level vaccination coverage, mortality stats, and PLACES community-level health estimates).
* **Endpoint:** `data.cdc.gov/resource/{dataset_identifier}.json`
* **Features:** Supports **SoQL** (Socrata Query Language), allowing SQL-like filtering, aggregations, `$where` clauses, and pagination in JSON/CSV formats without requiring complex authentications for public tiers.

### 📍 CDC PLACES API

* **What it provides:** Model-based population health estimates down to the county, census tract, and ZIP Code Tabulation Area (ZCTA) levels across all US states.
* **Use case:** Ingesting local baseline health indicators and chronic disease burdens to configure location-specific demographic models.

### 📚 CDC Content Services / Media API

* **What it provides:** Programmatic access to CDC’s structured public health guidance, articles, topic lists, and media assets in JSON/XML.
* **Endpoint:** `tools.cdc.gov/api/v2/resources/media`

### 🏢 NIOCCS Industry & Occupation Coding API

* **What it provides:** Machine learning web API that translates unstructured industry and occupation narrative text into standardized NAICS and SOC codes in real time.
* **Endpoint:** `wwwn.cdc.gov/nioccs/IOCode`

---

## 2. National Institutes of Health (NIH) & NCBI

The NIH ecosystem provides extensive REST APIs through the **National Center for Biotechnology Information (NCBI)**, the **National Library of Medicine (NLM)**, and **NIH Extramural Research Databases**.

### 🔬 NCBI Entrez Programming Utilities (E-Utilities)

* **What it provides:** The gold standard API for accessing all 38+ NCBI biomedical databases, including **PubMed** (literature citations), **PMC** (PubMed Central full-text articles), **SRA** (Sequence Read Archive), and **GenBank** (nucleotide sequences).
* **Key Endpoints:**
* `esearch.fcgi`: Text searching across database fields.
* `efetch.fcgi`: Retrieving full records or structured XML/JSON payloads.
* `elink.fcgi`: Discovering hyper-linked relationships between citations and genomic records.


* **Base URL:** `eutils.ncbi.nlm.nih.gov/entrez/eutils/`

### 💰 NIH RePORTER API (V2)

* **What it provides:** Programmatic access to all NIH-funded extramural research projects, principal investigators, grant funding allocations, indirect costs, study sections, and resulting publications.
* **Use case:** Tracking scientific research funding trends, active grant portfolios, and institutional award metrics.
* **Endpoint:** `api.reporter.nih.gov/v2/projects/search` (POST JSON payloads)

### 💊 NLM RxNorm & Clinical Tables APIs

* **What it provides:** Normalized concepts for clinical drugs (RxNorm), disease classifications, and clinical vocabularies (SNOMED CT, LOINC, ICD-10).
* **Base URL:** `rxnav.nlm.nih.gov/REST/`
* **Use case:** Standardizing drug names, ingredient mappings, and clinical observation fields across software interfaces.

---

## 3. Comparative Summary for Developer Pipelines

| Portal / API | Agency | Core Data Domain | Best Format / Protocol |
| --- | --- | --- | --- |
| **SODA (`data.cdc.gov`)** | CDC | Disease surveillance, mortality, public health metrics | REST / JSON (via SoQL) |
| **E-Utilities** | NIH/NCBI | PubMed literature, PMC articles, genomic metadata | REST / XML & JSON |
| **NIH RePORTER V2** | NIH | Federal research grants, principal investigators, publications | REST / JSON (POST payload queries) |
| **RxNav / RxNorm** | NIH/NLM | Standardized drug vocabularies, clinical tables | REST / JSON |
| **OpenFDA** | FDA | Adverse events, drug/device labels, enforcement reports | REST / JSON |
---
12:54
---
Suggested Next Steps for the Workspace
Now that your OSINT data adapters and mathematical epidemiology solvers are wired and committed (70a7a52), here are three potential focus areas:

Pipeline Integration: Connect the CDCSodaApiAdapter outputs directly to the SurveillanceParameterFitter so raw SoQL query streams feed directly into the scipy.optimize.curve_fit ODE parameter estimation engine.

MCP Tool Binding: Wrap these three adapters into SME/Em-Cubed Model Context Protocol (MCP) bridges to enable external agent execution during interactive chat sessions.

Cache & Rate Limiting Layer: Add local SQLite caching or asynchronous rate-limiting throttlers to comply with federal API guidelines (e.g., maintaining max 1 request/sec for NIH RePORTER V2).
