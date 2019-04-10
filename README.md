# PytSite Content Plugin


## Changelog


### 6.0 (2019-04-10)

Support of `odm_ui-7.14`.


### 5.21.1 (2019-04-01)

Permissions checking issue fixed.


### 5.21 (2019-03-21)

Support of `odm-6.2`.


### 5.20 (2019-03-04)

Support of `odm-6.0`.


### 5.19 (2019-02-27)

- New event `content@view` added.


### 5.18.1 (2019-02-27)

Cleanup.


### 5.18 (2019-02-25)

- Status constants added.
- Statuses checking fixed.


### 5.17.3 (2019-02-20)

Status notification fixed.


### 5.17.2 (2019-02-20)

Hook's value usage fixed.


### 5.17.1 (2019-02-19)

Content status checking fixed.


### 5.17 (2019-02-19)

Support of `flag` plugin added.


### 5.16.1 (2019-02-18)

- Default value of `Content.publish_time` model set to 8:00 of the day.
- Permission definition fixed. 


### 5.16 (2019-01-31)

- `published` and `unpublished` entity's statuses made mandatory.
- Statuses description ID format changed.


### 5.15.7 (2019-01-30)

Permissions checking fixed.


### 5.15.6 (2019-01-30)

Permissions checking fixed.


### 5.15.5 (2019-01-30)

Typo fixed.


### 5.15.4 (2019-01-30)

`widget.StatusSelect.items` made adjustable.


### 5.15.3 (2019-01-30)

Content status notification emails fixed.


### 5.15.2 (2019-01-30)

Statuses CSS fix in ODM UI Browser rows.


### 5.15.1 (2019-01-30)

`widget.StatusSelect` items set fixed.


### 5.15 (2019-01-30)

- Typo fixed.
- `content_status_change()` renamed to `content_on_status_change()`.


### 5.14.2 (2019-01-29)

Content status selection issue fixed.


### 5.14.1 (2019-01-29)

Content status descriptions fixed in ODM UI browser.


### 5.14 (2019-01-28)

- New API function `get_model_class()` added.
- API functions `get_statuses()` removed.
- New class methods added to `model.Content`: `content_statuses()` and
  `content_statuses_descriptions()`.


### 5.13.1 (2019-01-26)

`min_length` and `max_length` parameters support in text input widgets.


### 5.13 (2019-01-10)

Support of `odm-5.9`.


### 5.12.2 (2019-01-10)

`model.Content.odm_ui_browser_setup_finder()` hook fixed.


### 5.12.1 (2019-01-08)

Typo fix.


### 5.12 (2019-01-08)

Support of `odm_ui-7.x`.


### 5.11.1 (2019-01-07)

`plugin.json` fixed.


### 5.11 (2019-01-07)

- Support of `odm-5.7`, `odm_auth-3.0`, `odm_ui-6.1`.
- New `view` permission.
- New `EntitySelect` widget.


### 5.10 (2019-01-02)

Support of `odm_ui-6.x`.


### 5.9 (2018-12-12)

Support of `odm_http_api-5.x`.


### 5.8 (2018-12-12)

New field `thumbnail` added to `Content.as_jsonable()`'s response.


### 5.7 (2018-11-29)

`model.Content.odm_ui_browser_row()` now returns a `dict`.


### 5.6.4 (2018-11-26)

Light refactoring.


### 5.6.3 (2018-11-26)

Light refactoring.


### 5.6.2 (2018-11-26)

Content status change notification bug fixed.


### 5.6.1 (2018-11-26)

Typo fixed.


### 5.6 (2018-11-26)

- New ODM field and property `model.Content.prev_status` added.
- New hook `content_status_change()` added.
- Content author notification added about content status change.
- Configuration option `send_waiting_notifications` renamed to
  `waiting_status_admin_notification`.
- New configuration option added: `status_change_author_notification`.


### 5.5 (2018-11-25)

- Support of `odm-5.4`.
- Route alias field setting fixed.


### 5.4.3 (2018-11-21)

`ContentWithURL.route_alias` field setting fixed.


### 5.4.2 (2018-11-20)

`View` controller fixed.


### 5.4.1 (2018-11-15)

`Index` controller fixed.


### 5.4 (2018-11-14)

