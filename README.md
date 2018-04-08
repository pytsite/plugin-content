# PytSite Content Plugin


## Changelog


### 3.1 (2018-04-08)

- Support of `odm_auth-1.6`.
- Cleanup.


### 3.0 (2018-04-06)

- Support of `auth-2.0`, `odm-2.0`.
- Default value of registry value `content.max_image_size` reduced to 5.
- Permissions renamed and defition its logic refactored.


### 2.6.1 (2018-03-26)

Query contruction fixed in 'content@index' routing rule.


### 2.6 (2018-03-15)

Support fow `widget-1.6`.


### 2.5.2 (2018-03-13)

Admin's sidebar permissions issue fixed.


### 2.5.1 (2018-02-20)

Permissions issue fixed.


### 2.5 (2018-02-18)

Signature of `register_model()` changed:

* `icon` renamed to `menu_icon`;
* new argument `menu_sid` added.


### 2.4 (2018-02-11)

Support for PytSite-7.9.


### 2.3.1 (2018-02-07)

Support for PytSite-7.7.


### 2.3 (2018-01-26)

- Support for `admin-1.3` and `settings-1.3`.


### 2.2.8 (2018-01-12)

Init fixed.


### 2.2.7 (2018-01-08)

Non-existent fields checking added while RSS generation.


### 2.2.6 (2018-01-02)

ODM UI hook's response fixed.


### 2.2.5 (2017-12-21)

Admin sidebar item addition fixed.


### 2.2.4 (2017-12-21)

Init fixed.


### 2.2.3 (2017-12-21)

Init fixed.


### 2.2.2 (2017-12-20)

Init fixed.


### 2.2.1 (2017-12-20)

Init refactored.


### 2.2 (2017-12-13)

Support for PytSite-7.0.


### 2.1 (2017-12-02)

Support for PytSite-6.1.


### 2.0 (2017-11-25)
Support for PytSite-6.0.


### 1.3 (2017-10-10)

- Support for latest PytSite release 5.3.
- Fixed caching to 'publish_time'-related queries.


### 1.2 (2017-10-09)

Added caching to 'publish_time'-related queries.


### 1.1.1 (2017-10-08)

Fixed entity status changing on abuse report.


### 1.1 (2017-10-08)

Added a new HTTP API endpoint `content@post_abuse`.


### 1.0.2 (2017-10-02)

Added `css` argument to `paginate()` function.


### 1.0.1 (2017-09-27)

Fixed language global usage.


### 1.0 (2017-09-13)

Updated to support latest PytSite version 5.0.


### 0.5 (2017-09-02)

Home page meta tags management moved to core of PytSite.


### 0.4.12 (2017-08-27)

`plugin.json` updated.


### 0.4.11 (2017-08-09)

Fixed HTML structure building in `widget.Search`.


### 0.4.10 (2017-08-02)

Fixed rouite alias entities locking errors.


### 0.4.9 (2017-07-03)

Support for latest PytSite-1.0 release.


### 0.4.8 (2017-06-21)

Updated to support latest PytSite version 0.99.46.


### 0.4.7 (2017-06-19)

Updated to support latest PytSite version 0.99.45.


### 0.4.6 (2017-06-15)

Endpoint controllers' names shortened.


### 0.4.5 (2017-06-15)

Removed unnecessary controller existence checking.


### 0.4.4 (2017-06-15)

Updated to support latest PytSite version 0.99.39.


### 0.4.3 (2017-06-08)

Fixed translations.


### 0.4.2 (2017-06-08)

Fixed permission checking according to latest PytSite core update.


### 0.4.1 (2017-05-30)
Added ability to configure images maximum size and files number. 


### 0.4 (2017-05-22)

- Added setting to enable/disable automatic body images enlarging.
- Fixed embedded video links parsing.


### 0.3.7 (2017-05-19)

Fixed permissions checking in widgets.


### 0.3.6 (2017-05-07)

Fixed incorrect call to `tpl.render()` in modify form endpoint.


### 0.3.5 (2017-05-05)

Updated controllers' signatures.


### 0.3.4 (2017-05-04)

Fixed translation strings.


### 0.3.3 (2017-05-03)

Fixed invalid JS assets target location.


### 0.3.2 (2017-05-02)

Fixed console command `content:generate`.


### 0.3.1 (2017-05-02)

Fixed image tags processing.


### 0.3 (2017-04-28)

Support for latest PytSite asset management changes.


### 0.2.24 (2017-03-31)

Fixed lang message ID.


### 0.2.23 (2017-03-30)

Fixed event subscription method.


### 0.2.22 (2017-03-23)

Fixed issues related to missing `route_alias` field in `model.ContentWithURL`.


### 0.2.21 (2017-03-21)

Support fore latest PytSite `widget`'s changes.


### 0.2.20 (2017-03-15)

Added new content entities index endpoint name variants.


### 0.2.19 (2017-03-14)

Added new content entity view endpoint name variants.


### 0.2.18 (2017-03-06)

Fixed processing entities with missed route alias.


### 0.2.17 (2017-03-03)

Fixed missing route alias handling.


### 0.2.16 (2017-03-03)

Support for latest PytSite router's API function rename.


### 0.2.15 (2017-02-28)

Fixed content generation console command.


### 0.2.14 (2017-02-28)

Fixed content generation console command.


### 0.2.13 (2017-02-23)

Route names updated.


### 0.2.12 (2017-02-17)

- Sitemap generation improved.
- Settings form fixed.


### 0.2.11 (2017-02-13)

Removed neutral language from settings form.


### 0.2.10 (2017-02-08)

Fixed admin UI permissions issue.


### 0.2.9 (2017-02-07)

Removed unnecessary database index.


### 0.2.8 (2017-02-07)

- Added support for latest PytSite `odm_auth` changes.
- Fixed HTTP API related issues.


### 0.2.7 (2017-02-02)

Fixed entity views count HTTP API request processing.


### 0.2.6 (2017-01-26)

HTTP API update.


### 0.2.5 (2017-01-21)

Support latest PytSite `widget`'s changes.


### 0.2.4 (2017-01-16)

Fixed comments count update code.


### 0.2.3 (2017-01-16)

Models JSON representations fixed.


### 0.2.2 (2017-01-15)

`route_alias` field moved from [Article](https://github.com/pytsite/plugin-article) plugin's model.


### 0.2.1 (2017-01-15)

JS form helper moved from [Article](https://github.com/pytsite/plugin-article) plugin.


### 0.2 (2017-01-13)

- New field **description**.
- Indexes reviewed.


### 0.1.3 (2017-01-12)

- Support for latest PytSite `form`'s changes.
- Translation usage fixed.


### 0.1.2 (2017-01-08)

Removed non existent widget usage.


### 0.1.1 (2017-01-08)

- plugin.json updated.
- Unnecessary widgets moved to the `tag` plugin.


### 0.1 (2017-01-08)
First release.
