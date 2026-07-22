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