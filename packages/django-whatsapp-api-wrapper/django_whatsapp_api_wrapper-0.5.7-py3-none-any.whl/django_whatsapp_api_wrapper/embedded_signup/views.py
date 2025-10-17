from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
import requests
import random

from ..models import WhatsAppCloudApiBusiness, WhatsAppEmbeddedSignUp, MetaApp
from .serializers import WhatsAppCloudApiBusinessSerializer, BusinessCallbackSerializer, EmbeddedSignupEventSerializer
from ..authentication.base import BaseAuthenticatedAPIView


logger = logging.getLogger(__name__)


class EmbeddedSignupCallbackView(BaseAuthenticatedAPIView):

    def post(self, request, *args, **kwargs):
        # Log dos dados recebidos para debugging
        logger.info(
            "EmbeddedSignup callback received - raw data",
            extra={
                'user_id': request.user.id,
                'user_email': getattr(request.user, 'email', None),
                'raw_data': request.data
            }
        )
        
        serializer = EmbeddedSignupEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        payload = serializer.validated_data
        data = payload.get('data', {})
        event = payload.get('event')
        
        # Log dos dados recebidos
        logger.info(
            "EmbeddedSignup callback received",
            extra={
                'user_id': user.id,
                'user_email': getattr(user, 'email', None),
                'event': event,
                'payload': payload
            }
        )
        
        # Salvar dados no modelo WhatsAppCloudApiBusiness apenas se for evento de sucesso
        if event in ['FINISH', 'FINISH_ONLY_WABA', 'FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING']:
            phone_number_id = data.get('phone_number_id', '')
            
            if phone_number_id:
                try:
                    # Buscar WhatsAppCloudApiBusiness pelo phone_number_id
                    business, created = WhatsAppCloudApiBusiness.objects.update_or_create(
                        phone_number_id=phone_number_id,
                        defaults={
                            'waba_id': data.get('waba_id', ''),
                            'business_id': data.get('business_id', ''),
                            'phone_number': data.get('phone_number', ''),
                            'token': data.get('business_token', ''),  # Usando business_token como token
                            'api_version': 'v23.0',  # Versão padrão da API
                        }
                    )
                    
                    action = 'created' if created else 'updated'
                    
                    logger.info(
                        f"WhatsAppCloudApiBusiness {action} successfully",
                        extra={
                            'user_id': user.id,
                            'phone_number_id': phone_number_id,
                            'action': action
                        }
                    )
                except Exception as e:
                    logger.error(
                        "Failed to save WhatsAppCloudApiBusiness or WhatsAppEmbeddedSignUp data",
                        extra={
                            'user_id': user.id,
                            'phone_number_id': phone_number_id,
                            'error': str(e),
                            'payload': payload
                        },
                        exc_info=True
                    )
            else:
                logger.warning(
                    "phone_number_id not provided in callback data",
                    extra={
                        'user_id': user.id,
                        'event': event,
                        'data': data
                    }
                )
        else:
            logger.info(
                "Non-success event received, data not saved",
                extra={
                    'user_id': user.id,
                    'event': event,
                    'phone_number_id': data.get('phone_number_id', '')
                }
            )

        return Response({
            "status": "ok",
            "user_id": user.id,
            "event": event,
            "saved": event in ['FINISH', 'FINISH_ONLY_WABA', 'FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING'],
            "received": payload,
        }, status=status.HTTP_200_OK)


