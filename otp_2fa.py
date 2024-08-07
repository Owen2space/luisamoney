import requests


def registerotpcontent(code):
    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>2fa Code</title>
        </head>
        <body>
            <div style="text-align: center; font-family: monospace, sans-serif; background-color: #202225; color: #ccc; padding: 20px;border: 1px solid #737373; border-radius: 5px">
                <h1 style="color: #ccc;">Two Factor Authentication</h1>
                <p style="color: #ccc;">Use this code to complete your registration:</p>
                <div style="background-color: #2f3136; padding: 10px; border: 1px solid #737373; border-radius: 5px;">
                    
                    <h3 style="color: #00b972; font-size: 32px;">{code}</h3>
                </div>
                <p style="color: #ccc; ">If you didn't request this code, please ignore this email.</p>
                <p style="color: #ccc; ">&copy; 2023 Diskord</p>
            </div>
        </body>
        </html>
        """


def resetotpcontent(code):
    return f"""
            <!DOCTYPE html>
        <html>
        <head>
            <title>2fa Code</title>
        </head>
        <body>
            <div style="text-align: center; font-family: monospace, sans-serif; background-color: #202225; color: #ccc; padding: 20px;border: 1px solid #737373; border-radius: 5px">
                <h1 style="color: #ccc;">Two Factor Authentication</h1>
                <p style="color: #ccc;">Use this code to reset your password</p>
                <div style="background-color: #2f3136; padding: 10px; border: 1px solid #737373; border-radius: 5px;">
                    
                    <h3 style="color: #00b972; font-size: 32px;">{code}</h3>
                </div>
                <p style="color: #ccc; ">If you didn't request this code, please ignore this email.</p>
                <p style="color: #ccc; ">&copy; 2023 Diskord</p>
            </div>
        </body>
        </html>
    """


def send_otp(otp, email_phone_to):
    url = "https://freemail.maev.lol"
    payload = {
        "api_key": "guest",
        "sender_name": "Luisa Money",
        "subject": "OTP Code for Luisa Money",
        "message": registerotpcontent(otp),
        "message_type": "html",
        "footer": "",
        "receiver_email": email_phone_to,
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return response.json()


def send_otp_reset_password_email(otp, email_phone):
    url = "https://freemail.maev.lol"
    payload = {
        "api_key": "guest",
        "sender_name": "Luisa Money",
        "subject": "OTP Code for Luisa Money",
        "message": resetotpcontent(otp),
        "message_type": "html",
        "footer": "",
        "receiver_email": email_phone,
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

if __name__ == "__main__":
    send_otp("123456", "iannm254@gmail.com")
