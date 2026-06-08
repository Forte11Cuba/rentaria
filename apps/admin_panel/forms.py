from django import forms
from django.forms import inlineformset_factory
from django.utils.text import slugify

from apps.accounts.models import Account, Operation
from apps.forms.models import FormField, ContractTemplate
from apps.units.models import UnitModel, Unit, PricePlan
from apps.shops.models import Shop
from apps.users.models import User


class ChangeEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        labels = {'email': 'Correo electrónico'}

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Este correo ya está en uso por otro usuario.')
        return email


class ShopSuperadminForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['nombre', 'slug', 'dueno']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dueno'].queryset = User.objects.filter(
            rol='owner', estado='active'
        ).order_by('username')
        self.fields['dueno'].label_from_instance = lambda u: f'{u.username} — {u.email}'
        self.fields['nombre'].label = 'Nombre de la tienda'
        self.fields['slug'].label = 'Slug (URL única)'
        self.fields['dueno'].label = 'Dueño'


class ShopOwnerForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = [
            'nombre', 'slug', 'logo',
            'whatsapp_activo', 'whatsapp_numero',
            'btcpay_activo', 'btcpay_url', 'btcpay_api_key', 'btcpay_store_id', 'btcpay_webhook_secret',
            'public_api',
            'email_from_name', 'email_from_address',
        ]
        labels = {
            'nombre': 'Nombre de la tienda',
            'slug': 'Slug (URL única, ej: mi-tienda)',
            'logo': 'Logo de la tienda',
            'whatsapp_activo': 'Activar botón de WhatsApp',
            'whatsapp_numero': 'Número WhatsApp (con código de país, sin +)',
            'btcpay_activo': 'Activar pago Bitcoin (BTCPay)',
            'btcpay_url': 'BTCPay URL (ej: https://btcpay.mi-servidor.com)',
            'btcpay_api_key': 'BTCPay API Key',
            'btcpay_store_id': 'BTCPay Store ID',
            'btcpay_webhook_secret': 'Webhook Secret (opcional, para seguridad)',
            'public_api': 'Activar API pública del catálogo',
            'email_from_name': 'Nombre del remitente (ej: Bitride)',
            'email_from_address': 'Correo del remitente (ej: reservas@bitride.rent)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['logo'].required = False


class UnitModelForm(forms.ModelForm):
    class Meta:
        model = UnitModel
        fields = ['marca', 'modelo', 'descripcion', 'min_dias_alquiler', 'imagen', 'activo']
        labels = {
            'marca': 'Marca',
            'modelo': 'Modelo',
            'descripcion': 'Descripción',
            'min_dias_alquiler': 'Mínimo de días de alquiler',
            'imagen': 'Imagen',
            'activo': 'Modelo activo (visible para clientes)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = False
        self.fields['imagen'].required = False


class PricePlanForm(forms.ModelForm):
    class Meta:
        model = PricePlan
        fields = ['dias_max', 'precio_dia']
        labels = {
            'dias_max': 'Hasta (días)',
            'precio_dia': 'Precio/día (USD)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dias_max'].required = False


PricePlanFormSet = inlineformset_factory(
    UnitModel, PricePlan,
    form=PricePlanForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['chapa', 'modelo']
        labels = {
            'chapa': 'Chapa / Placa',
            'modelo': 'Modelo',
        }

    def __init__(self, *args, tienda=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tienda is not None:
            self.fields['modelo'].queryset = UnitModel.objects.filter(
                tienda=tienda, activo=True
            ).order_by('marca', 'modelo')


class FormFieldForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = ['etiqueta', 'variable', 'tipo', 'requerido', 'es_email_cliente']
        labels = {
            'etiqueta': 'Etiqueta (texto visible al cliente)',
            'variable': 'Variable (usada en la plantilla del contrato)',
            'tipo': 'Tipo de campo',
            'requerido': 'Campo obligatorio',
            'es_email_cliente': 'Usar como email del cliente (para enviar confirmaciones)',
        }

    def __init__(self, *args, tienda=None, **kwargs):
        self.tienda = tienda
        super().__init__(*args, **kwargs)
        self.fields['variable'].required = False

    def clean_variable(self):
        variable = self.cleaned_data.get('variable', '').strip()
        if not variable:
            etiqueta = self.cleaned_data.get('etiqueta') or self.data.get('etiqueta', '')
            variable = slugify(str(etiqueta)).replace('-', '_')
        return variable

    def clean(self):
        cleaned = super().clean()
        variable = cleaned.get('variable')
        if self.tienda and variable:
            qs = FormField.objects.filter(tienda=self.tienda, variable=variable)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('variable', 'Ya existe un campo con esta variable en la tienda.')
        return cleaned


class ContractTemplateForm(forms.ModelForm):
    class Meta:
        model = ContractTemplate
        fields = ['contenido_md']
        widgets = {
            'contenido_md': forms.Textarea(),
        }


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['nombre', 'moneda']
        labels = {
            'nombre': 'Nombre de la cuenta',
            'moneda': 'Moneda (ej: USD, CUP, EUR)',
        }


class OperationForm(forms.Form):
    TIPO_CHOICES = [('ingreso', 'Ingreso / Beneficio'), ('gasto', 'Gasto / Egreso')]
    tipo = forms.ChoiceField(choices=TIPO_CHOICES, label='Tipo')
    descripcion = forms.CharField(max_length=500, required=False, label='Descripción')
    monto = forms.DecimalField(
        max_digits=14, decimal_places=2, min_value=0,
        label='Monto (positivo)',
    )
    fecha = forms.DateField(
        label='Fecha',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )


class TransferForm(forms.Form):
    cuenta_origen = forms.ModelChoiceField(queryset=Account.objects.none(), label='Cuenta origen')
    monto_origen = forms.DecimalField(
        max_digits=14, decimal_places=2, min_value=0,
        label='Monto a debitar',
    )
    tasa_cambio = forms.DecimalField(
        max_digits=14, decimal_places=6, min_value=0,
        label='Tasa de cambio (unidades destino / unidad origen)',
        initial=1,
    )
    cuenta_destino = forms.ModelChoiceField(queryset=Account.objects.none(), label='Cuenta destino')
    monto_destino = forms.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False,
        label='Monto a acreditar (opcional — se calcula automáticamente)',
    )
    descripcion = forms.CharField(max_length=500, required=False, label='Descripción')
    fecha = forms.DateField(
        label='Fecha',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, tienda=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tienda:
            qs = Account.objects.filter(tienda=tienda, activa=True).order_by('nombre')
            self.fields['cuenta_origen'].queryset = qs
            self.fields['cuenta_destino'].queryset = qs

    def clean(self):
        cleaned = super().clean()
        origen = cleaned.get('cuenta_origen')
        destino = cleaned.get('cuenta_destino')
        if origen and destino and origen == destino:
            raise forms.ValidationError('La cuenta origen y destino deben ser diferentes.')
        monto_origen = cleaned.get('monto_origen')
        tasa = cleaned.get('tasa_cambio')
        if monto_origen is not None and tasa is not None and not cleaned.get('monto_destino'):
            cleaned['monto_destino'] = (monto_origen * tasa).quantize(monto_origen)
        return cleaned