class BusinessCallbackView(BaseAuthenticatedAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BusinessCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data.get('data', {})
        
        phone_number_id = data.get('phone_number_id')
        waba_id = data.get('waba_id')
        business_id = data.get('business_id')
        code = data.get('code')
        meta_app_id = data.get('meta_app_id')
        
        logger.info(
            "Business callback received - raw data",
            extra={
                'user_id': request.user.id,
                'user_email': getattr(request.user, 'email', None),
                'raw_data': request.data,
                'data': data,
                'phone_number_id': phone_number_id,
                'waba_id': waba_id,
                'business_id': business_id,
                'meta_app_id': meta_app_id,
                'code': code
            }
        )
        
        try:
            # Buscar WhatsAppCloudApiBusiness pelo phone_number_id
            business = WhatsAppCloudApiBusiness.objects.get(phone_number_id=phone_number_id)
            
            # Atualizar WhatsAppCloudApiBusiness
            business.code = code
            business.save()
            
            # Buscar MetaApp
            meta_app = MetaApp.objects.get(app_id=meta_app_id)
            
            # ETAPA 1: Trocar código por business token
            business_token = self._exchange_code_for_token(code, meta_app, business.api_version)
            if business_token:
                business.token = business_token
                business.save()
                
                # ETAPA 2: Assinar webhooks na WABA
                webhook_success = self._subscribe_to_webhooks(business_token, business.waba_id, business.api_version)
                
                if webhook_success:
                    # ETAPA 3: Cadastrar número de telefone
                    desired_pin = self._register_phone_number(business_token, business.phone_number_id, business.api_version)
                    
                    if desired_pin:
                        # Salvar o PIN no modelo WhatsAppCloudApiBusiness
                        business.desired_pin = desired_pin
                        business.save()
                        
                        logger.info(
                            "Business callback processed successfully",
                            extra={
                                'user_id': user.id,
                                'business_id': business.id,
                                'embedded_signup_id': embedded_signup.id,
                                'webhook_subscribed': webhook_success,
                                'phone_registered': True
                            }
                        )
                        
                        return Response({
                            "status": "success",
                            "message": "Business callback processed successfully",
                            "business_id": business.id,
                            "webhook_subscribed": webhook_success,
                            "phone_registered": True
                        }, status=status.HTTP_200_OK)
                    else:
                        logger.error("Failed to register phone number")
                        return Response({
                            "status": "error",
                            "message": "Failed to register phone number"
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    logger.error("Failed to subscribe to webhooks")
                    return Response({
                        "status": "error",
                        "message": "Failed to subscribe to webhooks"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error("Failed to exchange code for business token")
                return Response({
                    "status": "error",
                    "message": "Failed to exchange code for business token"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except WhatsAppCloudApiBusiness.DoesNotExist:
            logger.error("WhatsAppCloudApiBusiness not found", extra={'phone_number_id': phone_number_id})
            return Response({
                "status": "error",
                "message": "WhatsApp Business not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except MetaApp.DoesNotExist:
            logger.error("MetaApp not found", extra={'meta_app_id': meta_app_id})
            return Response({
                "status": "error",
                "message": "Meta App not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(
                "Business callback processing failed",
                extra={
                    'user_id': user.id,
                    'error': str(e),
                    'data': data
                },
                exc_info=True
            )
            return Response({
                "status": "error",
                "message": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _exchange_code_for_token(self, code, meta_app, api_version):
        """ETAPA 1: Trocar código por business token"""
        try:
            url = f"https://graph.facebook.com/{api_version}/oauth/access_token"
            params = {
                'client_id': meta_app.app_id,
                'client_secret': meta_app.app_secret,
                'code': code
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            business_token = data.get('access_token')
            
            logger.info("Code exchanged for business token successfully")
            return business_token
            
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            return None

    def _subscribe_to_webhooks(self, business_token, waba_id, api_version):
        """ETAPA 2: Assinar webhooks na WABA"""
        try:
            url = f"https://graph.facebook.com/{api_version}/{waba_id}/subscribed_apps"
            headers = {
                'Authorization': f'Bearer {business_token}'
            }
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            success = data.get('success', False)
            
            if success:
                logger.info("Webhooks subscribed successfully")
            else:
                logger.error("Failed to subscribe to webhooks")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to subscribe to webhooks: {str(e)}")
            return False

    def _register_phone_number(self, business_token, phone_number_id, api_version):
        """ETAPA 3: Cadastrar número de telefone"""
        try:
            # Gerar PIN aleatório de 6 dígitos
            desired_pin = str(random.randint(100000, 999999))
            
            url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/register"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {business_token}'
            }
            data = {
                'messaging_product': 'whatsapp',
                'pin': desired_pin
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            success = result.get('success', False)
            
            if success:
                logger.info("Phone number registered successfully")
                return desired_pin
            else:
                logger.error("Failed to register phone number")
                return None
                
        except Exception as e:
            logger.error(f"Failed to register phone number: {str(e)}")
            return None
