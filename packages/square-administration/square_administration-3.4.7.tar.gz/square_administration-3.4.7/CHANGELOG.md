# changelog

## v3.4.7

- remove setup.py and switch to pyproject.toml

## v3.4.6

- env
    - SQUARE_LOGGER -> FORMATTER_CHOICE + ENABLE_REDACTION
- dependencies
    - square_logger>=3.0.0.

## v3.4.5

- core
    - bugfix: change logic for util_get_all_greetings_v0 as per db schema changes.

## v3.4.4 (unstable)

- bugfix remove async keyword from all util functions.

## v3.4.3 (unstable)

- move application logic from routes to util_functions.

## v3.4.2

- docs
    - move changelog to a new file.
    - update README.
    - switch to GNU General Public License v3.0.

## v3.4.1

- dependencies
    - square_authentication_helper>=3.0.0 and fix breaking changes for validate_and_get_payload_from_token_v0.

## v3.4.0

- authentication
    - add update_password_v0.

## v3.3.1

- authentication
    - move refresh token to cookie in register_login_google_v0, reset_password_and_login_using_backup_code_v0 and
      reset_password_and_login_using_reset_email_code_v0.

## v3.3.0

- authentication
    - add new endpoint -> register_login_google_v0.
    - add new endpoint -> reset_password_and_login_using_backup_code_v0.
    - add new endpoint -> reset_password_and_login_using_reset_email_code_v0.

## v3.2.2

- remove config.ini and config.testing.ini from version control.

## v3.2.1

- testing
    - update get_patched_configuration and create_client_and_cleanup to be session scoped.
- env
    - add ALLOW_ORIGINS

## v3.2.0

- move global_int_app_id getting logic from configuration.py to utils->common
- env
    - add DB_IP, DB_PORT, DB_USERNAME, DB_PASSWORD
    - add config.testing.ini
    - file path reading through os.path.join method.
- testing
    - add conftest file to create and cleanup test database, also to patch config file.
    - update existing tests to use the new fixtures.

## v3.1.1

- bump square_logger to 2.0.0

## v3.1.0

- add pytest as dependency.
- add dummy test case.

## v3.0.2

- update logic to get usernames for non-anonymous greetings in get_all_greetings_v0.

## v3.0.1

- add logging decorator to all functions.

## v3.0.0

- add new parameter -> password in authentication -> remove_app_for_self_v0.

## v2.4.0

- auto docker image build github action.

## v2.3.0

- env
    - add new variable COOKIE_DOMAIN.
- util
    - add is_https.
- authentication
    - add domain, exp_time, secure and http_only flags for cookies generated in login_username_v0, register_username_v0.

## v2.2.1

- authentication
    - add validation for refresh token app id in logout_v0, generate_access_token_v0.

## v2.2.0

- authentication
    - logout_v0, generate_access_token_v0 remove refresh token from request header and accept in cookie.

## v2.1.0

- add authentication -> logout_v0, generate_access_token_v0.

## v2.0.0

- remove refresh token from response body and send in cookies.

## v1.2.1

- fix bug in core -> get_all_greetings_v0, now sending full response instead of only main.

## v1.2.0

- set allow_credentials=True.

## v1.1.0

- add core -> get_all_greetings_v0.

## v1.0.0

- initial implementation.
