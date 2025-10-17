import typer

from prim_cli.entities.phone_number import PhoneNumber, PhoneNumberRepository

from prim_cli.utils.utils import confirm, format_phone_number, get_authenticated_session, make_request, print_info, print_error

app = typer.Typer()

@app.command("phone")
def phone():
    """Manage your phone number."""
    response = make_request(f"/v1/auth/session")
    if not response or "data" not in response:
        print_error("Failed to get session.")
        return
    phone_id = response["data"]["phoneNumberId"]
    phone_number_repository = PhoneNumberRepository()
    if not phone_id:
        print_info("You do not have a phone number associated with your account.")
        if confirm("Add a phone number?"):
            phone_number = PhoneNumber(user_id=response["data"]["id"])
            phone_number = phone_number_repository.create(phone_number)
            if not phone_number:
                print_error("Failed to add phone number.")
                return
            print_info(f"Phone number: {format_phone_number(phone_number.phone_number)}")
        else:
            return
    else:
        phone_number = phone_number_repository.get()
        if not phone_number:
            print_error("Failed to get phone number.")
            return
        print_info(f"Phone number: {format_phone_number(phone_number.phone_number)}")