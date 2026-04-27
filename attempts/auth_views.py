from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from functools import wraps
from .models import User, CompanionRequest


def require_auth(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    import json
    try:
        body = json.loads(request.body)
        email = body.get('email', '').strip()
        password = body.get('password', '').strip()
        display_name = body.get('display_name', '').strip()

        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)

        if len(password) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already in use'}, status=400)

        user = User.objects.create_user(
            email=email,
            password=password,
            display_name=display_name,
            is_active=True,
        )

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'display_name': user.display_name,
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    import json
    try:
        body = json.loads(request.body)
        email = body.get('email', '').strip()
        password = body.get('password', '').strip()

        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)

        user = authenticate(request, username=email, password=password)

        if user is None:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'display_name': user.display_name,
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return JsonResponse({'ok': True}, status=200)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def me(request):
    import json
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method == 'GET':
        return JsonResponse({
            'id': request.user.id,
            'email': request.user.email,
            'display_name': request.user.display_name,
            'companion_visibility': request.user.companion_visibility,
        }, status=200)

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)

            if 'display_name' in body:
                request.user.display_name = body['display_name'].strip()

            if 'companion_visibility' in body:
                request.user.companion_visibility = bool(body['companion_visibility'])

            if 'password' in body and 'current_password' in body:
                current_password = body.get('current_password', '').strip()
                new_password = body.get('password', '').strip()

                if not request.user.check_password(current_password):
                    return JsonResponse({'error': 'Current password is incorrect'}, status=400)

                if len(new_password) < 8:
                    return JsonResponse({'error': 'New password must be at least 8 characters'}, status=400)

                request.user.set_password(new_password)

            request.user.save()

            return JsonResponse({
                'id': request.user.id,
                'email': request.user.email,
                'display_name': request.user.display_name,
                'companion_visibility': request.user.companion_visibility,
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def companions_list(request):
    sent_accepted = CompanionRequest.objects.filter(
        from_user=request.user,
        status='accepted'
    ).values_list('to_user', flat=True)

    received_accepted = CompanionRequest.objects.filter(
        to_user=request.user,
        status='accepted'
    ).values_list('from_user', flat=True)

    accepted_companions = User.objects.filter(
        Q(pk__in=sent_accepted) | Q(pk__in=received_accepted)
    ).values('id', 'email', 'display_name')

    sent_pending = CompanionRequest.objects.filter(
        from_user=request.user,
        status='pending'
    ).select_related('to_user').values(
        'id', 'to_user__id', 'to_user__email', 'to_user__display_name'
    )

    received_pending = CompanionRequest.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user').values(
        'id', 'from_user__id', 'from_user__email', 'from_user__display_name'
    )

    return JsonResponse({
        'accepted': list(accepted_companions),
        'sent_pending': [
            {
                'id': r['id'],
                'user': {
                    'id': r['to_user__id'],
                    'email': r['to_user__email'],
                    'display_name': r['to_user__display_name'],
                }
            }
            for r in sent_pending
        ],
        'received_pending': [
            {
                'id': r['id'],
                'user': {
                    'id': r['from_user__id'],
                    'email': r['from_user__email'],
                    'display_name': r['from_user__display_name'],
                }
            }
            for r in received_pending
        ],
    }, status=200)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def send_companion_request(request):
    import json
    try:
        body = json.loads(request.body)
        email = body.get('email', '').strip()

        if not email:
            return JsonResponse({'error': 'Email required'}, status=400)

        try:
            to_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        if to_user == request.user:
            return JsonResponse({'error': 'Cannot send request to yourself'}, status=400)

        companion_request, created = CompanionRequest.objects.get_or_create(
            from_user=request.user,
            to_user=to_user,
        )

        if not created:
            return JsonResponse({'error': 'Request already exists'}, status=400)

        return JsonResponse({
            'id': companion_request.id,
            'status': companion_request.status,
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def accept_companion(request, pk):
    try:
        companion_request = CompanionRequest.objects.get(pk=pk)

        if companion_request.to_user != request.user:
            return JsonResponse({'error': 'Not authorized'}, status=403)

        companion_request.status = 'accepted'
        companion_request.save()

        return JsonResponse({'status': companion_request.status}, status=200)

    except CompanionRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def reject_companion(request, pk):
    try:
        companion_request = CompanionRequest.objects.get(pk=pk)

        if companion_request.to_user != request.user:
            return JsonResponse({'error': 'Not authorized'}, status=403)

        companion_request.status = 'rejected'
        companion_request.save()

        return JsonResponse({'status': companion_request.status}, status=200)

    except CompanionRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
def remove_companion(request, pk):
    try:
        companion_request = CompanionRequest.objects.get(pk=pk)

        if companion_request.from_user != request.user and companion_request.to_user != request.user:
            return JsonResponse({'error': 'Not authorized'}, status=403)

        companion_request.delete()

        return JsonResponse({'ok': True}, status=200)

    except CompanionRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
