from django.urls import path
from .views import EmbeddedSignupCallbackView, BusinessCallbackView

urlpatterns = [
    path('callback/', EmbeddedSignupCallbackView.as_view(), name='embedded_signup_callback'),
    path('business-callback/', BusinessCallbackView.as_view(), name='business_callback'),
]
