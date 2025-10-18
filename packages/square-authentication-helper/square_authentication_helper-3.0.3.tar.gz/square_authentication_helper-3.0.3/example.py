from random import randint

from square_authentication_helper import SquareAuthenticationHelper, TokenType

square_authentication_helper_obj = SquareAuthenticationHelper()
username = "temp" + str(randint(1, 2000))
password = "temp"
app_id = 1

# Example: register username
register_username_output = square_authentication_helper_obj.register_username_v0(
    username=username,
    password=password,
    app_id=app_id,
)
print(register_username_output)

# Example: get user details
get_user_app_ids_output = square_authentication_helper_obj.get_user_details_v0(
    access_token=register_username_output["data"]["main"]["access_token"],
)
print(get_user_app_ids_output)

# Example: update user app ids (redundant but will not insert any new data)
update_user_app_ids_output = square_authentication_helper_obj.update_user_app_ids_v0(
    access_token=register_username_output["data"]["main"]["access_token"],
    app_ids_to_add=[app_id],
    app_ids_to_remove=[],
)
print(update_user_app_ids_output)


# Example: login username
login_username_output = square_authentication_helper_obj.login_username_v0(
    username=username,
    password=password,
    app_id=app_id,
    assign_app_id_if_missing=False,
)
print(login_username_output)

# Example: update username
new_username = "temp" + str(randint(1, 2000))
update_username_output = square_authentication_helper_obj.update_username_v0(
    new_username=new_username,
    access_token=login_username_output["data"]["main"]["access_token"],
)
print(update_username_output)

# Example: update password
new_password = "temp_new"
update_password_output = square_authentication_helper_obj.update_password_v0(
    old_password=password,
    new_password=new_password,
    access_token=login_username_output["data"]["main"]["access_token"],
)
print(update_username_output)

# Example: generate access token
generate_access_token_output = (
    square_authentication_helper_obj.generate_access_token_v0(
        refresh_token=login_username_output["data"]["main"]["refresh_token"],
    )
)
print(generate_access_token_output)

# Example: validate access token
validate_access_token_output = (
    square_authentication_helper_obj.validate_and_get_payload_from_token_v0(
        token=generate_access_token_output["data"]["main"]["access_token"],
        token_type=TokenType.access_token,
    )
)
print(validate_access_token_output)

# Example: logout
logout_output = square_authentication_helper_obj.logout_v0(
    refresh_token=login_username_output["data"]["main"]["refresh_token"],
)
print(logout_output)

# Example: logout apps
logout_apps_output = square_authentication_helper_obj.logout_apps_v0(
    access_token=login_username_output["data"]["main"]["access_token"],
    app_ids=[app_id],
)
print(logout_apps_output)

# Example: logout all
logout__all_output = square_authentication_helper_obj.logout_all_v0(
    access_token=login_username_output["data"]["main"]["access_token"],
)
print(logout__all_output)

# Example: delete user
# note: access token can still be used after log out, until it expires.
delete_user_output = square_authentication_helper_obj.delete_user_v0(
    password=new_password,
    access_token=generate_access_token_output["data"]["main"]["access_token"],
)
print(delete_user_output)
