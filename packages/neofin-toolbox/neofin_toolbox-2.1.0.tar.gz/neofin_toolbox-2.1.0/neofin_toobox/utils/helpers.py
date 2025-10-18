from chalice import Response


def make_response(body, request=None, status_code=200, headers={}):
    my_origin = 'http://app.neofin.com.br,https://app.neofin.com.br,https://app.neofin.dev.br,https://sandbox.neofin.com.br,https://internal.neofin.dev.br,https://internal.neofin.com.br'

    if request:
        if 'Origin' in request.headers or 'origin' in request.headers:
            if request.headers["Origin"] or request.headers["origin"]:
                my_origin = request.headers["Origin"]

    default_headers = {
        "Access-Control-Allow-Origin": my_origin,
        "Content-type": "application/json",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "authorization,content-type,x-empcookie",
        "Access-Control-Allow-Methods": "POST,PUT,GET,OPTIONS,DELETE",
    }

    return Response(
        body=body,
        status_code=status_code,
        headers={**default_headers, **headers}
    )

def get_default_origins():
    domain_list = [
        'http://app.finbee.com.br',
        'https://app.finbee.com.br',
        'http://app.neofin.com.br',
        'https://app.neofin.com.br',
        'http://127.0.0.1:8001',
        'http://localhost:3000',
        'http://localhost:3000',
        'http://app.neofin.dev.br',
        'https://app.neofin.dev.br',
        'https://sandbox.neofin.com.br',
        'https://internal.neofin.dev.br',
        'https://internal.neofin.com.br'
    ]
    return domain_list + [f"{domain}/" for domain in domain_list]


def handle_cors_options(app, allowed_origins):
    request = app.current_request
    origin = (
            request.headers.get('origin')
            or request.headers.get('Origin')
            or request.headers.get("Referer")
            or request.headers.get("referer")
    )

    print("ALLOWED ORIGINS: ", allowed_origins)
    print("ORIGIN: ", origin)

    if origin not in allowed_origins:
        return Response(
            body={"error": "CORS origin not allowed"},
            status_code=403,
            headers={"Content-Type": "application/json"}
        )

    headers = {
        "Access-Control-Allow-Methods": "POST,PUT,GET,OPTIONS,DELETE",
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "authorization,content-type,x-empcookie",
        "Access-Control-Max-Age": "6000",
    }

    return Response(
        body={"message": "OK"},
        status_code=200,
        headers=headers
    )