Support of `odm_ui-5.x`.


### 5.3 (2018-11-03)

Support of `odm-5.1`.


### 5.2 (2018-10-22)

Support of `assetman-5.x` and `widget-4.x`.


### 5.1.1 (2018-10-12)

NPM dependencies fixed.


### 5.1 (2018-10-12)

Support of `assetman-4.x`.


### 5.0.2 (2018-10-11)

`plugin.json` fixed.


### 5.0.1 (2018-10-08)

`plugin.json` fixed.


### 5.0 (2018-10-08)

Support of `pytsite-8.x` and `assetman-3.x`.


### 4.20.2 (2018-09-21)

Sitemap generation fixed.


### 4.20.1 (2018-09-21)

Route alias setting fixed.


### 4.20 (2018-09-14)

Limited support of search across multiple models removed.


### 4.19 (2018-09-14)

Support of `odm-4.0`.


### 4.18.1 (2018-09-09)

Missing controllers args fixed.


### 4.18 (2018-09-09)

Breadcrumbs generation added.


### 4.17 (2018-09-07)

Support of `odm-3.7`.


### 4.16 (2018-08-28)

Support of `odm_ui-3.19`.


### 4.15.1 (2018-08-23)

User's `full_name` usage replaced with `first_last_name`.


### 4.15 (2018-08-21)

Support of `widget-2.11`.


### 4.14 (2018-08-12)

Images source changed in `content:generate` logic.


### 4.13.1 (2018-08-10)

Little fixes to support Twitter Bootstrap 4.


### 4.13 (2018-08-09)

Support of `odm_auth-1.9`.


### 4.12 (2018-08-08)

Support of `form-4.12`.


### 4.11 (2018-07-29)

Support of `auth-3.5`, `form-4.7`, `widget-2.4`.


### 4.10.1 (2018-07-22)

Content view URL generation issue fixed.


### 4.10 (2018-06-24)

Support of `odm_auth-1.8`.


### 4.9 (2018-06-16)

- Limited support for searching across multiple models added.
- `publish_time` field moved back from the `article` plugin.


### 4.8 (2018-06-07)

Support of `auth_ui-3.5`.


### 4.7 (2018-06-01)

Support of `pytsite-7.24`.


### 4.6 (2018-05-30)

`widget.EntitySelect` removed.


### 4.5 (2018-05-14)

New contructor's argument in `widget.ModelCheckboxes`: `filter`.


### 4.4.2 (2018-05-13)

Couple of bugfixes.


### 4.4.1 (2018-04-26)

Metatag's title setting fixed in forms controllers.


### 4.4 (2018-04-25)

Support of `auth-3.0`.


### 4.3.9 (2018-04-15)

- Authentication filters added to routing rules.
- Modify form title hidden by default now.


### 4.3.8 (2018-04-15)

Content delete form submit rule methods fixed.


### 4.3.7 (2018-04-15)

Admin forms router rule names fixed.


### 4.3.6 (2018-04-15)

Route rule argument name fixed.


### 4.3.5 (2018-04-15)

Route rule argument name fixed.


### 4.3.4 (2018-04-15)

Missing route added.


### 4.3.3 (2018-04-15)

Routes argument names fixed.


### 4.3.2 (2018-04-15)

Router's rule definition fixed.


### 4.3.1 (2018-04-15)

Referer checking fixed.


### 4.3 (2018-04-15)

Support of `odm_ui-3.2`.


### 4.2 (2018-04-14)

ODM UI model router's rules detection added.


### 4.1.3 (2018-04-14)

Router's rule path fixed.


### 4.1.2 (2018-04-14)

Permissions issue fixed.


### 4.1.1 (2018-04-14)

`plugin.json` fixed.


### 4.1 (2018-04-14)

Support of `odm_ui-3.0`.


### 4.0.1 (2018-04-12)

Missing `Browser` controller's rule added.


### 4.0 (2018-04-12)

- New `Browse` controller added.
- Support for application-provided default templates added.
- Names of application-provided expected routes changed.


### 3.1.3 (2018-04-09)

Some user notifications added.


### 3.1.2 (2018-04-09)

Tpl argument name fixed.


### 3.1.1 (2018-04-08)

Cleanup.


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
