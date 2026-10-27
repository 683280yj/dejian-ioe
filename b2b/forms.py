from django import forms

from .models import Customer, PurchaseOrder, PurchaseOrderLine, WholesaleOrder, WholesaleOrderLine, SupplierStatement


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['code', 'name', 'kind', 'contact_person', 'phone', 'region', 'address',
                  'credit_limit', 'payment_terms_days', 'is_active']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'warehouse', 'expected_date', 'notes']
        widgets = {'expected_date': forms.DateInput(attrs={'type': 'date'})}


class PurchaseOrderLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderLine
        fields = ['product', 'quantity', 'unit_price']


class WholesaleOrderForm(forms.ModelForm):
    class Meta:
        model = WholesaleOrder
        fields = ['customer', 'warehouse', 'notes']


class WholesaleOrderLineForm(forms.ModelForm):
    class Meta:
        model = WholesaleOrderLine
        fields = ['product', 'quantity', 'unit_price']


class SupplierStatementForm(forms.ModelForm):
    class Meta:
        model = SupplierStatement
        fields = ['supplier', 'period_start', 'period_end', 'supplier_amount', 'notes']
        widgets = {'period_start': forms.DateInput(attrs={'type': 'date'}),
                   'period_end': forms.DateInput(attrs={'type': 'date'})}

    def clean(self):
        data = super().clean()
        if data.get('period_start') and data.get('period_end') and data['period_start'] > data['period_end']:
            raise forms.ValidationError('期间开始不能晚于结束')
        return data


class SupplierAmountForm(forms.ModelForm):
    class Meta:
        model = SupplierStatement
        fields = ['supplier_amount', 'notes']


class SettlementForm(forms.Form):
    amount = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0.01, label='金额')
    reference = forms.CharField(max_length=100, required=False, label='凭证号/流水号')
