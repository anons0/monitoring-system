import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Account
from .serializers import AccountSerializer
from .services import AccountService

logger = logging.getLogger('accounts')

@method_decorator(login_required, name='dispatch')
class AccountViewSet(viewsets.ModelViewSet):
    """ViewSet for managing accounts"""
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start an account client"""
        account = self.get_object()
        try:
            result = AccountService.start_account(account)
            if result:
                return Response({'status': 'started'})
            else:
                return Response({'error': 'Failed to start account'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error starting account {account.id}: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop an account client"""
        account = self.get_object()
        try:
            result = AccountService.stop_account(account)
            if result:
                return Response({'status': 'stopped'})
            else:
                return Response({'error': 'Failed to stop account'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error stopping account {account.id}: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def add_account(request):
    """Add a new account"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            api_id = data.get('api_id')
            api_hash = data.get('api_hash')
            
            if not all([phone_number, api_id, api_hash]):
                return JsonResponse({'error': 'Phone number, API ID, and API Hash are required'}, status=400)
            
            account = AccountService.add_account(phone_number, api_id, api_hash)
            return JsonResponse({
                'id': account.id,
                'phone_number': account.phone_number,
                'status': account.status,
                'requires_login': True
            })
        except Exception as e:
            logger.error(f"Error adding account: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def login_account(request, account_id):
    """Initiate account login process"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
        
    if request.method == 'POST':
        try:
            account = Account.objects.get(id=account_id)
            result = AccountService.initiate_login(account)
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Login code sent to your phone'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Login failed')
                }, status=400)
                
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)
        except Exception as e:
            logger.error(f"Error initiating login for account {account_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def verify_login(request, account_id):
    """Verify login code and complete authentication"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            password = data.get('password')  # Optional 2FA password
            
            if not code:
                return JsonResponse({'error': 'Verification code is required'}, status=400)
            
            account = Account.objects.get(id=account_id)
            result = AccountService.verify_login(account, code, password)
            
            return JsonResponse(result)
            
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account not found'}, status=404)
        except Exception as e:
            logger.error(f"Error verifying login for account {account_id}: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def test_account(request, account_id):
    """Test account connection"""
    try:
        account = Account.objects.get(id=account_id)
        result = AccountService.test_account(account)
        return JsonResponse({'success': result})
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    except Exception as e:
        logger.error(f"Error testing account {account_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)