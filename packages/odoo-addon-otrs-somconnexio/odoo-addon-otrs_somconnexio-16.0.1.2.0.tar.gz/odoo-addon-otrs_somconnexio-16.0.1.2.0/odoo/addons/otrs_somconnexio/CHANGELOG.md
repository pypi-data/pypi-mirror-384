# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
## [16.0.1.2.0] - 2025-10-14
### Added
- [#1396](https://git.coopdevs.org/coopdevs/som-connexio/odoo/odoo-somconnexio/-/merge_requests/1396) Add Responsible employe to leads and inform it it to OTRS tickets
### Fixed
- [#1635](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1635) Fix _get_parent_pack_contract always return contract

## [16.0.1.1.2] - 2025-09-30
### Fixed
- [#1623](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1623) Send lead notes as text and not html
- [#1619](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1619): Fix product category filter in mobile_contract_otrs_view

## [16.0.1.1.1] - 2025-09-19
### Fixed
- [#1540](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1540) Send activation_notes as text and not html

## [16.0.1.1.0] - 2025-09-17
### Changed
- [#1577](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1577) Adaptation to switchboard_somconnexio version 16.0.1.1.0

## [16.0.1.0.10] - 2025-09-16
### Fixed
- [#1566](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1566) Refactor listeners

## [16.0.1.0.9] - 2025-08-26
### Fixed
- [#1587](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1587) Remove the drop view if exists in PartnerOTRSView init

## [16.0.1.0.8] - 2025-06-25
### Changed
- [#1405](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1405) Adaptation to new multimedia modules

## [16.0.1.0.7] - 2025-06-19
### Fixed
- [#1539](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1539) Fix compute mobile_contracts_available_to_pack

## [16.0.1.0.6] - 2025-06-09
### Fixed
- [#1523](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1523) Uncomment the sim_delivery_tracking_code value

## [16.0.1.0.5] - 2025-06-06
### Fixed
- [#1518](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1518) Fix CacheMiss error in _compute_is_pack_full
- [#1513](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1513) Remove unused "summary" param in change tariff process

## [16.0.1.0.4] - 2025-06-02
### Fixed
- [#1510](https://git.coopdevs.org/coopdevs/som-connexio/odoo/odoo-somconnexio/-/merge_requests/1510) Add origin to virtual records mobile tariff change

## [16.0.1.0.3] - 2025-05-28
### Added
- [#1500](https://git.coopdevs.org/coopdevs/som-connexio/odoo/odoo-somconnexio/-/merge_requests/1500) Add code field in crm team

### Fixed
- [#1501](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1501) Only create OTRS tickets after lead validation, not edition
- [#1497](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1497) Always assign `will_force_other_mobiles_to_quit-pack` field in their computation

## [16.0.1.0.2] - 2025-05-28
### Added
- [#1492](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1492) Execute method create_additional_data_otrs_ticket as queue.job

## [16.0.1.0.1] - 2025-05-27
### Fixed
- [#1470](https://git.coopdevs.org/coopdevs/som-connexio/odoo-somconnexio/-/merge_requests/1470) Call super() within otrs.crm.lead.listener `on_record_write` method

## [16.0.1.0.0] - 2025-05-26
### Added
- Migrate otrs_somconnexio module to ODOO v16
