import threading

_user = threading.local()


class CurrentUserMiddleware:
    """
    Middleware para almacenar el usuario autenticado en un hilo local.
    De esta forma se puede acceder en cualquier parte del código.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user if request.user.is_authenticated else None
        response = self.get_response(request)
        return response


def get_current_user():
    """Obtiene el usuario actual desde el hilo local"""
    return getattr(_user, "value", None)
