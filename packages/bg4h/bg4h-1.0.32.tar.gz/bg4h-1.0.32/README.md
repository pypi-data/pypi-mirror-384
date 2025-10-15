# BG4h

bee gees for Humans Table Definitions

## ChangeLog

### 1.0.32 - 15.10.2025

- new field:  contact_person = "TPRESUPUESTOS107"

### 1.0.31 - 14.10.2025

- new field: email = "TPRESUPUESTOS150"

### 1.0.30 - 10.10.2025

- new fields for TDATOSDECONTROL
    taxes_per_article = 'TDATOSDECONTROL4'
    taxes_per_budget_doc = 'TDATOSDECONTROL5'
    default_sell_doc_tax_code = 'TDATOSDECONTROL14'
    default_client_agrarian_tax_code = 'TDATOSDECONTROL15'
    default_client_exempt_tax_code = 'TDATOSDECONTROL16'
    default_client_eu_tax_code = 'TDATOSDECONTROL17'
    default_provider_tax_code = 'TDATOSDECONTROL18'
    default_provider_agrarian_tax_code = 'TDATOSDECONTROL19'
    default_provider_exempt_tax_code = 'TDATOSDECONTROL20'
    default_provider_eu_tax_code = 'TDATOSDECONTROL21'
    default_sell_doc_special_tax_code = 'TDATOSDECONTROL35'
    default_family_code = 'TDATOSDECONTROL42'
    default_client_general_agrarian_tax_code = 'TDATOSDECONTROL62'
    default_provider_general_agrarian_tax_code = 'TDATOSDECONTROL63'
    default_currency = 'TDATOSDECONTROL85'


- rename fields:
    article_tax_code > default_article_tax_code = 'TDATOSDECONTROL40'


### 1.0.29 - 08.10.2025

- added: expire_date = "TSTOCKOTROSCONTROLES3"
- fix: pvp_accountant = "TVALORESVENTAS5"
- fix: price_tax_included_intgernal -> price_tax_included_internal = "TVALORESVENTAS34"
- fix: margin_percentage  -> article_margin_percentage = "TVALORESVENTAS21"
- fix: code -> article_code = "TVALORESVENTAS2"
- fix: desc -> article_desc = "TVALORESVENTAS3"

### 1.0.28 26.09.2025

- rename delivery_document_series,delivery_document_number, delivery_document_date to document_series,document_number,document_date

- added: percentage_on_amounts ="TVENTAS122"

### 1.0.27 - 22.09.2025

- Add observations variable to tTareas class and format existing attributes

### 1.0.26 - 22.09.2025

- fix: data_default_value -> changed from TTAREAS12 to TTAREAS17
- fix: data_default_inital_value -> is now TTAREAS12

### 1.0.25 - 19.09.2025

- added: observations = "CCUENTASTESORERIA14"

### 1.0.24 - 21.08.2025

- Add index_numerico variable to BgSoc class for AvisosElementos

### 1.0.23 - 19.08.2025

- fix: in var name of tavisoschecklist table name

### 1.0.22 - 12.08.2025

- added fields to ttareas
- added fields to tvalorespresupuestos

### 1.0.21 - 05.07.2025

- fix: rename table and fiels TFICHASELEMENTOS -> TFICHAELEMENTOS

### 1.0.20 - 05.07.2025

- fix: batch_manufacturation -> lot_number = "TFICHASELEMENTOS6"

### v1.0.19 - 04.07.2025

- added optional_line = TVALORESPRESUPUESTOS53

### v1.0.18 - 04.07.2025

- add new tables for checklist
- TAVISOSCHECKLIST
- TAVISOSCHECKLISTIMP
- TMANTENIMIENTOSSAT
- TVALORESMANTENIMIENTOSSAT

### v1.0.17

- import_limit = "CCUENTASTESORERIA15"
- TNOMINAS added

### v1.0.16

- contract_source = "TAVISOSREPARACIONESCLIENTES37"
- time_of_call = "TAVISOSREPARACIONESCLIENTES48"
- fee_code ="TAVISOSREPARACIONESCLIENTES157"
- table: IntervencionesAvisos

### v1.0.15

- project_code_invoice = "TAVISOSREPARACIONESCLIENTES80"
- in_charge_code_header = "TAVISOSREPARACIONESCLIENTES119"
- worker_code1_header = "TAVISOSREPARACIONESCLIENTES120"
- worker_code2_header = "TAVISOSREPARACIONESCLIENTES121"
- worker_code3_header = "TAVISOSREPARACIONESCLIENTES122"

### v1.0.14 16.05.2025

- fix TVENTAS
- added TVALORESPOSIBLESLOCALIZACIONESART

### v1.0.13 09.05.2025

- added quotation series and code to AvisosReparacionesClientes
- added vehicle_code to tventas

### v1.0.12 03.02.2025

- added missings vars tpersonal
- rename tobras state -> status

### v1.0.11 12.12.2024

- fix: correct class definition syntax for StockMinMaxAlmacen

### v1.0.10 10.12.2024

- added defs for stockminmaxalmacen

### v1.0.9 01.12.2024

- fixed wrong defs on Inmovilizados
- added defs for OtrosCostes and ValoresOtrosCostes

### v1.0.8 01.12.2024

- added new fields to `bg_soc.py`
- fixed typos in `bg_main.py`
- added missing field definitions in various tables

### v1.0.7 25.11.2024

- added missing index field tarticulosavisos

### v1.0.6 27.09.2024

- added missing fields in ttareasavisos

### v1.0.5 17.09.2024

- added missing worker 1-3 fields -> tavisosreparacionesclientes

### v1.0.4 02.08.2024

- added missing fields
- fix misspeling table ttrabajosavisos -> trabajosavisos

### v1.0.3 13.03.2024

- fixed spelling in vars of Personal table in BgMain

### v1.0.2 - 27.01.2024

- added missing fields from table vacaciones

### v1.0.1 - 10.01.2024

- added long description to setup.py
- fixed ttarea6 -> to TTAREAS6

### v1.0.0 - 18.12.2023

- ts/net lib converted to python
- spellfix
- added todos for unknown / unclear values

## Publish

Hacer Build:
python setup.py sdist

Publicar:
twine upload dist/*
