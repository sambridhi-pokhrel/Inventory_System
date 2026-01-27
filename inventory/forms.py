from django import forms
from .models import Item, Transaction
from django.core.exceptions import ValidationError

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['item', 'transaction_type', 'quantity', 'unit_price', 'notes']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_item'
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_transaction_type'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'id': 'id_quantity'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'id': 'id_unit_price'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this transaction...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add labels and help text
        self.fields['item'].label = 'Select Item'
        self.fields['transaction_type'].label = 'Transaction Type'
        self.fields['quantity'].label = 'Quantity'
        self.fields['unit_price'].label = 'Unit Price ($)'
        self.fields['notes'].label = 'Notes (Optional)'
        
        # Add help text
        self.fields['quantity'].help_text = 'Number of items to buy/sell'
        self.fields['unit_price'].help_text = 'Price per unit'
        
        # Filter items to show only those with stock for sales
        if 'transaction_type' in self.data and self.data['transaction_type'] == 'SALE':
            self.fields['item'].queryset = Item.objects.filter(quantity__gt=0)
    
    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        transaction_type = cleaned_data.get('transaction_type')
        quantity = cleaned_data.get('quantity')
        
        if item and transaction_type == 'SALE' and quantity:
            if item.quantity < quantity:
                raise ValidationError(
                    f"Insufficient stock for {item.name}. Available: {item.quantity}, Requested: {quantity}"
                )
        
        return cleaned_data

class TransactionFilterForm(forms.Form):
    TRANSACTION_CHOICES = [
        ('', 'All Transactions'),
        ('SALE', 'Sales Only'),
        ('PURCHASE', 'Purchases Only'),
    ]
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        required=False,
        empty_label="All Items",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )