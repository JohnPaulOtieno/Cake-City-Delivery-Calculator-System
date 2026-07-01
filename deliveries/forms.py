from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Delivery
from stores.models import Store


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
        label="First Name",
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
        label="Last Name",
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
        label="Email Address",
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Choose a username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class DeliveryForm(forms.ModelForm):
    """Form for creating a new delivery order."""
    
    store = forms.ModelChoiceField(
        queryset=Store.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'store-select'}),
        label="Store",
        help_text="Select the store for this delivery (will be auto-filled with nearest store)"
    )
    
    customer_address = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'customer-address',
            'placeholder': 'Enter customer address in Nairobi...',
            'autocomplete': 'off'
        }),
        label="Customer Address",
        help_text="Enter the delivery destination address"
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+254 7XX XXX XXX',
            'autocomplete': 'tel'
        }),
        label="Customer Phone (Optional)",
        help_text="Phone number for SMS notification (e.g., +254712345678)"
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special delivery instructions...'
        }),
        label="Delivery Notes"
    )
    
    # Hidden fields for coordinates
    customer_latitude = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    customer_longitude = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    distance_km = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    fare_ksh = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    class Meta:
        model = Delivery
        fields = ['store', 'customer_address', 'customer_phone', 'customer_latitude', 
                 'customer_longitude', 'distance_km', 'fare_ksh', 'notes']
    
    def clean_customer_address(self):
        """Validate that address is not empty."""
        address = self.cleaned_data.get('customer_address')
        if not address or not address.strip():
            raise forms.ValidationError("Please enter a valid address.")
        return address
    
    def clean_fare_ksh(self):
        """Ensure fare was calculated."""
        fare = self.cleaned_data.get('fare_ksh')
        if fare is None or fare <= 0:
            raise forms.ValidationError("Fare calculation failed. Please check the address.")
        return fare
    
    def clean_distance_km(self):
        """Ensure distance was calculated."""
        distance = self.cleaned_data.get('distance_km')
        if distance is None or distance <= 0:
            raise forms.ValidationError("Distance calculation failed. Please check the address.")
        return distance


class OrderHistoryFilterForm(forms.Form):
    """Form for filtering delivery order history."""
    
    DATE_RANGE_CHOICES = [
        ('all', 'All Time'),
        ('today', 'Today'),
        ('week', 'Last 7 Days'),
        ('month', 'Last 30 Days'),
        ('custom', 'Custom Range'),
    ]
    
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        initial='month',
        widget=forms.RadioSelect(),
        label="Date Range"
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="From"
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="To"
    )
    
    store = forms.ModelChoiceField(
        queryset=Store.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Filter by Store",
        empty_label="All Stores"
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Delivery.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Status"
    )
