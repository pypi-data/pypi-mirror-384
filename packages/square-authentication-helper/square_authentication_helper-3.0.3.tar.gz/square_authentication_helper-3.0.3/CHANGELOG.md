# changelog

## v3.0.3

- remove setup.py and switch to pyproject.toml

## v3.0.2

- docs
    - add GNU license.
    - update setup.py classifiers, author name.
    - move changelog to different file.

## v3.0.1

- logout_apps_v0 internally uses POST method instead of DELETE, compatible with square_authentication>=10.0.0.

## v3.0.0

- **breaking change**: new mandatory parameter `app_id` in validate_and_get_payload_from_token_v0.

## v2.5.2

- bugfix in update_user_recovery_methods_v0 (json serializer and optional parameters).

## v2.5.1

- bugfix in method for update_profile_details_v0.

## v2.5.0

- delete_user_v0 now uses post method.
- add update_user_recovery_methods_v0.
- add generate_account_backup_codes_v0.
- add reset_password_and_login_using_backup_code_v0.
- add send_reset_password_email_v0.
- update parameters for update_password_v0.
- add validate_email_verification_code_v0.
- add send_verification_email_v0.
- add update_profile_details_v0.
- add reset_password_and_login_using_reset_email_code_v0.
- add register_login_google_v0.
- dependencies
    - add square_database_structure>=2.5.7.

## v2.4.1

- make profile_photo in update_profile_photo_v0 optional.

## v2.4.0

- add update_profile_photo_v0.

## v2.3.1

- bump to square_commons>=2.0.0.

## v2.3.0

- add logout_apps_v0 and logout_all_v0.

## v2.2.0

- add validate_and_get_payload_from_token_v0.

## v2.1.0

- login_username_v0 now uses post method and has new optional flag assign_app_id_if_missing that defaults to false.
- use make_request_json_output to call api endpoints.

## v2.0.0

- add functions for
    - update_username_v0
    - update_password_v0
    - delete_user_v0
- move data in password related endpoints to request body from params.
- new optional param, app_id in register_username_v0.
- generate_access_token_v0 now only needs refresh token.
- logout_v0 now only needs refresh token.
- update_user_app_ids_v0 now only updates ids for self (user). added access token as input param and removed user_id.
- get_user_app_ids_v0 is now get_user_details_v0 with access token as the only input param.

## v1.0.0

- initial implementation.

