from django.db import models

class MetaApp(models.Model):
    """
    Modelo para armazenar informações de um Aplicativo Meta
    """
    name = models.CharField(max_length=50)
    app_id = models.CharField(max_length=50)
    app_secret = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class WhatsAppCloudApiBusiness(models.Model):
    """
    Modelo para armazenar informações da conta WhatsApp Business API
    """
    token = models.TextField(
        verbose_name="Token",
        help_text="Token de acesso da API do WhatsApp Business"
    )
    api_version = models.CharField(
        max_length=20,
        verbose_name="API Version",
        help_text="Versão da API"
    )
    phone_number_id = models.CharField(
        max_length=50,
        verbose_name="Phone Number ID",
        help_text="ID do número de telefone da empresa no WhatsApp Business"
    )

    waba_id = models.CharField(
        max_length=50,
        verbose_name="WABA ID",
        help_text="ID da conta WhatsApp Business"
    )
    business_id = models.CharField(
        max_length=50,
        verbose_name="Business Portfolio ID",
        help_text="ID do portfólio de negócios"
    )
    phone_number = models.CharField(
        max_length=20,
        verbose_name="Número de Telefone",
        help_text="Número de telefone da empresa",
        null=True,
        blank=True
    )
    
    verify_token = models.CharField(
        max_length=100,
        verbose_name="Verify Token",
        help_text="Token de verificação do webhook",
        null=True,
        blank=True
    )
    
    code = models.TextField(
        verbose_name="Code",
        help_text="Código retornado pelo Business Callback",
        null=True,
        blank=True
    )
    
    desired_pin = models.CharField(
        max_length=6,
        verbose_name="Desired PIN",
        help_text="PIN de 6 dígitos para verificação em duas etapas do número de telefone da empresa",
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )

    class Meta:
        verbose_name = "WhatsApp Business API"
        verbose_name_plural = "WhatsApp Business APIs"
        ordering = ['-created_at']

    def __str__(self):
        return f"WhatsApp Business - {self.phone_number or self.waba_id}"


class WhatsAppEmbeddedSignUp(models.Model):
    """
    Modelo para armazenar dados do Embedded Signup do WhatsApp
    """
    business = models.ForeignKey(
        WhatsAppCloudApiBusiness,
        on_delete=models.CASCADE,
        related_name='embedded_signups',
        verbose_name="WhatsApp Business"
    )
    code = models.TextField(
        verbose_name="Code",
        help_text="Código retornado pelo Embedded Signup quando o cliente completou o fluxo com sucesso",
        null=True,
        blank=True
    )
    business_token = models.TextField(
        verbose_name="Business Token",
        help_text="Token de negócio do cliente retornado pelo Embedded Signup",
        null=True,
        blank=True
    )
    desired_pin = models.CharField(
        max_length=6,
        verbose_name="Desired PIN",
        help_text="PIN de 6 dígitos para verificação em duas etapas do número de telefone da empresa",
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )

    class Meta:
        verbose_name = "WhatsApp Embedded Signup"
        verbose_name_plural = "WhatsApp Embedded Signups"
        ordering = ['-created_at']

    def __str__(self):
        return f"Embedded Signup - {self.business.phone_number or self.business.waba_id}"
