from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def perfil_necessario(*perfis_permitidos):
    """
    Decorator para controlar acesso a views por perfil de usuário
    (ADMINISTRADOR, GESTOR, ATENDENTE).
    Superusuários do Django possuem acesso total irrestrito.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('secretaria:login')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            perfil = getattr(request.user, 'perfil', None)
            if not perfil or not perfil.ativo:
                messages.error(request, 'Sua conta de usuário está desativada ou não possui perfil atribuído.')
                return redirect('secretaria:login')

            if perfil.perfil in perfis_permitidos:
                return view_func(request, *args, **kwargs)

            messages.warning(request, 'Acesso não autorizado para o seu perfil de usuário.')
            return redirect('secretaria:lista_demandas')

        return _wrapped_view
    return decorator

